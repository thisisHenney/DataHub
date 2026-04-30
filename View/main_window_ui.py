# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLayout,
    QMainWindow, QPlainTextEdit, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QStatusBar, QTabWidget,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1201, 877)
        font = QFont()
        font.setFamilies([u"Pretendard"])
        MainWindow.setFont(font)
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionConnect_all = QAction(MainWindow)
        self.actionConnect_all.setObjectName(u"actionConnect_all")
        self.actionDisconnect_all = QAction(MainWindow)
        self.actionDisconnect_all.setObjectName(u"actionDisconnect_all")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_4 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(-1, 0, -1, -1)
        self.groupBox_7 = QGroupBox(self.centralwidget)
        self.groupBox_7.setObjectName(u"groupBox_7")
        font1 = QFont()
        font1.setFamilies([u"\ub098\ub214\uc2a4\ud018\uc5b4\ub77c\uc6b4\ub4dc"])
        font1.setPointSize(10)
        font1.setBold(True)
        self.groupBox_7.setFont(font1)
        self.groupBox_7.setStyleSheet(u"QGroupBox {\n"
"    border: 1 solid;\n"
"    border-radius: 6;\n"
"    margin-top: 9;\n"
"    border-color : #c8c8c8;\n"
"    padding: 3;\n"
"}\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    left: 10;\n"
"    padding: 2 3;\n"
"}")
        self.verticalLayout_7 = QVBoxLayout(self.groupBox_7)
        self.verticalLayout_7.setSpacing(6)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(-1, 16, -1, 6)
        self.pushButton_connect_all = QPushButton(self.groupBox_7)
        self.pushButton_connect_all.setObjectName(u"pushButton_connect_all")
        self.pushButton_connect_all.setEnabled(True)
        font2 = QFont()
        font2.setFamilies([u"\ub098\ub214\uc2a4\ud018\uc5b4\ub77c\uc6b4\ub4dc"])
        font2.setPointSize(10)
        self.pushButton_connect_all.setFont(font2)

        self.verticalLayout_7.addWidget(self.pushButton_connect_all)

        self.pushButton_disconnect_all = QPushButton(self.groupBox_7)
        self.pushButton_disconnect_all.setObjectName(u"pushButton_disconnect_all")
        self.pushButton_disconnect_all.setEnabled(True)
        self.pushButton_disconnect_all.setFont(font2)

        self.verticalLayout_7.addWidget(self.pushButton_disconnect_all)

        self.line_7 = QFrame(self.groupBox_7)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setFont(font2)
        self.line_7.setFrameShape(QFrame.Shape.HLine)
        self.line_7.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_7.addWidget(self.line_7)

        self.pushButton_open_received_path_datahub = QPushButton(self.groupBox_7)
        self.pushButton_open_received_path_datahub.setObjectName(u"pushButton_open_received_path_datahub")
        self.pushButton_open_received_path_datahub.setEnabled(True)
        self.pushButton_open_received_path_datahub.setFont(font2)

        self.verticalLayout_7.addWidget(self.pushButton_open_received_path_datahub)

        self.pushButton_setting_datahub = QPushButton(self.groupBox_7)
        self.pushButton_setting_datahub.setObjectName(u"pushButton_setting_datahub")
        self.pushButton_setting_datahub.setEnabled(False)
        self.pushButton_setting_datahub.setFont(font2)

        self.verticalLayout_7.addWidget(self.pushButton_setting_datahub)

        self.checkBox_auto_reconnect = QCheckBox(self.groupBox_7)
        self.checkBox_auto_reconnect.setObjectName(u"checkBox_auto_reconnect")
        self.checkBox_auto_reconnect.setFont(font2)
        self.checkBox_auto_reconnect.setChecked(False)

        self.verticalLayout_7.addWidget(self.checkBox_auto_reconnect)

        self.line_8 = QFrame(self.groupBox_7)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setFont(font2)
        self.line_8.setFrameShape(QFrame.Shape.HLine)
        self.line_8.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_7.addWidget(self.line_8)

        self.pushButton_create_sim_data = QPushButton(self.groupBox_7)
        self.pushButton_create_sim_data.setObjectName(u"pushButton_create_sim_data")
        self.pushButton_create_sim_data.setEnabled(True)
        self.pushButton_create_sim_data.setFont(font2)

        self.verticalLayout_7.addWidget(self.pushButton_create_sim_data)

        self.line_11 = QFrame(self.groupBox_7)
        self.line_11.setObjectName(u"line_11")
        self.line_11.setFont(font2)
        self.line_11.setFrameShape(QFrame.Shape.HLine)
        self.line_11.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_7.addWidget(self.line_11)

        self.pushButton_show_log = QPushButton(self.groupBox_7)
        self.pushButton_show_log.setObjectName(u"pushButton_show_log")
        self.pushButton_show_log.setEnabled(True)
        self.pushButton_show_log.setFont(font2)

        self.verticalLayout_7.addWidget(self.pushButton_show_log)

        self.pushButton_open_solver_data_log = QPushButton(self.groupBox_7)
        self.pushButton_open_solver_data_log.setObjectName(u"pushButton_open_solver_data_log")
        self.pushButton_open_solver_data_log.setEnabled(True)
        self.pushButton_open_solver_data_log.setFont(font2)

        self.verticalLayout_7.addWidget(self.pushButton_open_solver_data_log)

        self.line_9 = QFrame(self.groupBox_7)
        self.line_9.setObjectName(u"line_9")
        self.line_9.setFont(font2)
        self.line_9.setFrameShape(QFrame.Shape.HLine)
        self.line_9.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_7.addWidget(self.line_9)

        self.pushButton_run_live_viewer = QPushButton(self.groupBox_7)
        self.pushButton_run_live_viewer.setObjectName(u"pushButton_run_live_viewer")
        self.pushButton_run_live_viewer.setEnabled(True)
        self.pushButton_run_live_viewer.setFont(font2)

        self.verticalLayout_7.addWidget(self.pushButton_run_live_viewer)

        self.line_10 = QFrame(self.groupBox_7)
        self.line_10.setObjectName(u"line_10")
        self.line_10.setFont(font2)
        self.line_10.setFrameShape(QFrame.Shape.HLine)
        self.line_10.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_7.addWidget(self.line_10)

        self.pushButton_open_solver_data_log_2 = QPushButton(self.groupBox_7)
        self.pushButton_open_solver_data_log_2.setObjectName(u"pushButton_open_solver_data_log_2")
        self.pushButton_open_solver_data_log_2.setEnabled(True)
        self.pushButton_open_solver_data_log_2.setFont(font2)

        self.verticalLayout_7.addWidget(self.pushButton_open_solver_data_log_2)

        self.verticalSpacer_7 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer_7)


        self.horizontalLayout_6.addWidget(self.groupBox_7)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        font3 = QFont()
        font3.setFamilies([u"Pretendard"])
        font3.setPointSize(10)
        font3.setBold(True)
        self.tabWidget.setFont(font3)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_5 = QVBoxLayout(self.tab)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.groupBox = QGroupBox(self.tab)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setFont(font1)
        self.groupBox.setStyleSheet(u"QGroupBox {\n"
"    border: 1 solid;\n"
"    border-radius: 6;\n"
"    margin-top: 9;\n"
"    border-color : #c8c8c8;\n"
"    padding: 3;\n"
"}\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    left: 10;\n"
"    padding: 2 3;\n"
"}")
        self.verticalLayout_9 = QVBoxLayout(self.groupBox)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(-1, 16, -1, 6)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, -1, -1, -1)
        self.groupBox_keti = QGroupBox(self.groupBox)
        self.groupBox_keti.setObjectName(u"groupBox_keti")
        self.groupBox_keti.setFont(font1)
        self.groupBox_keti.setStyleSheet(u"QGroupBox {\n"
"    border: 1 solid;\n"
"    border-radius: 6;\n"
"    margin-top: 9;\n"
"    border-color : #c8c8c8;\n"
"    padding: 3;\n"
"}\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    left: 10;\n"
"    padding: 2 3;\n"
"}")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_keti)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, 12, -1, 6)
        self.horizontalLayout_keti = QHBoxLayout()
        self.horizontalLayout_keti.setObjectName(u"horizontalLayout_keti")

        self.verticalLayout_2.addLayout(self.horizontalLayout_keti)

        self.line_3 = QFrame(self.groupBox_keti)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFont(font2)
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line_3)

        self.horizontalLayout_menu_keti = QHBoxLayout()
        self.horizontalLayout_menu_keti.setObjectName(u"horizontalLayout_menu_keti")
        self.horizontalLayout_menu_keti.setContentsMargins(-1, 0, -1, -1)
        self.horizontalSpacer_7 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_menu_keti.addItem(self.horizontalSpacer_7)

        self.pushButton_open_received_path_keti = QPushButton(self.groupBox_keti)
        self.pushButton_open_received_path_keti.setObjectName(u"pushButton_open_received_path_keti")
        self.pushButton_open_received_path_keti.setEnabled(True)
        self.pushButton_open_received_path_keti.setFont(font2)

        self.horizontalLayout_menu_keti.addWidget(self.pushButton_open_received_path_keti)

        self.pushButton_setting_keti = QPushButton(self.groupBox_keti)
        self.pushButton_setting_keti.setObjectName(u"pushButton_setting_keti")
        self.pushButton_setting_keti.setEnabled(False)
        self.pushButton_setting_keti.setFont(font2)

        self.horizontalLayout_menu_keti.addWidget(self.pushButton_setting_keti)


        self.verticalLayout_2.addLayout(self.horizontalLayout_menu_keti)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.label = QLabel(self.groupBox_keti)
        self.label.setObjectName(u"label")
        self.label.setFont(font2)

        self.horizontalLayout_2.addWidget(self.label)

        self.text_thread_keti = QLabel(self.groupBox_keti)
        self.text_thread_keti.setObjectName(u"text_thread_keti")
        self.text_thread_keti.setMinimumSize(QSize(0, 24))
        font4 = QFont()
        font4.setFamilies([u"\ub098\ub214\uc2a4\ud018\uc5b4\ub77c\uc6b4\ub4dc"])
        font4.setPointSize(10)
        font4.setBold(False)
        self.text_thread_keti.setFont(font4)
        self.text_thread_keti.setFrameShape(QFrame.Shape.Panel)
        self.text_thread_keti.setFrameShadow(QFrame.Shadow.Sunken)
        self.text_thread_keti.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_2.addWidget(self.text_thread_keti)

        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.verticalSpacer_6 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_6)


        self.gridLayout.addWidget(self.groupBox_keti, 2, 6, 1, 1)

        self.groupBox_pintel = QGroupBox(self.groupBox)
        self.groupBox_pintel.setObjectName(u"groupBox_pintel")
        self.groupBox_pintel.setFont(font1)
        self.groupBox_pintel.setStyleSheet(u"QGroupBox {\n"
"    border: 1 solid;\n"
"    border-radius: 6;\n"
"    margin-top: 9;\n"
"    border-color : #c8c8c8;\n"
"    padding: 3;\n"
"}\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    left: 10;\n"
"    padding: 2 3;\n"
"}")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_pintel)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, 12, -1, 6)
        self.horizontalLayout_pintel = QHBoxLayout()
        self.horizontalLayout_pintel.setObjectName(u"horizontalLayout_pintel")

        self.verticalLayout_3.addLayout(self.horizontalLayout_pintel)

        self.line_2 = QFrame(self.groupBox_pintel)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFont(font2)
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_3.addWidget(self.line_2)

        self.horizontalLayout_menu_pintel = QHBoxLayout()
        self.horizontalLayout_menu_pintel.setObjectName(u"horizontalLayout_menu_pintel")
        self.horizontalLayout_menu_pintel.setContentsMargins(-1, 0, -1, -1)
        self.horizontalSpacer_6 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_menu_pintel.addItem(self.horizontalSpacer_6)

        self.pushButton_open_received_path_pintel = QPushButton(self.groupBox_pintel)
        self.pushButton_open_received_path_pintel.setObjectName(u"pushButton_open_received_path_pintel")
        self.pushButton_open_received_path_pintel.setEnabled(True)
        self.pushButton_open_received_path_pintel.setFont(font2)

        self.horizontalLayout_menu_pintel.addWidget(self.pushButton_open_received_path_pintel)

        self.pushButton_setting_pintel = QPushButton(self.groupBox_pintel)
        self.pushButton_setting_pintel.setObjectName(u"pushButton_setting_pintel")
        self.pushButton_setting_pintel.setEnabled(False)
        self.pushButton_setting_pintel.setFont(font2)

        self.horizontalLayout_menu_pintel.addWidget(self.pushButton_setting_pintel)


        self.verticalLayout_3.addLayout(self.horizontalLayout_menu_pintel)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(-1, 0, -1, -1)
        self.label_2 = QLabel(self.groupBox_pintel)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font2)

        self.horizontalLayout_7.addWidget(self.label_2)

        self.text_thread_pintel = QLabel(self.groupBox_pintel)
        self.text_thread_pintel.setObjectName(u"text_thread_pintel")
        self.text_thread_pintel.setMinimumSize(QSize(0, 24))
        self.text_thread_pintel.setFont(font4)
        self.text_thread_pintel.setFrameShape(QFrame.Shape.Panel)
        self.text_thread_pintel.setFrameShadow(QFrame.Shadow.Sunken)
        self.text_thread_pintel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_7.addWidget(self.text_thread_pintel)

        self.horizontalLayout_7.setStretch(1, 1)

        self.verticalLayout_3.addLayout(self.horizontalLayout_7)

        self.verticalSpacer_5 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_5)


        self.gridLayout.addWidget(self.groupBox_pintel, 2, 0, 1, 1)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.groupBox_datahub = QGroupBox(self.groupBox)
        self.groupBox_datahub.setObjectName(u"groupBox_datahub")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_datahub.sizePolicy().hasHeightForWidth())
        self.groupBox_datahub.setSizePolicy(sizePolicy)
        self.groupBox_datahub.setMaximumSize(QSize(220, 270))
        self.groupBox_datahub.setFont(font1)
        self.groupBox_datahub.setStyleSheet(u"QGroupBox {\n"
"    border: 1 solid;\n"
"    border-radius: 6;\n"
"    margin-top: 9;\n"
"    border-color : #c8c8c8;\n"
"    padding: 3;\n"
"}\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    left: 10;\n"
"    padding: 2 3;\n"
"}")
        self.verticalLayout = QVBoxLayout(self.groupBox_datahub)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 12, -1, 6)

        self.horizontalLayout_5.addWidget(self.groupBox_datahub)


        self.gridLayout.addLayout(self.horizontalLayout_5, 2, 3, 1, 1)

        self.verticalLayout_txrx_pintel = QVBoxLayout()
        self.verticalLayout_txrx_pintel.setObjectName(u"verticalLayout_txrx_pintel")
        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_txrx_pintel.addItem(self.verticalSpacer)

        self.progressBar_tx_pintel = QProgressBar(self.groupBox)
        self.progressBar_tx_pintel.setObjectName(u"progressBar_tx_pintel")
        self.progressBar_tx_pintel.setEnabled(True)
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.progressBar_tx_pintel.sizePolicy().hasHeightForWidth())
        self.progressBar_tx_pintel.setSizePolicy(sizePolicy1)
        self.progressBar_tx_pintel.setMinimumSize(QSize(20, 0))
        self.progressBar_tx_pintel.setMaximumSize(QSize(16777215, 8))
        self.progressBar_tx_pintel.setFont(font2)
        self.progressBar_tx_pintel.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.progressBar_tx_pintel.setStyleSheet(u"QProgressBar {\n"
"        border: 1px solid gray;\n"
"        text-align: center;\n"
"    }\n"
"    QProgressBar::chunk {\n"
"        background-color:  darkmagenta;\n"
"        width: 5px;\n"
"        margin: 1px;\n"
"    }")
        self.progressBar_tx_pintel.setMaximum(100)
        self.progressBar_tx_pintel.setValue(2)
        self.progressBar_tx_pintel.setTextVisible(False)
        self.progressBar_tx_pintel.setInvertedAppearance(True)
        self.progressBar_tx_pintel.setTextDirection(QProgressBar.Direction.TopToBottom)

        self.verticalLayout_txrx_pintel.addWidget(self.progressBar_tx_pintel)

        self.progressBar_rx_pintel = QProgressBar(self.groupBox)
        self.progressBar_rx_pintel.setObjectName(u"progressBar_rx_pintel")
        sizePolicy1.setHeightForWidth(self.progressBar_rx_pintel.sizePolicy().hasHeightForWidth())
        self.progressBar_rx_pintel.setSizePolicy(sizePolicy1)
        self.progressBar_rx_pintel.setMinimumSize(QSize(20, 0))
        self.progressBar_rx_pintel.setMaximumSize(QSize(16777215, 8))
        self.progressBar_rx_pintel.setFont(font2)
        self.progressBar_rx_pintel.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.progressBar_rx_pintel.setStyleSheet(u"QProgressBar {\n"
"        border: 1px solid gray;\n"
"        text-align: center;\n"
"    }\n"
"    QProgressBar::chunk {\n"
"        background-color:  darkblue;\n"
"        width: 5px;\n"
"        margin: 1px;\n"
"    }")
        self.progressBar_rx_pintel.setMaximum(100)
        self.progressBar_rx_pintel.setValue(2)
        self.progressBar_rx_pintel.setTextVisible(False)
        self.progressBar_rx_pintel.setOrientation(Qt.Orientation.Horizontal)
        self.progressBar_rx_pintel.setInvertedAppearance(False)

        self.verticalLayout_txrx_pintel.addWidget(self.progressBar_rx_pintel)

        self.verticalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_txrx_pintel.addItem(self.verticalSpacer_2)


        self.gridLayout.addLayout(self.verticalLayout_txrx_pintel, 2, 1, 1, 2)

        self.verticalLayout_txrx_keti = QVBoxLayout()
        self.verticalLayout_txrx_keti.setObjectName(u"verticalLayout_txrx_keti")
        self.verticalSpacer_3 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_txrx_keti.addItem(self.verticalSpacer_3)

        self.progressBar_tx_keti = QProgressBar(self.groupBox)
        self.progressBar_tx_keti.setObjectName(u"progressBar_tx_keti")
        self.progressBar_tx_keti.setMinimumSize(QSize(20, 0))
        self.progressBar_tx_keti.setMaximumSize(QSize(16777215, 8))
        self.progressBar_tx_keti.setFont(font2)
        self.progressBar_tx_keti.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.progressBar_tx_keti.setStyleSheet(u"QProgressBar {\n"
"        border: 1px solid gray;\n"
"        text-align: center;\n"
"    }\n"
"    QProgressBar::chunk {\n"
"        background-color:  darkmagenta;\n"
"        width: 5px;\n"
"        margin: 1px;\n"
"    }")
        self.progressBar_tx_keti.setMaximum(100)
        self.progressBar_tx_keti.setValue(2)
        self.progressBar_tx_keti.setTextVisible(False)
        self.progressBar_tx_keti.setOrientation(Qt.Orientation.Horizontal)
        self.progressBar_tx_keti.setInvertedAppearance(False)

        self.verticalLayout_txrx_keti.addWidget(self.progressBar_tx_keti)

        self.progressBar_rx_keti = QProgressBar(self.groupBox)
        self.progressBar_rx_keti.setObjectName(u"progressBar_rx_keti")
        self.progressBar_rx_keti.setMinimumSize(QSize(20, 0))
        self.progressBar_rx_keti.setMaximumSize(QSize(16777215, 8))
        font5 = QFont()
        font5.setFamilies([u"\ub098\ub214\uc2a4\ud018\uc5b4\ub77c\uc6b4\ub4dc"])
        font5.setPointSize(10)
        font5.setKerning(True)
        self.progressBar_rx_keti.setFont(font5)
        self.progressBar_rx_keti.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.progressBar_rx_keti.setStyleSheet(u"QProgressBar {\n"
"        border: 1px solid gray;\n"
"        text-align: center;\n"
"    }\n"
"    QProgressBar::chunk {\n"
"        background-color:  darkblue;\n"
"        width: 5px;\n"
"        margin: 1px;\n"
"    }")
        self.progressBar_rx_keti.setMaximum(100)
        self.progressBar_rx_keti.setValue(2)
        self.progressBar_rx_keti.setTextVisible(False)
        self.progressBar_rx_keti.setInvertedAppearance(True)
        self.progressBar_rx_keti.setTextDirection(QProgressBar.Direction.TopToBottom)

        self.verticalLayout_txrx_keti.addWidget(self.progressBar_rx_keti)

        self.verticalSpacer_4 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_txrx_keti.addItem(self.verticalSpacer_4)


        self.gridLayout.addLayout(self.verticalLayout_txrx_keti, 2, 4, 1, 2)

        self.horizontalLayout_txrx_vueron = QHBoxLayout()
        self.horizontalLayout_txrx_vueron.setSpacing(6)
        self.horizontalLayout_txrx_vueron.setObjectName(u"horizontalLayout_txrx_vueron")
        self.horizontalLayout_txrx_vueron.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_txrx_vueron.addItem(self.horizontalSpacer)

        self.progressBar_tx_vueron = QProgressBar(self.groupBox)
        self.progressBar_tx_vueron.setObjectName(u"progressBar_tx_vueron")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.progressBar_tx_vueron.sizePolicy().hasHeightForWidth())
        self.progressBar_tx_vueron.setSizePolicy(sizePolicy2)
        self.progressBar_tx_vueron.setMinimumSize(QSize(0, 20))
        self.progressBar_tx_vueron.setMaximumSize(QSize(8, 16777215))
        self.progressBar_tx_vueron.setFont(font2)
        self.progressBar_tx_vueron.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.progressBar_tx_vueron.setStyleSheet(u"QProgressBar {\n"
"        border: 1px solid gray;\n"
"        text-align: center;\n"
"    }\n"
"    QProgressBar::chunk {\n"
"        background-color:  darkmagenta;\n"
"        height: 5px;\n"
"        margin: 1px;\n"
"    }")
        self.progressBar_tx_vueron.setMaximum(100)
        self.progressBar_tx_vueron.setValue(2)
        self.progressBar_tx_vueron.setTextVisible(False)
        self.progressBar_tx_vueron.setOrientation(Qt.Orientation.Vertical)
        self.progressBar_tx_vueron.setInvertedAppearance(False)
        self.progressBar_tx_vueron.setTextDirection(QProgressBar.Direction.TopToBottom)

        self.horizontalLayout_txrx_vueron.addWidget(self.progressBar_tx_vueron)

        self.progressBar_rx_vueron = QProgressBar(self.groupBox)
        self.progressBar_rx_vueron.setObjectName(u"progressBar_rx_vueron")
        sizePolicy2.setHeightForWidth(self.progressBar_rx_vueron.sizePolicy().hasHeightForWidth())
        self.progressBar_rx_vueron.setSizePolicy(sizePolicy2)
        self.progressBar_rx_vueron.setMinimumSize(QSize(0, 20))
        self.progressBar_rx_vueron.setMaximumSize(QSize(8, 16777215))
        self.progressBar_rx_vueron.setFont(font2)
        self.progressBar_rx_vueron.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.progressBar_rx_vueron.setStyleSheet(u"QProgressBar {\n"
"        border: 1px solid gray;\n"
"        text-align: center;\n"
"    }\n"
"    QProgressBar::chunk {\n"
"        background-color:  darkblue;\n"
"        height: 5px;\n"
"        margin: 1px;\n"
"    }")
        self.progressBar_rx_vueron.setMaximum(100)
        self.progressBar_rx_vueron.setValue(2)
        self.progressBar_rx_vueron.setTextVisible(False)
        self.progressBar_rx_vueron.setOrientation(Qt.Orientation.Vertical)
        self.progressBar_rx_vueron.setInvertedAppearance(True)
        self.progressBar_rx_vueron.setTextDirection(QProgressBar.Direction.TopToBottom)

        self.horizontalLayout_txrx_vueron.addWidget(self.progressBar_rx_vueron)

        self.horizontalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_txrx_vueron.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout_txrx_vueron, 1, 0, 1, 7)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(-1, -1, 0, -1)
        self.horizontalSpacer_11 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_11)

        self.groupBox_vueron = QGroupBox(self.groupBox)
        self.groupBox_vueron.setObjectName(u"groupBox_vueron")
        self.groupBox_vueron.setFont(font1)
        self.groupBox_vueron.setStyleSheet(u"QGroupBox {\n"
"    border: 1 solid;\n"
"    border-radius: 6;\n"
"    margin-top: 9;\n"
"    border-color : #c8c8c8;\n"
"    padding: 3;\n"
"}\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    left: 10;\n"
"    padding: 2 3;\n"
"}")
        self.verticalLayout_8 = QVBoxLayout(self.groupBox_vueron)
        self.verticalLayout_8.setSpacing(6)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(-1, 12, -1, 6)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, 0, 0)
        self.horizontalLayout_vueron_1 = QHBoxLayout()
        self.horizontalLayout_vueron_1.setObjectName(u"horizontalLayout_vueron_1")
        self.horizontalLayout_vueron_1.setContentsMargins(-1, 0, -1, -1)

        self.horizontalLayout.addLayout(self.horizontalLayout_vueron_1)

        self.line_4 = QFrame(self.groupBox_vueron)
        self.line_4.setObjectName(u"line_4")
        sizePolicy2.setHeightForWidth(self.line_4.sizePolicy().hasHeightForWidth())
        self.line_4.setSizePolicy(sizePolicy2)
        self.line_4.setFont(font2)
        self.line_4.setFrameShadow(QFrame.Shadow.Plain)
        self.line_4.setFrameShape(QFrame.Shape.VLine)

        self.horizontalLayout.addWidget(self.line_4)

        self.horizontalLayout_vueron_2 = QHBoxLayout()
        self.horizontalLayout_vueron_2.setObjectName(u"horizontalLayout_vueron_2")

        self.horizontalLayout.addLayout(self.horizontalLayout_vueron_2)


        self.verticalLayout_8.addLayout(self.horizontalLayout)

        self.line_5 = QFrame(self.groupBox_vueron)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFont(font2)
        self.line_5.setFrameShape(QFrame.Shape.HLine)
        self.line_5.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_8.addWidget(self.line_5)

        self.horizontalLayout_menu_vueron = QHBoxLayout()
        self.horizontalLayout_menu_vueron.setObjectName(u"horizontalLayout_menu_vueron")
        self.horizontalLayout_menu_vueron.setContentsMargins(-1, 0, -1, -1)
        self.horizontalSpacer_5 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_menu_vueron.addItem(self.horizontalSpacer_5)

        self.pushButton_open_received_path_vueron = QPushButton(self.groupBox_vueron)
        self.pushButton_open_received_path_vueron.setObjectName(u"pushButton_open_received_path_vueron")
        self.pushButton_open_received_path_vueron.setEnabled(True)
        self.pushButton_open_received_path_vueron.setFont(font2)

        self.horizontalLayout_menu_vueron.addWidget(self.pushButton_open_received_path_vueron)

        self.pushButton_setting_vueron = QPushButton(self.groupBox_vueron)
        self.pushButton_setting_vueron.setObjectName(u"pushButton_setting_vueron")
        self.pushButton_setting_vueron.setEnabled(False)
        self.pushButton_setting_vueron.setFont(font2)

        self.horizontalLayout_menu_vueron.addWidget(self.pushButton_setting_vueron)


        self.verticalLayout_8.addLayout(self.horizontalLayout_menu_vueron)


        self.horizontalLayout_3.addWidget(self.groupBox_vueron)

        self.horizontalSpacer_10 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_10)


        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 0, 1, 7)

        self.horizontalLayout_txrx_nextfoam = QHBoxLayout()
        self.horizontalLayout_txrx_nextfoam.setSpacing(6)
        self.horizontalLayout_txrx_nextfoam.setObjectName(u"horizontalLayout_txrx_nextfoam")
        self.horizontalLayout_txrx_nextfoam.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.horizontalSpacer_3 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_txrx_nextfoam.addItem(self.horizontalSpacer_3)

        self.progressBar_tx_nextfoam = QProgressBar(self.groupBox)
        self.progressBar_tx_nextfoam.setObjectName(u"progressBar_tx_nextfoam")
        sizePolicy2.setHeightForWidth(self.progressBar_tx_nextfoam.sizePolicy().hasHeightForWidth())
        self.progressBar_tx_nextfoam.setSizePolicy(sizePolicy2)
        self.progressBar_tx_nextfoam.setMinimumSize(QSize(0, 20))
        self.progressBar_tx_nextfoam.setMaximumSize(QSize(8, 16777215))
        self.progressBar_tx_nextfoam.setFont(font2)
        self.progressBar_tx_nextfoam.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.progressBar_tx_nextfoam.setStyleSheet(u"QProgressBar {\n"
"        border: 1px solid gray;\n"
"        text-align: center;\n"
"    }\n"
"    QProgressBar::chunk {\n"
"        background-color:  darkmagenta;\n"
"        height: 5px;\n"
"        margin: 1px;\n"
"    }")
        self.progressBar_tx_nextfoam.setMaximum(100)
        self.progressBar_tx_nextfoam.setValue(2)
        self.progressBar_tx_nextfoam.setTextVisible(False)
        self.progressBar_tx_nextfoam.setOrientation(Qt.Orientation.Vertical)
        self.progressBar_tx_nextfoam.setInvertedAppearance(True)

        self.horizontalLayout_txrx_nextfoam.addWidget(self.progressBar_tx_nextfoam)

        self.progressBar_rx_nextfoam = QProgressBar(self.groupBox)
        self.progressBar_rx_nextfoam.setObjectName(u"progressBar_rx_nextfoam")
        sizePolicy2.setHeightForWidth(self.progressBar_rx_nextfoam.sizePolicy().hasHeightForWidth())
        self.progressBar_rx_nextfoam.setSizePolicy(sizePolicy2)
        self.progressBar_rx_nextfoam.setMinimumSize(QSize(0, 20))
        self.progressBar_rx_nextfoam.setMaximumSize(QSize(8, 16777215))
        self.progressBar_rx_nextfoam.setFont(font2)
        self.progressBar_rx_nextfoam.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.progressBar_rx_nextfoam.setStyleSheet(u"QProgressBar {\n"
"        border: 1px solid gray;\n"
"        text-align: center;\n"
"    }\n"
"    QProgressBar::chunk {\n"
"        background-color:  darkblue;\n"
"        height: 5px;\n"
"        margin: 1px;\n"
"    }")
        self.progressBar_rx_nextfoam.setMaximum(100)
        self.progressBar_rx_nextfoam.setValue(2)
        self.progressBar_rx_nextfoam.setTextVisible(False)
        self.progressBar_rx_nextfoam.setOrientation(Qt.Orientation.Vertical)
        self.progressBar_rx_nextfoam.setInvertedAppearance(False)
        self.progressBar_rx_nextfoam.setTextDirection(QProgressBar.Direction.TopToBottom)

        self.horizontalLayout_txrx_nextfoam.addWidget(self.progressBar_rx_nextfoam)

        self.horizontalSpacer_4 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_txrx_nextfoam.addItem(self.horizontalSpacer_4)


        self.gridLayout.addLayout(self.horizontalLayout_txrx_nextfoam, 3, 0, 1, 7)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer_12 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_12)

        self.groupBox_nextfoam = QGroupBox(self.groupBox)
        self.groupBox_nextfoam.setObjectName(u"groupBox_nextfoam")
        self.groupBox_nextfoam.setFont(font1)
        self.groupBox_nextfoam.setStyleSheet(u"QGroupBox {\n"
"    border: 1 solid;\n"
"    border-radius: 6;\n"
"    margin-top: 9;\n"
"    border-color : #c8c8c8;\n"
"    padding: 3;\n"
"}\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    left: 10;\n"
"    padding: 2 3;\n"
"}")
        self.verticalLayout_6 = QVBoxLayout(self.groupBox_nextfoam)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(-1, 12, -1, 6)
        self.horizontalLayout_nextfoam = QHBoxLayout()
        self.horizontalLayout_nextfoam.setObjectName(u"horizontalLayout_nextfoam")

        self.verticalLayout_6.addLayout(self.horizontalLayout_nextfoam)

        self.line = QFrame(self.groupBox_nextfoam)
        self.line.setObjectName(u"line")
        self.line.setFont(font2)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_6.addWidget(self.line)

        self.horizontalLayout_menu_nextfoam = QHBoxLayout()
        self.horizontalLayout_menu_nextfoam.setObjectName(u"horizontalLayout_menu_nextfoam")
        self.horizontalLayout_menu_nextfoam.setContentsMargins(-1, 0, -1, -1)
        self.horizontalSpacer_8 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_menu_nextfoam.addItem(self.horizontalSpacer_8)

        self.pushButton_open_received_path_nextfoam = QPushButton(self.groupBox_nextfoam)
        self.pushButton_open_received_path_nextfoam.setObjectName(u"pushButton_open_received_path_nextfoam")
        self.pushButton_open_received_path_nextfoam.setEnabled(True)
        self.pushButton_open_received_path_nextfoam.setFont(font2)

        self.horizontalLayout_menu_nextfoam.addWidget(self.pushButton_open_received_path_nextfoam)

        self.pushButton_setting_nextfoam = QPushButton(self.groupBox_nextfoam)
        self.pushButton_setting_nextfoam.setObjectName(u"pushButton_setting_nextfoam")
        self.pushButton_setting_nextfoam.setEnabled(False)
        self.pushButton_setting_nextfoam.setFont(font2)

        self.horizontalLayout_menu_nextfoam.addWidget(self.pushButton_setting_nextfoam)


        self.verticalLayout_6.addLayout(self.horizontalLayout_menu_nextfoam)


        self.horizontalLayout_4.addWidget(self.groupBox_nextfoam)

        self.horizontalSpacer_13 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_13)


        self.gridLayout.addLayout(self.horizontalLayout_4, 4, 0, 1, 7)


        self.verticalLayout_9.addLayout(self.gridLayout)


        self.verticalLayout_5.addWidget(self.groupBox)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_10 = QVBoxLayout(self.tab_2)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.groupBox_2 = QGroupBox(self.tab_2)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setFont(font3)
        self.groupBox_2.setStyleSheet(u"QGroupBox {\n"
"    border: 1 solid;\n"
"    border-radius: 6;\n"
"    margin-top: 9;\n"
"    border-color : #c8c8c8;\n"
"    padding: 3;\n"
"}\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    left: 10;\n"
"    padding: 2 3;\n"
"}")
        self.horizontalLayout_9 = QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.plainTextEdit_output = QPlainTextEdit(self.groupBox_2)
        self.plainTextEdit_output.setObjectName(u"plainTextEdit_output")
        font6 = QFont()
        font6.setPointSize(10)
        self.plainTextEdit_output.setFont(font6)
        self.plainTextEdit_output.setReadOnly(True)

        self.horizontalLayout_9.addWidget(self.plainTextEdit_output)


        self.verticalLayout_10.addWidget(self.groupBox_2)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_9)

        self.pushButton = QPushButton(self.tab_2)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout_8.addWidget(self.pushButton)


        self.verticalLayout_10.addLayout(self.horizontalLayout_8)

        self.tabWidget.addTab(self.tab_2, "")

        self.horizontalLayout_6.addWidget(self.tabWidget)


        self.verticalLayout_4.addLayout(self.horizontalLayout_6)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionConnect_all.setText(QCoreApplication.translate("MainWindow", u"Connect all", None))
        self.actionDisconnect_all.setText(QCoreApplication.translate("MainWindow", u"Disconnect all", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("MainWindow", u"< Menu >", None))
        self.pushButton_connect_all.setText(QCoreApplication.translate("MainWindow", u"\uc804\uccb4 \uc5f0\uacb0", None))
        self.pushButton_disconnect_all.setText(QCoreApplication.translate("MainWindow", u"\uc804\uccb4 \uc5f0\uacb0 \ud574\uc81c", None))
        self.pushButton_open_received_path_datahub.setText(QCoreApplication.translate("MainWindow", u"\ub85c\uadf8 \ubcf4\uae30", None))
        self.pushButton_setting_datahub.setText(QCoreApplication.translate("MainWindow", u"\uc124\uc815", None))
        self.checkBox_auto_reconnect.setText(QCoreApplication.translate("MainWindow", u"\uc790\ub3d9 \uc7ac\uc811\uc18d", None))
        self.pushButton_create_sim_data.setText(QCoreApplication.translate("MainWindow", u"Create Sim Data", None))
        self.pushButton_show_log.setText(QCoreApplication.translate("MainWindow", u"Show Log", None))
        self.pushButton_open_solver_data_log.setText(QCoreApplication.translate("MainWindow", u"Solver Data Log", None))
        self.pushButton_run_live_viewer.setText(QCoreApplication.translate("MainWindow", u"Live Viewer", None))
        self.pushButton_open_solver_data_log_2.setText(QCoreApplication.translate("MainWindow", u"Solver Data Log", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"< Monitoring Dashboard >", None))
        self.groupBox_keti.setTitle(QCoreApplication.translate("MainWindow", u"< Client - KETI >", None))
        self.pushButton_open_received_path_keti.setText(QCoreApplication.translate("MainWindow", u"\ub85c\uadf8 \ubcf4\uae30", None))
        self.pushButton_setting_keti.setText(QCoreApplication.translate("MainWindow", u"\uc124\uc815", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Running Threads:", None))
        self.text_thread_keti.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.groupBox_pintel.setTitle(QCoreApplication.translate("MainWindow", u"< Client - PINTEL >", None))
        self.pushButton_open_received_path_pintel.setText(QCoreApplication.translate("MainWindow", u"\ub85c\uadf8 \ubcf4\uae30", None))
        self.pushButton_setting_pintel.setText(QCoreApplication.translate("MainWindow", u"\uc124\uc815", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Running Threads:", None))
        self.text_thread_pintel.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.groupBox_datahub.setTitle(QCoreApplication.translate("MainWindow", u"< Data Hub >", None))
        self.progressBar_tx_pintel.setFormat("")
        self.progressBar_rx_pintel.setFormat("")
        self.progressBar_tx_keti.setFormat("")
        self.progressBar_rx_keti.setFormat("")
        self.progressBar_tx_vueron.setFormat("")
        self.progressBar_rx_vueron.setFormat("")
        self.groupBox_vueron.setTitle(QCoreApplication.translate("MainWindow", u"< Client - Vueron >", None))
        self.pushButton_open_received_path_vueron.setText(QCoreApplication.translate("MainWindow", u"\ub85c\uadf8 \ubcf4\uae30", None))
        self.pushButton_setting_vueron.setText(QCoreApplication.translate("MainWindow", u"\uc124\uc815", None))
        self.progressBar_tx_nextfoam.setFormat("")
        self.progressBar_rx_nextfoam.setFormat("")
        self.groupBox_nextfoam.setTitle(QCoreApplication.translate("MainWindow", u"< Client - NEXTfoam >", None))
        self.pushButton_open_received_path_nextfoam.setText(QCoreApplication.translate("MainWindow", u"\ub85c\uadf8 \ubcf4\uae30", None))
        self.pushButton_setting_nextfoam.setText(QCoreApplication.translate("MainWindow", u"\uc124\uc815", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Network View", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"< Output >", None))
        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"Clear", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Message", None))
    # retranslateUi

