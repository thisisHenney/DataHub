#!/usr/bin/env python3
# -*-coding:utf8-*-

import json
import os
import shutil
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


class _BackupThread(QThread):
    """received_data 파일을 사용자 지정 폴더로 비동기 이동 (스냅샷 방식)."""
    progress = Signal(int, int)                 # (current, total)
    finished_with_stats = Signal(int, int, str) # (moved, total_size_bytes, dest_dir)

    def __init__(self, data_path: Path, backup_dest: Path, parent=None):
        super().__init__(parent)
        self._data_path = data_path
        self._backup_dest = backup_dest

    def run(self):
        # 시작 시점 스냅샷 — .tmp(atomic write 중) 제외
        snapshot = []
        for root, dirs, files in os.walk(self._data_path):
            for f in files:
                if not f.endswith('.tmp'):
                    snapshot.append(Path(root) / f)

        total = len(snapshot)
        if total == 0:
            self.finished_with_stats.emit(0, 0, '')
            return

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest_root = self._backup_dest / f'received_data_{ts}'

        moved, total_size, last_emit = 0, 0, 0
        for i, src_path in enumerate(snapshot):
            try:
                rel = src_path.relative_to(self._data_path)
                dst_path = dest_root / rel
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                if not src_path.is_file():
                    continue
                size = src_path.stat().st_size
                shutil.move(str(src_path), str(dst_path))
                moved += 1
                total_size += size
            except Exception:
                pass
            if i - last_emit >= 100 or i + 1 == total:
                self.progress.emit(i + 1, max(total, 1))
                last_emit = i

        self.finished_with_stats.emit(moved, total_size, str(dest_root))


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

        # 각 소스의 송신 주기가 길어 merge 사이클마다 데이터가 없을 수 있음.
        # 신규 데이터 도착 전까지 직전 데이터를 재사용해 union이 비지 않게 함.
        # 체크박스로 ON/OFF 가능 (기본 ON, _setup_backup_ui에서 체크박스 생성 시 확정)
        self._last_pintel_data = None
        self._last_pintel_data_lock = threading.Lock()
        self._last_vueron_data = None
        self._last_vueron_data_lock = threading.Lock()
        self._last_keti_data = None
        self._last_keti_data_lock = threading.Lock()
        self._use_data_cache = True

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

        self._setup_backup_ui()
        self._setup_keti_send_interval()

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
        if hasattr(self, 'backup_trigger_timer'):
            self.backup_trigger_timer.stop()
        if hasattr(self, 'backup_countdown_timer'):
            self.backup_countdown_timer.stop()
        if hasattr(self, '_backup_thread') and self._backup_thread is not None:
            self._backup_thread.wait(5000)

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

        # 전체 데이터 캐시 초기화
        with self._last_pintel_data_lock:
            self._last_pintel_data = None
        with self._last_vueron_data_lock:
            self._last_vueron_data = None
        with self._last_keti_data_lock:
            self._last_keti_data = None

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

    def _setup_backup_ui(self):
        from PySide6.QtWidgets import (QFrame, QProgressBar, QHBoxLayout,
                                       QWidget, QLineEdit, QCheckBox)
        layout = self.ui.verticalLayout_7
        insert_idx = layout.count() - 1  # verticalSpacer_7 바로 앞

        def _sep():
            s = QFrame(self.ui.groupBox_7)
            s.setFrameShape(QFrame.Shape.HLine)
            s.setFrameShadow(QFrame.Shadow.Sunken)
            return s

        layout.insertWidget(insert_idx, _sep()); insert_idx += 1

        # 동시 저장 checkable 버튼
        self.btn_dual_save = QPushButton('동시 저장 대기', self.ui.groupBox_7)
        self.btn_dual_save.setCheckable(True)
        self.btn_dual_save.setChecked(False)
        self.btn_dual_save.setStyleSheet(
            'QPushButton { font-size: 9pt; padding: 2px 4px; }'
            'QPushButton:checked { background-color: #5b8dd9; color: white;'
            ' border: 1px solid #3a6abf; }')
        self.btn_dual_save.toggled.connect(self._toggle_dual_save)
        layout.insertWidget(insert_idx, self.btn_dual_save); insert_idx += 1

        layout.insertWidget(insert_idx, _sep()); insert_idx += 1

        # 백업 경로 행: [LineEdit] [...버튼]
        path_row = QWidget(self.ui.groupBox_7)
        path_hl = QHBoxLayout(path_row)
        path_hl.setContentsMargins(0, 0, 0, 0)
        path_hl.setSpacing(4)
        self.lineEdit_backup_dest = QLineEdit(path_row)
        self.lineEdit_backup_dest.setReadOnly(True)
        self.lineEdit_backup_dest.setPlaceholderText('백업 경로 미설정')
        self.lineEdit_backup_dest.setFixedHeight(22)
        self.lineEdit_backup_dest.setStyleSheet('font-size: 7pt;')
        self.btn_backup_dest = QPushButton('...', path_row)
        self.btn_backup_dest.setFixedSize(24, 22)
        self.btn_backup_dest.setStyleSheet('font-size: 8pt; padding: 0;')
        self.btn_backup_dest.clicked.connect(self._on_select_backup_dest)
        path_hl.addWidget(self.lineEdit_backup_dest, 1)
        path_hl.addWidget(self.btn_backup_dest)
        layout.insertWidget(insert_idx, path_row); insert_idx += 1

        # 상태 레이블 (카운트다운 / 이동중...)
        self.label_backup_status = QLabel('', self.ui.groupBox_7)
        self.label_backup_status.setFixedHeight(16)
        self.label_backup_status.setStyleSheet('font-size: 7pt; color: #7f8c9b;')
        layout.insertWidget(insert_idx, self.label_backup_status); insert_idx += 1

        # 진행 progressbar (평소 hidden)
        self.progressBar_backup = QProgressBar(self.ui.groupBox_7)
        self.progressBar_backup.setFixedHeight(8)
        self.progressBar_backup.setTextVisible(False)
        self.progressBar_backup.setRange(0, 100)
        self.progressBar_backup.setVisible(False)
        layout.insertWidget(insert_idx, self.progressBar_backup); insert_idx += 1

        # 지금 백업 버튼
        self.btn_backup_now = QPushButton('지금 백업', self.ui.groupBox_7)
        self.btn_backup_now.setFixedHeight(22)
        self.btn_backup_now.setStyleSheet('font-size: 7pt; padding: 1px 6px;')
        self.btn_backup_now.clicked.connect(self._on_trigger_backup)
        layout.insertWidget(insert_idx, self.btn_backup_now); insert_idx += 1

        # 구분선
        layout.insertWidget(insert_idx, _sep()); insert_idx += 1

        # 데이터 캐시 기능 안내 라벨
        self.label_data_cache = QLabel('데이터 누락 시 이전 값 재사용', self.ui.groupBox_7)
        self.label_data_cache.setStyleSheet('font-size: 7pt; color: #555;')
        layout.insertWidget(insert_idx, self.label_data_cache); insert_idx += 1

        # 데이터 캐시 ON/OFF 체크박스 (기본 ON)
        self.checkBox_data_cache = QCheckBox('사용함', self.ui.groupBox_7)
        self.checkBox_data_cache.setStyleSheet('font-size: 8pt;')
        self.checkBox_data_cache.setChecked(True)
        self.checkBox_data_cache.toggled.connect(self._toggle_data_cache)
        layout.insertWidget(insert_idx, self.checkBox_data_cache); insert_idx += 1
        self._use_data_cache = True

        # 상태 초기화
        self._backup_dest = None
        self._backup_thread = None
        self._backup_interval_sec = 3600
        self._backup_countdown = self._backup_interval_sec
        self._current_dual_base = None

        # 1시간 백업 트리거 타이머 (경로 설정 후 start)
        self.backup_trigger_timer = QTimer(self)
        self.backup_trigger_timer.setInterval(self._backup_interval_sec * 1000)
        self.backup_trigger_timer.timeout.connect(self._on_trigger_backup)

        # 1초 카운트다운 표시 타이머 (항상 동작)
        self.backup_countdown_timer = QTimer(self)
        self.backup_countdown_timer.setInterval(1000)
        self.backup_countdown_timer.timeout.connect(self._on_backup_countdown_tick)
        self.backup_countdown_timer.start()

        self._load_backup_config()

    # ── 데이터 캐시 토글 ──────────────────────────────────────────────────────

    def _toggle_data_cache(self, checked: bool):
        self._use_data_cache = checked
        if not checked:
            # 끄면 캐시 비워서 즉시 효과 (이후 신규 데이터 없으면 union에 누락)
            with self._last_pintel_data_lock:
                self._last_pintel_data = None
            with self._last_vueron_data_lock:
                self._last_vueron_data = None
            with self._last_keti_data_lock:
                self._last_keti_data = None
            self.log('데이터 캐시 OFF — 신규 데이터 없으면 union에 누락')
        else:
            self.log('데이터 캐시 ON — 신규 데이터 없으면 직전 데이터 재사용')

    # ── 자동 백업 핸들러 ──────────────────────────────────────────────────────

    def _on_select_backup_dest(self):
        if self._backup_thread is not None and self._backup_thread.isRunning():
            return  # 이동 중 경로 변경 차단
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, '백업 폴더 선택')
        if not folder:
            return
        self._backup_dest = Path(folder)
        self.lineEdit_backup_dest.setText(folder)
        self._save_backup_config()
        self._backup_countdown = self._backup_interval_sec
        self.backup_trigger_timer.stop()
        self.backup_trigger_timer.start()
        self.log(f'[Backup] 경로 설정: {folder}')

    def _on_trigger_backup(self):
        if not self._backup_dest:
            self.log('[Backup] 백업 경로가 설정되지 않았습니다.')
            return
        if self._backup_thread is not None and self._backup_thread.isRunning():
            self.log('[Backup] 이미 백업 진행 중입니다.')
            return
        self.btn_backup_dest.setEnabled(False)
        self.btn_backup_now.setEnabled(False)
        self.progressBar_backup.setRange(0, 1)
        self.progressBar_backup.setValue(0)
        self.progressBar_backup.setVisible(True)
        self.label_backup_status.setText('이동중...')
        self._backup_thread = _BackupThread(self.app_info.data_path, self._backup_dest, self)
        self._backup_thread.progress.connect(self._on_backup_progress)
        self._backup_thread.finished_with_stats.connect(self._on_backup_finished)
        self._backup_thread.finished.connect(self._backup_thread.deleteLater)
        self._backup_thread.start()
        self._backup_countdown = self._backup_interval_sec

    def _on_backup_progress(self, current, total):
        if self.progressBar_backup.maximum() != total:
            self.progressBar_backup.setRange(0, total)
        self.progressBar_backup.setValue(current)

    def _on_backup_finished(self, moved, total_size, dest_dir):
        self.progressBar_backup.setVisible(False)
        self.btn_backup_dest.setEnabled(True)
        self.btn_backup_now.setEnabled(True)
        self._backup_thread = None
        if dest_dir:
            self.log(f'[Backup] {moved}개 ({self._format_size(total_size)}) → {dest_dir}')
        else:
            self.log('[Backup] 이동할 파일이 없습니다.')

    def _on_backup_countdown_tick(self):
        if self._backup_thread is not None and self._backup_thread.isRunning():
            return  # 이동중 레이블은 _on_trigger_backup이 설정
        if not self._backup_dest:
            self.label_backup_status.setText('경로 미설정')
            return
        self._backup_countdown -= 1
        if self._backup_countdown <= 0:
            self._backup_countdown = self._backup_interval_sec
        h, rem = divmod(self._backup_countdown, 3600)
        m, s = divmod(rem, 60)
        self.label_backup_status.setText(f'다음 백업: {h:02d}:{m:02d}:{s:02d}')

    def _save_backup_config(self):
        config_path = self.app_info.settings_path / 'backup_config.json'
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({'backup_dest': str(self._backup_dest) if self._backup_dest else ''}, f)
        except Exception as e:
            self.log(f'[Backup] 설정 저장 실패: {e}')

    def _load_backup_config(self):
        config_path = self.app_info.settings_path / 'backup_config.json'
        try:
            if config_path.is_file():
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                dest = cfg.get('backup_dest', '')
                if dest and Path(dest).is_dir():
                    self._backup_dest = Path(dest)
                    self.lineEdit_backup_dest.setText(dest)
                    self.backup_trigger_timer.start()
        except Exception as e:
            self.log(f'[Backup] 설정 로드 실패: {e}')

    # ── 동시 저장 토글 ────────────────────────────────────────────────────────

    def _setup_keti_send_interval(self):
        from PySide6.QtWidgets import QComboBox, QLabel

        _INTERVAL_ITEMS = [
            ('매 수신마다', 0), ('0.5초', 500), ('1초', 1000), ('2초', 2000),
            ('3초', 3000), ('4초', 4000), ('5초', 5000), ('10초', 10000),
            ('15초', 15000), ('20초', 20000), ('30초', 30000), ('40초', 40000),
            ('1분', 60000), ('2분', 120000), ('3분', 180000), ('4분', 240000),
            ('5분', 300000), ('10분', 600000),
        ]

        # ── KETI 전송 주기 ──────────────────────────────────────────────────
        self._keti_send_interval_ms = 0
        self._last_keti_send_time = None
        self._keti_send_lock = threading.Lock()

        self.comboBox_keti_send_interval = QComboBox(self.ui.groupBox_keti)
        for label, ms in _INTERVAL_ITEMS:
            self.comboBox_keti_send_interval.addItem(label, ms)
        self.comboBox_keti_send_interval.setFixedHeight(22)
        self.comboBox_keti_send_interval.setStyleSheet('font-size: 8pt;')
        self.comboBox_keti_send_interval.currentIndexChanged.connect(self._on_keti_send_interval_changed)

        lbl_keti = QLabel('송신시간', self.ui.groupBox_keti)
        lbl_keti.setStyleSheet('font-size: 8pt;')
        self.ui.horizontalLayout_menu_keti.insertWidget(0, self.comboBox_keti_send_interval)
        self.ui.horizontalLayout_menu_keti.insertWidget(0, lbl_keti)

        # ── Pintel 전송 주기 ─────────────────────────────────────────────────
        self._pintel_send_interval_ms = 0
        self._last_pintel_send_time = None
        self._pintel_send_lock = threading.Lock()

        self.comboBox_pintel_send_interval = QComboBox(self.ui.groupBox_pintel)
        for label, ms in _INTERVAL_ITEMS:
            self.comboBox_pintel_send_interval.addItem(label, ms)
        self.comboBox_pintel_send_interval.setFixedHeight(22)
        self.comboBox_pintel_send_interval.setStyleSheet('font-size: 8pt;')
        self.comboBox_pintel_send_interval.currentIndexChanged.connect(self._on_pintel_send_interval_changed)

        lbl_pintel = QLabel('송신시간', self.ui.groupBox_pintel)
        lbl_pintel.setStyleSheet('font-size: 8pt;')
        self.ui.horizontalLayout_menu_pintel.insertWidget(0, self.comboBox_pintel_send_interval)
        self.ui.horizontalLayout_menu_pintel.insertWidget(0, lbl_pintel)

    def _on_keti_send_interval_changed(self, index):
        ms = self.comboBox_keti_send_interval.itemData(index)
        with self._keti_send_lock:
            self._keti_send_interval_ms = ms
            self._last_keti_send_time = None
        self.log(f'[KETI] 전송 주기: {self.comboBox_keti_send_interval.currentText()}')

    def _on_pintel_send_interval_changed(self, index):
        ms = self.comboBox_pintel_send_interval.itemData(index)
        with self._pintel_send_lock:
            self._pintel_send_interval_ms = ms
            self._last_pintel_send_time = None
        self.log(f'[Pintel] 전송 주기: {self.comboBox_pintel_send_interval.currentText()}')

    def _toggle_dual_save(self, checked: bool):
        all_clients = [self.client_pintel, self.client_keti,
                       self.client_vueron_01, self.client_vueron_02]
        if checked:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            dual_base = self.app_info.data_path.parent / f'received_data_{ts}'
            self._current_dual_base = dual_base
            for client in all_clients:
                if hasattr(client, 'savers'):
                    for saver in client.savers:
                        saver.dual_path_base = dual_base
            self.btn_dual_save.setText('동시 저장중')
            self.log(f'[DualSave] ON → {dual_base.name}')
        else:
            self._current_dual_base = None
            for client in all_clients:
                if hasattr(client, 'savers'):
                    for saver in client.savers:
                        saver.dual_path_base = None
            self.btn_dual_save.setText('동시 저장 대기')
            self.log('[DualSave] OFF')

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
        # 자동재접속을 먼저 비활성화해야 disconnect 중 on_disconnected_task가 재접속 타이머를 등록하지 않음
        if self.ui.checkBox_auto_reconnect.isChecked():
            self.ui.checkBox_auto_reconnect.setChecked(False)
        self.client_pintel.disconnect_from_server()
        self.client_vueron_01.disconnect_from_server()
        self.client_vueron_02.disconnect_from_server()
        self.client_keti.disconnect_from_server()
        self.client_nextfoam.disconnect_from_server()

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
