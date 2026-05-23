#!/usr/bin/env python3
# -*- coding:utf8 -*-
import traceback
from collections import deque
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

import vtk
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPolyData
from vtkmodules.vtkIOLegacy import vtkDataSetReader

from Lib.Json.JsonRW import JsonRW
from PySide6.QtCore import QThread, Signal
from Lib.Converter.vtk_json_converter import VtkJsonConverter, CompanyType

SEND_PINTEL_MERGED = 'PVX-V30/PA-7F000001/POT/CROWD/CROWD_MERGED'
SEND_KETI_CONGESTION = 'crowd_congestion'

_DAY_MILLI_SEC = 86_400_000

_writer_queue = deque()
_writer_event = threading.Event()
_writer_lock = threading.Lock()

# writer 큐가 SOFT_CAP을 넘어가면 saver가 잠시 대기 (backpressure)
# HARD_WAIT_SEC 초과 시엔 데이터 손실 방지를 위해 강제로 enqueue
_WRITER_QUEUE_SOFT_CAP = 2000
_WRITER_QUEUE_HARD_WAIT_SEC = 2.0

_on_point_data_lock = threading.Lock()


def _deep_copy_vtk(data):
    """vtk 객체를 thread-safe하게 분리. None이면 None 반환."""
    if data is None:
        return None
    copy = data.NewInstance()
    copy.DeepCopy(data)
    return copy


class FileWriterThread(QThread):
    def __init__(self):
        super().__init__()
        self.is_running = True
        self._last_warn_time = 0.0

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
                    tmp_path = str(Path(path).absolute()) + '.tmp'
                    writer = vtkDataSetWriter()
                    writer.SetFileName(tmp_path)
                    writer.SetInputData(payload)
                    writer.SetFileTypeToBinary()
                    writer.Write()
                    try:
                        os.replace(tmp_path, str(Path(path).absolute()))
                    except OSError:
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass
                        raise

                qlen = len(_writer_queue)
                if qlen >= 50:
                    now = time.monotonic()
                    if now - self._last_warn_time >= 10.0:
                        print(f'[Writer] queue length {qlen}')
                        self._last_warn_time = now

            except Exception:
                print("[Writer Notice]:")
                traceback.print_exc()

        # stop 후 남은 큐를 best-effort로 flush
        while True:
            with _writer_lock:
                item = _writer_queue.popleft() if _writer_queue else None
            if item is None:
                break
            try:
                kind, path, payload = item
                if kind == 'json_compressed':
                    payload.save_compressed_json(path)
                elif kind == 'json':
                    payload.save(path)
                elif kind == 'vtk':
                    tmp_path = str(Path(path).absolute()) + '.tmp'
                    writer = vtkDataSetWriter()
                    writer.SetFileName(tmp_path)
                    writer.SetInputData(payload)
                    writer.SetFileTypeToBinary()
                    writer.Write()
                    try:
                        os.replace(tmp_path, str(Path(path).absolute()))
                    except OSError:
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass
            except Exception:
                traceback.print_exc()


def _enqueue_write(kind, path, payload):
    # backpressure: writer가 디스크 I/O로 못 따라잡으면 saver를 잠시 대기시켜
    # 큐가 무한히 커지는 것을 방지. 단, HARD_WAIT 초과 시엔 데이터 손실 방지를
    # 위해 강제로 append (writer가 죽었거나 영구히 막혔을 경우 대비).
    waited = 0.0
    while waited < _WRITER_QUEUE_HARD_WAIT_SEC:
        with _writer_lock:
            if len(_writer_queue) < _WRITER_QUEUE_SOFT_CAP:
                _writer_queue.append((kind, path, payload))
                _writer_event.set()
                return
        time.sleep(0.05)
        waited += 0.05
    with _writer_lock:
        _writer_queue.append((kind, path, payload))
    _writer_event.set()


def get_writer_queue_size():
    with _writer_lock:
        return len(_writer_queue)


def clear_writer_queue():
    with _writer_lock:
        _writer_queue.clear()


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
        self.dual_path_base = None   # None=OFF, Path=ON → received_data/received_data_YYYYMMDD_HHMMSS
        self._last_warn_time = 0.0

    def notify(self):
        self._event.set()

    def stop(self):
        self.is_running = False
        self._event.set()

    def run(self):
        while self.is_running:
            try:
                if self.stack:
                    filepath, filename, json_data = self.stack.popleft()

                    if isinstance(json_data, (str, bytes, bytearray)):
                        message = json_data
                        json_data = JsonRW()
                        if not json_data.load(message):
                            continue

                    # vtk 변환 + dict 등록을 json enqueue보다 먼저 수행.
                    # _enqueue_write 가 backpressure 로 blocking 되면 그 동안 merge 에서
                    # vtk_data_dict 를 못 읽어 빈 merge 가 발생하는 것을 방지.
                    self.converter.set_data_company(self.CompanyType)
                    valid = self.converter.load_array_from_reader(json_data)
                    if isinstance(valid, str):
                        print(valid)
                        continue
                    if self.converter.array.size == 0:
                        continue
                    vtk_result = self.converter.make_vtk()
                    # make_vtk() 이후엔 self.array(파싱된 numpy 캐시)는 더 이상 쓰이지 않음.
                    # 즉시 해제하여 saver 스레드 40개+가 잡고 있는 메모리를 줄임.
                    self.converter.array = np.array([])
                    with self.vtk_data_lock:
                        self.vtk_data_dict[filename] = vtk_result

                    # dict 등록 후에 I/O 큐잉 (blocking 돼도 merge 에는 영향 없음)
                    if self.CompanyType == CompanyType.Vueron or self.CompanyType == CompanyType.Pintel:
                        _enqueue_write('json_compressed', filepath/(filename + '.json'), json_data)
                    else:
                        _enqueue_write('json', filepath / (filename + '.json'), json_data)

                    # writer 쪽에는 deep copy를 보내야 merger와 race 없이 안전하게 .Write() 가능
                    vtk_for_write = _deep_copy_vtk(vtk_result)
                    _enqueue_write('vtk', filepath/'VTK'/(filename + '.vtk'), vtk_for_write)

                    # dual 저장 (동시 저장 버튼 ON 시)
                    dual = self.dual_path_base
                    if dual is not None:
                        try:
                            dual_filepath = dual / filepath.name
                            dual_filepath.mkdir(parents=True, exist_ok=True)
                            (dual_filepath / 'VTK').mkdir(parents=True, exist_ok=True)
                            if self.CompanyType in (CompanyType.Vueron, CompanyType.Pintel):
                                _enqueue_write('json_compressed', dual_filepath / (filename + '.json'), json_data)
                            else:
                                _enqueue_write('json', dual_filepath / (filename + '.json'), json_data)
                            vtk_for_dual = _deep_copy_vtk(vtk_result)
                            _enqueue_write('vtk', dual_filepath / 'VTK' / (filename + '.vtk'), vtk_for_dual)
                        except Exception:
                            traceback.print_exc()

                    slen = len(self.stack)
                    if slen >= 10:
                        now = time.monotonic()
                        if now - self._last_warn_time >= 10.0:
                            print(self.CompanyType.name, "stack length", slen)
                            self._last_warn_time = now
                else:
                    self._event.wait(timeout=0.5)
                    self._event.clear()

            except Exception:
                print("[Saver Notice]:")
                traceback.print_exc()

        # stop 후 남은 stack은 buffer만 빠르게 write queue로 넘김 (vtk 변환은 생략)
        while self.stack:
            try:
                filepath, filename, json_data = self.stack.popleft()
                if isinstance(json_data, (str, bytes, bytearray)):
                    message = json_data
                    json_data = JsonRW()
                    if not json_data.load(message):
                        continue
                if self.CompanyType == CompanyType.Vueron or self.CompanyType == CompanyType.Pintel:
                    _enqueue_write('json_compressed', filepath/(filename + '.json'), json_data)
                else:
                    _enqueue_write('json', filepath / (filename + '.json'), json_data)
            except Exception:
                traceback.print_exc()


class FileMergingThread(QThread):
    merge_info = Signal(str)  # merge 상태 정보를 UI로 전달

    _base_grid_cache = None
    _base_grid_cache_lock = threading.Lock()

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

        # target_time이 datetime 이외 값으로 들어와도 run 진입 시 검사함
        self.target_time = target_time if isinstance(target_time, datetime) else datetime.now()
        self.chunk_size = chunk_size
        self.merging_time = 2.0

        self.app_info = app_info

        self._stopped = False

    def stop(self):
        self._stopped = True

    def run(self):
        if self._stopped:
            return
        if not isinstance(self.target_time, datetime):
            self.target_time = datetime.now()
        try:
            self.run_merge()
        except Exception:
            print("[Merge Notice]:")
            traceback.print_exc()

    def _load_base_grid(self):
        with FileMergingThread._base_grid_cache_lock:
            if FileMergingThread._base_grid_cache is None:
                reader = vtkDataSetReader()
                reader.SetFileName(str(self.app_info.app_path / 'Lib/Converter/grid.vtk'))
                reader.Update()
                FileMergingThread._base_grid_cache = reader.GetOutput()
            # merge_vtk_data_in_grid mutates the grid in-place, so each thread needs its own copy
            copy = vtkImageData()
            copy.DeepCopy(FileMergingThread._base_grid_cache)
            return copy

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

        if self._stopped:
            return

        # select+pop을 단일 락 구간에서 처리하여 다른 merge 스레드와 동일 데이터 중복 송신 방지
        arr = self._safe_parse_filenames(pintel_filename_list)
        if arr is not None:
            times = arr[:, 2]
            dt_array = self.timestamp_to_dt(times)

            valid_mask = dt_array < merge_limit_milli_sec
            valid_idxs = np.where(valid_mask)[0]
            expired_keys = [pintel_filename_list[idx] for idx in np.where(dt_array > merge_limit_milli_sec)[0]]

            with self.pintel_lock:
                if valid_idxs.size > 0:
                    valid_ids = arr[valid_idxs, 0]
                    unique_ids = np.unique(valid_ids)
                    for s_id in unique_ids:
                        sid_mask = valid_ids == s_id
                        sid_idxs = valid_idxs[sid_mask]
                        min_idx = sid_idxs[np.argmin(dt_array[sid_idxs])]
                        key = pintel_filename_list[min_idx]
                        data = self.vtk_data_dict_pintel.pop(key, None)
                        if data is not None:
                            pintel_data_list.append(data)
                for key in expired_keys:
                    self.vtk_data_dict_pintel.pop(key, None)

        if self._stopped:
            return

        arr = self._safe_parse_filenames(keti_filename_list)
        if arr is not None:
            times = arr[:, 2]
            dt_array = self.timestamp_to_dt(times)
            valid_idxs = np.where(dt_array < merge_limit_milli_sec)[0]
            expired_keys = [keti_filename_list[idx] for idx in np.where(dt_array > merge_limit_milli_sec)[0]]

            with self.keti_lock:
                if valid_idxs.size > 0:
                    min_idx = valid_idxs[np.argmin(dt_array[valid_idxs])]
                    keti_data = self.vtk_data_dict_keti.pop(keti_filename_list[min_idx], None)
                for key in expired_keys:
                    self.vtk_data_dict_keti.pop(key, None)

        if self._stopped:
            return

        arr = self._safe_parse_filenames(vueron_filename_list)
        if arr is not None:
            times = arr[:, 2]
            dt_array = self.timestamp_to_dt(times)
            expired_keys = [vueron_filename_list[idx] for idx in np.where(dt_array > merge_limit_milli_sec)[0]]

            with self.vueron_lock:
                for s_id in (1, 2):
                    c1 = arr[:, 0] == s_id
                    c2 = dt_array < merge_limit_milli_sec
                    idxs = np.where(np.logical_and(c1, c2))[0]
                    if not idxs.size > 0:
                        continue
                    min_idx = idxs[np.argmin(dt_array[idxs])]
                    key = vueron_filename_list[min_idx]
                    data = self.vtk_data_dict_vueron.pop(key, None)
                    if data is not None:
                        vueron_data_list.append(data)
                for key in expired_keys:
                    self.vtk_data_dict_vueron.pop(key, None)

        if self._stopped:
            return

        has_pintel = len(pintel_data_list) > 0
        has_keti = keti_data is not None
        has_vueron = len(vueron_data_list) > 0

        if not has_pintel and not has_keti and not has_vueron:
            return

        base_grid = self._load_base_grid()
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
        json_data.set_buffer(dict_for_json)
        json_data.save_compressed_json(self.app_info.keti_path/f'Send/{merged_filename}.json')
        self.converter.write_vtk_file(self.app_info.keti_path/f'Send/VTK/{merged_filename}.vtk')

        # 직렬화는 한 번만 — get_buffer()는 json.dumps()를 매번 새로 수행하므로 변수에 캐시
        json_buffer = json_data.get_buffer()

        # 전송 주기 throttle
        _should_send = True
        _interval_ms = getattr(self.parent, '_keti_send_interval_ms', 0)
        if _interval_ms > 0:
            _send_lock = getattr(self.parent, '_keti_send_lock', None)
            if _send_lock is not None:
                with _send_lock:
                    _now_ms = datetime.now().timestamp() * 1000
                    _last = self.parent._last_keti_send_time
                    if _last is None or (_now_ms - _last) >= _interval_ms:
                        self.parent._last_keti_send_time = _now_ms
                    else:
                        _should_send = False

        if _should_send:
            # KETI로 전달할 데이터
            self.parent.client_keti.send_message(SEND_KETI_CONGESTION, json_buffer)
            # LIMES에 전달할 데이터(PINTEL mqtt 포트 이용)
            self.parent.client_pintel.send_message(SEND_PINTEL_MERGED, json_buffer)

        # [8eight] Binary 파일 생성 (여러 merge 스레드 동시 진입 방지)
        should_generate_point = False
        with _on_point_data_lock:
            if self.parent.app_info.on_point_data == 0:
                self.parent.app_info.on_point_data = 1
                should_generate_point = True

        if should_generate_point:
            try:
                self.converter.merge_vtk_data_in_points(
                    base_grid, pintel_data=pintel_data_list,
                    vueron_data=vueron_data_list,
                    keti_data=keti_data,
                    merged_grid=merged_grid)
                if self.converter.array.shape[0] > 0:
                    point_file_name = self.app_info.e8ight_path/f'Send/{merged_filename}.e8b'
                    self.converter.write_binary_file_for_e8(point_file_name)
            finally:
                with _on_point_data_lock:
                    self.parent.app_info.on_point_data = 2

    def _safe_parse_filenames(self, names):
        """filename 리스트를 (id, date, time) int 배열로 안전 변환. 실패 시 None."""
        if not names:
            return None
        try:
            arr = np.array([n.split('_') for n in names], dtype=int)
        except (ValueError, TypeError):
            return None
        if arr.ndim != 2 or arr.shape[1] < 3:
            return None
        return arr

    def timestamp_to_dt(self, int_time_arr):
        times = int_time_arr
        hours = times // 10000000
        minute = (times // 100000) % 100
        m_seconds = times % 100000
        total_m_seconds = hours * 3600000 + minute * 60000 + m_seconds
        target_m_seconds = (self.target_time.hour * 3600000
                            + self.target_time.minute * 60000
                            + self.target_time.second * 1000
                            + self.target_time.microsecond // 1000)
        dt_array = np.abs(total_m_seconds - target_m_seconds)
        # 자정 경계 처리: 12시간 이상 차이면 day-wrap으로 간주하여 보정
        wrap_mask = dt_array > (_DAY_MILLI_SEC // 2)
        dt_array = np.where(wrap_mask, _DAY_MILLI_SEC - dt_array, dt_array)
        return dt_array

def to_absolute_path(path_str: str) -> Path:
    # 위치가 명확하지 않으니 실제 경로가 맞는지 확인할 것
    return Path(path_str).expanduser().resolve()

def is_opened(file_name):
    try:
        with open(file_name, 'r+'):
            pass
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
