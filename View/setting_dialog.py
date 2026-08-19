#!/usr/bin/env python3
# -*-coding:utf8-*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QCheckBox, QLabel, QPushButton, QHBoxLayout
)


class SettingDialog(QDialog):
    """DataHub 설정 다이얼로그. 필요한 설정 항목을 이 안에 추가해 나간다."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle('DataHub 설정')
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)

        general_group = QGroupBox('일반')
        general_layout = QVBoxLayout(general_group)
        self.checkBox_always_on_top = QCheckBox('프로그램 항상 위에 표시')
        general_layout.addWidget(self.checkBox_always_on_top)
        layout.addWidget(general_group)

        if self.main_window is not None:
            self.checkBox_always_on_top.setChecked(self.main_window.get_always_on_top())

        group = QGroupBox('개별 수신 데이터 저장')
        group_layout = QVBoxLayout(group)

        info_label = QLabel('통합 데이터는 항상 저장됩니다. 아래는 각 소스별 원본(개별) 수신 데이터 저장 여부입니다.')
        info_label.setWordWrap(True)
        info_label.setStyleSheet('color: #888; font-size: 8pt;')
        group_layout.addWidget(info_label)

        self.checkBox_save_pintel = QCheckBox('Pintel')
        self.checkBox_save_keti = QCheckBox('KETI')
        self.checkBox_save_vueron = QCheckBox('Vueron')
        for cb in (self.checkBox_save_pintel, self.checkBox_save_keti, self.checkBox_save_vueron):
            group_layout.addWidget(cb)

        layout.addWidget(group)

        if self.main_window is not None:
            self.checkBox_save_pintel.setChecked(self.main_window.get_source_save_enabled('pintel'))
            self.checkBox_save_keti.setChecked(self.main_window.get_source_save_enabled('keti'))
            self.checkBox_save_vueron.setChecked(self.main_window.get_source_save_enabled('vueron'))

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.button_apply = QPushButton('적용')
        self.button_cancel = QPushButton('취소')
        self.button_apply.clicked.connect(self._on_apply)
        self.button_cancel.clicked.connect(self.reject)
        button_row.addWidget(self.button_apply)
        button_row.addWidget(self.button_cancel)
        layout.addLayout(button_row)

    def _on_apply(self):
        if self.main_window is not None:
            self.main_window.set_always_on_top(self.checkBox_always_on_top.isChecked())
            self.main_window.set_source_save_enabled('pintel', self.checkBox_save_pintel.isChecked())
            self.main_window.set_source_save_enabled('keti', self.checkBox_save_keti.isChecked())
            self.main_window.set_source_save_enabled('vueron', self.checkBox_save_vueron.isChecked())
            self.main_window.save_app_settings()
        # 항상 위 표시를 켜면 MainWindow가 topmost가 되면서 이 모달 다이얼로그가
        # 순간적으로 뒤로 밀릴 수 있어, 닫히기 직전 다시 앞으로 가져온다.
        self.raise_()
        self.activateWindow()
        self.accept()
