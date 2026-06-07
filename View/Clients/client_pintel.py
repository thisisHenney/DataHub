#!/usr/bin/env python3
# -*-coding:utf8-*-

import threading
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIntValidator

from Lib.File import make_dir, FileSaverThread
from Lib.Json.JsonRW import JsonRW
from Lib.Network.MQTT import MqttWidget
from Lib.Converter.vtk_json_converter import VtkJsonConverter, CompanyType


PINTEL_IP='192.168.10.112'
PINTEL_PORT=1883
PINTEL_TOPIC_CAMERA = 'PVX-V30/PA-7F000001/POT/CROWD/JSON'
PINTEL_TOPIC_MERGED = 'PVX-V30/PA-7F000001/POT/CROWD/CROWD_MERGED'

class ClientPintel(MqttWidget):
    def __init__(self, parent, vtk_data_dict, vtk_data_lock=None):
        super().__init__()

        self.parent = parent
        self.app_info = self.parent.app_info

        self.converter = VtkJsonConverter()
        self.vtk_data_dict = vtk_data_dict
        self.vtk_data_lock = vtk_data_lock or threading.Lock()

        self.count_thread = 0
        self.num_thread = 16
        self.savers = [FileSaverThread(CompanyType.Pintel, self.vtk_data_dict, self.vtk_data_lock) for i in range(self.num_thread)]

        self.checking_timer = QTimer()
        self._no_rx_count = 0

        self._initialize()

    def _initialize(self):
        make_dir(self.app_info.pintel_path)
        make_dir(self.app_info.pintel_path/'VTK')

        ui = self.ui
        ui.ip_comboBox.lineEdit().returnPressed.connect(self.connect_to_server)
        ui.ip_comboBox.currentTextChanged.connect(self.change_connect_ip)

        ui.port_comboBox.setValidator(QIntValidator())
        ui.port_comboBox.lineEdit().returnPressed.connect(self.connect_to_server)
        ui.port_comboBox.currentTextChanged.connect(self.change_connect_port)

        ui.connect_button.clicked.connect(self.connect_to_server)
        ui.disconnect_button.clicked.connect(self.disconnect_from_server)

        self.checking_timer.setInterval(1000)
        self.checking_timer.timeout.connect(self._on_timer_check_thread)

    def set_defaults(self):
        super().set_defaults()

        self.set_disconnected_ui()

        self.set_ip_port(PINTEL_IP, PINTEL_PORT)
        self.set_require_login(True)
        self.set_id_pw('master', 'master')
        self.set_topics(PINTEL_TOPIC_CAMERA)

        self.set_defaults_progressbar()
        self.parent.ui.text_thread_pintel.setText('-')

    def end(self):
        super().end()
        self.checking_timer.stop()
        for saver in self.savers:
            saver.stop()
        for saver in self.savers:
            saver.wait(3000)

    def set_ip_port_task(self, ip, port):
        if ip:
            self.ui.ip_comboBox.setCurrentText(f'{ip}')
        if port:
            self.ui.port_comboBox.setCurrentText(f'{port}')

    def set_defaults_progressbar(self):
        self.parent.ui.progressBar_tx_pintel.setRange(0, 100)
        self.parent.ui.progressBar_tx_pintel.setValue(0)

        self.parent.ui.progressBar_rx_pintel.setRange(0, 100)
        self.parent.ui.progressBar_rx_pintel.setValue(0)

    def set_change_progressbar_tx(self, running=False):
        max_value = self.parent.ui.progressBar_tx_pintel.maximum()
        if not running and max_value == 0:
            self.parent.ui.progressBar_tx_pintel.setRange(0, 100)
        elif running and max_value == 100:
            self.parent.ui.progressBar_tx_pintel.setRange(0, 0)

    def set_change_progressbar_rx(self, running=False):
        if not running:
            self.parent.ui.progressBar_rx_pintel.setRange(0, 100)
        else:
            self.parent.ui.progressBar_rx_pintel.setRange(0, 0)

    def on_connected_task(self):
        self.ui.lineEdit.setText(f'Connected')
        self.set_connected_ui()

        self.set_defaults_progressbar()

        self.checking_timer.start()

    def on_disconnected_task(self):
        self.ui.lineEdit.setText(f'Disconnected')
        self.set_disconnected_ui()

        self.set_defaults_progressbar()

        if self.parent.is_reconnect:
            QTimer.singleShot(3000, self._on_timer_reconnect)

    def _on_timer_reconnect(self):
        curtime = f'{datetime.now().strftime("%Y.%m.%d %H:%M:%S")}'
        self.parent.log(f'Pintel >> Reconnect at ({curtime})')
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

    def _on_timer_check_thread(self):
        count = 0
        for saver in self.savers:
            if saver.is_running:
                count += 1
        self.parent.ui.text_thread_pintel.setText(f'{count}')

    def on_notice_task(self, msg):
        self.ui.lineEdit.setText(msg)
        self.parent.log(f'Pintel >> {msg}')

    def on_message_task(self, tuple_data):
        topic = tuple_data[0]
        if topic == PINTEL_TOPIC_CAMERA:
            self.on_message_task_by_topic_camera(tuple_data[1])

    def on_message_task_by_topic_camera(self, topic_data):
        json_data = JsonRW()
        result = json_data.load(topic_data)
        if not result:
            self.parent.log('PINTEL >> Invalid Json Data')
            log_path = Path(f'{self.app_info.app_path}/Data/Error/pintel/error_pintel.log')
            log_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                if isinstance(topic_data, (bytes, bytearray)):
                    data_str = topic_data.decode('utf-8', errors='replace')
                else:
                    data_str = str(topic_data)
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f'[{datetime.now().isoformat()}] {data_str}\n---\n')
            except Exception:
                pass
            return

        timestamp_data = json_data.get('common[4]')
        id_list = json_data.get('common')
        if timestamp_data is None or not id_list or len(id_list) < 2:
            self.parent.log('PINTEL >> Missing common/timestamp fields')
            return

        try:
            timestamp_data = str(timestamp_data)
            timestamp = int(timestamp_data[:-3])
            ms = timestamp_data[-3:]
            dt = datetime.utcfromtimestamp(timestamp)
            timestamp_filename = dt.strftime("%Y%m%d_%H%M%S")+ms
            id_data = f'{int(id_list[0]):02d}{int(id_list[1]):02d}'
        except (ValueError, TypeError, IndexError):
            self.parent.log('PINTEL >> Invalid timestamp/id format')
            return

        filename = f"{id_data}_{timestamp_filename}"

        idx = self.count_thread % self.num_thread
        self.count_thread = (idx + 1) % self.num_thread
        saver = self.savers[idx]
        saver.stack.append((self.app_info.pintel_path, filename, json_data))
        saver.notify()

    def on_message_task_by_topic_merged(self, topic_data):
        ...

    def send_message_task(self, topic, msg):
        self.set_change_progressbar_tx(True)

    def on_restore_ui_task(self):
        self.set_disconnected_ui()
        if self.parent.is_reconnect:
            QTimer.singleShot(3000, self._on_timer_reconnect)

    def change_connect_ip(self, ip):
        if not ip == 'localhost':
            self.set_ip_port(ip, '')
        else:
            self.set_require_login(False)
            self.set_ip_port(ip, '1883')

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
