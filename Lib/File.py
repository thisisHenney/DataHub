#!/usr/bin/env python3
# -*- coding:utf8 -*-
from collections import deque
from copy import deepcopy
from datetime import datetime, timedelta
import glob
import os
import fnmatch
import shutil
import threading
import time
import json
from pathlib import Path
import numpy as np

from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPolyData
from vtkmodules.vtkIOLegacy import vtkDataSetReader

from Lib.Json.JsonRW import JsonRW
from PySide6.QtCore import QThread, Signal
from Lib.Converter.vtk_json_converter import VtkJsonConverter, CompanyType

SEND_PINTEL_MERGED = 'PVX-V30/PA-7F000001/POT/CROWD/CROWD_MERGED'
SEND_KETI_CONGESTION = 'crowd_congestion'


_writer_queue = deque()
_writer_event = threading.Event()
_writer_lock = threading.Lock()


class FileWriterThread(QThread):
    def __init__(self):
        super().__init__()
        self.is_running = True

    def stop(self):
        self.is_running = False
        _writer_event.set()

    def run(self):
        from vtkmodules.vtkIOLegacy import vtkDataSetWriter
        while self.is_running:
            try:
                with _writer_lock:
                    item = _writer_queue.popleft() if _writer_queue else None

                if item is None:
                    _writer_event.wait(timeout=0.5)
                    _writer_event.clear()
                    continue

                kind, path, payload = item
                if kind == 'json_compressed':
                    payload.save_compressed_json(path)
                elif kind == 'json':
                    payload.save(path)
                elif kind == 'vtk':
                    writer = vtkDataSetWriter()
                    writer.SetFileName(str(Path(path).absolute()))
                    writer.SetInputData(payload)
                    writer.SetFileTypeToBinary()
                    writer.Write()

                if len(_writer_queue) >= 50:
                    print(f'[Writer] queue length {len(_writer_queue)}')

            except Exception as e:
                print("[Writer Notice]: " + str(e))


def _enqueue_write(kind, path, payload):
    with _writer_lock:
        _writer_queue.append((kind, path, payload))
    _writer_event.set()


def get_writer_queue_size():
    with _writer_lock:
        return len(_writer_queue)


class FileSaverThread(QThread):
    finished = Signal(str)  # 저장 완료 시 메시지 전달

    def __init__(self, company_type: CompanyType, vtk_data_dict, vtk_data_lock=None):
        super().__init__()
        self.converter = VtkJsonConverter()
        self.CompanyType = company_type

        self.stack = deque()
        self.is_running = True
        self.vtk_data_dict = vtk_data_dict
        self.vtk_data_lock = vtk_data_lock or threading.Lock()
        self._event = threading.Event()

    def notify(self):
        self._event.set()

    def stop(self):
        self.is_running = False
        self._event.set()

    def run(self):
        while self.is_running:
            try:
                if self.stack:
                    filepath, filename, message = self.stack.popleft()

                    json_data = JsonRW()
                    json_data.load(message)
                    if self.CompanyType == CompanyType.Vueron or self.CompanyType == CompanyType.Pintel:
                        _enqueue_write('json_compressed', filepath/(filename + '.json'), json_data)
                    else:
                        _enqueue_write('json', filepath / (filename + '.json'), json_data)

                    self.converter.set_data_company(self.CompanyType)
                    valid = self.converter.load_array_from_json_string(message)
                    if isinstance(valid, str):
                        print(valid)
                        continue
                    vtk_result = self.converter.make_vtk()
                    with self.vtk_data_lock:
                        self.vtk_data_dict[filename] = vtk_result

                    _enqueue_write('vtk', filepath/'VTK'/(filename + '.vtk'), vtk_result)
                    if len(self.stack) >= 10:
                        print(self.CompanyType.name, "stack length", len(self.stack))
                else:
                    self._event.wait(timeout=0.5)
                    self._event.clear()

            except Exception as e:
                print("[Notice]: " + str(e))


class FileMergingThread(QThread):
    merge_info = Signal(str)  # merge 상태 정보를 UI로 전달

    def __init__(self, parent, vtk_data_dict_pintel: dict[str, vtkImageData],
                 vtk_data_dict_keti: dict[str, vtkPolyData],
                 vtk_data_dict_vueron: dict[str, vtkPolyData],
                 target_time, chunk_size, app_info,
                 pintel_lock=None, keti_lock=None, vueron_lock=None):
        super().__init__()

        self.parent = parent

        self.converter = VtkJsonConverter()
        self.vtk_data_dict_pintel = vtk_data_dict_pintel
        self.vtk_data_dict_keti = vtk_data_dict_keti
        self.vtk_data_dict_vueron = vtk_data_dict_vueron

        self.pintel_lock = pintel_lock or threading.Lock()
        self.keti_lock = keti_lock or threading.Lock()
        self.vueron_lock = vueron_lock or threading.Lock()

        self.target_time = target_time
        self.chunk_size = chunk_size
        self.merging_time = 2.0

        self.app_info = app_info

        self.count_limes = 0
        self._stopped = False

    def stop(self):
        self._stopped = True

    def run(self):
        if self._stopped:
            return
        self.run_merge()

    def run_merge(self, merge_limit_milli_sec=60000):
        pintel_data_list = []

        keti_data = None

        vueron_data_list = []

        with self.pintel_lock:
            pintel_filename_list = list(self.vtk_data_dict_pintel.keys())
        with self.keti_lock:
            keti_filename_list = list(self.vtk_data_dict_keti.keys())
        with self.vueron_lock:
            vueron_filename_list = list(self.vtk_data_dict_vueron.keys())

        pintel_used_keys = set()
        keti_used_key = None
        vueron_used_keys = set()

        if pintel_filename_list:
            arr = np.array([p.split('_') for p in pintel_filename_list], dtype=int)
            times = arr[:, 2]
            dt_array = self.timestamp_to_dt(times)

            valid_mask = dt_array < merge_limit_milli_sec
            valid_idxs = np.where(valid_mask)[0]
            if valid_idxs.size > 0:
                valid_ids = arr[valid_idxs, 0]
                unique_ids = np.unique(valid_ids)
                with self.pintel_lock:
                    for s_id in unique_ids:
                        sid_mask = valid_ids == s_id
                        sid_idxs = valid_idxs[sid_mask]
                        min_idx = sid_idxs[np.argmin(dt_array[sid_idxs])]
                        key = pintel_filename_list[min_idx]
                        if key in self.vtk_data_dict_pintel:
                            pintel_data_list.append(self.vtk_data_dict_pintel[key])
                            pintel_used_keys.add(key)

            expired_keys = {pintel_filename_list[idx] for idx in np.where(dt_array > merge_limit_milli_sec)[0]}
            keys_to_delete = pintel_used_keys | expired_keys
            if keys_to_delete:
                with self.pintel_lock:
                    for key in keys_to_delete:
                        self.vtk_data_dict_pintel.pop(key, None)

        if keti_filename_list:
            arr = np.array([p.split('_') for p in keti_filename_list], dtype=int)
            times = arr[:, 2]
            dt_array = self.timestamp_to_dt(times)
            idxs = np.where(dt_array < merge_limit_milli_sec)[0]
            if idxs.size > 0:
                min_idx = idxs[np.argmin(dt_array[idxs])]
                keti_used_key = keti_filename_list[min_idx]
                with self.keti_lock:
                    if keti_used_key in self.vtk_data_dict_keti:
                        keti_data = self.vtk_data_dict_keti[keti_used_key]

            expired_keys = {keti_filename_list[idx] for idx in np.where(dt_array > merge_limit_milli_sec)[0]}
            keys_to_delete = expired_keys | ({keti_used_key} if keti_used_key else set())
            if keys_to_delete:
                with self.keti_lock:
                    for key in keys_to_delete:
                        self.vtk_data_dict_keti.pop(key, None)

        if vueron_filename_list:
            arr = np.array([p.split('_') for p in vueron_filename_list], dtype=int)
            times = arr[:, 2]
            dt_array = self.timestamp_to_dt(times)

            for s_id in (1, 2):
                c1 = arr[:, 0] == s_id
                c2 = dt_array < merge_limit_milli_sec
                idxs = np.where(np.logical_and(c1, c2))[0]

                if not idxs.size > 0:
                    continue

                min_idx = idxs[np.argmin(dt_array[idxs])]
                key = vueron_filename_list[min_idx]
                with self.vueron_lock:
                    if key in self.vtk_data_dict_vueron:
                        vueron_data_list.append(self.vtk_data_dict_vueron[key])
                        vueron_used_keys.add(key)

            expired_keys = {vueron_filename_list[idx] for idx in np.where(dt_array > merge_limit_milli_sec)[0]}
            keys_to_delete = vueron_used_keys | expired_keys
            if keys_to_delete:
                with self.vueron_lock:
                    for key in keys_to_delete:
                        self.vtk_data_dict_vueron.pop(key, None)

        has_pintel = len(pintel_data_list) > 0
        has_keti = keti_data is not None
        has_vueron = len(vueron_data_list) > 0

        if not has_pintel and not has_keti and not has_vueron:
            return

        reader = vtkDataSetReader()
        reader.SetFileName(str(self.app_info.app_path /'Lib/Converter/grid.vtk'))
        reader.Update()
        base_grid = reader.GetOutput()
        merged_grid = self.converter.merge_vtk_data_in_grid(
            base_grid, pintel_data=pintel_data_list,
            vueron_data=vueron_data_list,
            keti_data=keti_data)
        merged_timestamp = self.target_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        merged_filename = self.target_time.strftime('%Y%m%d_%H%M%S%f')[:-3]

        now = datetime.now()
        delay_sec = (now - self.target_time).total_seconds()
        sources = []
        if has_pintel:
            sources.append(f"P({len(pintel_data_list)})")
        if has_keti:
            sources.append("K")
        if has_vueron:
            sources.append(f"V({len(vueron_data_list)})")
        info = f"[{now.strftime('%H:%M:%S')}] Merge: {'+'.join(sources)} | target: {self.target_time.strftime('%H:%M:%S.%f')[:-3]} | delay: {delay_sec:.1f}s"
        self.merge_info.emit(info)
        dict_for_json = self.converter.make_json_dict_for_keti(merged_timestamp)
        json_data = JsonRW()
        json_data._buffer = dict_for_json
        json_data.save_compressed_json(self.app_info.keti_path/f'Send/{merged_filename}.json')
        self.converter.write_vtk_file(self.app_info.keti_path/f'Send/VTK/{merged_filename}.vtk')

        # KETI로 전달할 데이터
        self.parent.client_keti.send_message(SEND_KETI_CONGESTION, json_data.get_buffer())

        # LIMES에 전달할 데이터(PINTEL mqtt 포트 이용)
        self.count_limes += 1
        self.parent.client_pintel.send_message(SEND_PINTEL_MERGED, json_data.get_buffer())

        # [8eight] Binary 파일 생성
        if self.parent.app_info.on_point_data == 0:
            self.parent.app_info.on_point_data = 1
            self.converter.merge_vtk_data_in_points(
                base_grid, pintel_data=pintel_data_list,
                vueron_data=vueron_data_list,
                keti_data=keti_data,
                merged_grid=merged_grid)
            if self.converter.array.shape[0] > 0:
                point_file_name = self.app_info.e8ight_path/f'Send/{merged_filename}.e8b'
                self.converter.write_binary_file_for_e8(point_file_name)

            self.parent.app_info.on_point_data = 2

    def timestamp_to_dt(self, int_time_arr):
        times = int_time_arr
        hours = times // 10000000
        minute = (times // 100000) % 100
        m_seconds = times % 100000
        total_m_seconds = hours * 3600000 + minute * 60000 + m_seconds
        self.target_time: datetime
        target_m_seconds = (self.target_time.hour * 3600000
                            + self.target_time.minute * 60000
                            + self.target_time.second * 1000
                            + self.target_time.microsecond // 1000)
        dt_array = np.abs(total_m_seconds - target_m_seconds)
        return dt_array

def to_absolute_path(path_str: str) -> Path:
    # 위치가 명확하지 않으니 실제 경로가 맞는지 확인할 것
    return Path(path_str).expanduser().resolve()

def is_opened(file_name):
    try:
        with open(file_name, 'r+') as file:
            file.close()
        return False
    except IOError:
        return True


def is_link(file_name):
    return Path(file_name).is_symlink()


def is_dir(file_name):
    return Path(file_name).is_dir() and Path(file_name).exists()


def is_dir_empty(file_name):
    return not find_all(file_name)


def is_file(file_name):
    return Path(file_name).is_file()


def get_temporary_path():
    import tempfile
    return tempfile.gettempdir()


def get_file_size(file_name):
    return os.stat(file_name).st_size


def get_file_time(file_name, mode='create'):
    from datetime import datetime
    get_time = 0
    if mode == 'access':
        get_time = os.stat(file_name).st_atime
    elif mode == 'modify':
        get_time = os.stat(file_name).st_mtime
    else:   # mode == 'create':
        get_time = os.stat(file_name).st_ctime
    result_time = datetime.fromtimestamp(get_time)
    # time.year, time.month, time.day
    # time.hour, time.minute, time.second, time.microsecond
    return result_time


def read_file(file_name):
    data = ''
    if Path(file_name).is_file():
        with open(file_name, 'r') as f:
            data = f.read()
    return data


def read_file_all_lines(file_name):
    read_data = []
    if Path(file_name).is_file():
        with open(file_name, 'r') as f:
            read_data = f.readlines()
    return read_data


def read_file_lines(file_name, start=0, length=0, remove_return_line=True):
    read_data = []
    if os.path.isfile(file_name):
        with open(file_name, 'r') as f:
            read_data = f.readlines()

    num = len(read_data)
    last = num
    if start >= num:
        return []
    if start < 0:
        start = num + start

    if length > 0:
        last = start + length
        if last >= num:
            last = num
    read_data = read_data[start:last]

    if remove_return_line:
        changed_read_data = []
        for dd in read_data:
            changed_read_data.append(dd.replace('\n', ''))
        return changed_read_data
    return read_data


def write_file(file_name, data):
    with open(file_name, 'w') as f:
        f.write(data)
    return True


def write_list_file(file_name, data):
    with open(file_name, 'w') as f:
        for d in data:
            f.write(d)
    return True


def append_file(file_name, data, add_return=False):
    with open(file_name, 'a') as f:
        if add_return:
            f.write('\n')
        f.write(data)
    return True


def split_file_path(file_name):
    split_data = os.path.split(file_name)
    return split_data


def get_parent_dir(file_name):
    result = ''
    if is_dir(file_name):
        result = to_absolute_path(file_name).parent
    else:
        result = to_absolute_path(file_name).parent.parent
    return str(result)


def get_current_dir(file_name):
    result = ''
    if is_dir(file_name):
        result = to_absolute_path(file_name)
    else:
        result = to_absolute_path(file_name).parent
    return str(result)


def get_file_path(file_name, upper=-1): # path/name.ext > path
    if upper <= 0:
        parent_path = os.path.split(file_name)
        path_name = get_file_path(parent_path[0], upper + 1)
        if upper == 0:
            path_name = file_name
        elif len(path_name) <= (-upper):
            path_name = './'    # before '/'
    else:
        path_name = os.path.dirname(file_name)
    return path_name


def get_file_name_ext(file_name):       # path/name.ext > name.ext
    file_name_ext = os.path.basename(file_name)
    return file_name_ext


def get_file_name(file_name):       # path/name.ext > name
    file_name_ext = os.path.basename(file_name)
    name = os.path.splitext(file_name_ext)
    return name[0]


def get_file_ext(file_name):        # path/name.ext (ext, EXT) > ext (ext, ext)
    file_name = os.path.splitext(file_name)
    ext = file_name[1].replace('.', '')
    return ext.lower()


def get_drive_name(file):   # not yet
    result = os.path.splitdrive(file)   # if Windows
    return result[0]


def find_dir(path='.', option='*', recursive=True, include_path=True, sorting=True):
    path = to_absolute_path(path)

    count_dirs = 0
    found_dirs = []
    for full_path, sub_path, file_name in os.walk(path):
        for ff in fnmatch.filter(sub_path, option):
            if include_path:
                ff = str(Path(full_path).joinpath(ff))
                count_dirs += 1
            found_dirs.append(ff)
        if not recursive:
            if sorting:
                found_dirs.sort()
            return found_dirs
    if sorting:
        found_dirs.sort()
    return found_dirs


def find_files(path='.', option='*', recursive=True, include_path=True, sorting=True):
    path = to_absolute_path(path)

    count_files = 0
    found_files = []
    for full_path, sub_path, file_name in os.walk(path):
        for ff in fnmatch.filter(file_name, option):
            if include_path:
                ff = str(Path(full_path).joinpath(ff))
            found_files.append(ff)
            count_files += 1
        if not recursive:
            if sorting:
                found_files.sort()
            return found_files
    if sorting:
        found_files.sort()
    return found_files


def find_all(path='.', option='*', recursive=True, include_path=True, sorting=True):
    count_dirs = 0
    count_files = 0
    found_items = []
    path = to_absolute_path(path)

    for full_path, sub_path, file_name in os.walk(path):
        # Dir
        for ff in fnmatch.filter(sub_path, option):
            if include_path:
                ff = str(Path(full_path).joinpath(ff))
            found_items.append(ff)
            count_dirs += 1
        # File
        for ff in fnmatch.filter(file_name, option):
            if include_path:
                ff = str(Path(full_path).joinpath(ff))
            found_items.append(ff)
            count_files += 1
        # sub dir
        if not recursive:
            if sorting:
                found_items.sort()
            return found_items
    if sorting:
        found_items.sort()
    return found_items


def check_file_ext(file_ext, names):
    if not isinstance(names, list | tuple):
        return False

    for dd in names:
        if dd == file_ext:
            return True
    return False


def make_dir(path, exist_ok=True):
    path = to_absolute_path(path)
    Path(path).mkdir(parents=True, exist_ok=exist_ok)


def delete_files(files):
    if not isinstance(files, list):
        files = [files]

    for f in files:
        f = to_absolute_path(f)
        if f and Path(f).is_file():
            os.remove(f)


def delete_dir(path):
    path = to_absolute_path(path)

    if not path:
        return
    if path == '/' or path == '//':
        return

    shutil.rmtree(path, ignore_errors=True)


#  함수 다시 확인 하기
def copy_files(src_dir, dest_dir, pattern='*'):
    src_dir = to_absolute_path(src_dir)
    dest_dir = to_absolute_path(dest_dir)

    for root, _, files in os.walk(src_dir):
        for file_name in files:
            if fnmatch.fnmatch(file_name, pattern):
                src_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(root, src_dir)
                dest_path = os.path.join(dest_dir, rel_path)

                if not os.path.exists(dest_path):
                    os.makedirs(dest_path, exist_ok=True)

                shutil.copy2(src_path, dest_path)

def move_files(src_dir, dest_dir, pattern='*'):
    src_dir = to_absolute_path(src_dir)
    dest_dir = to_absolute_path(dest_dir)

    for root, _, files in os.walk(src_dir):
        for file_name in files:
            if fnmatch.fnmatch(file_name, pattern):
                src_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(root, src_dir)
                dest_path = os.path.join(dest_dir, rel_path)

                if not os.path.exists(dest_path):
                    os.makedirs(dest_path, exist_ok=True)

                shutil.move(src_path, dest_path)


def copy_file2(src, obj):
    src = to_absolute_path(src)
    obj = to_absolute_path(obj)

    fil_name_ext = get_file_name_ext(src)
    obj_file = Path(obj) / fil_name_ext
    shutil.copy2(src, obj_file)


def copy_dir(src, obj):
    src = to_absolute_path(src)
    obj = to_absolute_path(obj)

    shutil.copytree(src, obj)


def create_web_link_file(filename:str, url: str, path:str='.'):
    if not url.startswith("http"):
        raise ValueError("유효한 웹 주소를 입력하세요. (http 또는 https로 시작해야 합니다.)")

    if not filename.endswith(".url"):
        filename += ".url"

    full_path = os.path.join(path, filename)

    with open(full_path, "w", encoding="utf-8") as file:
        file.write(f"[InternetShortcut]\nURL={url}\n")

    return full_path
