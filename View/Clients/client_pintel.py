#!/usr/bin/env python3
# -*-coding:utf8-*-

import threading
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIntValidator

from Lib.File import make_dir, FileSaverThread, MessageParserThread
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
        for saver in self.savers:
            saver.backlog_notice.connect(self.parent.log)

        # JSON 파싱을 GUI 스레드가 아니라 이 백그라운드 스레드에서 수행 (수신량 많을 때
        # 화면 갱신이 밀리는 것 방지). 자세한 이유는 Lib/File.py의 MessageParserThread 참고.
        self.parser = MessageParserThread(self._parse_camera_message)
        self.parser.notice.connect(self.parent.log)
        self.parser.data_time.connect(self.ui.label_data_time.setText)

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
        # 여기는 GUI 스레드(큐드 시그널로 호출됨). 무거운 JSON 파싱은 안 하고 바로
        # 백그라운드 파서 스레드로 넘긴다.
        self.parser.push(topic_data)

    def _parse_camera_message(self, topic_data):
        """MessageParserThread 위에서 실행됨 (GUI 스레드 아님) — self.parent.log()
        대신 반드시 self.parser.notice.emit()으로 알림을 보낼 것."""
        json_data = JsonRW()
        result = json_data.load(topic_data)
        if not result:
            self.parser.notice.emit('PINTEL >> Invalid Json Data')
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

        # common[0]은 상황에 따라 바뀌는 값이라 안 쓰고, common[1]이 실제 카메라 번호라
        # 이걸로 소스를 구분한다. common[4]는 타임스탬프.
        timestamp_data = json_data.get('common[4]')
        camera_no = json_data.get('common[1]')
        if timestamp_data is None or camera_no is None:
            self.parser.notice.emit('PINTEL >> Missing timestamp/camera number (common[4]/common[1])')
            return

        try:
            timestamp_data = str(timestamp_data)
            timestamp = int(timestamp_data[:-3])
            ms = timestamp_data[-3:]
            # Pintel 카메라 장비는 자체 시계가 이미 KST로 맞춰진 상태에서 epoch를 만들어
            # 보낸다(즉 UTC로 그냥 해석한 값이 실제 KST 시각과 동일). 실측 결과
            # no_shift(=utcfromtimestamp 그대로)가 now()와 일치하고 +9h를 더하면 9시간
            # 앞선(다음날 새벽) 시각이 되는 것을 확인했으므로 KST 보정을 적용하지 않는다.
            dt = datetime.utcfromtimestamp(timestamp)
            timestamp_filename = dt.strftime("%Y%m%d_%H%M%S")+ms
            camera_no = int(camera_no)
        except (ValueError, TypeError, IndexError):
            self.parser.notice.emit('PINTEL >> Invalid timestamp/camera number format')
            return

        # 시스템 수신 시각이 아니라, 메시지 안에 담긴 데이터 자체의 시각을 표시
        self.parser.data_time.emit(f'최근 수신 데이터 시간: {dt.strftime("%Y-%m-%d %H:%M:%S")}.{ms} (cam {camera_no})')

        filename = f"{camera_no:04d}_{timestamp_filename}"

        idx = self.count_thread % self.num_thread
        self.count_thread = (idx + 1) % self.num_thread
        saver = self.savers[idx]
        saver.push((self.app_info.pintel_path, filename, json_data))

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
