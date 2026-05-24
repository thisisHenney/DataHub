#!/usr/bin/env python3
# -*- coding:utf8 -*-

import ssl
import paho.mqtt.client as mqtt
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import QWidget
from Lib.Network.View.mqtt_ui import Ui_Form_Mqtt

STATE_READY=0
STATE_SUBSCRIBING=1
STATE_SUBSCRIBED=2
STATE_FAILED=3


class MqttClientThread(QThread):
    connected = Signal()
    disconnected = Signal()
    received_message = Signal(tuple)
    notice = Signal(str)
    restore_ui = Signal()

    def __init__(self):
        super().__init__()

        self.ip = 'localhost'   # 127.0.0.1
        self.port = 1883        # 1883(mqtt://~), 8883(mqtts://~)
        self.is_require_login = False
        self.login_id = None
        self.login_pw = None
        self.topics = {}    # {topic: state}

        self.client = mqtt.Client()

        self._init_callback()

    def _init_callback(self):
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe  # Not really necessary
        self.client.on_unsubscribe = self.on_unsubscribe  # Not really necessary

    def is_connected(self):
        return self.client.is_connected()

    def set_ip_port(self, ip:str, port:int):
        if ip:
            self.ip = ip
        if port:
            self.port = int(port)
    
    def add_topics(self, topics):
        if not isinstance(topics, list):
            topics = [topics]
        
        for topic in topics:
            if topic:
                self.topics[topic] = 0
    
    def set_topics(self, topics, qos=0):
        if not isinstance(topics, list):
            topics = [topics]

        for topic in topics:
            if topic:
                self.topics[topic] = qos

    def set_require_login(self, state=True):
        self.is_require_login = state

    def set_id_pw(self, login_id, login_pw):
        if login_id and login_pw:
            self.is_require_login = True
            self.login_id = login_id
            self.login_pw = login_pw

    def _subscribe_to_topics(self, qos=0):
        for topic in self.topics:
            self.client.subscribe(topic, qos)
            self.notice.emit(f'[mqtt] Subscribed to [{topic}]')

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected.emit()
            self._subscribe_to_topics()
        else:
            self.notice.emit('[mqtt:Err] Failed to connect')
            self.restore_ui.emit()

    def on_disconnect(self, client, userdata, rc):
        # rc=0은 정상 종료, 그 외는 비정상 (keepalive 초과, 네트워크 끊김, broker 강제종료 등).
        # 진단을 위해 rc 코드와 paho 표준 사유 문자열을 함께 로깅.
        try:
            reason = mqtt.error_string(rc)
        except Exception:
            reason = 'unknown'
        if rc == 0:
            self.notice.emit(f'[mqtt] Disconnected cleanly (rc=0, {reason})')
        else:
            self.notice.emit(f'[mqtt:Err] Unexpected disconnect (rc={rc}, {reason})')
        # 비정상 disconnect에서도 disconnected를 emit해야 재접속 로직이 동작함.
        self.disconnected.emit()

    def on_message(self, client, userdata, msg):
        data = (msg.topic, msg.payload.decode())
        self.received_message.emit(data)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        if 128 in granted_qos:
            self.notice.emit(f'[mqtt:Err] Subscription failed')
        else:   # 0, 1, 2
            self.notice.emit(f'[mqtt] Subscription registered')

    def on_unsubscribe(self, client, userdata, mid):
        self.notice.emit(f'[mqtt] Unsubscription confirmed (MID={mid})')

    def run(self):
        result = self._connect_to_server()
        if not result:
            self.restore_ui.emit()

    def _connect_to_server(self):
        if self.is_connected():
            self.notice.emit('[mqtt:Err] Already connected')
            return False

        if not self.ip or self.port == 0:
            self.notice.emit(f'[mqtt:Err] Enter IP and port')
            return False

        try:
            # 이전 loop_start()가 남아있을 수 있으므로 먼저 정리
            try:
                self.client.loop_stop()
            except Exception:
                pass

            if self.is_require_login:
                self.client.username_pw_set(self.login_id , self.login_pw)

            self.client.connect(self.ip, self.port, keepalive=120)
            self.client.loop_start()
            return True

        except Exception as e:
            self.notice.emit(f'[mqtt:Err] {e}')
            return False

    def disconnect_from_server(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.wait(3000)  # QThread가 완전히 종료될 때까지 최대 3초 대기

    def subscribe(self, topic='', qos=0):
        if not topic or topic in self.topics:
            return False

        self.topics[topic] = qos
        self.client.subscribe(topic, qos)
        self.notice.emit(f'[mqtt] Subscribed to [{topic}] with QoS {qos}')
        return True

    def send_message(self, topic, msg):
        try:
            self.client.publish(topic, msg)
        except Exception as e:
            self.notice.emit(f"[mqtt:Err] Failed to send message: {e}")

    def unsubscribe(self, topic):
        if topic not in self.topics:
            return False

        self.topics.pop(topic)
        self.client.unsubscribe(topic)
        self.notice.emit(f'[mqtt] Unsubscribed from [{topic}]')
        return True


class MqttWidget(QWidget):
    def __init__(self, ui_foam=Ui_Form_Mqtt):
        super().__init__()

        self.ui = ui_foam()
        self.ui.setupUi(self)

        self.client = MqttClientThread()

        self.rx_state = False
        self.rx_count = 0
        # self.pre_rx_count = 0

        self.tx_state = False
        self.tx_count = 0
        # self.pre_tx_count = 0

        self.txrx_timer = QTimer()

        self._init_signal()

    def _init_signal(self):
        self.client.connected.connect(self._on_connected)
        self.client.disconnected.connect(self._on_disconnected)
        self.client.received_message.connect(self._on_message)
        self.client.notice.connect(self._on_notice)
        self.client.restore_ui.connect(self._on_restore_ui)

    def set_defaults(self):
        self.txrx_timer.setInterval(200)
        self.txrx_timer.timeout.connect(self._on_timer_check_txrx_state)

    def end(self):
        self.txrx_timer.stop()
        self.disconnect_from_server()

    def set_ip_port(self, ip, port):
        self.client.set_ip_port(ip, port)
        self.set_ip_port_task(ip, port)

    def set_ip_port_task(self, ip, port):
        ...

    def set_id_pw(self, login_id, login_pw):
        self.client.set_id_pw(login_id, login_pw)
        self.set_id_pw_task(login_id, login_pw)

    def set_id_pw_task(self, login_id, login_pw):
        ...

    def set_require_login(self, state=True):
        self.client.is_require_login = state

    def set_tls(self, file=''):
        self.client.client.tls_set(
            ca_certs=file,  # CA 인증서('*.crt' 파일) 경로
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS_CLIENT
        )
        # SAN 검증 필수 (테스트 시 True 로 임시 우회 가능)
        self.client.client.tls_insecure_set(False)

    def set_topics(self, topics):
        self.client.set_topics(topics)

    def set_topics_task(self, topics):
        ...

    def _on_timer_check_txrx_state(self):
        # tx
        if self.tx_count > 0:
            self.tx_state = True
            self.tx_count = 0
        else:
            self.tx_state = False

        # rx
        if self.rx_count > 0:
            self.rx_state = True
            self.rx_count = 0
        else:
            self.rx_state = False

        self.on_timer_check_txrx_state_task(self.tx_state, self.rx_state)

    def on_timer_check_txrx_state_task(self, tx_state, rx_state):
        ...

    def _on_connected(self):
        self._set_status_style(False)
        self.txrx_timer.start()
        self.on_connected_task()

    def on_connected_task(self):
        ...

    def _on_disconnected(self):
        self.txrx_timer.stop()
        self.on_disconnected_task()

    def on_disconnected_task(self):
        ...

    def _set_status_style(self, is_error=False):
        if is_error:
            self.ui.lineEdit.setStyleSheet('border: 1.5px solid #e53935; border-radius: 4px; padding: 2px 4px;')
        else:
            self.ui.lineEdit.setStyleSheet('')

    def _on_notice(self, msg):
        self._set_status_style('Err' in msg)
        self.on_notice_task(msg)

    def on_notice_task(self, msg):
        ...

    def _on_message(self, tuple_data):
        self.rx_count += 1
        self.on_message_task(tuple_data)

    def on_message_task(self, tuple_data):
        ...

    def _on_restore_ui(self):
        self.on_restore_ui_task()

    def on_restore_ui_task(self):
        ...

    def send_message(self, topic='', msg=''):
        if not self.client.is_connected():
            return

        self.tx_count += 1

        if topic and msg:
            self.client.send_message(topic, msg)
        self.send_message_task(topic, msg)

    def send_message_task(self, topic, msg):
        ...

    def connect_to_server(self):
        if self.client.is_connected():
            return
        if self.client.isRunning():
            return

        self.connect_to_server_pretask()
        self.client.start()

    def connect_to_server_pretask(self):
        ...

    def disconnect_from_server(self):
        if self.client is None:
            return

        if self.client.is_connected():
            self.client.disconnect_from_server()
        self.disconnect_from_server_task()

    def disconnect_from_server_task(self):
        ...
