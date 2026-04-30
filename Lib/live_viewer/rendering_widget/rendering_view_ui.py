# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'rendering_view.ui'
##
## Created by: Qt User Interface Compiler version 6.4.3
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from .flat_push_button import FlatPushButton
from .rendering_widget import RenderingWidget
from . import resource_rc

class Ui_RenderingView(object):
    def setupUi(self, RenderingView):
        if not RenderingView.objectName():
            RenderingView.setObjectName(u"RenderingView")
        RenderingView.resize(557, 76)
        self.verticalLayout = QVBoxLayout(RenderingView)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(RenderingView)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout_3 = QVBoxLayout(self.frame)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.widget = QWidget(self.frame)
        self.widget.setObjectName(u"widget")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.axis = FlatPushButton(self.widget)
        self.axis.setObjectName(u"axis")
        self.axis.setMaximumSize(QSize(32, 32))
        icon = QIcon()
        icon.addFile(u":/graphicsIcons/originAxes", QSize(), QIcon.Normal, QIcon.Off)
        self.axis.setIcon(icon)
        self.axis.setIconSize(QSize(22, 22))
        self.axis.setCheckable(True)
        self.axis.setChecked(False)

        self.horizontalLayout.addWidget(self.axis)

        self.cubeAxis = FlatPushButton(self.widget)
        self.cubeAxis.setObjectName(u"cubeAxis")
        self.cubeAxis.setMaximumSize(QSize(32, 32))
        icon1 = QIcon()
        icon1.addFile(u":/graphicsIcons/ruler", QSize(), QIcon.Normal, QIcon.Off)
        self.cubeAxis.setIcon(icon1)
        self.cubeAxis.setIconSize(QSize(24, 24))
        self.cubeAxis.setCheckable(True)

        self.horizontalLayout.addWidget(self.cubeAxis)

        self.ruler = FlatPushButton(self.widget)
        self.ruler.setObjectName(u"ruler")
        self.ruler.setMaximumSize(QSize(32, 32))
        icon2 = QIcon()
        icon2.addFile(u":/graphicsIcons/distance.png", QSize(), QIcon.Normal, QIcon.Off)
        self.ruler.setIcon(icon2)
        self.ruler.setIconSize(QSize(24, 24))
        self.ruler.setCheckable(True)

        self.horizontalLayout.addWidget(self.ruler)

        self.perspective = FlatPushButton(self.widget)
        self.perspective.setObjectName(u"perspective")
        self.perspective.setMaximumSize(QSize(32, 32))
        icon3 = QIcon()
        icon3.addFile(u":/graphicsIcons/2d-label-icon.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.perspective.setIcon(icon3)
        self.perspective.setIconSize(QSize(24, 24))
        self.perspective.setCheckable(True)

        self.horizontalLayout.addWidget(self.perspective)

        self.fit = FlatPushButton(self.widget)
        self.fit.setObjectName(u"fit")
        self.fit.setMaximumSize(QSize(32, 32))
        icon4 = QIcon()
        icon4.addFile(u":/icons/expand.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.fit.setIcon(icon4)
        self.fit.setIconSize(QSize(24, 24))

        self.horizontalLayout.addWidget(self.fit)

        self.alignAxis = FlatPushButton(self.widget)
        self.alignAxis.setObjectName(u"alignAxis")
        self.alignAxis.setMaximumSize(QSize(32, 32))
        icon5 = QIcon()
        icon5.addFile(u":/graphicsIcons/alignAxis.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.alignAxis.setIcon(icon5)
        self.alignAxis.setIconSize(QSize(24, 24))

        self.horizontalLayout.addWidget(self.alignAxis)

        self.rotate = FlatPushButton(self.widget)
        self.rotate.setObjectName(u"rotate")
        self.rotate.setMaximumSize(QSize(32, 32))
        icon6 = QIcon()
        icon6.addFile(u":/icons/reload.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.rotate.setIcon(icon6)
        self.rotate.setIconSize(QSize(24, 24))

        self.horizontalLayout.addWidget(self.rotate)

        self.renderingMode = QComboBox(self.widget)
        self.renderingMode.addItem("")
        self.renderingMode.addItem("")
        self.renderingMode.addItem("")
        self.renderingMode.addItem("")
        self.renderingMode.addItem("")
        self.renderingMode.setObjectName(u"renderingMode")
        self.renderingMode.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout.addWidget(self.renderingMode)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.frame_2 = QFrame(self.widget)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Box)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(2, 1, 1, 1)
        self.label = QLabel(self.frame_2)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label.setFont(font)

        self.horizontalLayout_2.addWidget(self.label)

        self.bg2 = QPushButton(self.frame_2)
        self.bg2.setObjectName(u"bg2")
        self.bg2.setMaximumSize(QSize(24, 24))

        self.horizontalLayout_2.addWidget(self.bg2)

        self.bg1 = QPushButton(self.frame_2)
        self.bg1.setObjectName(u"bg1")
        self.bg1.setMaximumSize(QSize(24, 24))

        self.horizontalLayout_2.addWidget(self.bg1)


        self.horizontalLayout.addWidget(self.frame_2)


        self.verticalLayout_3.addWidget(self.widget)

        self.view = RenderingWidget(self.frame)
        self.view.setObjectName(u"view")

        self.verticalLayout_3.addWidget(self.view)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(RenderingView)

        QMetaObject.connectSlotsByName(RenderingView)
    # setupUi

    def retranslateUi(self, RenderingView):
#if QT_CONFIG(tooltip)
        self.axis.setToolTip(QCoreApplication.translate("RenderingView", u" Set the axis direction based on the origin", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.cubeAxis.setToolTip(QCoreApplication.translate("RenderingView", u" Display x,y and z axis coordinates", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.ruler.setToolTip(QCoreApplication.translate("RenderingView", u"Ruler", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.perspective.setToolTip(QCoreApplication.translate("RenderingView", u" Toggle between Persepctive and Orthogonal views", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.fit.setToolTip(QCoreApplication.translate("RenderingView", u" Show the entire model in the windows to fit the view", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.alignAxis.setToolTip(QCoreApplication.translate("RenderingView", u" View the model from cross-section of the closest-axis, aligning with current state", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.rotate.setToolTip(QCoreApplication.translate("RenderingView", u" Rotate the model by 90 degrees", None))
#endif // QT_CONFIG(tooltip)
        self.renderingMode.setItemText(0, QCoreApplication.translate("RenderingView", u"Feature Edges", None))
        self.renderingMode.setItemText(1, QCoreApplication.translate("RenderingView", u"Points", None))
        self.renderingMode.setItemText(2, QCoreApplication.translate("RenderingView", u"Surface", None))
        self.renderingMode.setItemText(3, QCoreApplication.translate("RenderingView", u"Surface With Edges", None))
        self.renderingMode.setItemText(4, QCoreApplication.translate("RenderingView", u"Wireframe", None))

        self.label.setText(QCoreApplication.translate("RenderingView", u"BG", None))
        self.bg2.setText("")
        self.bg1.setText("")
        pass
    # retranslateUi

