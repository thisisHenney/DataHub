#!/usr/bin/env python3
# -*-coding:utf8-*-

import re
from datetime import datetime
from pathlib import Path
from PySide6.QtGui import QIntValidator

from Lib.File import make_dir, FileSaverThread
from Lib.Json.JsonRW import JsonRW
from Lib.Network.MQTT import MqttWidget


NEXTFOAM_IP='localhost'
NEXTFOAM_PORT=1883
NEXTFOAM_TOPIC='/topic/test'


class ClientNextfoam(MqttWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.parent = parent
        self.app_info = self.parent.app_info
        self._no_rx_count = 0

        self._initialize()

    def _initialize(self):
        make_dir(self.app_info.nextfoam_path)

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

        self.set_ip_port(NEXTFOAM_IP, NEXTFOAM_PORT)
        self.set_topics(NEXTFOAM_TOPIC)

        self.set_defaults_progressbar()

    def end(self):
        super().end()

    def set_ip_port_task(self, ip, port):
        if ip:
            self.ui.ip_comboBox.setCurrentText(f'{ip}')
        if port:
            self.ui.port_comboBox.setCurrentText(f'{port}')

    def set_defaults_progressbar(self):
        self.parent.ui.progressBar_tx_nextfoam.setRange(0, 100)
        self.parent.ui.progressBar_tx_nextfoam.setValue(0)

        self.parent.ui.progressBar_rx_nextfoam.setRange(0, 100)
        self.parent.ui.progressBar_rx_nextfoam.setValue(0)

    def set_change_progressbar_tx(self, running=False):
        max_value = self.parent.ui.progressBar_tx_nextfoam.maximum()
        if not running and max_value == 0:
            self.parent.ui.progressBar_tx_nextfoam.setRange(0, 100)
        elif running and max_value == 100:
            self.parent.ui.progressBar_tx_nextfoam.setRange(0, 0)

    def set_change_progressbar_rx(self, running=False):
        if not running:
            self.parent.ui.progressBar_rx_nextfoam.setRange(0, 100)
        else:
            self.parent.ui.progressBar_rx_nextfoam.setRange(0, 0)

    def on_connected_task(self):
        self.ui.lineEdit.setText(f'Connected')
        self.set_connected_ui()

        self.set_defaults_progressbar()

    def on_disconnected_task(self):
        self.ui.lineEdit.setText(f'Disconnected')
        self.set_disconnected_ui()

        self.set_defaults_progressbar()

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

    def on_message_task(self, tuple_data):
        self.set_change_progressbar_rx(True)

        topic = tuple_data[0]
        message = tuple_data[1]

        json_data = JsonRW()
        result = json_data.load(message)
        if result:
            time_path = 'timestamp'
            timestamp_data = json_data.get(time_path)
            # filename = f'{timestamp_data}.txt'
            filename = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            json_data.save(Path(f'{self.app_info.nextfoam_path}/{filename}'))
        else:
            self.ui.lineEdit.setText('Receiving..Error')

    def send_message_task(self, topic, msg):
        self.set_change_progressbar_tx(True)

    def on_restore_ui_task(self):
        self.set_disconnected_ui()

    def change_connect_ip(self, ip):
        self.set_ip_port(ip, '')

    def change_connect_port(self, port):
        self.set_ip_port('', port)

    def connect_to_server_pretask(self):
        ui = self.ui

        # print(self.client.ip, self.client.port)
        # print(ui.ip_comboBox.currentText())

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

    def set_disconnected_ui(self):
        ui = self.ui
        ui.ip_comboBox.setEnabled(True)
        ui.port_comboBox.setEnabled(True)
        ui.connect_button.setText('Connect')
        ui.connect_button.setEnabled(True)
        ui.disconnect_button.setEnabled(False)
