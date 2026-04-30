#!/usr/bin/env python3
# -*- coding:utf8 -*-

import asyncio
import websockets
import json
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import QWidget
from PySide6.QtWebSockets import QWebSocket

from Lib.Network.View.websocket_ui import Ui_Form_WebSocket


class WebSocketClientThread(QThread):
    connected = Signal()
    disconnected = Signal()
    received_message = Signal(tuple)
    notice = Signal(str)
    restore_ui = Signal()

    def __init__(self,):
        super().__init__()

        self.ip = '127.0.0.1'
        self.port = 10205   # 80(ws://), 443(wss://)
        self.path = ''      # /ws/v1/mbembo/area/2
        self.is_secure = False
        self.uri = f'ws://{self.ip}:{self.port}{self.path}'

        self.websocket = None
        self._connected = False
        self._loop = None

    def is_connected(self):
        return self._connected

    def set_ip_port(self, ip:str, port:int, path:str):
        if ip:
            self.ip = ip
        if port:
            self.port = int(port)
        if path:
            self.path = path

    def run(self):
        self._loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect_to_server())

        finally:
            if self._connected:
                self._loop.run_until_complete(self._disconnect())
            self._loop.stop()
            self._loop.close()

    async def _connect_to_server(self):
        if self._connected:
            self.notice.emit("[websocket:Err] Already connected")
            return

        if not self.ip or self.port == 0:
            self.notice.emit(f'[websocket:Err] Enter IP and port')
            return

        try:
            self.uri = f'ws://{self.ip}:{self.port}{self.path}'
            self.notice.emit(f'[websocket] {self.uri}')
            self.websocket = await websockets.connect(self.uri)
            self._connected = True
            self.connected.emit()

            await self.receive_messages()

        except Exception as e:
            self.handle_connection_error(e)
            self.restore_ui.emit()

    async def receive_messages(self):
        try:
            while self._connected:
                message = await self.websocket.recv()
                try:
                    json_data = json.loads(message)
                    data = (json.dumps(json_data, indent=2), None)
                    self.received_message.emit(data)
                except json.JSONDecodeError:
                    # self.handle_receive_error(ValueError("Invalid JSON data received"))
                    ...

        except websockets.exceptions.ConnectionClosedOK:
            pass
        except Exception as e:
            self.handle_receive_error(e)

    def send_message(self, message):
        if self.websocket and self._connected:
            asyncio.run_coroutine_threadsafe(self.websocket.send(message), self._loop)

    async def _disconnect(self):
        if not self._connected:
            return
        if self.websocket:
            await asyncio.shield(self.websocket.close())
        self._connected = False
        self.disconnected.emit()

    def disconnect_from_server(self):
        if self.websocket and self._connected and self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self._loop)
            self.wait(3000)  # QThread가 완전히 종료될 때까지 최대 3초 대기

    def handle_connection_error(self, error):
        error_messages = {
            websockets.exceptions.InvalidURI: "[websocket:Err] Invalid server URI.",
            websockets.exceptions.InvalidHandshake: "[websocket:Err] Invalid handshake with server.",
            websockets.exceptions.SecurityError: "[websocket:Err] Security error occurred.",
        }
        message = error_messages.get(type(error), "[websocket:Err] Server is not running")
        self.notice.emit(message)

    def handle_receive_error(self, error):
        error_messages = {
            websockets.exceptions.ConnectionClosedError: "[websocket:Err] Connection lost (server error)",
        }
        message = error_messages.get(type(error), f"[websocket:Err] {error}")
        self.notice.emit(message)


class WebSocketWidget(QWidget):
    def __init__(self, ui_foam=Ui_Form_WebSocket):
        super().__init__()

        self.ui = ui_foam()
        self.ui.setupUi(self)

        self.client = WebSocketClientThread()
        self.rx_state = False
        self.rx_count = 0
        self.pre_rx_count = 0

        self.tx_state = False
        self.tx_count = 0
        self.pre_tx_count = 0

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

    def set_ip_port(self, ip, port, path=''):
        self.client.set_ip_port(ip, port, path)
        self.set_ip_port_task(ip, port, path)

    def set_ip_port_task(self, ip, port, path):
        ...

    def _on_timer_check_txrx_state(self):
        # tx
        if self.tx_count > self.pre_tx_count:
            self.tx_state = True
        else:
            self.tx_state = False

        self.pre_tx_count = self.tx_count

        # rx
        if self.rx_count > self.pre_rx_count:
            self.rx_state = True
        else:
            self.rx_state = False

        self.pre_rx_count = self.rx_count

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

    def send_message(self, msg1='', msg2=None):
        if not self.client.is_connected():
            return

        self.tx_count += 1

        if msg1:
            self.client.send_message(msg1)
        self.send_message_task(msg1)

    def send_message_task(self, msg):
        ...

    def connect_to_server(self):
        if self.client.is_connected():
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
