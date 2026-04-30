#!/usr/bin/env python3
# -*-coding:utf8-*-

import re
from pathlib import Path
from Lib.File import make_dir, FileSaverThread
from Lib.Json.JsonRW import JsonRW
from Lib.Network.MQTT import MqttWidget


class ClientE8ight(MqttWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.app_info = self.parent.app_info

        self._initialize()

    def _initialize(self):
        make_dir(self.app_info.e8ight_path)
        make_dir(self.app_info.e8ight_path/'Send')

    def set_defaults(self):
        ...

    def end(self):
        super().end()
