#!/usr/bin/env python3
# -*- coding:utf8 -*-
# !/bin/bash

import json
import os
import copy

class JsonRW:
    def __init__(self):
        self.file = ''
        self._buffer = {}
        self._split_char = '.'

    def create(self, file=''):
        self.file = file
        self._buffer = {}
        self.save()

    def save(self, file=''):
        if file:
            self.file = file
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(copy.deepcopy(self._buffer), f, ensure_ascii=False, indent=4)

    def read(self, file='', encoding='utf-8'):
        self.file = file
        try:
            with open(self.file, 'r', encoding=encoding) as f:
                self._buffer = json.load(f)
            return True
        except (ValueError, json.JSONDecodeError, FileNotFoundError):
            return False

    def set_split_char(self, char='.'):
        self._split_char = char

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

    def _ensure_list_length(self, _buffer, key):
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

    def add(self, keys, value=''):
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

