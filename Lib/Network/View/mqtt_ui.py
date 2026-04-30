# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mqtt.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QSplitter, QToolButton, QVBoxLayout, QWidget)

class Ui_Form_Mqtt(object):
    def setupUi(self, Form_Mqtt):
        if not Form_Mqtt.objectName():
            Form_Mqtt.setObjectName(u"Form_Mqtt")
        Form_Mqtt.resize(276, 109)
        font = QFont()
        font.setFamilies([u"\ub9d1\uc740 \uace0\ub515"])
        font.setPointSize(10)
        Form_Mqtt.setFont(font)
        self.verticalLayout = QVBoxLayout(Form_Mqtt)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(Form_Mqtt)
        self.label.setObjectName(u"label")
        font1 = QFont()
        font1.setFamilies([u"\ub9d1\uc740 \uace0\ub515"])
        font1.setPointSize(9)
        self.label.setFont(font1)

        self.horizontalLayout.addWidget(self.label)

        self.ip_comboBox = QComboBox(Form_Mqtt)
        self.ip_comboBox.addItem("")
        self.ip_comboBox.addItem("")
        self.ip_comboBox.addItem("")
        self.ip_comboBox.addItem("")
        self.ip_comboBox.addItem("")
        self.ip_comboBox.setObjectName(u"ip_comboBox")
        self.ip_comboBox.setMinimumSize(QSize(130, 0))
        font2 = QFont()
        font2.setFamilies([u"\ub9d1\uc740 \uace0\ub515"])
        font2.setPointSize(9)
        font2.setBold(False)
        self.ip_comboBox.setFont(font2)
        self.ip_comboBox.setEditable(True)

        self.horizontalLayout.addWidget(self.ip_comboBox)

        self.label_2 = QLabel(Form_Mqtt)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font1)

        self.horizontalLayout.addWidget(self.label_2)

        self.port_comboBox = QComboBox(Form_Mqtt)
        self.port_comboBox.addItem("")
        self.port_comboBox.addItem("")
        self.port_comboBox.addItem("")
        self.port_comboBox.addItem("")
        self.port_comboBox.setObjectName(u"port_comboBox")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.port_comboBox.sizePolicy().hasHeightForWidth())
        self.port_comboBox.setSizePolicy(sizePolicy)
        self.port_comboBox.setMinimumSize(QSize(70, 0))
        self.port_comboBox.setFont(font2)
        self.port_comboBox.setEditable(True)

        self.horizontalLayout.addWidget(self.port_comboBox)

        self.horizontalLayout.setStretch(1, 3)
        self.horizontalLayout.setStretch(3, 1)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setSpacing(4)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.toolButton_settings = QToolButton(Form_Mqtt)
        self.toolButton_settings.setObjectName(u"toolButton_settings")

        self.horizontalLayout_5.addWidget(self.toolButton_settings)

        self.horizontalSpacer_2 = QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_2)

        self.connect_button = QPushButton(Form_Mqtt)
        self.connect_button.setObjectName(u"connect_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.connect_button.sizePolicy().hasHeightForWidth())
        self.connect_button.setSizePolicy(sizePolicy1)
        self.connect_button.setMinimumSize(QSize(0, 0))
        font3 = QFont()
        font3.setFamilies([u"\ub9d1\uc740 \uace0\ub515"])
        font3.setPointSize(9)
        font3.setBold(True)
        self.connect_button.setFont(font3)
        self.connect_button.setStyleSheet(u"QPushButton {\n"
"    padding: 3px;\n"
"    color: #000000;\n"
"    border: 1px solid #a0a0a0;\n"
"	border-radius: 3px;\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,\n"
"                                stop: 0 #fcfcfc, stop: 1 #eeeeee);\n"
"}\n"
"\n"
"QPushButton::disabled {\n"
"	color: #aaaaaa;\n"
"    border-radius: 3px;\n"
"	background-color: #dddddd;\n"
"}\n"
"\n"
"QPushButton::hover {\n"
"    border: 1px solid darkgray;\n"
"    border-radius: 3px;\n"
"	background-color: #f9f9f9;\n"
"}\n"
"\n"
"QPushButton::pressed {\n"
"	background-color: #dddddd;\n"
"}")
        self.connect_button.setAutoDefault(False)

        self.horizontalLayout_5.addWidget(self.connect_button)

        self.disconnect_button = QPushButton(Form_Mqtt)
        self.disconnect_button.setObjectName(u"disconnect_button")
        self.disconnect_button.setEnabled(True)
        sizePolicy1.setHeightForWidth(self.disconnect_button.sizePolicy().hasHeightForWidth())
        self.disconnect_button.setSizePolicy(sizePolicy1)
        self.disconnect_button.setMinimumSize(QSize(0, 0))
        self.disconnect_button.setFont(font2)
        self.disconnect_button.setStyleSheet(u"QPushButton {\n"
"    padding: 3px;\n"
"    color: #000000;\n"
"    border: 1px solid #a0a0a0;\n"
"	border-radius: 3px;\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,\n"
"                                stop: 0 #fcfcfc, stop: 1 #eeeeee);\n"
"}\n"
"\n"
"QPushButton::disabled {\n"
"	color: #aaaaaa;\n"
"    border-radius: 3px;\n"
"	background-color: #dddddd;\n"
"}\n"
"\n"
"QPushButton::hover {\n"
"    border: 1px solid darkgray;\n"
"    border-radius: 3px;\n"
"	background-color: #f9f9f9;\n"
"}\n"
"\n"
"QPushButton::pressed {\n"
"	background-color: #dddddd;\n"
"}")
        self.disconnect_button.setAutoDefault(True)

        self.horizontalLayout_5.addWidget(self.disconnect_button)

        self.horizontalLayout_5.setStretch(2, 5)
        self.horizontalLayout_5.setStretch(3, 5)

        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.splitter = QSplitter(Form_Mqtt)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setFont(font1)
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.lineEdit = QLineEdit(self.splitter)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setMinimumSize(QSize(0, 27))
        font4 = QFont()
        font4.setFamilies([u"\ub9d1\uc740 \uace0\ub515"])
        font4.setPointSize(10)
        font4.setBold(False)
        font4.setItalic(False)
        font4.setUnderline(False)
        self.lineEdit.setFont(font4)
        self.lineEdit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lineEdit.setStyleSheet(u"QLineEdit{\n"
"	border: 1 solid darkgray;\n"
"	border-radius: 4;\n"
"	border-color : orange;\n"
"}")
        self.lineEdit.setFrame(True)
        self.lineEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setClearButtonEnabled(False)
        self.splitter.addWidget(self.lineEdit)

        self.verticalLayout.addWidget(self.splitter)

        QWidget.setTabOrder(self.ip_comboBox, self.port_comboBox)
        QWidget.setTabOrder(self.port_comboBox, self.connect_button)
        QWidget.setTabOrder(self.connect_button, self.disconnect_button)

        self.retranslateUi(Form_Mqtt)

        self.connect_button.setDefault(True)


        QMetaObject.connectSlotsByName(Form_Mqtt)
    # setupUi

    def retranslateUi(self, Form_Mqtt):
        Form_Mqtt.setWindowTitle(QCoreApplication.translate("Form_Mqtt", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form_Mqtt", u"IP:", None))
        self.ip_comboBox.setItemText(0, QCoreApplication.translate("Form_Mqtt", u"localhost", None))
        self.ip_comboBox.setItemText(1, QCoreApplication.translate("Form_Mqtt", u"127.0.0.1", None))
        self.ip_comboBox.setItemText(2, QCoreApplication.translate("Form_Mqtt", u"192.168.2.60", None))
        self.ip_comboBox.setItemText(3, QCoreApplication.translate("Form_Mqtt", u"112.216.142.34", None))
        self.ip_comboBox.setItemText(4, QCoreApplication.translate("Form_Mqtt", u"175.45.202.48", None))

        self.ip_comboBox.setCurrentText(QCoreApplication.translate("Form_Mqtt", u"localhost", None))
        self.ip_comboBox.setPlaceholderText("")
        self.label_2.setText(QCoreApplication.translate("Form_Mqtt", u"Port:", None))
        self.port_comboBox.setItemText(0, QCoreApplication.translate("Form_Mqtt", u"1883", None))
        self.port_comboBox.setItemText(1, QCoreApplication.translate("Form_Mqtt", u"7400", None))
        self.port_comboBox.setItemText(2, QCoreApplication.translate("Form_Mqtt", u"7500", None))
        self.port_comboBox.setItemText(3, QCoreApplication.translate("Form_Mqtt", u"8883", None))

        self.port_comboBox.setPlaceholderText("")
        self.toolButton_settings.setText(QCoreApplication.translate("Form_Mqtt", u"...", None))
        self.connect_button.setText(QCoreApplication.translate("Form_Mqtt", u"Connect", None))
        self.disconnect_button.setText(QCoreApplication.translate("Form_Mqtt", u"Disconnect", None))
        self.lineEdit.setText(QCoreApplication.translate("Form_Mqtt", u"Ready (MQTT)", None))
    # retranslateUi

