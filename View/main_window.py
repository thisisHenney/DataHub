#!/usr/bin/env python3
# -*-coding:utf8-*-

import os
import subprocess
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from PySide6.QtCore import QTimer, QPoint, Qt, QThread, Signal
from PySide6.QtGui import QGuiApplication, QCloseEvent
from PySide6.QtWidgets import QMainWindow, QLabel, QPushButton, QMessageBox
from Lib.File import make_dir, FileMergingThread, FileWriterThread, get_writer_queue_size, clear_writer_queue
from View.main_window_ui import Ui_MainWindow


class _ClearDataThread(QThread):
    """received_data 폴더의 모든 파일을 비동기로 삭제."""
    progress = Signal(int, int)  # (current, total)
    finished_with_stats = Signal(int, int)  # (deleted, total_size)

    def __init__(self, data_path, parent=None):
        super().__init__(parent)
        self._data_path = data_path

    def run(self):
        all_files = []
        for root, dirs, files in os.walk(self._data_path):
            for f in files:
                all_files.append(os.path.join(root, f))

        total = len(all_files)
        total_size = 0
        for f in all_files:
            try:
                total_size += os.path.getsize(f)
            except OSError:
                pass

        deleted = 0
        last_emit = 0
        for i, filepath in enumerate(all_files):
            try:
                os.remove(filepath)
                deleted += 1
            except Exception:
                pass
            # UI 갱신 부하 줄이기 위해 일정 간격으로만 emit
            if i - last_emit >= 50 or i + 1 == total:
                self.progress.emit(i + 1, max(total, 1))
                last_emit = i

        self.finished_with_stats.emit(deleted, total_size)

from View.Clients.client_pintel import ClientPintel
from View.Clients.client_vueron_01 import ClientVueron01
from View.Clients.client_vueron_02 import ClientVueron02
from View.Clients.client_keti import ClientKeti
from View.Clients.client_e8ight import ClientE8ight
from View.Clients.client_nextfoam import ClientNextfoam


class MainWindow(QMainWindow):
    def __init__(self, app_info):
        super().__init__()
        self.app_info = app_info

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.vtk_data_dict_pintel = {}
        self.vtk_data_dict_keti = {}
        self.vtk_data_dict_vueron = {}

        self.pintel_lock = threading.Lock()
        self.keti_lock = threading.Lock()
        self.vueron_lock = threading.Lock()

        self.is_reconnect = False
        self._clear_thread = None

        self.client_pintel = ClientPintel(self, self.vtk_data_dict_pintel, self.pintel_lock)
        self.client_vueron_01 = ClientVueron01(self, self.vtk_data_dict_vueron, self.vueron_lock)
        self.client_vueron_02 = ClientVueron02(self, self.vtk_data_dict_vueron, self.vueron_lock)
        self.client_keti = ClientKeti(self, self.vtk_data_dict_keti, self.keti_lock)
        self.client_e8ight = ClientE8ight(self)
        self.client_nextfoam = ClientNextfoam(self)

        now = datetime.now()
        total_seconds = now.timestamp()
        rounded_seconds = round(total_seconds / 0.2) * 0.2
        self.target_time = datetime.fromtimestamp(rounded_seconds)

        self.count_thread = 0
        self.num_merge_threads = 3
        self.merging_thread_list = [
            FileMergingThread(self, self.vtk_data_dict_pintel,
                              self.vtk_data_dict_keti,
                              self.vtk_data_dict_vueron,
                              self.target_time, 0,
                              self.app_info,
                              self.pintel_lock, self.keti_lock, self.vueron_lock)
            for i in range(self.num_merge_threads)]
        for mt in self.merging_thread_list:
            mt.merge_info.connect(self._on_merge_info)

        self.num_writer_threads = 4
        self.writer_thread_list = [FileWriterThread() for _ in range(self.num_writer_threads)]
        for wt in self.writer_thread_list:
            wt.start()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.make_file_merging_thread)
        self.timer.start(500)

        self._initialize()
        self._setup_merge_info_ui()
        self.ui.groupBox_2.setTitle('< Log >')

        self.setWindowTitle(f'DataHub-v1.2-[{self.app_info.data_path}]')

    def make_file_merging_thread(self):
        # target_time을 0.2초 grid로 정렬하여 jitter 흡수
        now = datetime.now()
        rounded_seconds = round(now.timestamp() / 0.2) * 0.2
        self.target_time = datetime.fromtimestamp(rounded_seconds)

        # idle한 머지 스레드를 찾아서 할당 (한 스레드가 hang해도 다른 스레드 사용 가능)
        n = len(self.merging_thread_list)
        chosen = None
        for offset in range(n):
            idx = (self.count_thread + offset) % n
            mt = self.merging_thread_list[idx]
            if not mt.isRunning():
                chosen = (idx, mt)
                break
        if chosen is None:
            return  # 모든 머지 스레드가 바쁨

        idx, merging_thread = chosen
        merging_thread._stopped = False
        merging_thread.target_time = self.target_time
        merging_thread.start()

        self.count_thread = (idx + 1) % n

    def _initialize(self):
        self.ui.pushButton_connect_all.clicked.connect(self.clicked_connect_all)
        self.ui.pushButton_disconnect_all.clicked.connect(self.clicked_disconnect_all)

        self.ui.pushButton_open_received_path_datahub.clicked.connect(self.clicked_open_received_path_datahub)
        # self.ui.pushButton_setting_datahub.clicked.connect(self.clicked_)
        self.ui.checkBox_auto_reconnect.stateChanged.connect(self.onStateChanged_auto_reconnect)

        self.ui.pushButton_create_sim_data.clicked.connect(self.clicked_create_sim_data)
        self.ui.pushButton_show_log.clicked.connect(self.clicked_show_log)
        self.ui.pushButton_open_solver_data_log.clicked.connect(self.clicked_open_solver_data_log)

        self.ui.pushButton_run_live_viewer.clicked.connect(self.clicked_run_live_viewer)

        self.ui.pushButton_open_received_path_vueron.clicked.connect(self.clicked_open_received_path_vueron)
        self.ui.pushButton_open_received_path_pintel.clicked.connect(self.clicked_open_received_path_pintel)
        self.ui.pushButton_open_received_path_keti.clicked.connect(self.clicked_open_received_path_keti)
        self.ui.pushButton_setting_keti.clicked.connect(self.clicked_setting_keti)

        self.ui.pushButton_open_received_path_nextfoam.clicked.connect(self.clicked_open_received_path_nextfoam)

        self.ui.pushButton_connect_all.setStyleSheet(
            'background-color: #4a8c6f; color: white; border: 1px solid #3d7a5f;')
        self.ui.pushButton_disconnect_all.setStyleSheet(
            'background-color: #8c5a5a; color: white; border: 1px solid #7a4d4d;')
        self.ui.pushButton_run_live_viewer.setStyleSheet(
            'background-color: #6b5b8a; color: white; border: 1px solid #5c4d78;')

        self._setup_progressbars()
        self._setup_groupbox_sizing()

        self.ui.horizontalLayout_pintel.addWidget(self.client_pintel)
        self.ui.horizontalLayout_vueron_1.addWidget(self.client_vueron_01)
        self.ui.horizontalLayout_vueron_2.addWidget(self.client_vueron_02)
        self.ui.horizontalLayout_keti.addWidget(self.client_keti)
        self.ui.horizontalLayout_nextfoam.addWidget(self.client_nextfoam)

        make_dir(self.app_info.settings_path)
        make_dir(self.app_info.data_path)

    def _setup_groupbox_sizing(self):
        pass

    def _setup_progressbars(self):
        tx_style = ("QProgressBar { border: 1px solid #c0c4ca; background-color: #f0ecf4; }"
                    "QProgressBar::chunk { background-color: #ab47bc; width: 5px; margin: 1px; }")
        rx_style = ("QProgressBar { border: 1px solid #c0c4ca; background-color: #ecf4ec; }"
                    "QProgressBar::chunk { background-color: #43a047; width: 5px; margin: 1px; }")
        for name in ['pintel', 'keti', 'vueron', 'nextfoam']:
            tx = getattr(self.ui, f'progressBar_tx_{name}', None)
            rx = getattr(self.ui, f'progressBar_rx_{name}', None)
            if tx:
                tx.setStyleSheet(tx_style)
            if rx:
                rx.setStyleSheet(rx_style)

    def log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        text = f'[{timestamp}] {msg}'
        if 'Err' in msg or 'Error' in msg or 'Invalid' in msg:
            self.ui.plainTextEdit_output.appendHtml(
                f'<span style="color: #e53935;">{text}</span>')
        else:
            self.ui.plainTextEdit_output.appendPlainText(text)

    def set_defaults(self):
        self.client_pintel.set_defaults()
        self.client_vueron_01.set_defaults()
        self.client_vueron_02.set_defaults()
        self.client_keti.set_defaults()
        self.client_nextfoam.set_defaults()

        self.ui.checkBox_auto_reconnect.setChecked(True)

        self.set_window_center()
        # self.showMaximized()

    def closeEvent(self, e: QCloseEvent):
        reply = QMessageBox.question(
            self, 'Exit',
            'Are you sure you want to quit?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.end()
            e.accept()
        else:
            e.ignore()

    def close_window(self):
        self.close()

    def end(self):
        self.timer.stop()
        if hasattr(self, 'queue_timer'):
            self.queue_timer.stop()

        for mt in self.merging_thread_list:
            mt.stop()

        self.client_pintel.end()
        self.client_vueron_01.end()
        self.client_vueron_02.end()
        self.client_keti.end()
        self.client_e8ight.end()
        self.client_nextfoam.end()

        for mt in self.merging_thread_list:
            mt.wait(5000)

        for wt in self.writer_thread_list:
            wt.stop()
        for wt in self.writer_thread_list:
            wt.wait(5000)

        if hasattr(self, '_clear_thread') and self._clear_thread is not None:
            self._clear_thread.wait(2000)

    def _setup_merge_info_ui(self):
        from PySide6.QtWidgets import QGridLayout, QFrame

        layout = self.ui.groupBox_datahub.layout()
        if layout is None:
            from PySide6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self.ui.groupBox_datahub)

        style_title = 'font-size: 8pt; color: #7f8c9b;'
        style_value = 'font-size: 9pt; font-weight: bold; color: #2c3e50;'

        from PySide6.QtWidgets import QSpacerItem, QSizePolicy

        grid = QGridLayout()
        grid.setContentsMargins(4, 8, 4, 4)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(12)

        lbl = QLabel('Now')
        lbl.setStyleSheet(style_title)
        grid.addWidget(lbl, 0, 0)
        self.label_merge_now = QLabel('-')
        self.label_merge_now.setStyleSheet(style_value)
        grid.addWidget(self.label_merge_now, 0, 1)

        lbl = QLabel('Target')
        lbl.setStyleSheet(style_title)
        grid.addWidget(lbl, 1, 0)
        self.label_merge_target = QLabel('-')
        self.label_merge_target.setStyleSheet(style_value)
        grid.addWidget(self.label_merge_target, 1, 1)

        lbl = QLabel('Delay')
        lbl.setStyleSheet(style_title)
        grid.addWidget(lbl, 2, 0)
        self.label_merge_delay = QLabel('-')
        self.label_merge_delay.setStyleSheet(style_value)
        grid.addWidget(self.label_merge_delay, 2, 1)

        lbl = QLabel('Network')
        lbl.setStyleSheet(style_title)
        grid.addWidget(lbl, 3, 0)
        self.label_merge_data = QLabel('-')
        self.label_merge_data.setStyleSheet(style_value)
        grid.addWidget(self.label_merge_data, 3, 1)

        lbl = QLabel('Thread')
        lbl.setStyleSheet(style_title)
        grid.addWidget(lbl, 4, 0)
        self.label_merge_thread = QLabel('-')
        self.label_merge_thread.setStyleSheet(style_value)
        grid.addWidget(self.label_merge_thread, 4, 1)

        layout.addLayout(grid)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        from PySide6.QtWidgets import QProgressBar
        self.progressBar_clear = QProgressBar()
        self.progressBar_clear.setFixedHeight(8)
        self.progressBar_clear.setTextVisible(False)
        self.progressBar_clear.setRange(0, 100)
        self.progressBar_clear.setValue(0)
        self.progressBar_clear.setVisible(False)
        layout.addWidget(self.progressBar_clear)

        self.btn_clear = QPushButton('Clear Data')
        self.btn_clear.setFixedHeight(20)
        self.btn_clear.setStyleSheet('font-size: 7pt; padding: 1px 6px;')
        self.btn_clear.clicked.connect(self._on_clear_data)
        layout.addWidget(self.btn_clear)

        # 1초마다 Queue 정보 업데이트
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self._update_queue_info)
        self.queue_timer.start(1000)

    def _on_clear_data(self):
        if hasattr(self, '_clear_thread') and self._clear_thread is not None and self._clear_thread.isRunning():
            return

        reply = QMessageBox.question(
            self, 'Clear Data',
            'received_data 내 모든 파일을 삭제하시겠습니까?\n(폴더는 유지됩니다)',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        self.btn_clear.setEnabled(False)
        self._set_data_pause(True)

        # saver가 stop 직전에 enqueue한 writer 작업을 비워서 삭제와의 race 방지
        clear_writer_queue()

        # vtk_data_dict 비우기
        with self.pintel_lock:
            self.vtk_data_dict_pintel.clear()
        with self.keti_lock:
            self.vtk_data_dict_keti.clear()
        with self.vueron_lock:
            self.vtk_data_dict_vueron.clear()

        # saver stack 비우기
        for client in [self.client_pintel, self.client_keti,
                       self.client_vueron_01, self.client_vueron_02]:
            if hasattr(client, 'savers'):
                for saver in client.savers:
                    saver.stack.clear()

        self.progressBar_clear.setRange(0, 1)
        self.progressBar_clear.setValue(0)
        self.progressBar_clear.setVisible(True)

        self._clear_thread = _ClearDataThread(self.app_info.data_path, self)
        self._clear_thread.progress.connect(self._on_clear_progress)
        self._clear_thread.finished_with_stats.connect(self._on_clear_finished)
        self._clear_thread.finished.connect(self._clear_thread.deleteLater)
        self._clear_thread.start()

    def _on_clear_progress(self, current, total):
        if self.progressBar_clear.maximum() != total:
            self.progressBar_clear.setRange(0, total)
        self.progressBar_clear.setValue(current)

    def _on_clear_finished(self, deleted, total_size):
        self.progressBar_clear.setVisible(False)
        self.btn_clear.setEnabled(True)
        self._set_data_pause(False)
        self.log(f'[Clear] {deleted} files ({self._format_size(total_size)}) deleted from {self.app_info.data_path}')
        self._clear_thread = None

    @staticmethod
    def _format_size(size_bytes):
        if size_bytes < 1024:
            return f'{size_bytes} B'
        elif size_bytes < 1024 * 1024:
            return f'{size_bytes / 1024:.1f} KB'
        elif size_bytes < 1024 * 1024 * 1024:
            return f'{size_bytes / (1024 * 1024):.1f} MB'
        else:
            return f'{size_bytes / (1024 * 1024 * 1024):.2f} GB'

    def _set_data_pause(self, pause):
        """pause=True: saver 스레드 중단, False: 재시작"""
        for client in [self.client_pintel, self.client_keti,
                       self.client_vueron_01, self.client_vueron_02]:
            if hasattr(client, 'savers'):
                for saver in client.savers:
                    if pause:
                        saver.stop()
                        saver.wait(2000)
                    else:
                        saver.is_running = True
                        saver._event.clear()
                        if not saver.isRunning():
                            saver.start()

    def _update_queue_info(self):
        p = len(self.vtk_data_dict_pintel)
        k = len(self.vtk_data_dict_keti)
        v = len(self.vtk_data_dict_vueron)
        busy = sum(1 for mt in self.merging_thread_list if mt.isRunning())
        self.label_merge_data.setText(f'P:{p}  K:{k}  V:{v}')
        self.label_merge_thread.setText(f'{busy} / {len(self.merging_thread_list)}')
        self.label_merge_now.setText(datetime.now().strftime('%H:%M:%S.%f')[:-3])

    def _on_merge_info(self, info):
        parts = info.split(' | ')
        for p in parts:
            if 'target:' in p:
                self.label_merge_target.setText(p.split('target:')[1].strip())
            elif 'delay:' in p:
                self.label_merge_delay.setText(p.split('delay:')[1].strip())

    def set_window_center(self):
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.left(), screen_geometry.top())

    def clicked_connect_all(self):
        self.log('Connect All')
        self.client_pintel.connect_to_server()
        self.client_vueron_01.connect_to_server()
        self.client_vueron_02.connect_to_server()
        self.client_keti.connect_to_server()
        self.client_nextfoam.connect_to_server()

    def clicked_disconnect_all(self):
        self.log('Disconnect All')
        self.client_pintel.disconnect_from_server()
        self.client_vueron_01.disconnect_from_server()
        self.client_vueron_02.disconnect_from_server()
        self.client_keti.disconnect_from_server()
        self.client_nextfoam.disconnect_from_server()

        if self.ui.checkBox_auto_reconnect.isChecked():
            self.ui.checkBox_auto_reconnect.setChecked(False)

    def clicked_open_received_path_datahub(self):
        self.log('Open received data folder')
        os.startfile(self.app_info.data_path)

    def onStateChanged_auto_reconnect(self, state):
        if state == 0:
            self.is_reconnect = False
            self.log('Auto reconnect: OFF')
        elif state == 2:
            self.is_reconnect = True
            self.log('Auto reconnect: ON')

    def clicked_create_sim_data(self):
        self.log('Create Sim Data')
        if self.app_info.on_point_data != 1:
            self.app_info.on_point_data = 0

    def clicked_show_log(self):
        self.log('Open log folder')
        os.startfile(self.app_info.data_path)

    def clicked_open_solver_data_log(self):
        self.log('Open solver data log')
        os.startfile(self.app_info.e8ight_path/'Send')

    def clicked_run_live_viewer(self):
        self.log('Launch Live Viewer')
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable, '--live-viewer'], env=os.environ.copy())
        else:
            main_py = Path(os.path.dirname(__file__)).parent / 'main.py'
            subprocess.Popen([sys.executable, str(main_py), '--live-viewer'], env=os.environ.copy())

    def clicked_open_received_path_vueron(self):
        self.log('Open Vueron received folder')
        os.startfile(self.app_info.vueron_01_path)
        os.startfile(self.app_info.vueron_02_path)

    def clicked_open_received_path_pintel(self):
        self.log('Open Pintel received folder')
        os.startfile(self.app_info.pintel_path)

    def clicked_open_received_path_keti(self):
        self.log('Open KETI received folder')
        os.startfile(self.app_info.keti_path)

    def clicked_setting_pintel(self):
        self.log('Setting Pintel (not implemented)')
        # self.client_pintel.send_message('/topic/test',
        #                               ' {"timestamp": "2025-05-15 16:52:47.953", "common": [1, 2, 0, 0, 181514875]}')

    def clicked_setting_keti(self):
        self.log('Setting KETI (not implemented)')

    def clicked_open_received_path_nextfoam(self):
        self.log('Open NEXTfoam received folder')
        os.startfile(self.app_info.nextfoam_path)
