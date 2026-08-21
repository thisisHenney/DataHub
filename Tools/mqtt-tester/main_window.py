#!/usr/bin/env python3
# -*- coding:utf8 -*-

import json
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QCheckBox, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QPlainTextEdit, QListWidget,
    QListWidgetItem, QFileDialog, QGroupBox, QMessageBox,
)

from mqtt_client import MqttClientThread
from settings import load_settings, save_settings

QOS_OPTIONS = ['0', '1', '2']


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MQTT Tester')
        self.resize(1200, 760)

        self.client = MqttClientThread()
        self.client.connected.connect(self._on_connected)
        self.client.disconnected.connect(self._on_disconnected)
        self.client.message_received.connect(self._on_message)
        self.client.notice.connect(self._on_notice)

        self.topic_data = {}   # {full_topic: {'payload':bytes,'qos':int,'retain':bool,'ts':float,'count':int}}
        self._tree_nodes = {}  # {path_prefix: QTreeWidgetItem}
        self._selected_topic = None
        self._dirty_topics = set()

        self._build_ui()
        self._load_settings()

        # 대량 수신 시 메시지마다 트리/상세뷰를 갱신하면 GUI 스레드가 밀려서
        # 응답없음 상태가 되므로, 화면 갱신은 타이머로 묶어서(batch) 처리한다.
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(150)
        self._flush_timer.timeout.connect(self._flush_pending)
        self._flush_timer.start()

    # ---------------------------------------------------------------- UI

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        root.addWidget(self._build_connection_bar())
        root.addWidget(self._build_subscribe_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_topic_tree())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, stretch=1)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(110)
        root.addWidget(self.log_view)

    def _build_connection_bar(self):
        box = QGroupBox('Connection')
        layout = QHBoxLayout(box)

        self.edit_ip = QLineEdit('localhost')
        self.edit_port = QLineEdit('1883')
        self.edit_client_id = QLineEdit('')
        self.edit_client_id.setPlaceholderText('client id (optional)')
        self.edit_user = QLineEdit('')
        self.edit_user.setPlaceholderText('user (broker마다 필요 여부 다름)')
        self.edit_pass = QLineEdit('')
        self.edit_pass.setPlaceholderText('password')
        self.edit_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.check_tls = QCheckBox('TLS')

        self.btn_connect = QPushButton('Connect')
        self.btn_disconnect = QPushButton('Disconnect')
        self.btn_disconnect.setEnabled(False)
        self.label_status = QLabel('Disconnected')

        self.btn_connect.clicked.connect(self._on_click_connect)
        self.btn_disconnect.clicked.connect(self._on_click_disconnect)

        for label, widget in [('IP', self.edit_ip), ('Port', self.edit_port),
                               ('Client ID', self.edit_client_id), ('User', self.edit_user),
                               ('Pass', self.edit_pass)]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)
        layout.addWidget(self.check_tls)
        layout.addWidget(self.btn_connect)
        layout.addWidget(self.btn_disconnect)
        layout.addWidget(self.label_status)
        layout.addStretch(1)
        return box

    def _build_subscribe_bar(self):
        box = QGroupBox('Subscribe')
        layout = QHBoxLayout(box)

        self.edit_topic_filter = QLineEdit('#')
        self.combo_sub_qos = QComboBox()
        self.combo_sub_qos.addItems(QOS_OPTIONS)
        self.btn_subscribe = QPushButton('Subscribe')
        self.btn_subscribe.clicked.connect(self._on_click_subscribe)
        self.edit_topic_filter.returnPressed.connect(self._on_click_subscribe)

        self.list_subs = QListWidget()
        self.list_subs.setMaximumHeight(60)
        self.list_subs.itemDoubleClicked.connect(self._on_unsubscribe_item)

        layout.addWidget(QLabel('Topic filter'))
        layout.addWidget(self.edit_topic_filter, stretch=1)
        layout.addWidget(QLabel('QoS'))
        layout.addWidget(self.combo_sub_qos)
        layout.addWidget(self.btn_subscribe)
        layout.addWidget(QLabel('Active (double-click to unsubscribe):'))
        layout.addWidget(self.list_subs, stretch=2)
        return box

    def _build_topic_tree(self):
        box = QGroupBox('Topics')
        layout = QVBoxLayout(box)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Topic', 'Count', 'Last seen'])
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        layout.addWidget(self.tree)
        return box

    def _build_right_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        info_row = QHBoxLayout()
        self.label_detail_topic = QLabel('-')
        self.label_detail_meta = QLabel('-')
        self.btn_save = QPushButton('Save to file...')
        self.btn_save.clicked.connect(self._on_click_save)
        info_row.addWidget(QLabel('Topic:'))
        info_row.addWidget(self.label_detail_topic, stretch=1)
        info_row.addWidget(self.label_detail_meta)
        info_row.addWidget(self.btn_save)
        layout.addLayout(info_row)

        tabs = QTabWidget()
        self.raw_view = QPlainTextEdit()
        self.raw_view.setReadOnly(True)
        tabs.addTab(self.raw_view, 'Raw')

        self.json_tree = QTreeWidget()
        self.json_tree.setHeaderLabels(['Key', 'Value'])
        tabs.addTab(self.json_tree, 'JSON')
        layout.addWidget(tabs, stretch=2)

        layout.addWidget(self._build_publish_form())
        return container

    def _build_publish_form(self):
        box = QGroupBox('Publish')
        layout = QVBoxLayout(box)

        form = QFormLayout()
        self.edit_pub_topic = QLineEdit('')
        form.addRow('Topic', self.edit_pub_topic)
        layout.addLayout(form)

        self.edit_pub_payload = QPlainTextEdit()
        self.edit_pub_payload.setMaximumHeight(80)
        layout.addWidget(self.edit_pub_payload)

        row = QHBoxLayout()
        self.combo_pub_qos = QComboBox()
        self.combo_pub_qos.addItems(QOS_OPTIONS)
        self.check_pub_retain = QCheckBox('Retain')
        self.btn_publish = QPushButton('Publish')
        self.btn_publish.clicked.connect(self._on_click_publish)
        row.addWidget(QLabel('QoS'))
        row.addWidget(self.combo_pub_qos)
        row.addWidget(self.check_pub_retain)
        row.addStretch(1)
        row.addWidget(self.btn_publish)
        layout.addLayout(row)
        return box

    # ------------------------------------------------------------- events

    def _log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_view.appendPlainText(f'[{timestamp}] {msg}')

    def _on_click_connect(self):
        ip = self.edit_ip.text().strip()
        try:
            port = int(self.edit_port.text().strip())
        except ValueError:
            QMessageBox.warning(self, 'MQTT Tester', 'Port must be a number')
            return

        self.client.configure(
            ip, port,
            client_id=self.edit_client_id.text().strip(),
            login_id=self.edit_user.text().strip() or None,
            login_pw=self.edit_pass.text() or None,
            use_tls=self.check_tls.isChecked(),
        )
        self.btn_connect.setEnabled(False)
        self.label_status.setText('Connecting...')
        self.client.start()
        self._save_settings()

    def _on_click_disconnect(self):
        self.client.disconnect_from_server()

    def _on_connected(self):
        self.label_status.setText('Connected')
        self.btn_connect.setEnabled(False)
        self.btn_disconnect.setEnabled(True)
        self._log('Connected')

    def _on_disconnected(self):
        self.label_status.setText('Disconnected')
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self._log('Disconnected')

    def _on_notice(self, msg):
        self._log(msg)
        if msg.startswith('[Err]') and not self.client.is_connected():
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.label_status.setText('Disconnected')

    def _on_click_subscribe(self):
        topic_filter = self.edit_topic_filter.text().strip()
        if not topic_filter:
            return
        qos = int(self.combo_sub_qos.currentText())
        if self.client.subscribe(topic_filter, qos):
            item = QListWidgetItem(f'{topic_filter} (QoS {qos})')
            item.setData(Qt.ItemDataRole.UserRole, topic_filter)
            self.list_subs.addItem(item)
            self._save_settings()

    def _on_unsubscribe_item(self, item: QListWidgetItem):
        topic_filter = item.data(Qt.ItemDataRole.UserRole)
        self.client.unsubscribe(topic_filter)
        self.list_subs.takeItem(self.list_subs.row(item))
        self._save_settings()

    def _on_message(self, topic, payload, qos, retain, ts):
        entry = self.topic_data.get(topic)
        if entry is None:
            entry = {'count': 0}
            self.topic_data[topic] = entry
        entry['payload'] = payload
        entry['qos'] = qos
        entry['retain'] = retain
        entry['ts'] = ts
        entry['count'] += 1

        self._dirty_topics.add(topic)

    def _flush_pending(self):
        if not self._dirty_topics:
            return
        dirty, self._dirty_topics = self._dirty_topics, set()

        self.tree.setUpdatesEnabled(False)
        try:
            for topic in dirty:
                entry = self.topic_data.get(topic)
                if entry is not None:
                    self._update_tree_node(topic, entry)
        finally:
            self.tree.setUpdatesEnabled(True)

        if self._selected_topic in dirty:
            self._show_detail(self._selected_topic)

    def _update_tree_node(self, topic, entry):
        parts = topic.split('/')
        parent = None
        path = ''
        for part in parts:
            path = part if not path else f'{path}/{part}'
            node = self._tree_nodes.get(path)
            if node is None:
                node = QTreeWidgetItem([part, '', ''])
                if parent is None:
                    self.tree.addTopLevelItem(node)
                else:
                    parent.addChild(node)
                self._tree_nodes[path] = node
            parent = node

        # parent(leaf) now holds the full-topic node
        leaf = parent
        leaf.setText(1, str(entry['count']))
        leaf.setText(2, datetime.fromtimestamp(entry['ts']).strftime('%H:%M:%S.%f')[:-3])
        leaf.setData(0, Qt.ItemDataRole.UserRole, topic)

    def _on_tree_selection_changed(self):
        items = self.tree.selectedItems()
        if not items:
            return
        topic = items[0].data(0, Qt.ItemDataRole.UserRole)
        if not topic:
            return
        self._selected_topic = topic
        self._show_detail(topic)

    def _show_detail(self, topic):
        entry = self.topic_data.get(topic)
        if entry is None:
            return
        self.label_detail_topic.setText(topic)
        dt = datetime.fromtimestamp(entry['ts']).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        self.label_detail_meta.setText(
            f"QoS {entry['qos']} | retain={entry['retain']} | count={entry['count']} | {dt}")

        payload = entry['payload']
        try:
            text = payload.decode('utf-8')
        except UnicodeDecodeError:
            text = repr(payload)
        self.raw_view.setPlainText(text)

        self.json_tree.clear()
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            parsed = None
        if parsed is not None:
            self._populate_json_tree(self.json_tree.invisibleRootItem(), parsed)
            self.json_tree.expandToDepth(1)

    def _populate_json_tree(self, parent_item, value):
        if isinstance(value, dict):
            for key, val in value.items():
                self._add_json_node(parent_item, str(key), val)
        elif isinstance(value, list):
            for idx, val in enumerate(value):
                self._add_json_node(parent_item, f'[{idx}]', val)
        else:
            parent_item.addChild(QTreeWidgetItem(['', json.dumps(value)]))

    def _add_json_node(self, parent_item, key, value):
        if isinstance(value, (dict, list)):
            node = QTreeWidgetItem([key, ''])
            parent_item.addChild(node)
            self._populate_json_tree(node, value)
        else:
            parent_item.addChild(QTreeWidgetItem([key, json.dumps(value)]))

    def _on_click_save(self):
        if not self._selected_topic:
            return
        entry = self.topic_data.get(self._selected_topic)
        if entry is None:
            return
        default_name = self._selected_topic.replace('/', '_') + '.json'
        path, _ = QFileDialog.getSaveFileName(self, 'Save payload', default_name)
        if not path:
            return
        with open(path, 'wb') as f:
            f.write(entry['payload'])
        self._log(f'Saved payload to {path}')

    def _on_click_publish(self):
        topic = self.edit_pub_topic.text().strip()
        if not topic:
            QMessageBox.warning(self, 'MQTT Tester', 'Enter a topic to publish to')
            return
        payload = self.edit_pub_payload.toPlainText()
        qos = int(self.combo_pub_qos.currentText())
        retain = self.check_pub_retain.isChecked()
        self.client.publish(topic, payload, qos=qos, retain=retain)
        self._log(f'Published to [{topic}] (QoS {qos}, retain={retain})')

    # ------------------------------------------------------------ settings

    def _load_settings(self):
        s = load_settings()
        self.edit_ip.setText(s.get('ip', 'localhost'))
        self.edit_port.setText(str(s.get('port', 1883)))
        self.edit_client_id.setText(s.get('client_id', ''))
        self.edit_topic_filter.setText(s.get('topic_filter', '#'))
        for topic_filter in s.get('subscriptions', []):
            item = QListWidgetItem(f'{topic_filter} (QoS 0)')
            item.setData(Qt.ItemDataRole.UserRole, topic_filter)
            self.list_subs.addItem(item)

    def _save_settings(self):
        subs = [self.list_subs.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.list_subs.count())]
        save_settings({
            'ip': self.edit_ip.text().strip(),
            'port': self.edit_port.text().strip(),
            'client_id': self.edit_client_id.text().strip(),
            'topic_filter': self.edit_topic_filter.text().strip(),
            'subscriptions': subs,
        })

    def closeEvent(self, event):
        if self.client.is_connected():
            self.client.disconnect_from_server()
            self.client.wait(2000)
        event.accept()
