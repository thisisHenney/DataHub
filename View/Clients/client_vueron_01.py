#!/usr/bin/env python3
# -*-coding:utf8-*-

import threading
from datetime import datetime, timedelta
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIntValidator

from Lib.File import make_dir, FileSaverThread
from Lib.Json.JsonRW import JsonRW
from Lib.Network.WebSocket import WebSocketWidget

from Lib.Converter.vtk_json_converter import VtkJsonConverter, CompanyType


VUERON_IP = '192.168.10.212'
VUERON_PORT = 10205
VUERON_PATH='/ws/v1/mbembo/area/2'
# 확인용: ws://192.168.10.212:10205/ws/v1/mbembo/area/2


class ClientVueron01(WebSocketWidget):
    def __init__(self, parent, vtk_data_dict, vtk_data_lock=None):
        super().__init__()

        self.parent = parent
        self.app_info = self.parent.app_info

        self.converter = VtkJsonConverter()
        self.vtk_data_dict = vtk_data_dict
        self.vtk_data_lock = vtk_data_lock or threading.Lock()

        self.count_thread = 0
        self.num_thread = 4
        self.savers = [FileSaverThread(CompanyType.Vueron, self.vtk_data_dict, self.vtk_data_lock) for i in range(self.num_thread)]
        self._no_rx_count = 0

        self._initialize()

    def _initialize(self):
        make_dir(self.app_info.vueron_01_path)
        make_dir(self.app_info.vueron_01_path/'VTK')

        ui = self.ui
        ui.ip_comboBox.lineEdit().returnPressed.connect(self.connect_to_server)
        ui.ip_comboBox.currentTextChanged.connect(self.change_connect_ip)

        ui.port_comboBox.setValidator(QIntValidator())
        ui.port_comboBox.lineEdit().returnPressed.connect(self.connect_to_server)
        ui.port_comboBox.currentTextChanged.connect(self.change_connect_port)

        ui.connect_button.clicked.connect(self.connect_to_server)
        ui.disconnect_button.clicked.connect(self.disconnect_from_server)

    def set_defaults(self):
        super().set_defaults()
        self.set_disconnected_ui()
        self.set_ip_port(VUERON_IP, VUERON_PORT, VUERON_PATH)
        self.set_defaults_progressbar()

    def end(self):
        super().end()
        for saver in self.savers:
            saver.stop()
        for saver in self.savers:
            saver.wait(3000)

    def set_ip_port_task(self, ip, port, path):
        if ip:
            self.ui.ip_comboBox.setCurrentText(f'{ip}')
        if port:
            self.ui.port_comboBox.setCurrentText(f'{port}')

    def set_defaults_progressbar(self):
        self.parent.ui.progressBar_tx_vueron.setRange(0, 100)
        self.parent.ui.progressBar_tx_vueron.setValue(0)

        self.parent.ui.progressBar_rx_vueron.setRange(0, 100)
        self.parent.ui.progressBar_rx_vueron.setValue(0)

    def set_change_progressbar_tx(self, running=False):
        max_value = self.parent.ui.progressBar_tx_vueron.maximum()
        if not running and max_value == 0:
            self.parent.ui.progressBar_tx_vueron.setRange(0, 100)
        elif running and max_value == 100:
            self.parent.ui.progressBar_tx_vueron.setRange(0, 0)

    def set_change_progressbar_rx(self, running=False):
        if not running:
            self.parent.ui.progressBar_rx_vueron.setRange(0, 100)
        else:
            self.parent.ui.progressBar_rx_vueron.setRange(0, 0)

    def on_connected_task(self):
        self.ui.lineEdit.setText(f'Connected')
        self.set_connected_ui()

        self.set_defaults_progressbar()

    def on_disconnected_task(self):
        self.ui.lineEdit.setText(f'Disconnected')
        self.set_disconnected_ui()

        self.set_defaults_progressbar()

        if self.parent.is_reconnect:
            QTimer.singleShot(3000, self._on_timer_reconnect)

    def _on_timer_reconnect(self):
        curtime = f'{datetime.now().strftime("%Y.%m.%d %H:%M:%S")}'
        self.parent.log(f'Vueron1 >> Reconnect at ({curtime})')
        self.connect_to_server()

    def on_timer_check_txrx_state_task(self, tx_state, rx_state):
        if rx_state:
            self._no_rx_count = 0
            self.ui.lineEdit.setText('Receiving data...')
        else:
            self._no_rx_count += 1
            if self._no_rx_count >= 25:
                self.ui.lineEdit.setText('Waiting for data...')

        self.set_change_progressbar_tx(tx_state)
        self.set_change_progressbar_rx(rx_state)

    def on_notice_task(self, msg):
        self.ui.lineEdit.setText(msg)
        self.parent.log(msg)

    def on_message_task(self, tuple_data):
        self.set_change_progressbar_rx(True)

        message = tuple_data[0]
        empty = tuple_data[1]

        json_data = JsonRW()
        result = json_data.load(message)
        if not result:
            self.parent.log('Vueron_01 >> Invalid Json Data')
            log_path = Path(f'{self.app_info.app_path}/Data/Error/vueron/error_vueron_01.log')
            log_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                if isinstance(message, (bytes, bytearray)):
                    data_str = message.decode('utf-8', errors='replace')
                else:
                    data_str = str(message)
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f'[{datetime.now().isoformat()}] {data_str}\n---\n')
            except Exception:
                pass
            return

        timestamp_data = json_data.get('trID')
        id_data = json_data.get('payload.areaID')
        if not timestamp_data or id_data is None:
            self.parent.log('Vueron_01 >> Missing trID/areaID')
            return
        try:
            dt = datetime.strptime(timestamp_data, "%Y%m%d%H%M%S%f")
            dt_korean = dt + timedelta(hours=9)
            filename = (f"{id_data:04d}_" + dt_korean.strftime("%Y%m%d_%H%M%S") + f'{int(dt_korean.microsecond / 1000):03d}')
        except (ValueError, TypeError):
            self.parent.log('Vueron_01 >> Invalid trID format')
            return

        idx = self.count_thread % self.num_thread
        self.count_thread = (idx + 1) % self.num_thread
        saver = self.savers[idx]
        saver.stack.append((self.app_info.vueron_01_path, filename, json_data))
        saver.notify()

    def send_message_task(self, msg):
        self.set_change_progressbar_tx(True)

    def on_restore_ui_task(self):
        self.set_disconnected_ui()

    def change_connect_ip(self, ip):
        self.set_ip_port(ip, '')

    def change_connect_port(self, port):
        self.set_ip_port('', port)

    def connect_to_server_pretask(self):
        ui = self.ui

        ui.connect_button.setText('Connecting')
        ui.connect_button.setEnabled(False)
        ui.lineEdit.setText(f'...')

    def disconnect_from_server_task(self):
        self.set_disconnected_ui()

    def set_connected_ui(self):
        ui = self.ui
        ui.ip_comboBox.setEnabled(False)
        ui.port_comboBox.setEnabled(False)
        ui.connect_button.setEnabled(False)
        ui.connect_button.setText('Connected')
        ui.disconnect_button.setEnabled(True)

        for saver in self.savers:
            saver.is_running = True
            if not saver.isRunning():
                saver.start()

    def set_disconnected_ui(self):
        ui = self.ui
        ui.ip_comboBox.setEnabled(True)
        ui.port_comboBox.setEnabled(True)
        ui.connect_button.setText('Connect')
        ui.connect_button.setEnabled(True)
        ui.disconnect_button.setEnabled(False)

        for saver in self.savers:
            saver.is_running = False
