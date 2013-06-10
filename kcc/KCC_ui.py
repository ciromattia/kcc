# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'KCC.ui'
#
# Created: Mon Jun 10 17:51:15 2013
#      by: PyQt4 UI code generator 4.10.1
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
        KCC.resize(420, 345)
        KCC.setMinimumSize(QtCore.QSize(420, 345))
        KCC.setMaximumSize(QtCore.QSize(420, 345))
        font = QtGui.QFont()
        font.setPointSize(9)
        KCC.setFont(font)
        KCC.setFocusPolicy(QtCore.Qt.NoFocus)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/Icon/icons/comic2ebook.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        KCC.setWindowIcon(icon)
        KCC.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.Form = QtGui.QWidget(KCC)
        self.Form.setObjectName(_fromUtf8("Form"))
        self.OptionsAdvanced = QtGui.QFrame(self.Form)
        self.OptionsAdvanced.setEnabled(True)
        self.OptionsAdvanced.setGeometry(QtCore.QRect(10, 254, 421, 61))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.OptionsAdvanced.setFont(font)
        self.OptionsAdvanced.setObjectName(_fromUtf8("OptionsAdvanced"))
        self.gridLayout = QtGui.QGridLayout(self.OptionsAdvanced)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.ProcessingBox = QtGui.QCheckBox(self.OptionsAdvanced)
        self.ProcessingBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ProcessingBox.setObjectName(_fromUtf8("ProcessingBox"))
        self.gridLayout.addWidget(self.ProcessingBox, 1, 0, 1, 1)
        self.UpscaleBox = QtGui.QCheckBox(self.OptionsAdvanced)
        self.UpscaleBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.UpscaleBox.setObjectName(_fromUtf8("UpscaleBox"))
        self.gridLayout.addWidget(self.UpscaleBox, 1, 1, 1, 1)
        self.StretchBox = QtGui.QCheckBox(self.OptionsAdvanced)
        self.StretchBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.StretchBox.setObjectName(_fromUtf8("StretchBox"))
        self.gridLayout.addWidget(self.StretchBox, 3, 1, 1, 1)
        self.NoDitheringBox = QtGui.QCheckBox(self.OptionsAdvanced)
        self.NoDitheringBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.NoDitheringBox.setObjectName(_fromUtf8("NoDitheringBox"))
        self.gridLayout.addWidget(self.NoDitheringBox, 3, 2, 1, 1)
        self.BorderBox = QtGui.QCheckBox(self.OptionsAdvanced)
        self.BorderBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.BorderBox.setObjectName(_fromUtf8("BorderBox"))
        self.gridLayout.addWidget(self.BorderBox, 3, 0, 1, 1)
        self.NoRotateBox = QtGui.QCheckBox(self.OptionsAdvanced)
        self.NoRotateBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.NoRotateBox.setObjectName(_fromUtf8("NoRotateBox"))
        self.gridLayout.addWidget(self.NoRotateBox, 1, 2, 1, 1)
        self.DeviceBox = QtGui.QComboBox(self.Form)
        self.DeviceBox.setGeometry(QtCore.QRect(10, 200, 141, 31))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.DeviceBox.setFont(font)
        self.DeviceBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.DeviceBox.setObjectName(_fromUtf8("DeviceBox"))
        self.FormatBox = QtGui.QComboBox(self.Form)
        self.FormatBox.setGeometry(QtCore.QRect(260, 200, 151, 31))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.FormatBox.setFont(font)
        self.FormatBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.FormatBox.setObjectName(_fromUtf8("FormatBox"))
        self.ConvertButton = QtGui.QPushButton(self.Form)
        self.ConvertButton.setGeometry(QtCore.QRect(160, 200, 91, 32))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.ConvertButton.setFont(font)
        self.ConvertButton.setFocusPolicy(QtCore.Qt.NoFocus)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/Other/icons/convert.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ConvertButton.setIcon(icon1)
        self.ConvertButton.setObjectName(_fromUtf8("ConvertButton"))
        self.DirectoryButton = QtGui.QPushButton(self.Form)
        self.DirectoryButton.setGeometry(QtCore.QRect(10, 160, 141, 32))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.DirectoryButton.setFont(font)
        self.DirectoryButton.setFocusPolicy(QtCore.Qt.NoFocus)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/Other/icons/plus.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.DirectoryButton.setIcon(icon2)
        self.DirectoryButton.setObjectName(_fromUtf8("DirectoryButton"))
        self.FileButton = QtGui.QPushButton(self.Form)
        self.FileButton.setGeometry(QtCore.QRect(260, 160, 151, 32))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.FileButton.setFont(font)
        self.FileButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.FileButton.setIcon(icon2)
        self.FileButton.setObjectName(_fromUtf8("FileButton"))
        self.ClearButton = QtGui.QPushButton(self.Form)
        self.ClearButton.setGeometry(QtCore.QRect(160, 160, 91, 32))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.ClearButton.setFont(font)
        self.ClearButton.setFocusPolicy(QtCore.Qt.NoFocus)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8(":/Other/icons/minus.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ClearButton.setIcon(icon3)
        self.ClearButton.setObjectName(_fromUtf8("ClearButton"))
        self.OptionsBasic = QtGui.QFrame(self.Form)
        self.OptionsBasic.setGeometry(QtCore.QRect(10, 230, 421, 41))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.OptionsBasic.setFont(font)
        self.OptionsBasic.setObjectName(_fromUtf8("OptionsBasic"))
        self.MangaBox = QtGui.QCheckBox(self.OptionsBasic)
        self.MangaBox.setGeometry(QtCore.QRect(9, 10, 130, 18))
        self.MangaBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.MangaBox.setChecked(True)
        self.MangaBox.setObjectName(_fromUtf8("MangaBox"))
        self.HQPVBox = QtGui.QCheckBox(self.OptionsBasic)
        self.HQPVBox.setGeometry(QtCore.QRect(282, 10, 104, 18))
        self.HQPVBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.HQPVBox.setChecked(True)
        self.HQPVBox.setObjectName(_fromUtf8("HQPVBox"))
        self.RotateBox = QtGui.QCheckBox(self.OptionsBasic)
        self.RotateBox.setGeometry(QtCore.QRect(145, 10, 111, 18))
        self.RotateBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.RotateBox.setObjectName(_fromUtf8("RotateBox"))
        self.JobList = QtGui.QListWidget(self.Form)
        self.JobList.setGeometry(QtCore.QRect(10, 50, 401, 101))
        self.JobList.setFocusPolicy(QtCore.Qt.NoFocus)
        self.JobList.setProperty("showDropIndicator", False)
        self.JobList.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.JobList.setObjectName(_fromUtf8("JobList"))
        self.BasicModeButton = QtGui.QPushButton(self.Form)
        self.BasicModeButton.setGeometry(QtCore.QRect(10, 10, 141, 32))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.BasicModeButton.setFont(font)
        self.BasicModeButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.BasicModeButton.setObjectName(_fromUtf8("BasicModeButton"))
        self.AdvModeButton = QtGui.QPushButton(self.Form)
        self.AdvModeButton.setGeometry(QtCore.QRect(160, 10, 91, 32))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.AdvModeButton.setFont(font)
        self.AdvModeButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.AdvModeButton.setObjectName(_fromUtf8("AdvModeButton"))
        self.ExpertModeButton = QtGui.QPushButton(self.Form)
        self.ExpertModeButton.setEnabled(False)
        self.ExpertModeButton.setGeometry(QtCore.QRect(260, 10, 151, 32))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.ExpertModeButton.setFont(font)
        self.ExpertModeButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ExpertModeButton.setObjectName(_fromUtf8("ExpertModeButton"))
        self.OptionsAdvancedGamma = QtGui.QFrame(self.Form)
        self.OptionsAdvancedGamma.setEnabled(True)
        self.OptionsAdvancedGamma.setGeometry(QtCore.QRect(10, 305, 401, 41))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.OptionsAdvancedGamma.setFont(font)
        self.OptionsAdvancedGamma.setObjectName(_fromUtf8("OptionsAdvancedGamma"))
        self.GammaLabel = QtGui.QLabel(self.OptionsAdvancedGamma)
        self.GammaLabel.setGeometry(QtCore.QRect(0, 0, 161, 41))
        self.GammaLabel.setObjectName(_fromUtf8("GammaLabel"))
        self.GammaSlider = QtGui.QSlider(self.OptionsAdvancedGamma)
        self.GammaSlider.setGeometry(QtCore.QRect(140, 10, 261, 22))
        self.GammaSlider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.GammaSlider.setMaximum(500)
        self.GammaSlider.setSingleStep(5)
        self.GammaSlider.setOrientation(QtCore.Qt.Horizontal)
        self.GammaSlider.setObjectName(_fromUtf8("GammaSlider"))
        KCC.setCentralWidget(self.Form)
        self.ActionBasic = QtGui.QAction(KCC)
        self.ActionBasic.setCheckable(True)
        self.ActionBasic.setChecked(False)
        font = QtGui.QFont()
        font.setPointSize(9)
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
        self.UpscaleBox.setToolTip(_translate("KCC", "<html><head/><body><p>Enable image upscaling.</p><p>Aspect ratio will be preserved.</p></body></html>", None))
        self.UpscaleBox.setText(_translate("KCC", "Upscale images", None))
        self.StretchBox.setToolTip(_translate("KCC", "<html><head/><body><p>Enable image stretching.</p><p>Aspect ratio will be not preserved.</p></body></html>", None))
        self.StretchBox.setText(_translate("KCC", "Stretch images", None))
        self.NoDitheringBox.setToolTip(_translate("KCC", "<html><head/><body><p>Create PNG files instead JPEG.</p><p><span style=\" font-weight:600;\">Only for non-Kindle devices!</span></p></body></html>", None))
        self.NoDitheringBox.setText(_translate("KCC", "PNG output", None))
        self.BorderBox.setToolTip(_translate("KCC", "Fill space around images with black color.", None))
        self.BorderBox.setText(_translate("KCC", "Black borders", None))
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
        self.HQPVBox.setToolTip(_translate("KCC", "<html><head/><body><p>Enable high quality zoom.</p><p>Enabling it will <span style=\" font-weight:600;\">highly</span> increase size of output file and <span style=\" font-weight:600;\">slightly</span> reduce sharpness of not zoomed images.</p></body></html>", None))
        self.HQPVBox.setText(_translate("KCC", "HQ Panel View", None))
        self.RotateBox.setToolTip(_translate("KCC", "<html><head/><body><p>Disable page spliting.</p><p>They will be rotated instead.</p></body></html>", None))
        self.RotateBox.setText(_translate("KCC", "Horizontal mode", None))
        self.BasicModeButton.setText(_translate("KCC", "Basic", None))
        self.AdvModeButton.setText(_translate("KCC", "Advanced", None))
        self.ExpertModeButton.setText(_translate("KCC", "Expert", None))
        self.GammaLabel.setToolTip(_translate("KCC", "When converting color images setting this option to 1.0 MIGHT improve readability.", None))
        self.GammaLabel.setText(_translate("KCC", "Gamma correction: Auto", None))
        self.GammaSlider.setToolTip(_translate("KCC", "<html><head/><body><p>When converting color images setting this option to 1.0 <span style=\" font-weight:600;\">might</span> improve readability.</p></body></html>", None))
        self.ActionBasic.setText(_translate("KCC", "Basic", None))
        self.ActionAdvanced.setText(_translate("KCC", "Advanced", None))

import KCC_rc
