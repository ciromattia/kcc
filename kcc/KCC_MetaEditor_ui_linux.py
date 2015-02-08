# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui/MetaEditor.ui'
#
# Created: Sun Feb  8 03:24:23 2015
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MetaEditorDialog(object):
    def setupUi(self, MetaEditorDialog):
        MetaEditorDialog.setObjectName("MetaEditorDialog")
        MetaEditorDialog.resize(400, 320)
        MetaEditorDialog.setMinimumSize(QtCore.QSize(400, 320))
        MetaEditorDialog.setMaximumSize(QtCore.QSize(400, 320))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icon/icons/comic2ebook.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MetaEditorDialog.setWindowIcon(icon)
        self.horizontalLayoutWidget = QtWidgets.QWidget(MetaEditorDialog)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(10, 280, 381, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.StatusLabel = QtWidgets.QLabel(self.horizontalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.StatusLabel.sizePolicy().hasHeightForWidth())
        self.StatusLabel.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.StatusLabel.setFont(font)
        self.StatusLabel.setStyleSheet("color: rgb(255, 0, 0);")
        self.StatusLabel.setObjectName("StatusLabel")
        self.horizontalLayout.addWidget(self.StatusLabel)
        self.OKButton = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.OKButton.sizePolicy().hasHeightForWidth())
        self.OKButton.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.OKButton.setFont(font)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Other/icons/convert.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.OKButton.setIcon(icon1)
        self.OKButton.setObjectName("OKButton")
        self.horizontalLayout.addWidget(self.OKButton)
        self.CancelButton = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.CancelButton.sizePolicy().hasHeightForWidth())
        self.CancelButton.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.CancelButton.setFont(font)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/Other/icons/clear.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.CancelButton.setIcon(icon2)
        self.CancelButton.setObjectName("CancelButton")
        self.horizontalLayout.addWidget(self.CancelButton)
        self.EditorFrame = QtWidgets.QFrame(MetaEditorDialog)
        self.EditorFrame.setGeometry(QtCore.QRect(10, 10, 381, 271))
        self.EditorFrame.setObjectName("EditorFrame")
        self.formLayoutWidget = QtWidgets.QWidget(self.EditorFrame)
        self.formLayoutWidget.setGeometry(QtCore.QRect(0, 0, 381, 266))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.formLayoutWidget)
        self.label.setObjectName("label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label)
        self.SeriesLine = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.SeriesLine.setObjectName("SeriesLine")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.SeriesLine)
        self.label_2 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.VolumeLine = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.VolumeLine.setObjectName("VolumeLine")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.VolumeLine)
        self.label_3 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.NumberLine = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.NumberLine.setObjectName("NumberLine")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.NumberLine)
        self.label_4 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.WriterLine = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.WriterLine.setObjectName("WriterLine")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.WriterLine)
        self.label_5 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.PencillerLine = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.PencillerLine.setObjectName("PencillerLine")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.PencillerLine)
        self.label_6 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_6.setObjectName("label_6")
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.LabelRole, self.label_6)
        self.InkerLine = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.InkerLine.setObjectName("InkerLine")
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.FieldRole, self.InkerLine)
        self.label_7 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.LabelRole, self.label_7)
        self.ColoristLine = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.ColoristLine.setObjectName("ColoristLine")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.FieldRole, self.ColoristLine)
        self.label_8 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_8.setTextFormat(QtCore.Qt.RichText)
        self.label_8.setOpenExternalLinks(True)
        self.label_8.setObjectName("label_8")
        self.formLayout.setWidget(8, QtWidgets.QFormLayout.LabelRole, self.label_8)
        self.MUidLine = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.MUidLine.setObjectName("MUidLine")
        self.formLayout.setWidget(8, QtWidgets.QFormLayout.FieldRole, self.MUidLine)

        self.retranslateUi(MetaEditorDialog)
        QtCore.QMetaObject.connectSlotsByName(MetaEditorDialog)

    def retranslateUi(self, MetaEditorDialog):
        _translate = QtCore.QCoreApplication.translate
        MetaEditorDialog.setWindowTitle(_translate("MetaEditorDialog", "Metadata editor"))
        self.OKButton.setText(_translate("MetaEditorDialog", "Save"))
        self.CancelButton.setText(_translate("MetaEditorDialog", "Cancel"))
        self.label.setText(_translate("MetaEditorDialog", "Series:"))
        self.label_2.setText(_translate("MetaEditorDialog", "Volume:"))
        self.label_3.setText(_translate("MetaEditorDialog", "Number:"))
        self.label_4.setText(_translate("MetaEditorDialog", "Writer:"))
        self.label_5.setText(_translate("MetaEditorDialog", "Penciller:"))
        self.label_6.setText(_translate("MetaEditorDialog", "Inker:"))
        self.label_7.setText(_translate("MetaEditorDialog", "Colorist:"))
        self.label_8.setText(_translate("MetaEditorDialog", "<html><head/><body><p><a href=\"https://github.com/ciromattia/kcc/wiki/Manga-Cover-Database-support\"><span style=\" text-decoration: underline; color:#0000ff;\">MUid:</span></a></p></body></html>"))

from . import KCC_rc
