#!/usr/bin/env python3
# -*-coding:utf8-*-

import threading
from pathlib import Path
from datetime import datetime, timedelta
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIntValidator

from Lib.File import make_dir, FileSaverThread
from Lib.Json.JsonRW import JsonRW
from Lib.Network.MQTT import MqttWidget

from Lib.Converter.vtk_json_converter import VtkJsonConverter, CompanyType

KETI_IP='49.50.128.69'
KETI_PORT = 8883
KETI_TOPIC = 'rpi_density'


class ClientKeti(MqttWidget):
    def __init__(self, parent, vtk_data_dict, vtk_data_lock=None):
        super().__init__()

        self.parent = parent
        self.app_info = self.parent.app_info

        self.converter = VtkJsonConverter()
        self.vtk_data_dict = vtk_data_dict
        self.vtk_data_lock = vtk_data_lock or threading.Lock()

        self.count_thread = 0
        self.num_thread = 4
        self.savers = [FileSaverThread(CompanyType.KETI, self.vtk_data_dict, self.vtk_data_lock) for i in range(self.num_thread)]

        self.checking_timer = QTimer()
        self._no_rx_count = 0

        self._initialize()

    def _initialize(self):
        make_dir(self.app_info.keti_path)
        make_dir(self.app_info.keti_path/'VTK')
        make_dir(self.app_info.keti_path/'Send')
        make_dir(self.app_info.keti_path/'Send/VTK')

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

        self.set_ip_port(KETI_IP, KETI_PORT)
        self.set_require_login(True)
        self.set_id_pw('keti', '6CUBUxzGCvYYiEc')
        # 실제 연결 시 주석 해제
        self.set_tls(Path(self.parent.app_info.app_path/'Data'/'CA'/'ca.crt'))

        self.set_topics(KETI_TOPIC)

        self.set_defaults_progressbar()
        self.parent.ui.text_thread_keti.setText('-')

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
        self.parent.ui.progressBar_tx_keti.setRange(0, 100)
        self.parent.ui.progressBar_tx_keti.setValue(0)

        self.parent.ui.progressBar_rx_keti.setRange(0, 100)
        self.parent.ui.progressBar_rx_keti.setValue(0)

    def set_change_progressbar_tx(self, running=False):
        max_value = self.parent.ui.progressBar_tx_keti.maximum()
        if not running and max_value == 0:
            self.parent.ui.progressBar_tx_keti.setRange(0, 100)
        elif running and max_value == 100:
            self.parent.ui.progressBar_tx_keti.setRange(0, 0)

    def set_change_progressbar_rx(self, running=False):
        if not running:
            self.parent.ui.progressBar_rx_keti.setRange(0, 100)
        else:
            self.parent.ui.progressBar_rx_keti.setRange(0, 0)

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
        print(f'KETI >> Reconnect at ({curtime})')
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
        self.parent.ui.text_thread_keti.setText(f'{count}')

    def on_notice_task(self, msg):
        self.ui.lineEdit.setText(msg)
        self.parent.log(msg)

    def on_message_task(self, tuple_data):
        topic = tuple_data[0]
        if topic == KETI_TOPIC:
            self.on_message_task_topic_crowd_congestion(tuple_data[1])

    def on_message_task_topic_crowd_congestion(self, topic_data):
        message = topic_data

        json_data = JsonRW()
        result = json_data.load(message)
        if result:
            time_path = 'result_time'
            timestamp_data = json_data.get(time_path)   # "2025-05-24 09:15:56.236"
            dt = datetime.strptime(timestamp_data, "%Y-%m-%d %H:%M:%S.%f")
            dt_korean = dt + timedelta(hours=9)
            filename = ( "0001_" + dt_korean.strftime("%Y%m%d_%H%M%S") + f'{int(dt_korean.microsecond/1000):03d}')

            saver = self.savers[self.count_thread]
            saver.stack.append((self.app_info.keti_path, filename, json_data))
            saver.notify()
            self.count_thread += 1
            if self.count_thread == self.num_thread:
                self.count_thread = 0

        else:
            self.parent.log('KETI >> Invalid Json Data')
            log_path = Path(f'{self.app_info.app_path}/Data/Error/keti/error_keti.log')
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(topic_data)

    def send_message_task(self, topic, msg):
        self.set_change_progressbar_tx(True)

    def on_restore_ui_task(self):
        self.set_disconnected_ui()

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
