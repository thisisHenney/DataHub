# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QMenuBar, QPushButton,
    QSizePolicy, QSplitter, QStatusBar, QVBoxLayout,
    QWidget)

from Lib.live_viewer.rendering_widget.rendering_dock import RenderingView

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.pushButton = QPushButton(self.layoutWidget)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout.addWidget(self.pushButton)

        self.label = QLabel(self.layoutWidget)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout.addWidget(self.label)

        self.listWidget = QListWidget(self.layoutWidget)
        brush = QBrush(QColor(111, 111, 111, 255))
        brush.setStyle(Qt.BrushStyle.NoBrush)
        __qlistwidgetitem = QListWidgetItem(self.listWidget)
        __qlistwidgetitem.setCheckState(Qt.Unchecked);
        __qlistwidgetitem.setFont(font);
        __qlistwidgetitem.setForeground(brush);
        brush1 = QBrush(QColor(255, 135, 135, 255))
        brush1.setStyle(Qt.BrushStyle.NoBrush)
        __qlistwidgetitem1 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem1.setCheckState(Qt.Unchecked);
        __qlistwidgetitem1.setFont(font);
        __qlistwidgetitem1.setForeground(brush1);
        brush2 = QBrush(QColor(255, 55, 55, 255))
        brush2.setStyle(Qt.BrushStyle.NoBrush)
        __qlistwidgetitem2 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem2.setCheckState(Qt.Unchecked);
        __qlistwidgetitem2.setFont(font);
        __qlistwidgetitem2.setForeground(brush2);
        __qlistwidgetitem3 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem3.setCheckState(Qt.Checked);
        __qlistwidgetitem3.setFont(font);
        __qlistwidgetitem4 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem4.setCheckState(Qt.Checked);
        __qlistwidgetitem4.setFont(font);
        __qlistwidgetitem5 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem5.setCheckState(Qt.Checked);
        __qlistwidgetitem5.setFont(font);
        __qlistwidgetitem6 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem6.setCheckState(Qt.Checked);
        __qlistwidgetitem6.setFont(font);
        __qlistwidgetitem7 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem7.setCheckState(Qt.Checked);
        __qlistwidgetitem7.setFont(font);
        __qlistwidgetitem8 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem8.setCheckState(Qt.Checked);
        __qlistwidgetitem8.setFont(font);
        __qlistwidgetitem9 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem9.setCheckState(Qt.Checked);
        __qlistwidgetitem9.setFont(font);
        __qlistwidgetitem10 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem10.setCheckState(Qt.Checked);
        __qlistwidgetitem10.setFont(font);
        __qlistwidgetitem11 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem11.setCheckState(Qt.Checked);
        __qlistwidgetitem11.setFont(font);
        __qlistwidgetitem12 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem12.setCheckState(Qt.Checked);
        __qlistwidgetitem12.setFont(font);
        __qlistwidgetitem13 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem13.setCheckState(Qt.Checked);
        __qlistwidgetitem13.setFont(font);
        __qlistwidgetitem14 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem14.setCheckState(Qt.Checked);
        __qlistwidgetitem14.setFont(font);
        __qlistwidgetitem15 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem15.setCheckState(Qt.Checked);
        __qlistwidgetitem15.setFont(font);
        __qlistwidgetitem16 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem16.setCheckState(Qt.Unchecked);
        __qlistwidgetitem16.setFont(font);
        __qlistwidgetitem17 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem17.setCheckState(Qt.Unchecked);
        __qlistwidgetitem17.setFont(font);
        __qlistwidgetitem18 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem18.setCheckState(Qt.Unchecked);
        __qlistwidgetitem18.setFont(font);
        self.listWidget.setObjectName(u"listWidget")

        self.verticalLayout.addWidget(self.listWidget)

        self.splitter.addWidget(self.layoutWidget)
        self.view_dock = RenderingView(self.splitter)
        self.view_dock.setObjectName(u"view_dock")
        self.splitter.addWidget(self.view_dock)

        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"Refresh", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\ud654\uba74 \ub4dc\ub798\uadf8=\uc774\ub3d9 \ud720=\uc90c \u2192\n"
"\n"
"\u2193 \uc544\ub798 \uccb4\ud06c\ubc15\uc2a4\ub97c \ud074\ub9ad\ud558\uc5ec \ud45c\uc2dc/\uc228\uae40", None))

        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        ___qlistwidgetitem = self.listWidget.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("MainWindow", u"grid 2", None));
        ___qlistwidgetitem1 = self.listWidget.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("MainWindow", u"grid 10", None));
        ___qlistwidgetitem2 = self.listWidget.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("MainWindow", u"grid 100", None));
        ___qlistwidgetitem3 = self.listWidget.item(3)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("MainWindow", u"Pintel 1", None));
        ___qlistwidgetitem4 = self.listWidget.item(4)
        ___qlistwidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Pintel 2", None));
        ___qlistwidgetitem5 = self.listWidget.item(5)
        ___qlistwidgetitem5.setText(QCoreApplication.translate("MainWindow", u"Pintel 3", None));
        ___qlistwidgetitem6 = self.listWidget.item(6)
        ___qlistwidgetitem6.setText(QCoreApplication.translate("MainWindow", u"Pintel 4", None));
        ___qlistwidgetitem7 = self.listWidget.item(7)
        ___qlistwidgetitem7.setText(QCoreApplication.translate("MainWindow", u"Pintel 5", None));
        ___qlistwidgetitem8 = self.listWidget.item(8)
        ___qlistwidgetitem8.setText(QCoreApplication.translate("MainWindow", u"Pintel 6", None));
        ___qlistwidgetitem9 = self.listWidget.item(9)
        ___qlistwidgetitem9.setText(QCoreApplication.translate("MainWindow", u"Pintel 7", None));
        ___qlistwidgetitem10 = self.listWidget.item(10)
        ___qlistwidgetitem10.setText(QCoreApplication.translate("MainWindow", u"Pintel 8", None));
        ___qlistwidgetitem11 = self.listWidget.item(11)
        ___qlistwidgetitem11.setText(QCoreApplication.translate("MainWindow", u"Pintel 9", None));
        ___qlistwidgetitem12 = self.listWidget.item(12)
        ___qlistwidgetitem12.setText(QCoreApplication.translate("MainWindow", u"KETI", None));
        ___qlistwidgetitem13 = self.listWidget.item(13)
        ___qlistwidgetitem13.setText(QCoreApplication.translate("MainWindow", u"Vueron 1", None));
        ___qlistwidgetitem14 = self.listWidget.item(14)
        ___qlistwidgetitem14.setText(QCoreApplication.translate("MainWindow", u"Vueron 2", None));
        ___qlistwidgetitem15 = self.listWidget.item(15)
        ___qlistwidgetitem15.setText(QCoreApplication.translate("MainWindow", u"Union 1", None));
        ___qlistwidgetitem16 = self.listWidget.item(16)
        ___qlistwidgetitem16.setText(QCoreApplication.translate("MainWindow", u"Union 2", None));
        ___qlistwidgetitem17 = self.listWidget.item(17)
        ___qlistwidgetitem17.setText(QCoreApplication.translate("MainWindow", u"Union 3", None));
        ___qlistwidgetitem18 = self.listWidget.item(18)
        ___qlistwidgetitem18.setText(QCoreApplication.translate("MainWindow", u"Union 4", None));
        self.listWidget.setSortingEnabled(__sortingEnabled)

    # retranslateUi

