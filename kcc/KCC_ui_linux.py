# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'KCC-Linux.ui'
#
# Created: Tue Jan 14 15:50:14 2014
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_KCC(object):
    def setupUi(self, KCC):
        KCC.setObjectName(_fromUtf8("KCC"))
        KCC.resize(420, 397)
        KCC.setMinimumSize(QtCore.QSize(420, 397))
        KCC.setMaximumSize(QtCore.QSize(420, 397))
        font = QtGui.QFont()
        font.setPointSize(9)
        KCC.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/Icon/icons/comic2ebook.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        KCC.setWindowIcon(icon)
        KCC.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.Form = QtGui.QWidget(KCC)
        self.Form.setObjectName(_fromUtf8("Form"))
        self.OptionsAdvanced = QtGui.QFrame(self.Form)
        self.OptionsAdvanced.setEnabled(True)
        self.OptionsAdvanced.setGeometry(QtCore.QRect(1, 254, 421, 61))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(9)
        self.OptionsAdvanced.setFont(font)
        self.OptionsAdvanced.setObjectName(_fromUtf8("OptionsAdvanced"))
        self.gridLayout = QtGui.QGridLayout(self.OptionsAdvanced)
        self.gridLayout.setContentsMargins(9, -1, -1, -1)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.ProcessingBox = QtGui.QCheckBox(self.OptionsAdvanced)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.ProcessingBox.setFont(font)
        self.ProcessingBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ProcessingBox.setObjectName(_fromUtf8("ProcessingBox"))
        self.gridLayout.addWidget(self.ProcessingBox, 1, 0, 1, 1)
        self.UpscaleBox = QtGui.QCheckBox(self.OptionsAdvanced)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.UpscaleBox.setFont(font)
        self.UpscaleBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.UpscaleBox.setTristate(True)
        self.UpscaleBox.setObjectName(_fromUtf8("UpscaleBox"))
        self.gridLayout.addWidget(self.UpscaleBox, 1, 1, 1, 1)
        self.WebtoonBox = QtGui.QCheckBox(self.OptionsAdvanced)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.WebtoonBox.setFont(font)
        self.WebtoonBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.WebtoonBox.setObjectName(_fromUtf8("WebtoonBox"))
        self.gridLayout.addWidget(self.WebtoonBox, 3, 1, 1, 1)
        self.NoDitheringBox = QtGui.QCheckBox(self.OptionsAdvanced)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.NoDitheringBox.setFont(font)
        self.NoDitheringBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.NoDitheringBox.setObjectName(_fromUtf8("NoDitheringBox"))
        self.gridLayout.addWidget(self.NoDitheringBox, 3, 2, 1, 1)
        self.BorderBox = QtGui.QCheckBox(self.OptionsAdvanced)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.BorderBox.setFont(font)
        self.BorderBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.BorderBox.setTristate(True)
        self.BorderBox.setObjectName(_fromUtf8("BorderBox"))
        self.gridLayout.addWidget(self.BorderBox, 3, 0, 1, 1)
        self.NoRotateBox = QtGui.QCheckBox(self.OptionsAdvanced)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.NoRotateBox.setFont(font)
        self.NoRotateBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.NoRotateBox.setObjectName(_fromUtf8("NoRotateBox"))
        self.gridLayout.addWidget(self.NoRotateBox, 1, 2, 1, 1)
        self.DeviceBox = QtGui.QComboBox(self.Form)
        self.DeviceBox.setGeometry(QtCore.QRect(10, 200, 141, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(8)
        self.DeviceBox.setFont(font)
        self.DeviceBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.DeviceBox.setObjectName(_fromUtf8("DeviceBox"))
        self.FormatBox = QtGui.QComboBox(self.Form)
        self.FormatBox.setGeometry(QtCore.QRect(260, 200, 151, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(8)
        self.FormatBox.setFont(font)
        self.FormatBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.FormatBox.setObjectName(_fromUtf8("FormatBox"))
        self.ConvertButton = QtGui.QPushButton(self.Form)
        self.ConvertButton.setGeometry(QtCore.QRect(160, 200, 91, 32))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.ConvertButton.setFont(font)
        self.ConvertButton.setFocusPolicy(QtCore.Qt.NoFocus)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/Other/icons/convert.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ConvertButton.setIcon(icon1)
        self.ConvertButton.setObjectName(_fromUtf8("ConvertButton"))
        self.DirectoryButton = QtGui.QPushButton(self.Form)
        self.DirectoryButton.setGeometry(QtCore.QRect(10, 160, 141, 32))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(8)
        self.DirectoryButton.setFont(font)
        self.DirectoryButton.setFocusPolicy(QtCore.Qt.NoFocus)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/Other/icons/folder_new.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.DirectoryButton.setIcon(icon2)
        self.DirectoryButton.setObjectName(_fromUtf8("DirectoryButton"))
        self.FileButton = QtGui.QPushButton(self.Form)
        self.FileButton.setGeometry(QtCore.QRect(260, 160, 151, 32))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(8)
        self.FileButton.setFont(font)
        self.FileButton.setFocusPolicy(QtCore.Qt.NoFocus)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8(":/Other/icons/document_new.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.FileButton.setIcon(icon3)
        self.FileButton.setObjectName(_fromUtf8("FileButton"))
        self.ClearButton = QtGui.QPushButton(self.Form)
        self.ClearButton.setGeometry(QtCore.QRect(160, 160, 91, 32))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(8)
        self.ClearButton.setFont(font)
        self.ClearButton.setFocusPolicy(QtCore.Qt.NoFocus)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(_fromUtf8(":/Other/icons/clear.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ClearButton.setIcon(icon4)
        self.ClearButton.setObjectName(_fromUtf8("ClearButton"))
        self.OptionsBasic = QtGui.QFrame(self.Form)
        self.OptionsBasic.setGeometry(QtCore.QRect(1, 230, 421, 41))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(9)
        self.OptionsBasic.setFont(font)
        self.OptionsBasic.setObjectName(_fromUtf8("OptionsBasic"))
        self.MangaBox = QtGui.QCheckBox(self.OptionsBasic)
        self.MangaBox.setGeometry(QtCore.QRect(9, 10, 130, 18))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.MangaBox.setFont(font)
        self.MangaBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.MangaBox.setObjectName(_fromUtf8("MangaBox"))
        self.QualityBox = QtGui.QCheckBox(self.OptionsBasic)
        self.QualityBox.setGeometry(QtCore.QRect(282, 10, 135, 18))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.QualityBox.setFont(font)
        self.QualityBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.QualityBox.setTristate(True)
        self.QualityBox.setObjectName(_fromUtf8("QualityBox"))
        self.RotateBox = QtGui.QCheckBox(self.OptionsBasic)
        self.RotateBox.setGeometry(QtCore.QRect(145, 10, 130, 18))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.RotateBox.setFont(font)
        self.RotateBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.RotateBox.setObjectName(_fromUtf8("RotateBox"))
        self.JobList = QtGui.QListWidget(self.Form)
        self.JobList.setGeometry(QtCore.QRect(10, 50, 401, 101))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(8)
        font.setItalic(False)
        self.JobList.setFont(font)
        self.JobList.setFocusPolicy(QtCore.Qt.NoFocus)
        self.JobList.setStyleSheet(_fromUtf8("QListWidget#JobList {background:#ffffff;background-image:url(:/Other/icons/list_background.png);background-position:center center;background-repeat:no-repeat;}QScrollBar:vertical{border:1px solid #999;background:#FFF;width:5px;margin:0}QScrollBar::handle:vertical{background:DarkGray;min-height:0}QScrollBar::add-line:vertical{height:0;background:DarkGray;subcontrol-position:bottom;subcontrol-origin:margin}QScrollBar::sub-line:vertical{height:0;background:DarkGray;subcontrol-position:top;subcontrol-origin:margin}QScrollBar:horizontal{border:1px solid #999;background:#FFF;height:5px;margin:0}QScrollBar::handle:horizontal{background:DarkGray;min-width:0}QScrollBar::add-line:horizontal{width:0;background:DarkGray;subcontrol-position:bottom;subcontrol-origin:margin}QScrollBar::sub-line:horizontal{width:0;background:DarkGray;subcontrol-position:top;subcontrol-origin:margin}"))
        self.JobList.setProperty("showDropIndicator", False)
        self.JobList.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.JobList.setIconSize(QtCore.QSize(18, 18))
        self.JobList.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.JobList.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.JobList.setObjectName(_fromUtf8("JobList"))
        self.BasicModeButton = QtGui.QPushButton(self.Form)
        self.BasicModeButton.setGeometry(QtCore.QRect(10, 10, 195, 32))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(9)
        self.BasicModeButton.setFont(font)
        self.BasicModeButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.BasicModeButton.setObjectName(_fromUtf8("BasicModeButton"))
        self.AdvModeButton = QtGui.QPushButton(self.Form)
        self.AdvModeButton.setGeometry(QtCore.QRect(217, 10, 195, 32))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(9)
        self.AdvModeButton.setFont(font)
        self.AdvModeButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.AdvModeButton.setObjectName(_fromUtf8("AdvModeButton"))
        self.OptionsAdvancedGamma = QtGui.QFrame(self.Form)
        self.OptionsAdvancedGamma.setEnabled(True)
        self.OptionsAdvancedGamma.setGeometry(QtCore.QRect(10, 305, 401, 41))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(9)
        self.OptionsAdvancedGamma.setFont(font)
        self.OptionsAdvancedGamma.setObjectName(_fromUtf8("OptionsAdvancedGamma"))
        self.GammaLabel = QtGui.QLabel(self.OptionsAdvancedGamma)
        self.GammaLabel.setGeometry(QtCore.QRect(15, 0, 100, 40))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.GammaLabel.setFont(font)
        self.GammaLabel.setObjectName(_fromUtf8("GammaLabel"))
        self.GammaSlider = QtGui.QSlider(self.OptionsAdvancedGamma)
        self.GammaSlider.setGeometry(QtCore.QRect(110, 10, 275, 22))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.GammaSlider.setFont(font)
        self.GammaSlider.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.GammaSlider.setMaximum(500)
        self.GammaSlider.setSingleStep(5)
        self.GammaSlider.setOrientation(QtCore.Qt.Horizontal)
        self.GammaSlider.setObjectName(_fromUtf8("GammaSlider"))
        self.ProgressBar = QtGui.QProgressBar(self.Form)
        self.ProgressBar.setGeometry(QtCore.QRect(10, 10, 401, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.ProgressBar.setFont(font)
        self.ProgressBar.setProperty("value", 0)
        self.ProgressBar.setAlignment(QtCore.Qt.AlignJustify|QtCore.Qt.AlignVCenter)
        self.ProgressBar.setFormat(_fromUtf8(""))
        self.ProgressBar.setObjectName(_fromUtf8("ProgressBar"))
        self.OptionsExpert = QtGui.QFrame(self.Form)
        self.OptionsExpert.setGeometry(QtCore.QRect(1, 337, 421, 41))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(9)
        self.OptionsExpert.setFont(font)
        self.OptionsExpert.setObjectName(_fromUtf8("OptionsExpert"))
        self.ColorBox = QtGui.QCheckBox(self.OptionsExpert)
        self.ColorBox.setGeometry(QtCore.QRect(9, 11, 130, 18))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.ColorBox.setFont(font)
        self.ColorBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ColorBox.setObjectName(_fromUtf8("ColorBox"))
        self.OptionsExpertInternal = QtGui.QFrame(self.OptionsExpert)
        self.OptionsExpertInternal.setGeometry(QtCore.QRect(105, 0, 295, 40))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.OptionsExpertInternal.setFont(font)
        self.OptionsExpertInternal.setObjectName(_fromUtf8("OptionsExpertInternal"))
        self.gridLayout_2 = QtGui.QGridLayout(self.OptionsExpertInternal)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.wLabel = QtGui.QLabel(self.OptionsExpertInternal)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.wLabel.setFont(font)
        self.wLabel.setObjectName(_fromUtf8("wLabel"))
        self.gridLayout_2.addWidget(self.wLabel, 0, 0, 1, 1)
        self.customWidth = QtGui.QLineEdit(self.OptionsExpertInternal)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.customWidth.sizePolicy().hasHeightForWidth())
        self.customWidth.setSizePolicy(sizePolicy)
        self.customWidth.setMaximumSize(QtCore.QSize(40, 16777215))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.customWidth.setFont(font)
        self.customWidth.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.customWidth.setAcceptDrops(False)
        self.customWidth.setMaxLength(4)
        self.customWidth.setObjectName(_fromUtf8("customWidth"))
        self.gridLayout_2.addWidget(self.customWidth, 0, 1, 1, 1)
        self.hLabel = QtGui.QLabel(self.OptionsExpertInternal)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.hLabel.setFont(font)
        self.hLabel.setObjectName(_fromUtf8("hLabel"))
        self.gridLayout_2.addWidget(self.hLabel, 0, 2, 1, 1)
        self.customHeight = QtGui.QLineEdit(self.OptionsExpertInternal)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.customHeight.sizePolicy().hasHeightForWidth())
        self.customHeight.setSizePolicy(sizePolicy)
        self.customHeight.setMaximumSize(QtCore.QSize(40, 16777215))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        self.customHeight.setFont(font)
        self.customHeight.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.customHeight.setAcceptDrops(False)
        self.customHeight.setMaxLength(4)
        self.customHeight.setObjectName(_fromUtf8("customHeight"))
        self.gridLayout_2.addWidget(self.customHeight, 0, 3, 1, 1)
        KCC.setCentralWidget(self.Form)
        self.statusBar = QtGui.QStatusBar(KCC)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(8)
        self.statusBar.setFont(font)
        self.statusBar.setSizeGripEnabled(False)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        KCC.setStatusBar(self.statusBar)
        self.ActionBasic = QtGui.QAction(KCC)
        self.ActionBasic.setCheckable(True)
        self.ActionBasic.setChecked(False)
        font = QtGui.QFont()
        self.ActionBasic.setFont(font)
        self.ActionBasic.setObjectName(_fromUtf8("ActionBasic"))
        self.ActionAdvanced = QtGui.QAction(KCC)
        self.ActionAdvanced.setCheckable(True)
        self.ActionAdvanced.setObjectName(_fromUtf8("ActionAdvanced"))

        self.retranslateUi(KCC)
        QtCore.QMetaObject.connectSlotsByName(KCC)
        KCC.setTabOrder(self.DirectoryButton, self.FileButton)
        KCC.setTabOrder(self.FileButton, self.ConvertButton)
        KCC.setTabOrder(self.ConvertButton, self.ClearButton)

    def retranslateUi(self, KCC):
        KCC.setWindowTitle(_translate("KCC", "Kindle Comic Converter", None))
        self.ProcessingBox.setToolTip(_translate("KCC", "Disable image optimizations.", None))
        self.ProcessingBox.setText(_translate("KCC", "No optimisation", None))
        self.UpscaleBox.setToolTip(_translate("KCC", "<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - Nothing<br/></span>Images smaller than device resolution will not be resized.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Indeterminate - Stretching<br/></span>Images smaller than device resolution will be resized. Aspect ratio will be not preserved.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - Upscaling<br/></span>Images smaller than device resolution will be resized. Aspect ratio will be preserved.</p></body></html>", None))
        self.UpscaleBox.setText(_translate("KCC", "Stretch/Upscale", None))
        self.WebtoonBox.setToolTip(_translate("KCC", "<html><head/><body><p>Enable auto-splitting of webtoons like <span style=\" font-style:italic;\">Tower of God</span> or <span style=\" font-style:italic;\">Noblesse</span>.<br/>Pages with a low width, high height and vertical panel flow.</p></body></html>", None))
        self.WebtoonBox.setText(_translate("KCC", "Webtoon mode", None))
        self.NoDitheringBox.setToolTip(_translate("KCC", "<html><head/><body><p>Create PNG files instead JPEG.<br/>Quality increase is not noticeable on most of devices.<br/>Output files <span style=\" font-weight:600;\">might</span> be smaller.<br/><span style=\" font-weight:600;\">MOBI conversion will be much slower.</span></p></body></html>", None))
        self.NoDitheringBox.setText(_translate("KCC", "PNG output", None))
        self.BorderBox.setToolTip(_translate("KCC", "<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Unchecked - Autodetection<br/></span>Color of margins fill will be detected automatically.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Indeterminate - White<br/></span>Margins will be filled with white color.</p><p><span style=\" font-weight:600; text-decoration: underline;\">Checked - Black<br/></span>Margins will be filled with black color.</p></body></html>", None))
        self.BorderBox.setText(_translate("KCC", "W/B margins", None))
        self.NoRotateBox.setToolTip(_translate("KCC", "<html><head/><body><p>Disable splitting and rotation.</p></body></html>", None))
        self.NoRotateBox.setText(_translate("KCC", "No split/rotate", None))
        self.DeviceBox.setToolTip(_translate("KCC", "Target device.", None))
        self.FormatBox.setToolTip(_translate("KCC", "Output format.", None))
        self.ConvertButton.setText(_translate("KCC", "Convert", None))
        self.DirectoryButton.setText(_translate("KCC", "Add directory", None))
        self.FileButton.setText(_translate("KCC", "Add file", None))
        self.ClearButton.setText(_translate("KCC", "Clear list", None))
        self.MangaBox.setToolTip(_translate("KCC", "Enable right-to-left reading.", None))
        self.MangaBox.setText(_translate("KCC", "Manga mode", None))
        self.QualityBox.setToolTip(_translate("KCC", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'MS Shell Dlg 2\'; font-weight:600; text-decoration: underline;\">Unchecked - Normal quality mode<br /></span><span style=\" font-family:\'MS Shell Dlg 2\'; font-style:italic;\">Use it when Panel View support is not needed.</span><span style=\" font-family:\'MS Shell Dlg 2\'; font-weight:600; text-decoration: underline;\"><br /></span><span style=\" font-family:\'MS Shell Dlg 2\';\">- Maximum quality when zoom is not enabled.<br />- Poor quality when zoom is enabled.<br />- Lowest file size.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'MS Shell Dlg 2\'; font-weight:600; text-decoration: underline;\">Indeterminate - High quality mode<br /></span><span style=\" font-family:\'MS Shell Dlg 2\'; font-style:italic;\">Not zoomed image </span><span style=\" font-family:\'MS Shell Dlg 2\'; font-weight:600; font-style:italic;\">might </span><span style=\" font-family:\'MS Shell Dlg 2\'; font-style:italic;\">be a little blurry.<br /></span><span style=\" font-family:\'MS Shell Dlg 2\'; font-style:italic;\">Smaller images might be forcefully upscaled in this mode.</span><span style=\" font-family:\'MS Shell Dlg 2\'; font-weight:600; text-decoration: underline;\"><br /></span><span style=\" font-family:\'MS Shell Dlg 2\';\">- Medium/High quality when zoom is not enabled.<br />- Maximum quality when zoom is enabled.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'MS Shell Dlg 2\'; font-weight:600; text-decoration: underline;\">Checked - Ultra quality mode<br /></span><span style=\" font-family:\'MS Shell Dlg 2\'; font-style:italic;\">Maximum possible quality.</span><span style=\" font-family:\'MS Shell Dlg 2\'; font-weight:600; text-decoration: underline;\"><br /></span><span style=\" font-family:\'MS Shell Dlg 2\';\">- Maximum quality when zoom is not enabled.<br />- Maximum quality when zoom is enabled.<br />- Very high file size.</span></p></body></html>", None))
        self.QualityBox.setText(_translate("KCC", "High/Ultra quality", None))
        self.RotateBox.setToolTip(_translate("KCC", "<html><head/><body><p>Disable splitting of two-page spreads.<br/>They will be rotated instead.</p></body></html>", None))
        self.RotateBox.setText(_translate("KCC", "Horizontal mode", None))
        self.BasicModeButton.setText(_translate("KCC", "Basic", None))
        self.AdvModeButton.setText(_translate("KCC", "Advanced", None))
        self.GammaLabel.setText(_translate("KCC", "Gamma: Auto", None))
        self.ColorBox.setToolTip(_translate("KCC", "<html><head/><body><p>Don\'t convert images to grayscale.</p></body></html>", None))
        self.ColorBox.setText(_translate("KCC", "Color mode", None))
        self.wLabel.setToolTip(_translate("KCC", "Resolution of target device.", None))
        self.wLabel.setText(_translate("KCC", "Custom width: ", None))
        self.customWidth.setToolTip(_translate("KCC", "Resolution of target device.", None))
        self.customWidth.setInputMask(_translate("KCC", "0000; ", None))
        self.hLabel.setToolTip(_translate("KCC", "Resolution of target device.", None))
        self.hLabel.setText(_translate("KCC", "Custom height: ", None))
        self.customHeight.setToolTip(_translate("KCC", "Resolution of target device.", None))
        self.customHeight.setInputMask(_translate("KCC", "0000; ", None))
        self.ActionBasic.setText(_translate("KCC", "Basic", None))
        self.ActionAdvanced.setText(_translate("KCC", "Advanced", None))

from . import KCC_rc
