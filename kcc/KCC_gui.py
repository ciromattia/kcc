#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 Ciro Mattia Gonano <ciromattia@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted, provided that the
# above copyright notice and this permission notice appear in all
# copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
# AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
# DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA
# OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

__version__ = '3.0'
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import os
import sys
import shutil
import traceback
import comic2ebook
import kindlestrip
from image import ProfileData
from subprocess import call, STDOUT, PIPE
from PyQt4 import QtGui, QtCore


# noinspection PyBroadException
class Ui_KCC(object):
    def selectDir(self):
        if self.firstStart:
            self.firstStart = False
            GUI.JobList.clear()
        dname = QtGui.QFileDialog.getExistingDirectory(MainWindow, 'Select directory', '')
        # Lame UTF-8 security measure
        try:
            str(dname)
        except Exception:
            QtGui.QMessageBox.critical(MainWindow, 'KCC Error', "Path cannot contain non-ASCII characters.",
                                       QtGui.QMessageBox.Ok)
            return
        GUI.JobList.addItem(dname)
        self.clearEmptyJobs()

    def selectFile(self):
        if self.firstStart:
            self.firstStart = False
            GUI.JobList.clear()
        if self.UnRAR:
            fname = QtGui.QFileDialog.getOpenFileName(MainWindow, 'Select file', '', '*.cbz *.cbr *.zip *.rar *.pdf')
        else:
            fname = QtGui.QFileDialog.getOpenFileName(MainWindow, 'Select file', '', '*.cbz *.zip *.pdf')
        # Lame UTF-8 security measure
        try:
            str(fname)
        except Exception:
            QtGui.QMessageBox.critical(MainWindow, 'KCC Error', "Path cannot contain non-ASCII characters.",
                                       QtGui.QMessageBox.Ok)
            return
        GUI.JobList.addItem(fname)
        self.clearEmptyJobs()

    def clearJobs(self):
        GUI.JobList.clear()

    def clearEmptyJobs(self):
        for i in range(GUI.JobList.count()):
            if str(GUI.JobList.item(i).text()) == '':
                GUI.JobList.takeItem(i)

    def modeBasic(self):
        MainWindow.setMinimumSize(QtCore.QSize(420, 270))
        MainWindow.setMaximumSize(QtCore.QSize(420, 270))
        MainWindow.resize(420, 270)
        GUI.BasicModeButton.setStyleSheet('font-weight:Bold;')
        GUI.AdvModeButton.setStyleSheet('font-weight:Normal;')
        GUI.ExpertModeButton.setStyleSheet('font-weight:Normal;')
        GUI.FormatBox.setCurrentIndex(0)
        GUI.FormatBox.setEnabled(False)
        GUI.OptionsAdvanced.setEnabled(False)
        GUI.OptionsAdvancedGamma.setEnabled(False)
        GUI.ProcessingBox.hide()
        GUI.UpscaleBox.hide()
        GUI.NoRotateBox.hide()
        GUI.ProcessingBox.setChecked(False)
        GUI.UpscaleBox.setChecked(False)
        GUI.NoRotateBox.setChecked(False)
        GUI.BorderBox.setChecked(False)
        GUI.StretchBox.setChecked(False)
        GUI.NoDitheringBox.setChecked(False)
        GUI.GammaSlider.setValue(0)

    def modeAdvanced(self):
        MainWindow.setMinimumSize(QtCore.QSize(420, 345))
        MainWindow.setMaximumSize(QtCore.QSize(420, 345))
        MainWindow.resize(420, 345)
        GUI.BasicModeButton.setStyleSheet('font-weight:Normal;')
        GUI.AdvModeButton.setStyleSheet('font-weight:Bold;')
        GUI.ExpertModeButton.setStyleSheet('font-weight:Normal;')
        GUI.FormatBox.setEnabled(True)
        GUI.ProcessingBox.show()
        GUI.UpscaleBox.show()
        GUI.NoRotateBox.show()
        GUI.OptionsAdvancedGamma.setEnabled(True)
        GUI.OptionsAdvanced.setEnabled(True)

    def modeExpert(self):
        #TODO
        pass

    def modeConvert(self, enable):
        GUI.BasicModeButton.setEnabled(enable)
        GUI.AdvModeButton.setEnabled(enable)
        GUI.ExpertModeButton.setEnabled(enable)
        GUI.DirectoryButton.setEnabled(enable)
        GUI.ClearButton.setEnabled(enable)
        GUI.FileButton.setEnabled(enable)
        GUI.DeviceBox.setEnabled(enable)
        GUI.ConvertButton.setEnabled(enable)
        GUI.FormatBox.setEnabled(enable)
        GUI.OptionsBasic.setEnabled(enable)
        GUI.OptionsAdvanced.setEnabled(enable)
        GUI.OptionsAdvancedGamma.setEnabled(enable)

    def changeGamma(self, value):
        if value <= 9:
            value = 'Auto'
        else:
            value = float(value)
            value = '%.2f' % (value/100)
            self.GammaValue = value
        GUI.GammaLabel.setText('Gamma correction: ' + str(value))

    def addMessage(self, message, icon=None, replace=False):
        if icon:
            item = QtGui.QListWidgetItem(icon, message)
        else:
            item = QtGui.QListWidgetItem(message)
        if replace:
            GUI.JobList.takeItem(GUI.JobList.count()-1)
        GUI.JobList.addItem(item)
        MainWindow.repaint()

    def convertStart(self):
        if self.firstStart:
            self.firstStart = False
            GUI.JobList.clear()
        if GUI.JobList.count() == 0:
            self.addMessage('No files selected! Please choose files to convert.', self.errorIcon)
            self.firstStart = True
            return
        self.modeConvert(False)
        profile = ProfileData.ProfileLabels[str(GUI.DeviceBox.currentText())]
        argv = ["--profile=" + profile]
        currentJobs = []
        global errors
        if GUI.MangaBox.isChecked():
            argv.append("--manga-style")
        if GUI.RotateBox.isChecked():
            argv.append("--rotate")
        if not GUI.HQPVBox.isChecked():
            argv.append("--nopanelviewhq")
        if GUI.ProcessingBox.isChecked():
            argv.append("--noprocessing")
        if GUI.UpscaleBox.isChecked() and not GUI.StretchBox.isChecked():
            argv.append("--upscale")
        if GUI.NoRotateBox.isChecked():
            argv.append("--nosplitrotate")
        if GUI.BorderBox.isChecked():
            argv.append("--blackborders")
        if GUI.StretchBox.isChecked():
            argv.append("--stretch")
        if GUI.NoDitheringBox.isChecked():
            argv.append("--nodithering")
        if self.GammaValue > 0.09:
            argv.append("--gamma=" + self.GammaValue)
        if str(GUI.FormatBox.currentText()) == 'CBZ':
            argv.append("--cbz-output")
        for i in range(GUI.JobList.count()):
            currentJobs.append(str(GUI.JobList.item(i).text()))
        GUI.JobList.clear()
        for job in currentJobs:
            errors = False
            self.addMessage('Source: ' + job, self.infoIcon)
            if str(GUI.FormatBox.currentText()) == 'CBZ':
                self.addMessage('Creating CBZ file...', self.infoIcon)
            else:
                self.addMessage('Creating EPUB file...', self.infoIcon)
            jobargv = list(argv)
            jobargv.append(job)
            MainWindow.repaint()
            try:
                outputPath = comic2ebook.main(jobargv)
            except Exception as err:
                errors = True
                type_, value_, traceback_ = sys.exc_info()
                QtGui.QMessageBox.critical(MainWindow, 'KCC Error',
                                           "Error on file %s:\n%s\nTraceback:\n%s"
                                           % (jobargv[-1], str(err), traceback.format_tb(traceback_)),
                                           QtGui.QMessageBox.Ok)
                self.addMessage('KCC failed to create EPUB!', self.errorIcon)
                continue
            MainWindow.repaint()
            if not errors:
                if str(GUI.FormatBox.currentText()) == 'CBZ':
                    self.addMessage('Creating CBZ file... Done!', self.infoIcon, True)
                else:
                    self.addMessage('Creating EPUB file... Done!', self.infoIcon, True)
                if str(GUI.FormatBox.currentText()) == 'MOBI':
                    if not os.path.getsize(outputPath) > 314572800:
                        self.addMessage('Creating MOBI file...', self.infoIcon)
                        MainWindow.repaint()
                        retcode = call('kindlegen "' + outputPath + '"', stdout=PIPE, stderr=STDOUT, shell=True)
                        MainWindow.repaint()
                        if retcode == 0:
                            self.addMessage('Creating MOBI file... Done!', self.infoIcon, True)
                            self.addMessage('Removing SRCS header...', self.infoIcon)
                            mobiPath = outputPath.replace('.epub', '.mobi')
                            shutil.move(mobiPath, mobiPath + '_tostrip')
                            MainWindow.repaint()
                            try:
                                kindlestrip.main((mobiPath + '_tostrip', mobiPath))
                            except Exception:
                                errors = True
                                continue
                            MainWindow.repaint()
                            if not errors:
                                os.remove(mobiPath + '_tostrip')
                                self.addMessage('Removing SRCS header... Done!', self.infoIcon, True)
                            else:
                                shutil.move(mobiPath + '_tostrip', mobiPath)
                                self.addMessage('KindleStrip failed to remove SRCS header!', self.warningIcon)
                                self.addMessage('MOBI file will work correctly but it will be highly oversized.',
                                                self.warningIcon)
                        else:
                            os.remove(outputPath)
                            self.addMessage('KindleGen failed to create MOBI!', self.errorIcon)
                            self.addMessage('Try converting smaller batch.', self.errorIcon)
                    else:
                        os.remove(outputPath)
                        self.addMessage('Created EPUB file is too big for KindleGen!', self.errorIcon)
                        self.addMessage('Try converting smaller batch.', self.errorIcon)
        self.firstStart = True
        self.addMessage('All jobs completed.', self.warningIcon)
        self.modeConvert(True)

    def __init__(self, ui, KCC):
        global GUI, MainWindow
        GUI = ui
        MainWindow = KCC
        profiles = sorted(ProfileData.ProfileLabels.iterkeys())
        kindleIcon = QtGui.QIcon()
        kindleIcon.addPixmap(QtGui.QPixmap(":/Devices/icons/Kindle.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.firstStart = True
        self.GammaValue = 0
        self.infoIcon = QtGui.QIcon()
        self.infoIcon.addPixmap(QtGui.QPixmap(":/Status/icons/info.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.warningIcon = QtGui.QIcon()
        self.warningIcon.addPixmap(QtGui.QPixmap(":/Status/icons/warning.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.errorIcon = QtGui.QIcon()
        self.errorIcon.addPixmap(QtGui.QPixmap(":/Status/icons/error.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.addMessage('Welcome!', self.infoIcon)
        self.addMessage('Most of options have additional informations in their tooltips.', self.infoIcon)
        if call('kindlegen', stdout=PIPE, stderr=STDOUT, shell=True) == 0:
            self.KindleGen = True
            formats = ['MOBI', 'EPUB', 'CBZ']
        else:
            self.KindleGen = False
            formats = ['EPUB', 'CBZ']
            self.addMessage('Failed to detect KindleGen! Creating MOBI files is disabled.', self.warningIcon)
        if call('unrar', stdout=PIPE, stderr=STDOUT, shell=True) == 0:
            self.UnRAR = True
        else:
            self.UnRAR = False
            self.addMessage('Failed to detect UnRAR! Processing of CBR/RAR files is disabled.', self.warningIcon)

        GUI.BasicModeButton.clicked.connect(self.modeBasic)
        GUI.AdvModeButton.clicked.connect(self.modeAdvanced)
        GUI.ExpertModeButton.clicked.connect(self.modeExpert)
        GUI.DirectoryButton.clicked.connect(self.selectDir)
        GUI.ClearButton.clicked.connect(self.clearJobs)
        GUI.FileButton.clicked.connect(self.selectFile)
        GUI.ConvertButton.clicked.connect(self.convertStart)
        GUI.GammaSlider.valueChanged.connect(self.changeGamma)

        for profile in profiles:
            GUI.DeviceBox.addItem(kindleIcon, profile)
        GUI.DeviceBox.setCurrentIndex(10)
        for f in formats:
            formatIcon = QtGui.QIcon()
            formatIcon.addPixmap(QtGui.QPixmap(":/Formats/icons/" + f + ".png"), QtGui.QIcon.Normal,
                                 QtGui.QIcon.Off)
            GUI.FormatBox.addItem(formatIcon, f)
        GUI.FormatBox.setCurrentIndex(0)

        self.modeBasic()



