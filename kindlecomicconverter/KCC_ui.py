# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'KCC.ui'
##
## Created by: Qt User Interface Compiler version 6.9.3
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QProgressBar,
    QPushButton, QSizePolicy, QSlider, QSpinBox,
    QStatusBar, QWidget)
from . import KCC_rc

class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        if not mainWindow.objectName():
            mainWindow.setObjectName(u"mainWindow")
        mainWindow.resize(566, 573)
        icon = QIcon()
        icon.addFile(u":/Icon/icons/comic2ebook.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        mainWindow.setWindowIcon(icon)
        self.centralWidget = QWidget(mainWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self.gridLayout = QGridLayout(self.centralWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, -1, -1, 5)
        self.jobList = QListWidget(self.centralWidget)
        self.jobList.setObjectName(u"jobList")
        self.jobList.setMinimumSize(QSize(0, 150))
        self.jobList.setStyleSheet(u"")
        self.jobList.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.jobList.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.jobList.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.gridLayout.addWidget(self.jobList, 2, 0, 1, 2)

        self.toolWidget = QWidget(self.centralWidget)
        self.toolWidget.setObjectName(u"toolWidget")
        self.horizontalLayout = QHBoxLayout(self.toolWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.editorButton = QPushButton(self.toolWidget)
        self.editorButton.setObjectName(u"editorButton")
        self.editorButton.setMinimumSize(QSize(0, 30))
        icon1 = QIcon()
        icon1.addFile(u":/Other/icons/editor.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.editorButton.setIcon(icon1)

        self.horizontalLayout.addWidget(self.editorButton)

        self.kofiButton = QPushButton(self.toolWidget)
        self.kofiButton.setObjectName(u"kofiButton")
        self.kofiButton.setMinimumSize(QSize(0, 30))
        icon2 = QIcon()
        icon2.addFile(u":/Brand/icons/kofi_symbol.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.kofiButton.setIcon(icon2)
        self.kofiButton.setIconSize(QSize(19, 16))

        self.horizontalLayout.addWidget(self.kofiButton)

        self.wikiButton = QPushButton(self.toolWidget)
        self.wikiButton.setObjectName(u"wikiButton")
        self.wikiButton.setMinimumSize(QSize(0, 30))
        icon3 = QIcon()
        icon3.addFile(u":/Other/icons/wiki.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.wikiButton.setIcon(icon3)

        self.horizontalLayout.addWidget(self.wikiButton)


        self.gridLayout.addWidget(self.toolWidget, 0, 0, 1, 2)

        self.buttonWidget = QWidget(self.centralWidget)
        self.buttonWidget.setObjectName(u"buttonWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonWidget.sizePolicy().hasHeightForWidth())
        self.buttonWidget.setSizePolicy(sizePolicy)
        self.gridLayout_4 = QGridLayout(self.buttonWidget)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.convertButton = QPushButton(self.buttonWidget)
        self.convertButton.setObjectName(u"convertButton")
        self.convertButton.setMinimumSize(QSize(0, 30))
        font = QFont()
        font.setBold(True)
        self.convertButton.setFont(font)
        icon4 = QIcon()
        icon4.addFile(u":/Other/icons/convert.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.convertButton.setIcon(icon4)

        self.gridLayout_4.addWidget(self.convertButton, 1, 3, 1, 1)

        self.clearButton = QPushButton(self.buttonWidget)
        self.clearButton.setObjectName(u"clearButton")
        self.clearButton.setMinimumSize(QSize(0, 30))
        icon5 = QIcon()
        icon5.addFile(u":/Other/icons/clear.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.clearButton.setIcon(icon5)

        self.gridLayout_4.addWidget(self.clearButton, 0, 3, 1, 1)

        self.deviceBox = QComboBox(self.buttonWidget)
        self.deviceBox.setObjectName(u"deviceBox")
        self.deviceBox.setMinimumSize(QSize(0, 28))

        self.gridLayout_4.addWidget(self.deviceBox, 1, 1, 1, 1)

        self.fileButton = QPushButton(self.buttonWidget)
        self.fileButton.setObjectName(u"fileButton")
        self.fileButton.setMinimumSize(QSize(0, 30))
        icon6 = QIcon()
        icon6.addFile(u":/Other/icons/document_new.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.fileButton.setIcon(icon6)

        self.gridLayout_4.addWidget(self.fileButton, 0, 1, 1, 1)

        self.defaultOutputFolderButton = QPushButton(self.buttonWidget)
        self.defaultOutputFolderButton.setObjectName(u"defaultOutputFolderButton")
        self.defaultOutputFolderButton.setMinimumSize(QSize(0, 30))
        icon7 = QIcon()
        icon7.addFile(u":/Other/icons/folder_new.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.defaultOutputFolderButton.setIcon(icon7)

        self.gridLayout_4.addWidget(self.defaultOutputFolderButton, 0, 5, 1, 1)

        self.defaultOutputFolderBox = QCheckBox(self.buttonWidget)
        self.defaultOutputFolderBox.setObjectName(u"defaultOutputFolderBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.defaultOutputFolderBox.sizePolicy().hasHeightForWidth())
        self.defaultOutputFolderBox.setSizePolicy(sizePolicy1)
        self.defaultOutputFolderBox.setTristate(True)

        self.gridLayout_4.addWidget(self.defaultOutputFolderBox, 0, 4, 1, 1)

        self.formatBox = QComboBox(self.buttonWidget)
        self.formatBox.setObjectName(u"formatBox")
        self.formatBox.setMinimumSize(QSize(0, 28))

        self.gridLayout_4.addWidget(self.formatBox, 1, 4, 1, 2)

        self.clearButton.raise_()
        self.deviceBox.raise_()
        self.convertButton.raise_()
        self.formatBox.raise_()
        self.defaultOutputFolderButton.raise_()
        self.fileButton.raise_()
        self.defaultOutputFolderBox.raise_()

        self.gridLayout.addWidget(self.buttonWidget, 3, 0, 1, 2)

        self.progressBar = QProgressBar(self.centralWidget)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMinimumSize(QSize(0, 30))
        self.progressBar.setFont(font)
        self.progressBar.setVisible(False)
        self.progressBar.setAlignment(Qt.AlignmentFlag.AlignJustify|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.progressBar, 1, 0, 1, 2)

        self.customWidget = QWidget(self.centralWidget)
        self.customWidget.setObjectName(u"customWidget")
        self.customWidget.setVisible(False)
        self.gridLayout_3 = QGridLayout(self.customWidget)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.hLabel = QLabel(self.customWidget)
        self.hLabel.setObjectName(u"hLabel")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.hLabel.sizePolicy().hasHeightForWidth())
        self.hLabel.setSizePolicy(sizePolicy2)

        self.gridLayout_3.addWidget(self.hLabel, 0, 2, 1, 1)

        self.widthBox = QSpinBox(self.customWidget)
        self.widthBox.setObjectName(u"widthBox")
        self.widthBox.setMaximum(3200)

        self.gridLayout_3.addWidget(self.widthBox, 0, 1, 1, 1)

        self.wLabel = QLabel(self.customWidget)
        self.wLabel.setObjectName(u"wLabel")
        sizePolicy2.setHeightForWidth(self.wLabel.sizePolicy().hasHeightForWidth())
        self.wLabel.setSizePolicy(sizePolicy2)

        self.gridLayout_3.addWidget(self.wLabel, 0, 0, 1, 1)

        self.heightBox = QSpinBox(self.customWidget)
        self.heightBox.setObjectName(u"heightBox")
        self.heightBox.setMaximum(5120)

        self.gridLayout_3.addWidget(self.heightBox, 0, 3, 1, 1)


        self.gridLayout.addWidget(self.customWidget, 8, 0, 1, 2)

        self.croppingWidget = QWidget(self.centralWidget)
        self.croppingWidget.setObjectName(u"croppingWidget")
        self.croppingWidget.setVisible(False)
        self.gridLayout_5 = QGridLayout(self.croppingWidget)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.preserveMarginLabel = QLabel(self.croppingWidget)
        self.preserveMarginLabel.setObjectName(u"preserveMarginLabel")

        self.gridLayout_5.addWidget(self.preserveMarginLabel, 1, 0, 1, 1)

        self.croppingPowerLabel = QLabel(self.croppingWidget)
        self.croppingPowerLabel.setObjectName(u"croppingPowerLabel")

        self.gridLayout_5.addWidget(self.croppingPowerLabel, 0, 0, 1, 1)

        self.croppingPowerSlider = QSlider(self.croppingWidget)
        self.croppingPowerSlider.setObjectName(u"croppingPowerSlider")
        self.croppingPowerSlider.setMaximum(300)
        self.croppingPowerSlider.setSingleStep(1)
        self.croppingPowerSlider.setOrientation(Qt.Orientation.Horizontal)

        self.gridLayout_5.addWidget(self.croppingPowerSlider, 0, 1, 1, 1)

        self.preserveMarginBox = QSpinBox(self.croppingWidget)
        self.preserveMarginBox.setObjectName(u"preserveMarginBox")
        sizePolicy1.setHeightForWidth(self.preserveMarginBox.sizePolicy().hasHeightForWidth())
        self.preserveMarginBox.setSizePolicy(sizePolicy1)
        self.preserveMarginBox.setMaximum(99)
        self.preserveMarginBox.setSingleStep(5)
        self.preserveMarginBox.setValue(0)

        self.gridLayout_5.addWidget(self.preserveMarginBox, 1, 1, 1, 1)


        self.gridLayout.addWidget(self.croppingWidget, 9, 0, 1, 2)

        self.optionWidget = QWidget(self.centralWidget)
        self.optionWidget.setObjectName(u"optionWidget")
        self.gridLayout_2 = QGridLayout(self.optionWidget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gammaBox = QCheckBox(self.optionWidget)
        self.gammaBox.setObjectName(u"gammaBox")

        self.gridLayout_2.addWidget(self.gammaBox, 2, 2, 1, 1)

        self.mangaBox = QCheckBox(self.optionWidget)
        self.mangaBox.setObjectName(u"mangaBox")

        self.gridLayout_2.addWidget(self.mangaBox, 1, 0, 1, 1)

        self.borderBox = QCheckBox(self.optionWidget)
        self.borderBox.setObjectName(u"borderBox")
        self.borderBox.setTristate(True)

        self.gridLayout_2.addWidget(self.borderBox, 3, 0, 1, 1)

        self.interPanelCropBox = QCheckBox(self.optionWidget)
        self.interPanelCropBox.setObjectName(u"interPanelCropBox")
        self.interPanelCropBox.setTristate(True)

        self.gridLayout_2.addWidget(self.interPanelCropBox, 6, 2, 1, 1)

        self.fileFusionBox = QCheckBox(self.optionWidget)
        self.fileFusionBox.setObjectName(u"fileFusionBox")

        self.gridLayout_2.addWidget(self.fileFusionBox, 6, 0, 1, 1)

        self.authorEdit = QLineEdit(self.optionWidget)
        self.authorEdit.setObjectName(u"authorEdit")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.authorEdit.sizePolicy().hasHeightForWidth())
        self.authorEdit.setSizePolicy(sizePolicy3)
        self.authorEdit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.authorEdit.setClearButtonEnabled(False)

        self.gridLayout_2.addWidget(self.authorEdit, 0, 1, 1, 1)

        self.titleEdit = QLineEdit(self.optionWidget)
        self.titleEdit.setObjectName(u"titleEdit")
        sizePolicy3.setHeightForWidth(self.titleEdit.sizePolicy().hasHeightForWidth())
        self.titleEdit.setSizePolicy(sizePolicy3)
        self.titleEdit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.titleEdit.setClearButtonEnabled(False)

        self.gridLayout_2.addWidget(self.titleEdit, 0, 0, 1, 1)

        self.rotateFirstBox = QCheckBox(self.optionWidget)
        self.rotateFirstBox.setObjectName(u"rotateFirstBox")

        self.gridLayout_2.addWidget(self.rotateFirstBox, 8, 1, 1, 1)

        self.eraseRainbowBox = QCheckBox(self.optionWidget)
        self.eraseRainbowBox.setObjectName(u"eraseRainbowBox")

        self.gridLayout_2.addWidget(self.eraseRainbowBox, 7, 2, 1, 1)

        self.chunkSizeCheckBox = QCheckBox(self.optionWidget)
        self.chunkSizeCheckBox.setObjectName(u"chunkSizeCheckBox")

        self.gridLayout_2.addWidget(self.chunkSizeCheckBox, 7, 1, 1, 1)

        self.rotateBox = QCheckBox(self.optionWidget)
        self.rotateBox.setObjectName(u"rotateBox")
        self.rotateBox.setTristate(True)

        self.gridLayout_2.addWidget(self.rotateBox, 1, 1, 1, 1)

        self.outputSplit = QCheckBox(self.optionWidget)
        self.outputSplit.setObjectName(u"outputSplit")

        self.gridLayout_2.addWidget(self.outputSplit, 3, 1, 1, 1)

        self.metadataTitleBox = QCheckBox(self.optionWidget)
        self.metadataTitleBox.setObjectName(u"metadataTitleBox")
        self.metadataTitleBox.setTristate(True)

        self.gridLayout_2.addWidget(self.metadataTitleBox, 7, 0, 1, 1)

        self.qualityBox = QCheckBox(self.optionWidget)
        self.qualityBox.setObjectName(u"qualityBox")
        self.qualityBox.setTristate(True)

        self.gridLayout_2.addWidget(self.qualityBox, 1, 2, 1, 1)

        self.spreadShiftBox = QCheckBox(self.optionWidget)
        self.spreadShiftBox.setObjectName(u"spreadShiftBox")

        self.gridLayout_2.addWidget(self.spreadShiftBox, 5, 0, 1, 1)

        self.disableProcessingBox = QCheckBox(self.optionWidget)
        self.disableProcessingBox.setObjectName(u"disableProcessingBox")

        self.gridLayout_2.addWidget(self.disableProcessingBox, 5, 2, 1, 1)

        self.webtoonBox = QCheckBox(self.optionWidget)
        self.webtoonBox.setObjectName(u"webtoonBox")

        self.gridLayout_2.addWidget(self.webtoonBox, 2, 0, 1, 1)

        self.colorBox = QCheckBox(self.optionWidget)
        self.colorBox.setObjectName(u"colorBox")

        self.gridLayout_2.addWidget(self.colorBox, 3, 2, 1, 1)

        self.croppingBox = QCheckBox(self.optionWidget)
        self.croppingBox.setObjectName(u"croppingBox")
        self.croppingBox.setTristate(True)

        self.gridLayout_2.addWidget(self.croppingBox, 4, 2, 1, 1)

        self.maximizeStrips = QCheckBox(self.optionWidget)
        self.maximizeStrips.setObjectName(u"maximizeStrips")

        self.gridLayout_2.addWidget(self.maximizeStrips, 4, 1, 1, 1)

        self.noRotateBox = QCheckBox(self.optionWidget)
        self.noRotateBox.setObjectName(u"noRotateBox")

        self.gridLayout_2.addWidget(self.noRotateBox, 6, 1, 1, 1)

        self.deleteBox = QCheckBox(self.optionWidget)
        self.deleteBox.setObjectName(u"deleteBox")

        self.gridLayout_2.addWidget(self.deleteBox, 5, 1, 1, 1)

        self.upscaleBox = QCheckBox(self.optionWidget)
        self.upscaleBox.setObjectName(u"upscaleBox")
        self.upscaleBox.setTristate(True)

        self.gridLayout_2.addWidget(self.upscaleBox, 2, 1, 1, 1)

        self.mozJpegBox = QCheckBox(self.optionWidget)
        self.mozJpegBox.setObjectName(u"mozJpegBox")
        self.mozJpegBox.setTristate(True)

        self.gridLayout_2.addWidget(self.mozJpegBox, 4, 0, 1, 1)

        self.autoLevelBox = QCheckBox(self.optionWidget)
        self.autoLevelBox.setObjectName(u"autoLevelBox")

        self.gridLayout_2.addWidget(self.autoLevelBox, 8, 2, 1, 1)


        self.gridLayout.addWidget(self.optionWidget, 5, 0, 1, 2)

        self.gammaWidget = QWidget(self.centralWidget)
        self.gammaWidget.setObjectName(u"gammaWidget")
        self.gammaWidget.setVisible(False)
        self.horizontalLayout_2 = QHBoxLayout(self.gammaWidget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gammaLabel = QLabel(self.gammaWidget)
        self.gammaLabel.setObjectName(u"gammaLabel")

        self.horizontalLayout_2.addWidget(self.gammaLabel)

        self.gammaSlider = QSlider(self.gammaWidget)
        self.gammaSlider.setObjectName(u"gammaSlider")
        self.gammaSlider.setMaximum(250)
        self.gammaSlider.setSingleStep(5)
        self.gammaSlider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_2.addWidget(self.gammaSlider)


        self.gridLayout.addWidget(self.gammaWidget, 7, 0, 1, 2)

        self.chunkSizeWidget = QWidget(self.centralWidget)
        self.chunkSizeWidget.setObjectName(u"chunkSizeWidget")
        sizePolicy3.setHeightForWidth(self.chunkSizeWidget.sizePolicy().hasHeightForWidth())
        self.chunkSizeWidget.setSizePolicy(sizePolicy3)
        self.chunkSizeWidget.setVisible(False)
        self.horizontalLayout_4 = QHBoxLayout(self.chunkSizeWidget)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.chunkSizeLabel = QLabel(self.chunkSizeWidget)
        self.chunkSizeLabel.setObjectName(u"chunkSizeLabel")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.chunkSizeLabel.sizePolicy().hasHeightForWidth())
        self.chunkSizeLabel.setSizePolicy(sizePolicy4)

        self.horizontalLayout_4.addWidget(self.chunkSizeLabel)

        self.chunkSizeBox = QSpinBox(self.chunkSizeWidget)
        self.chunkSizeBox.setObjectName(u"chunkSizeBox")
        self.chunkSizeBox.setMinimum(100)
        self.chunkSizeBox.setMaximum(600)
        self.chunkSizeBox.setValue(400)

        self.horizontalLayout_4.addWidget(self.chunkSizeBox)

        self.chunkSizeWarnLabel = QLabel(self.chunkSizeWidget)
        self.chunkSizeWarnLabel.setObjectName(u"chunkSizeWarnLabel")
        sizePolicy4.setHeightForWidth(self.chunkSizeWarnLabel.sizePolicy().hasHeightForWidth())
        self.chunkSizeWarnLabel.setSizePolicy(sizePolicy4)

        self.horizontalLayout_4.addWidget(self.chunkSizeWarnLabel)


        self.gridLayout.addWidget(self.chunkSizeWidget, 6, 0, 1, 1)

        mainWindow.setCentralWidget(self.centralWidget)
        self.statusBar = QStatusBar(mainWindow)
        self.statusBar.setObjectName(u"statusBar")
        self.statusBar.setSizeGripEnabled(False)
        mainWindow.setStatusBar(self.statusBar)
        QWidget.setTabOrder(self.convertButton, self.clearButton)
        QWidget.setTabOrder(self.clearButton, self.deviceBox)
        QWidget.setTabOrder(self.deviceBox, self.formatBox)
        QWidget.setTabOrder(self.formatBox, self.mangaBox)
        QWidget.setTabOrder(self.mangaBox, self.rotateBox)
        QWidget.setTabOrder(self.rotateBox, self.qualityBox)
        QWidget.setTabOrder(self.qualityBox, self.webtoonBox)
        QWidget.setTabOrder(self.webtoonBox, self.upscaleBox)
        QWidget.setTabOrder(self.upscaleBox, self.gammaBox)
        QWidget.setTabOrder(self.gammaBox, self.borderBox)
        QWidget.setTabOrder(self.borderBox, self.outputSplit)
        QWidget.setTabOrder(self.outputSplit, self.colorBox)
        QWidget.setTabOrder(self.colorBox, self.mozJpegBox)
        QWidget.setTabOrder(self.mozJpegBox, self.maximizeStrips)
        QWidget.setTabOrder(self.maximizeStrips, self.croppingBox)
        QWidget.setTabOrder(self.croppingBox, self.spreadShiftBox)
        QWidget.setTabOrder(self.spreadShiftBox, self.deleteBox)
        QWidget.setTabOrder(self.deleteBox, self.disableProcessingBox)
        QWidget.setTabOrder(self.disableProcessingBox, self.chunkSizeBox)
        QWidget.setTabOrder(self.chunkSizeBox, self.noRotateBox)
        QWidget.setTabOrder(self.noRotateBox, self.interPanelCropBox)
        QWidget.setTabOrder(self.interPanelCropBox, self.eraseRainbowBox)
        QWidget.setTabOrder(self.eraseRainbowBox, self.heightBox)
        QWidget.setTabOrder(self.heightBox, self.croppingPowerSlider)
        QWidget.setTabOrder(self.croppingPowerSlider, self.editorButton)
        QWidget.setTabOrder(self.editorButton, self.wikiButton)
        QWidget.setTabOrder(self.wikiButton, self.jobList)
        QWidget.setTabOrder(self.jobList, self.gammaSlider)
        QWidget.setTabOrder(self.gammaSlider, self.widthBox)

        self.retranslateUi(mainWindow)

        QMetaObject.connectSlotsByName(mainWindow)
    # setupUi

    def retranslateUi(self, mainWindow):
        mainWindow.setWindowTitle(QCoreApplication.translate("mainWindow", u"Kindle Comic Converter", None))
#if QT_CONFIG(tooltip)
        self.jobList.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p>Double click on source to open metadata editor.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.editorButton.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Shift+Click to edit directory.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.editorButton.setText(QCoreApplication.translate("mainWindow", u"Metadata Editor", None))
        self.kofiButton.setText(QCoreApplication.translate("mainWindow", u"Support me on Ko-fi", None))
        self.wikiButton.setText(QCoreApplication.translate("mainWindow", u"Wiki", None))
#if QT_CONFIG(tooltip)
        self.convertButton.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Shift+Click to select the output directory for this list.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.convertButton.setText(QCoreApplication.translate("mainWindow", u"Convert", None))
        self.clearButton.setText(QCoreApplication.translate("mainWindow", u"Clear list", None))
#if QT_CONFIG(tooltip)
        self.deviceBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Target device.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.fileButton.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Add CBR, CBZ, CB7 or PDF file to queue.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.fileButton.setText(QCoreApplication.translate("mainWindow", u"Add file(s)", None))
#if QT_CONFIG(tooltip)
        self.defaultOutputFolderButton.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p>Use this to select the default output directory.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.defaultOutputFolderButton.setText("")
#if QT_CONFIG(tooltip)
        self.defaultOutputFolderBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - next to source<br/></span>Place output files next to source files</p><p><span style=\" font-weight:600; text-decoration: underline;\">Indeterminate - folder next to source<br/></span>Place output files in a folder next to source files</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - Custom<br/></span>Place output files in custom directory specified by right button</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.defaultOutputFolderBox.setText(QCoreApplication.translate("mainWindow", u"Output Folder", None))
#if QT_CONFIG(tooltip)
        self.formatBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Output format.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.hLabel.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Resolution of the target device.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.hLabel.setText(QCoreApplication.translate("mainWindow", u"Custom height:", None))
#if QT_CONFIG(tooltip)
        self.widthBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Resolution of the target device.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.wLabel.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Resolution of the target device.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.wLabel.setText(QCoreApplication.translate("mainWindow", u"Custom width:", None))
#if QT_CONFIG(tooltip)
        self.heightBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Resolution of the target device.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.preserveMarginLabel.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p>After calculating the cropping boundaries, &quot;back up&quot; a specified percentage amount.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.preserveMarginLabel.setText(QCoreApplication.translate("mainWindow", u"Preserve Margin %", None))
        self.croppingPowerLabel.setText(QCoreApplication.translate("mainWindow", u"Cropping power:", None))
#if QT_CONFIG(tooltip)
        self.gammaBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Disable automatic gamma correction.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.gammaBox.setText(QCoreApplication.translate("mainWindow", u"Custom gamma", None))
#if QT_CONFIG(tooltip)
        self.mangaBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Enable right-to-left reading.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.mangaBox.setText(QCoreApplication.translate("mainWindow", u"Right-to-left mode", None))
#if QT_CONFIG(tooltip)
        self.borderBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - Autodetection<br/></span>The color of margins fill will be detected automatically.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Indeterminate - White<br/></span>Margins will be untouched.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - Black<br/></span>Margins will be filled with black color.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.borderBox.setText(QCoreApplication.translate("mainWindow", u"W/B margins", None))
#if QT_CONFIG(tooltip)
        self.interPanelCropBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - Disabled<br/></span>Disabled</p><p><span style=\" font-weight:600; text-decoration: underline;\">Indeterminate - Horizontal<br/></span>Crop empty horizontal lines.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - Both<br/></span>Crop empty horizontal and vertical lines.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.interPanelCropBox.setText(QCoreApplication.translate("mainWindow", u"Inter-panel crop", None))
#if QT_CONFIG(tooltip)
        self.fileFusionBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p>Combines all selected files into a single file. (Helpful for combining chapters into volumes.)</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.fileFusionBox.setText(QCoreApplication.translate("mainWindow", u"File Fusion", None))
#if QT_CONFIG(tooltip)
        self.authorEdit.setToolTip(QCoreApplication.translate("mainWindow", u"Default Author is KCC", None))
#endif // QT_CONFIG(tooltip)
        self.authorEdit.setPlaceholderText(QCoreApplication.translate("mainWindow", u"Default Author", None))
#if QT_CONFIG(tooltip)
        self.titleEdit.setToolTip(QCoreApplication.translate("mainWindow", u"Default Title is based on filename, directory name or metadata", None))
#endif // QT_CONFIG(tooltip)
        self.titleEdit.setPlaceholderText(QCoreApplication.translate("mainWindow", u"Default Title", None))
#if QT_CONFIG(tooltip)
        self.rotateFirstBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p>When the spread splitter option is partially checked,</p><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - Rotate Last<br/></span>Put the rotated 2 page spread after the split spreads.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - Rotate First<br/></span>Put the rotated 2 page spread before the split spreads.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.rotateFirstBox.setText(QCoreApplication.translate("mainWindow", u"Rotate First", None))
#if QT_CONFIG(tooltip)
        self.eraseRainbowBox.setToolTip(QCoreApplication.translate("mainWindow", u"Erase rainbow effect on color eink screen by attenuating interfering frequencies", None))
#endif // QT_CONFIG(tooltip)
        self.eraseRainbowBox.setText(QCoreApplication.translate("mainWindow", u"Rainbow eraser", None))
#if QT_CONFIG(tooltip)
        self.chunkSizeCheckBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p><span style=\" font-weight:700; text-decoration: underline;\">Unchecked<br/></span>Maximal output file size is 100 MB for Webtoon, 400 MB for others before split occurs.</p><p><span style=\" font-weight:700; text-decoration: underline;\">Checked</span><br/>Output file size specified in &quot;Chunk size MB&quot; before split occurs.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.chunkSizeCheckBox.setText(QCoreApplication.translate("mainWindow", u"Chunk size", None))
#if QT_CONFIG(tooltip)
        self.rotateBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - Split<br/></span>Double page spreads will be cut into two separate pages.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Indeterminate - Split and rotate<br/></span>Double page spreads will be displayed twice. First split and then rotated. </p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - Rotate<br/></span>Double page spreads will be rotated.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.rotateBox.setText(QCoreApplication.translate("mainWindow", u"Spread splitter", None))
#if QT_CONFIG(tooltip)
        self.outputSplit.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - Automatic mode<br/></span>The output will be split automatically.</p><p style='white-space:pre'><span style=\" font-weight:600; text-decoration: underline;\">Checked - Volume mode<br/></span>Every subdirectory will be considered as a separate volume.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.outputSplit.setText(QCoreApplication.translate("mainWindow", u"Output split", None))
#if QT_CONFIG(tooltip)
        self.metadataTitleBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - Don't use metadata Title<br/></span>Write default title.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Indeterminate - Add metadata Title to the default schema<br/></span>Write default title with Title from ComicInfo.xml or other embedded metadata.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - Use metadata Title only<br/></span>Write Title from ComicInfo.xml or other embedded metadata.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.metadataTitleBox.setText(QCoreApplication.translate("mainWindow", u"Metadata Title", None))
#if QT_CONFIG(tooltip)
        self.qualityBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - 4 panels<br/></span>Zoom each corner separately.</p><p style='white-space:pre'><span style=\" font-weight:600; text-decoration: underline;\">Indeterminate - 2 panels<br/></span>Zoom only the top and bottom of the page.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - 4 high-quality panels<br/></span>Zoom each corner separately. Try to increase the quality of magnification. Check wiki for more details.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.qualityBox.setText(QCoreApplication.translate("mainWindow", u"Panel View 4/2/HQ", None))
#if QT_CONFIG(tooltip)
        self.spreadShiftBox.setToolTip(QCoreApplication.translate("mainWindow", u"Shift first page to opposite side in landscape for two page spread alignment", None))
#endif // QT_CONFIG(tooltip)
        self.spreadShiftBox.setText(QCoreApplication.translate("mainWindow", u"Spread shift", None))
#if QT_CONFIG(tooltip)
        self.disableProcessingBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Do not process any image, ignore profile and processing options.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.disableProcessingBox.setText(QCoreApplication.translate("mainWindow", u"Disable processing", None))
#if QT_CONFIG(tooltip)
        self.webtoonBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Enable special parsing mode for Korean Webtoons.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.webtoonBox.setText(QCoreApplication.translate("mainWindow", u"Webtoon mode", None))
#if QT_CONFIG(tooltip)
        self.colorBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p style='white-space:pre'>Disable conversion to grayscale.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.colorBox.setText(QCoreApplication.translate("mainWindow", u"Color mode", None))
#if QT_CONFIG(tooltip)
        self.croppingBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - Disabled</span></p><p>Disabled</p><p><span style=\" font-weight:600; text-decoration: underline;\">Indeterminate - Margins<br/></span>Margins</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - Margins + page numbers<br/></span>Margins +page numbers</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.croppingBox.setText(QCoreApplication.translate("mainWindow", u"Cropping mode", None))
#if QT_CONFIG(tooltip)
        self.maximizeStrips.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - 1x4<br/></span>Keep format 1x4 panels strips.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - 2x2<br/></span>Turn 1x4 strips to 2x2 to maximize screen usage.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.maximizeStrips.setText(QCoreApplication.translate("mainWindow", u"1x4 to 2x2 strips", None))
#if QT_CONFIG(tooltip)
        self.noRotateBox.setToolTip(QCoreApplication.translate("mainWindow", u"Do not rotate double page spreads in spread splitter option.", None))
#endif // QT_CONFIG(tooltip)
        self.noRotateBox.setText(QCoreApplication.translate("mainWindow", u"No rotate", None))
#if QT_CONFIG(tooltip)
        self.deleteBox.setToolTip(QCoreApplication.translate("mainWindow", u"Delete input file(s) or directory. It's not recoverable!", None))
#endif // QT_CONFIG(tooltip)
        self.deleteBox.setText(QCoreApplication.translate("mainWindow", u"Delete input", None))
#if QT_CONFIG(tooltip)
        self.upscaleBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - Nothing<br/></span>Images smaller than device resolution will not be resized.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Indeterminate - Stretching<br/></span>Images smaller than device resolution will be resized. Aspect ratio will be not preserved.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - Upscaling<br/></span>Images smaller than device resolution will be resized. Aspect ratio will be preserved.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.upscaleBox.setText(QCoreApplication.translate("mainWindow", u"Stretch/Upscale", None))
#if QT_CONFIG(tooltip)
        self.mozJpegBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - JPEG<br/></span>Use JPEG files</p><p><span style=\" font-weight:600; text-decoration: underline;\">Indeterminate - force PNG<br/></span>Create PNG files instead JPEG</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - mozJpeg<br/></span>10-20% smaller JPEG file, with the same image quality, but processing time multiplied by 2</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.mozJpegBox.setText(QCoreApplication.translate("mainWindow", u"JPEG/PNG/mozJpeg", None))
#if QT_CONFIG(tooltip)
        self.autoLevelBox.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p>Set the most common dark pixel value to be the black point for leveling on a page by page basis.</p><p>Skipped for any images that were originally color.</p><p>Use only if default autocontrast still results in very gray faded blacks. </p><p>Reccomended to use with Custom Gamma = 1.0 (Disabled).</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.autoLevelBox.setText(QCoreApplication.translate("mainWindow", u"Aggressive Black Point", None))
        self.gammaLabel.setText(QCoreApplication.translate("mainWindow", u"Gamma: Auto", None))
#if QT_CONFIG(tooltip)
        self.chunkSizeWidget.setToolTip(QCoreApplication.translate("mainWindow", u"<html><head/><body><p>Warning: chunk size greater than default may cause<br/>performance/battery issues, especially on older devices.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.chunkSizeLabel.setText(QCoreApplication.translate("mainWindow", u"Chunk size MB:", None))
        self.chunkSizeWarnLabel.setText(QCoreApplication.translate("mainWindow", u"Greater than default may cause performance issues on older ereaders.", None))
    # retranslateUi

