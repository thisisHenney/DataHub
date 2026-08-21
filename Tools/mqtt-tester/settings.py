#!/usr/bin/env python3
# -*- coding:utf8 -*-
"""Tiny local settings persistence — independent of DataHub's own settings mechanism."""

import json
from pathlib import Path

SETTINGS_PATH = Path(__file__).parent / 'settings.json'


def load_settings():
    if not SETTINGS_PATH.is_file():
        return {}
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_settings(data):
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
