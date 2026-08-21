#!/usr/bin/env python3
# -*-coding:utf8-*-

import threading
from pathlib import Path
from datetime import datetime, timedelta
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIntValidator

from Lib.File import make_dir, FileSaverThread, MessageParserThread
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
        for saver in self.savers:
            saver.backlog_notice.connect(self.parent.log)

        # JSON 파싱을 GUI 스레드가 아니라 이 백그라운드 스레드에서 수행 (수신량 많을 때
        # 화면 갱신이 밀리는 것 방지). 자세한 이유는 Lib/File.py의 MessageParserThread 참고.
        self.parser = MessageParserThread(self._parse_crowd_congestion_message)
        self.parser.notice.connect(self.parent.log)
        self.parser.data_time.connect(self.ui.label_data_time.setText)

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
        # 실제(운영) 서버 연결 시에만 주석 해제 — TLS가 없는 테스트 브로커에 접속하면
        # SSLEOFError(EOF occurred in violation of protocol)로 접속이 거부됨
        # self.set_tls(Path(self.parent.app_info.app_path/'Data'/'CA'/'ca.crt'))

        self.set_topics(KETI_TOPIC)

        self.set_defaults_progressbar()
        self.parent.ui.text_thread_keti.setText('-')

    def end(self):
        super().end()
        self.checking_timer.stop()
        self.parser.stop()
        self.parser.wait(3000)
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
        self.parent.remember_connected_ip(self)
        self.parent.save_network_settings()

        self.checking_timer.start()

    def on_disconnected_task(self):
        self.ui.lineEdit.setText(f'Disconnected')
        self.set_disconnected_ui()

        self.set_defaults_progressbar()

        if self.parent.is_reconnect and not self.user_disconnected:
            QTimer.singleShot(3000, self._on_timer_reconnect)

    def _on_timer_reconnect(self):
        curtime = f'{datetime.now().strftime("%Y.%m.%d %H:%M:%S")}'
        self.parent.log(f'KETI >> Reconnect at ({curtime})')
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
        self.parent.log(f'KETI >> {msg}')

    def on_message_task(self, tuple_data):
        topic = tuple_data[0]
        if topic == KETI_TOPIC:
            self.on_message_task_topic_crowd_congestion(tuple_data[1])

    def on_message_task_topic_crowd_congestion(self, topic_data):
        # 여기는 GUI 스레드(큐드 시그널로 호출됨). 무거운 JSON 파싱은 안 하고 바로
        # 백그라운드 파서 스레드로 넘긴다.
        self.parser.push(topic_data)

    def _parse_crowd_congestion_message(self, topic_data):
        """MessageParserThread 위에서 실행됨 (GUI 스레드 아님) — self.parent.log()
        대신 반드시 self.parser.notice.emit()으로 알림을 보낼 것."""
        message = topic_data

        json_data = JsonRW()
        result = json_data.load(message)
        if not result:
            self.parser.notice.emit('KETI >> Invalid Json Data')
            log_path = Path(f'{self.app_info.app_path}/Data/Error/keti/error_keti.log')
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

        timestamp_data = json_data.get('result_time')   # "2025-05-24 09:15:56.236"
        if not timestamp_data:
            self.parser.notice.emit('KETI >> Missing result_time')
            return
        try:
            dt = datetime.strptime(timestamp_data, "%Y-%m-%d %H:%M:%S.%f")
        except (ValueError, TypeError):
            self.parser.notice.emit('KETI >> Invalid result_time format')
            return
        dt_korean = dt + timedelta(hours=9)
        filename = ( "0001_" + dt_korean.strftime("%Y%m%d_%H%M%S") + f'{int(dt_korean.microsecond/1000):03d}')

        # 시스템 수신 시각이 아니라, 메시지 안에 담긴 데이터 자체의 시각을 표시
        self.parser.data_time.emit(f'최근 수신 데이터 시간: {dt_korean.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}')

        idx = self.count_thread % self.num_thread
        self.count_thread = (idx + 1) % self.num_thread
        saver = self.savers[idx]
        saver.push((self.app_info.keti_path, filename, json_data))

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

        self.parser.is_running = True
        if not self.parser.isRunning():
            self.parser.start()

        for saver in self.savers:
            saver.is_running = True
            saver.dropped_count = 0
            if not saver.isRunning():
                saver.start()

    def set_disconnected_ui(self):
        ui = self.ui
        ui.ip_comboBox.setEnabled(True)
        ui.port_comboBox.setEnabled(True)
        ui.connect_button.setText('Connect')
        ui.connect_button.setEnabled(True)
        ui.disconnect_button.setEnabled(False)

        self.parser.is_running = False
        for saver in self.savers:
            saver.is_running = False
