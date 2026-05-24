#!/usr/bin/env python3
# -*- coding:utf8 -*-

import json
import os
import re
import gzip
from pathlib import Path

_TRAILING_COMMA_RE = re.compile(r',\s*([\]}])')

SPLIT_CHAR = '.'


class JsonRW:
    """
    JSON read/write helper.

    Thread-safety invariant:
      `load()` 이후에는 `_buffer`를 mutate하지 말 것. saver와 writer가 동일
      JsonRW를 read-only로 공유하는 경우가 있어 mutation 시 race condition 발생.
    """
    def __init__(self):
        self._file = ''
        self._buffer = {}
        self._split_char = SPLIT_CHAR

    def get_file_name(self):
        return self._file

    def get_buffer(self):
        buffer = json.dumps(self._buffer)
        return buffer

    def get_json_data(self):
        return f'"{self._buffer}"'

    def set_buffer(self, data):
        self._buffer = data

    def set_split_char(self, char=SPLIT_CHAR):
        self._split_char = char

    @staticmethod
    def is_valid_json(json_data):
        try:
            json.loads(json_data)
            return True
        except json.JSONDecodeError:
            # print('[Error] Invalid json data')
            return False

    def create(self, file=''):
        if not file:
            return False
        self._file = Path(file)
        self.save()
        return True

    def read(self, file='', encoding='utf-8'):
        if not file or not os.path.isfile(file):
            print('[Error] Cannot find file')
            return False

        self._file = file
        try:
            with open(self._file, 'r', encoding=encoding) as f:
                self._buffer = json.load(f)
            return True
        except (ValueError, json.JSONDecodeError, FileNotFoundError):
            print('[Error] Cannot read json data')
            return False

    def save(self, file='', indent:None|int|str=4):
        if file:
            self._file = Path(file)

        target = Path(self._file)
        tmp = target.with_suffix(target.suffix + '.tmp')
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self._buffer, f, ensure_ascii=False, indent=indent)
            os.replace(tmp, target)
        except Exception:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass
            raise

    def save_compressed_json(self, file: Path):
        target = Path(file).with_suffix('.json.gz')
        tmp = target.with_suffix(target.suffix + '.tmp')
        try:
            with gzip.open(tmp, 'wt', encoding='utf-8', compresslevel=1) as f:
                json.dump(self._buffer, f, ensure_ascii=False, indent=None)
            os.replace(tmp, target)
            self._file = target
        except Exception:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass
            raise

    def load(self, json_data=""):
        try:
            self._buffer = json.loads(json_data)
            return True
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        # trailing comma 제거 후 재시도 (Pintel 장치 등 비표준 JSON 대응)
        try:
            cleaned = _TRAILING_COMMA_RE.sub(r'\1', json_data)
            self._buffer = json.loads(cleaned)
            return True
        except (json.JSONDecodeError, ValueError, TypeError):
            return False

    def check(self, keys):
        _buffer = self._buffer
        for key in self._parse_key(keys):
            if isinstance(key, int) and isinstance(_buffer, list):
                if len(_buffer) <= key:
                    return False
                _buffer = _buffer[key]
            elif isinstance(key, str) and isinstance(_buffer, dict):
                if key not in _buffer:
                    return False
                _buffer = _buffer[key]
            else:
                return False
        return True

    def get(self, keys):
        _buffer = self._buffer
        for key in self._parse_key(keys):
            if isinstance(key, int) and isinstance(_buffer, list):
                if key >= len(_buffer):
                    return None
                _buffer = _buffer[key]
            elif isinstance(key, str) and isinstance(_buffer, dict):
                _buffer = _buffer.get(key)
                if _buffer is None:
                    return None
            else:
                return None
        return _buffer

    def get_sub_num(self, keys=''):
        return len(self.get(keys)) if self.get(keys) else 0

    def get_sub_list_num(self, keys=''):
        _data = self.get(keys)
        return len(_data) if isinstance(_data, list) else 0

    def get_sub_names(self, keys=''):
        if not keys:
            return list(self._buffer.keys())
        else:
            return list(self.get(keys).keys())

    def _parse_key(self, key):
        parts = []
        for part in key.split(self._split_char):
            while '[' in part and ']' in part:
                index = part[part.index('[') + 1:part.index(']')]
                parts.append(part[:part.index('[')])
                parts.append(int(index))
                part = part[part.index(']') + 1:]
            if part:
                parts.append(part)
        return parts

    @staticmethod
    def _ensure_list_length(_buffer, key):
        while isinstance(_buffer, list) and len(_buffer) <= key:
            _buffer.append({})
        return _buffer

    def _navigate_to_key(self, keys):
        _buffer = self._buffer
        for key in keys[:-1]:
            if isinstance(key, int):
                _buffer = self._ensure_list_length(_buffer, key)[key]
            elif isinstance(key, str):
                if key not in _buffer:
                    return None
                _buffer = _buffer[key]
        return _buffer

    def _update_or_set(self, _buffer, last_key, value, mode='add'):
        if isinstance(last_key, int):
            self._ensure_list_length(_buffer, last_key)
            if mode == 'add' and isinstance(_buffer[last_key], dict) and isinstance(value, dict):
                _buffer[last_key].update(value)
            else:
                _buffer[last_key] = value
        else:
            current_value = _buffer.get(last_key, None)
            if isinstance(current_value, dict) and isinstance(value, dict):
                current_value.update(value)
            elif isinstance(value, list):
                if isinstance(current_value, list) and mode == 'add':
                    current_value.extend(value)
                else:
                    _buffer[last_key] = value
            else:
                if isinstance(current_value, list) and mode == 'add':
                    current_value.append(value)
                else:
                    _buffer[last_key] = [value] if isinstance(value, list) else value

    def add(self, keys, value=None):
        if value is None:
            value = ''
        keys = self._parse_key(keys)
        _buffer = self._navigate_to_key(keys)
        if _buffer is None:
            return False
        self._update_or_set(_buffer, keys[-1], value, mode='add')
        return True

    def set(self, keys, value=''):
        keys = self._parse_key(keys)
        _buffer = self._navigate_to_key(keys)
        if _buffer is None:
            return False
        self._update_or_set(_buffer, keys[-1], value, mode='set')
        return True

    def remove(self, keys, include_key=True):
        keys = self._parse_key(keys)
        _buffer = self._navigate_to_key(keys)
        if _buffer is None:
            return False

        last_key = keys[-1]
        if isinstance(last_key, int):
            if include_key and isinstance(_buffer, list) and len(_buffer) > last_key:
                _buffer.pop(last_key)
            else:
                _buffer[last_key] = ''
        else:
            if include_key and last_key in _buffer:
                del _buffer[last_key]
            else:
                _buffer[last_key] = {} if isinstance(_buffer[last_key], dict) else ''
        return True


# Test
if __name__ == '__main__':
    data = JsonRW()
    # result = data.read('data.json')
    # print(result)

    data.create('data.json')

    # data.add('name1', {'path':'/test/test1'})
    # data.add('name2', {'path':'/test/test2'})
    # data.save()

    # data.set(f'grid[1].domain.min[0]', 45)
    # data.save()
    # result = data.get('name1.path')
    # print(result)

    # result = data.get_sub_names('name1')
    # print(result)
    # result = data.get_sub_names()
    # print(result)
    # result = data.get('name1.path1')
    # print(result)

    data.add('root.sub1')
    data.add('root', {'sub2':2})


    result1 = data.get_json_data()
    print(result1)

    result2 = json.dumps(data.get_buffer())
    print(result2)


    data.save()

    # data.set(f'config.grid[{i}].domain.min[0]', int(d.domain_min[0]))

    # data.add('root.sub',[{'sub1-1':2, 'sub1-2':3, 'sub1-3':4}, {'sub2-1':5, 'sub2-2':6, 'sub2-3':7}])
    # data.add('root.sub', [0, 1])
    # data.add('root.sub[1]', 2)
    # data.add('root2.sub', 2)
    # data.save()

    # {
    #     "root": {
    #         "sub1": 1,
    #         "sub2": 2
    #     }
    # }
