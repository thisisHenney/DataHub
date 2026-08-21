#!/usr/bin/env python3
# -*- coding:utf8 -*-
"""Self-contained MQTT client thread (paho-mqtt + PySide6 signals).

Adapted from DataHub's Lib/Network/MQTT.py, but generalized to subscribe to an
arbitrary topic filter and deliberately kept free of any import from this
repo's Lib/View packages, so this tool stays copyable on its own.
"""

import ssl
import time

import paho.mqtt.client as mqtt
from PySide6.QtCore import QThread, Signal


class MqttClientThread(QThread):
    connected = Signal()
    disconnected = Signal()
    # (topic, payload_bytes, qos, retain, timestamp)
    message_received = Signal(str, bytes, int, bool, float)
    notice = Signal(str)

    def __init__(self):
        super().__init__()

        self.ip = 'localhost'
        self.port = 1883
        self.client_id = ''
        self.is_require_login = False
        self.login_id = None
        self.login_pw = None
        self.use_tls = False

        self.subscriptions = {}  # {topic_filter: qos}

        self.client = mqtt.Client(client_id=self.client_id or '', clean_session=True)
        self._init_callbacks()

    def _init_callbacks(self):
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe

    def is_connected(self):
        return self.client.is_connected()

    def configure(self, ip, port, client_id='', login_id=None, login_pw=None, use_tls=False):
        if ip:
            self.ip = ip
        if port:
            self.port = int(port)
        self.client_id = client_id or ''
        if login_id and login_pw:
            self.is_require_login = True
            self.login_id = login_id
            self.login_pw = login_pw
        else:
            self.is_require_login = False
        self.use_tls = use_tls

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected.emit()
            for topic_filter, qos in self.subscriptions.items():
                self.client.subscribe(topic_filter, qos)
                self.notice.emit(f'Subscribed to [{topic_filter}] (QoS {qos})')
        else:
            try:
                reason = mqtt.connack_string(rc)
            except Exception:
                reason = str(rc)
            self.notice.emit(f'[Err] Connect failed: {reason}')

    def _on_disconnect(self, client, userdata, rc):
        try:
            reason = mqtt.error_string(rc)
        except Exception:
            reason = 'unknown'
        if rc == 0:
            self.notice.emit(f'Disconnected (rc=0, {reason})')
        else:
            self.notice.emit(f'[Err] Unexpected disconnect (rc={rc}, {reason})')
        self.disconnected.emit()

    def _on_message(self, client, userdata, msg):
        self.message_received.emit(msg.topic, bytes(msg.payload), msg.qos, bool(msg.retain), time.time())

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        if any(q == 128 for q in granted_qos):
            self.notice.emit('[Err] Subscription rejected by broker')

    def run(self):
        if self.is_connected():
            self.notice.emit('[Err] Already connected')
            return
        if not self.ip or not self.port:
            self.notice.emit('[Err] IP/Port required')
            return

        try:
            try:
                self.client.loop_stop()
            except Exception:
                pass

            # client_id가 바뀌었을 수 있으니 매 연결마다 새 Client 인스턴스로 재구성
            self.client = mqtt.Client(client_id=self.client_id or '', clean_session=True)
            self._init_callbacks()

            if self.is_require_login:
                self.client.username_pw_set(self.login_id, self.login_pw)

            if self.use_tls:
                self.client.tls_set(cert_reqs=ssl.CERT_NONE)
                self.client.tls_insecure_set(True)

            self.client.connect(self.ip, self.port, keepalive=30)
            self.client.loop_forever(retry_first_connection=False)
        except Exception as e:
            self.notice.emit(f'[Err] {e}')
            self.disconnected.emit()

    def disconnect_from_server(self):
        try:
            self.client.disconnect()
        except Exception:
            pass

    def subscribe(self, topic_filter, qos=0):
        if not topic_filter or topic_filter in self.subscriptions:
            return False
        self.subscriptions[topic_filter] = qos
        if self.is_connected():
            self.client.subscribe(topic_filter, qos)
            self.notice.emit(f'Subscribed to [{topic_filter}] (QoS {qos})')
        return True

    def unsubscribe(self, topic_filter):
        if topic_filter not in self.subscriptions:
            return False
        self.subscriptions.pop(topic_filter)
        if self.is_connected():
            self.client.unsubscribe(topic_filter)
            self.notice.emit(f'Unsubscribed from [{topic_filter}]')
        return True

    def publish(self, topic, payload, qos=0, retain=False):
        if not self.is_connected():
            self.notice.emit('[Err] Not connected')
            return
        try:
            self.client.publish(topic, payload, qos=qos, retain=retain)
        except Exception as e:
            self.notice.emit(f'[Err] Publish failed: {e}')
