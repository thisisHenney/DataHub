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
from PySide6.QtCore import QEvent, QTimer, QPoint, Qt, QThread, Signal
from PySide6.QtGui import QGuiApplication, QCloseEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QMessageBox
from Lib.File import make_dir, FileMergingThread, FileWriterThread, get_writer_queue_size, clear_writer_queue
from View.main_window_ui import Ui_MainWindow
from View.setting_dialog import SettingDialog


class _ClearDataThread(QThread):
    """received_data 폴더의 모든 파일을 비동기로 삭제."""
    progress = Signal(int, int)  # (current, total)
    # total_size는 바이트 단위라 32bit int 범위(~2GB)를 쉽게 넘기므로 qint64로 선언
    finished_with_stats = Signal(int, 'qint64')  # (deleted, total_size)

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
    # total_size_bytes는 32bit int 범위(~2GB)를 쉽게 넘기므로 qint64로 선언
    finished_with_stats = Signal(int, 'qint64', str) # (moved, total_size_bytes, dest_dir)

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

        self._status_hint_widgets = {}  # widget -> statusbar에 표시할 문구 (마우스 hover 시)

        self.vtk_data_dict_pintel = {}
        self.vtk_data_dict_keti = {}
        self.vtk_data_dict_vueron = {}

        self.pintel_lock = threading.Lock()
        self.keti_lock = threading.Lock()
        self.vueron_lock = threading.Lock()

        # 각 소스의 송신 주기가 길어 merge 사이클마다 데이터가 없을 수 있음.
        # 신규 데이터 도착 전까지 직전 데이터를 재사용해 union이 비지 않게 함.
        # 체크박스로 ON/OFF 가능 (기본 ON, _setup_backup_ui에서 체크박스 생성 시 확정)
        self._last_pintel_data_by_id = {}  # 카메라 번호별 직전 데이터 (일부 카메라만 신규 도착해도 나머지는 유지)
        self._last_pintel_data_lock = threading.Lock()
        self._last_vueron_data = None
        self._last_vueron_data_lock = threading.Lock()
        self._last_keti_data = None
        self._last_keti_data_lock = threading.Lock()
        self._use_data_cache = True

        self._always_on_top_pref = False  # 설정값(순간적인 always-on-top 해제와 구분하기 위한 기준값)

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
            wt.queue_warning.connect(self.log)
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
        self.ui.pushButton_setting_datahub.clicked.connect(self.clicked_setting_datahub)
        self.ui.checkBox_auto_reconnect.stateChanged.connect(self.onStateChanged_auto_reconnect)

        self.ui.pushButton_create_sim_data.clicked.connect(self.clicked_create_sim_data)
        self.ui.pushButton_show_log.clicked.connect(self.clicked_show_log)
        self.ui.pushButton_open_solver_data_log.clicked.connect(self.clicked_open_solver_data_log)

        self.ui.pushButton_run_live_viewer.clicked.connect(self.clicked_run_live_viewer)

        self.ui.pushButton_open_received_path_vueron.clicked.connect(self.clicked_open_received_path_vueron)
        self.ui.pushButton_open_received_path_pintel.clicked.connect(self.clicked_open_received_path_pintel)
        self.ui.pushButton_open_received_path_keti.clicked.connect(self.clicked_open_received_path_keti)
        self.ui.pushButton_setting_keti.clicked.connect(self.clicked_setting_keti)

        self.ui.pushButton_connect_all.setStyleSheet(
            'background-color: #4a8c6f; color: white; border: 1px solid #3d7a5f;')
        self.ui.pushButton_disconnect_all.setStyleSheet(
            'background-color: #8c5a5a; color: white; border: 1px solid #7a4d4d;')
        self.ui.pushButton_run_live_viewer.setStyleSheet(
            'background-color: #6b5b8a; color: white; border: 1px solid #5c4d78;')

        # 왼쪽 메뉴에서 연결/연결 해제/Live Viewer를 제외한 나머지 버튼은 강조색 없이 회색으로 통일
        _gray_button_style = 'background-color: #7f8c9b; color: white; border: 1px solid #6b7787;'
        for btn in (self.ui.pushButton_open_received_path_datahub,
                    self.ui.pushButton_setting_datahub,
                    self.ui.pushButton_create_sim_data,
                    self.ui.pushButton_show_log,
                    self.ui.pushButton_open_solver_data_log):
            btn.setStyleSheet(_gray_button_style)

        self._setup_progressbars()
        self._setup_groupbox_sizing()

        self.ui.horizontalLayout_pintel.addWidget(self.client_pintel)
        self.ui.horizontalLayout_vueron_1.addWidget(self.client_vueron_01)
        self.ui.horizontalLayout_vueron_2.addWidget(self.client_vueron_02)
        self.ui.horizontalLayout_keti.addWidget(self.client_keti)
        # client_nextfoam은 더 이상 전용 UI 그룹박스가 없어 어느 레이아웃에도 붙이지 않지만,
        # Connect All/Disconnect All을 통해 계속 연결/해제는 가능하다.

        make_dir(self.app_info.settings_path)
        make_dir(self.app_info.data_path)

        self._setup_backup_ui()
        self._setup_keti_send_interval()

    def _setup_groupbox_sizing(self):
        # 왼쪽 "< Menu >" 그룹박스는 가로 정책을 Fixed로 고정해, 창을 최대화해도
        # 남는 공간을 흡수해 늘어나지 않고 항상 자기 내용물 크기(sizeHint)만큼만 차지하게 함.
        from PySide6.QtWidgets import QSizePolicy
        size_policy = self.ui.groupBox_7.sizePolicy()
        size_policy.setHorizontalPolicy(QSizePolicy.Policy.Fixed)
        self.ui.groupBox_7.setSizePolicy(size_policy)

    def _setup_progressbars(self):
        h_tx_style = ("QProgressBar { border: 1px solid #c0c4ca; background-color: #f0ecf4; }"
                      "QProgressBar::chunk { background-color: #ab47bc; width: 5px; margin: 1px; }")
        h_rx_style = ("QProgressBar { border: 1px solid #c0c4ca; background-color: #ecf4ec; }"
                      "QProgressBar::chunk { background-color: #43a047; width: 5px; margin: 1px; }")
        # Vueron bars are vertical — use height instead of width for the chunk
        v_tx_style = ("QProgressBar { border: 1px solid #c0c4ca; background-color: #f0ecf4; }"
                      "QProgressBar::chunk { background-color: #ab47bc; height: 5px; margin: 1px; }")
        v_rx_style = ("QProgressBar { border: 1px solid #c0c4ca; background-color: #ecf4ec; }"
                      "QProgressBar::chunk { background-color: #43a047; height: 5px; margin: 1px; }")
        for name in ['pintel', 'keti', 'nextfoam']:
            tx = getattr(self.ui, f'progressBar_tx_{name}', None)
            rx = getattr(self.ui, f'progressBar_rx_{name}', None)
            if tx:
                tx.setStyleSheet(h_tx_style)
            if rx:
                rx.setStyleSheet(h_rx_style)
        tx = getattr(self.ui, 'progressBar_tx_vueron', None)
        rx = getattr(self.ui, 'progressBar_rx_vueron', None)
        if tx:
            tx.setStyleSheet(v_tx_style)
        if rx:
            rx.setStyleSheet(v_rx_style)

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

        self.ui.checkBox_auto_reconnect.setChecked(False)

        self.set_window_center()

        # 각 클라이언트 set_defaults()가 IP/Port를 하드코딩된 기본값으로 세팅한 "이후"에
        # 불러와야 저장된 값이 기본값에 덮어씌워지지 않음
        self.load_app_settings()
        # self.showMaximized()

    def closeEvent(self, e: QCloseEvent):
        reply = QMessageBox.question(
            self, 'Exit',
            'Are you sure you want to quit?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.end()
            e.accept()
            # quitOnLastWindowClosed를 껐으므로(always-on-top 토글용) 실제 종료는 명시적으로 처리
            QApplication.instance().quit()
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

    def _register_status_hint(self, widget, text):
        """widget에 마우스를 올리면 text를 StatusBar에 표시, 벗어나면 지운다."""
        self._status_hint_widgets[widget] = text
        widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj in self._status_hint_widgets:
            if event.type() == QEvent.Type.Enter:
                self.ui.statusbar.showMessage(self._status_hint_widgets[obj])
            elif event.type() == QEvent.Type.Leave:
                self.ui.statusbar.clearMessage()
        return super().eventFilter(obj, event)

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

        def _add_row(row, title, tooltip):
            status_text = f'{title}: {tooltip.splitlines()[0]}'
            lbl = QLabel(title)
            lbl.setStyleSheet(style_title)
            lbl.setToolTip(tooltip)
            self._register_status_hint(lbl, status_text)
            grid.addWidget(lbl, row, 0)
            value = QLabel('-')
            value.setStyleSheet(style_value)
            value.setToolTip(tooltip)
            self._register_status_hint(value, status_text)
            grid.addWidget(value, row, 1)
            return value

        self.label_merge_now = _add_row(0, 'Now', '현재 시각 (1초마다 갱신)')
        self.label_merge_target = _add_row(
            1, 'Target', '이번 통합(union) 병합 사이클의 목표 시각 (0.2초 그리드로 정렬됨)')
        self.label_merge_delay = _add_row(
            2, 'Delay',
            '목표 시각(Target) 대비 병합이 실제로 끝난 시각의 지연(초).\n'
            '값이 커지거나 계속 튀면 병합/디스크 쓰기가 밀리고 있다는 뜻')
        self.label_merge_data = _add_row(
            3, 'Network',
            '아직 병합되지 않고 대기 중인 소스별(Pintel/KETI/Vueron) 데이터 개수')
        self.label_merge_hdd = _add_row(
            4, 'HDD',
            '소스별 개별(원본) 데이터 저장 상태.\n'
            'OK=정상, !N=그 소스의 저장 대기열이 N개 밀림, -=설정에서 저장을 꺼둔 소스.\n'
            '[Writer!N]이 붙으면 모든 소스가 공유하는 파일쓰기 큐 자체가 N개 밀린 것')
        self.label_merge_dropped = _add_row(
            5, 'Dropped',
            '소스별 저장 대기열이 가득 차서(용량 32개) 오래된 메시지가 버려진 누적 개수.\n'
            'MQTT/네트워크 큐 적체로 인한 실제 데이터 유실 지표 (저장 ON/OFF와 무관하게 집계)')
        self.label_merge_thread = _add_row(
            6, 'Thread',
            '통합 데이터 병합 스레드 풀 사용 현황 (사용 중 / 전체 3개).\n'
            '계속 꽉 차 있으면(3/3) 병합이 밀려서 일부 사이클이 스킵되고 있다는 뜻')

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
        self.btn_clear.setText('Deleting Data')
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
            self._last_pintel_data_by_id = {}
        with self._last_vueron_data_lock:
            self._last_vueron_data = None
        with self._last_keti_data_lock:
            self._last_keti_data = None

        # saver stack 비우기 + 누적 drop 카운트 리셋
        for client in self._all_source_clients():
            if hasattr(client, 'savers'):
                for saver in client.savers:
                    saver.stack.clear()
                    saver.dropped_count = 0

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
        self.btn_clear.setText('Clear Data')
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

        # 데이터 캐시 기능 안내 라벨 (기능은 유지하되 UI에서는 숨김)
        self.label_data_cache = QLabel('데이터 누락 시 이전 값 재사용', self.ui.groupBox_7)
        self.label_data_cache.setStyleSheet('font-size: 7pt; color: #555;')
        self.label_data_cache.setVisible(False)
        layout.insertWidget(insert_idx, self.label_data_cache); insert_idx += 1

        # 데이터 캐시 ON/OFF 체크박스 (기본 ON, UI에서는 숨기고 항상 ON으로 동작)
        self.checkBox_data_cache = QCheckBox('사용함', self.ui.groupBox_7)
        self.checkBox_data_cache.setStyleSheet('font-size: 8pt;')
        self.checkBox_data_cache.setChecked(True)
        self.checkBox_data_cache.setVisible(False)
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
                self._last_pintel_data_by_id = {}
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

    def _network_client_map(self):
        return {
            'pintel': self.client_pintel,
            'keti': self.client_keti,
            'vueron_01': self.client_vueron_01,
            'vueron_02': self.client_vueron_02,
            'nextfoam': self.client_nextfoam,
        }

    _IP_HISTORY_MAX = 15

    def _collect_network_settings(self):
        network = {}
        for name, client in self._network_client_map().items():
            entry = {'ip': client.client.ip, 'port': client.client.port}
            if hasattr(client.client, 'path'):  # WebSocket(Vueron)만 path를 가짐
                entry['path'] = client.client.path
            combo = client.ui.ip_comboBox
            entry['ip_history'] = [combo.itemText(i) for i in range(combo.count())
                                    if combo.itemText(i)][:self._IP_HISTORY_MAX]
            network[name] = entry
        return network

    def _apply_network_settings(self, network: dict):
        for name, client in self._network_client_map().items():
            entry = network.get(name)
            if not entry:
                continue
            combo = client.ui.ip_comboBox
            history = entry.get('ip_history', [])
            if history:
                # 저장된 순서(최근 접속 순)를 그대로 재현하도록 콤보박스를 다시 구성.
                # 단순히 없는 것만 추가하면 히스토리 항목이 기존 프리셋 뒤로 밀려 순서가 깨짐.
                combo.blockSignals(True)
                try:
                    remaining_presets = [combo.itemText(i) for i in range(combo.count())
                                          if combo.itemText(i) not in history]
                    combo.clear()
                    for ip in history:
                        combo.addItem(ip)
                    for ip in remaining_presets:
                        combo.addItem(ip)
                finally:
                    combo.blockSignals(False)
            ip = entry.get('ip')
            port = entry.get('port')
            if hasattr(client.client, 'path'):
                client.set_ip_port(ip, port, entry.get('path', ''))
            else:
                client.set_ip_port(ip, port)

    def remember_connected_ip(self, client):
        """접속에 성공한 IP를 그 소스의 ip_comboBox 맨 위로 올려서 드롭다운 히스토리에 누적."""
        combo = client.ui.ip_comboBox
        ip = client.client.ip
        if not ip:
            return
        combo.blockSignals(True)
        try:
            idx = combo.findText(ip)
            if idx != -1:
                combo.removeItem(idx)
            combo.insertItem(0, ip)
            combo.setCurrentIndex(0)
            while combo.count() > self._IP_HISTORY_MAX:
                combo.removeItem(combo.count() - 1)
        finally:
            combo.blockSignals(False)

    def save_network_settings(self):
        """연결 시점의 IP/Port를 즉시 저장 (각 클라이언트의 on_connected_task에서 호출)."""
        self.save_app_settings()

    def save_app_settings(self):
        config_path = self.app_info.settings_path / 'app_settings.json'
        try:
            make_dir(self.app_info.settings_path)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'always_on_top': self.get_always_on_top(),
                    'save_pintel': self.get_source_save_enabled('pintel'),
                    'save_keti': self.get_source_save_enabled('keti'),
                    'save_vueron': self.get_source_save_enabled('vueron'),
                    'network': self._collect_network_settings(),
                }, f)
        except Exception as e:
            self.log(f'[설정] 저장 실패: {e}')

    def load_app_settings(self):
        config_path = self.app_info.settings_path / 'app_settings.json'
        try:
            if config_path.is_file():
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                self.set_always_on_top(cfg.get('always_on_top', False))
                self.set_source_save_enabled('pintel', cfg.get('save_pintel', True))
                self.set_source_save_enabled('keti', cfg.get('save_keti', True))
                self.set_source_save_enabled('vueron', cfg.get('save_vueron', True))
                self._apply_network_settings(cfg.get('network', {}))
        except Exception as e:
            self.log(f'[설정] 로드 실패: {e}')

    def get_always_on_top(self) -> bool:
        return self._always_on_top_pref

    def set_always_on_top(self, checked: bool):
        self._always_on_top_pref = checked
        # setWindowFlags() 호출 즉시 창이 hide()되어 isVisible()이 False로 바뀌므로,
        # 반드시 flags 변경 "전" 가시성을 기억해뒀다가 그 값으로 재표시 여부를 판단해야 함.
        was_visible = self.isVisible()
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        if was_visible:
            self.show()  # setWindowFlags()는 창을 숨기므로 이미 떠 있던 경우 다시 표시해야 함
        self.log(f'[설정] 프로그램 항상 위에 표시 {"ON" if checked else "OFF"}')

    def get_source_save_enabled(self, company: str) -> bool:
        """company: 'pintel' | 'keti' | 'vueron'. 저장 스레드가 아직 없으면 기본값 True."""
        clients = self._source_clients(company)
        for client in clients:
            if hasattr(client, 'savers') and client.savers:
                return client.savers[0].save_enabled
        return True

    def set_source_save_enabled(self, company: str, checked: bool):
        """company: 'pintel' | 'keti' | 'vueron'. 개별(원본) 수신 데이터 저장 ON/OFF. 통합 데이터는 영향받지 않음."""
        for client in self._source_clients(company):
            if hasattr(client, 'savers'):
                for saver in client.savers:
                    saver.save_enabled = checked
        self.log(f'[{company.upper()}] 개별 수신 데이터 저장 {"ON" if checked else "OFF"} (통합 데이터는 항상 저장됨)')

    def _source_clients(self, company: str):
        return {
            'pintel': [self.client_pintel],
            'keti': [self.client_keti],
            'vueron': [self.client_vueron_01, self.client_vueron_02],
        }.get(company, [])

    def _all_source_clients(self):
        return [self.client_pintel, self.client_keti,
                self.client_vueron_01, self.client_vueron_02]

    def _toggle_dual_save(self, checked: bool):
        all_clients = self._all_source_clients()
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
        for client in self._all_source_clients():
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
        self.label_merge_hdd.setText(self._get_hdd_status_text())
        self._update_dropped_label()

    # HDD(개별 원본 파일) 저장이 밀리고 있는지 표시. 설정에서 저장을 꺼둔 소스는 '-'.
    # 임계값은 Lib/File.py의 콘솔 경고 임계값(saver.stack>=10, writer 큐>=50)과 동일하게 맞춤.
    _HDD_BACKLOG_WARN = 10
    _WRITER_QUEUE_WARN = 50

    def _hdd_status_for(self, company: str) -> str:
        # writer 큐는 소스 공용이라 여기서 같이 보면 다른 소스의 적체를 이 소스 탓으로 오인함.
        # 그래서 공용 큐 상태는 여기서 빼고, _get_hdd_status_text()에서 별도로 표시한다.
        if not self.get_source_save_enabled(company):
            return '-'
        max_backlog = 0
        for client in self._source_clients(company):
            if hasattr(client, 'savers'):
                for saver in client.savers:
                    max_backlog = max(max_backlog, len(saver.stack))
        if max_backlog >= self._HDD_BACKLOG_WARN:
            return f'!{max_backlog}'
        return 'OK'

    def _get_hdd_status_text(self):
        p = self._hdd_status_for('pintel')
        k = self._hdd_status_for('keti')
        v = self._hdd_status_for('vueron')
        text = f'P:{p}  K:{k}  V:{v}'
        qlen = get_writer_queue_size()
        if qlen >= self._WRITER_QUEUE_WARN:
            text += f'  [Writer!{qlen}]'
        return text

    # 소스별 saver 대기열(stack, maxlen=32)이 넘쳐서 오래된 메시지가 버려진 누적 개수.
    # save_enabled(저장 ON/OFF) 여부와 무관하게 항상 집계 — MQTT/네트워크 큐 적체 자체를 보기 위함.
    def _dropped_count_for(self, company: str) -> int:
        total = 0
        for client in self._source_clients(company):
            if hasattr(client, 'savers'):
                for saver in client.savers:
                    total += saver.dropped_count
        return total

    def _update_dropped_label(self):
        p = self._dropped_count_for('pintel')
        k = self._dropped_count_for('keti')
        v = self._dropped_count_for('vueron')
        self.label_merge_dropped.setText(f'P:{p}  K:{k}  V:{v}')
        if p or k or v:
            self.label_merge_dropped.setStyleSheet('font-size: 9pt; font-weight: bold; color: #e53935;')
        else:
            self.label_merge_dropped.setStyleSheet('font-size: 9pt; font-weight: bold; color: #2c3e50;')

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
        # 각 클라이언트의 disconnect_from_server()가 user_disconnected를 스스로 표시하므로
        # 자동재접속 체크박스는 그대로 두어도 재접속 타이머가 걸리지 않음
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

    def clicked_setting_datahub(self):
        dialog = SettingDialog(self)
        dialog.exec()
