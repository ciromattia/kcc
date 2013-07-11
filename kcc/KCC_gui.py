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
import urllib2
import comic2ebook
import kindlestrip
from image import ProfileData
from subprocess import call, Popen, STDOUT, PIPE
from PyQt4 import QtGui, QtCore
from xml.dom.minidom import parse
from HTMLParser import HTMLParser


class Icons:
    def __init__(self):
        self.deviceKindle = QtGui.QIcon()
        self.deviceKindle.addPixmap(QtGui.QPixmap(":/Devices/icons/Kindle.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.deviceOther = QtGui.QIcon()
        self.deviceOther.addPixmap(QtGui.QPixmap(":/Devices/icons/Other.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.MOBIFormat = QtGui.QIcon()
        self.MOBIFormat.addPixmap(QtGui.QPixmap(":/Formats/icons/MOBI.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.CBZFormat = QtGui.QIcon()
        self.CBZFormat.addPixmap(QtGui.QPixmap(":/Formats/icons/CBZ.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.EPUBFormat = QtGui.QIcon()
        self.EPUBFormat.addPixmap(QtGui.QPixmap(":/Formats/icons/EPUB.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.info = QtGui.QIcon()
        self.info.addPixmap(QtGui.QPixmap(":/Status/icons/info.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.warning = QtGui.QIcon()
        self.warning.addPixmap(QtGui.QPixmap(":/Status/icons/warning.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.error = QtGui.QIcon()
        self.error.addPixmap(QtGui.QPixmap(":/Status/icons/error.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)


class HTMLStripper(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


# noinspection PyBroadException
class VersionThread(QtCore.QThread):
    def __init__(self, parent):
        QtCore.QThread.__init__(self)
        self.parent = parent

    def __del__(self):
        self.wait()

    def run(self):
        try:
            XML = urllib2.urlopen('http://kcc.vulturis.eu/Version.php')
            XML = parse(XML)
        except Exception:
            return
        latestVersion = XML.childNodes[0].getElementsByTagName('latest')[0].childNodes[0].toxml()
        if tuple(map(int, (latestVersion.split(".")))) > tuple(map(int, (__version__.split(".")))):
            self.emit(QtCore.SIGNAL("addMessage"), '<a href="http://kcc.vulturis.eu/">'
                                                   '<b>New version is available!</b></a>', 'warning')


# noinspection PyBroadException
class WorkerThread(QtCore.QThread):
    def __init__(self, parent):
        QtCore.QThread.__init__(self)
        self.parent = parent

    def __del__(self):
        self.wait()

    def run(self):
        self.emit(QtCore.SIGNAL("modeConvert"), False)
        profile = ProfileData.ProfileLabels[str(GUI.DeviceBox.currentText())]
        argv = ["--profile=" + profile]
        currentJobs = []
        if GUI.MangaBox.isChecked():
            argv.append("--manga-style")
        if GUI.RotateBox.isChecked():
            argv.append("--rotate")
        if GUI.QualityBox.checkState() == 1:
            argv.append("--quality=1")
        elif GUI.QualityBox.checkState() == 2:
            argv.append("--quality=2")
        if self.parent.currentMode > 1:
            if GUI.ProcessingBox.isChecked():
                argv.append("--noprocessing")
            if GUI.UpscaleBox.isChecked():
                argv.append("--upscale")
            if GUI.NoRotateBox.isChecked():
                argv.append("--nosplitrotate")
            if GUI.BorderBox.isChecked():
                argv.append("--blackborders")
            if GUI.StretchBox.isChecked():
                argv.append("--stretch")
            if GUI.NoDitheringBox.isChecked():
                argv.append("--forcepng")
            if float(self.parent.GammaValue) > 0.09:
                argv.append("--gamma=" + self.parent.GammaValue)
            if str(GUI.FormatBox.currentText()) == 'CBZ':
                argv.append("--cbz-output")
        if self.parent.currentMode > 2:
            argv.append("--customwidth=" + str(GUI.customWidth.text()))
            argv.append("--customheight=" + str(GUI.customHeight.text()))
            if GUI.ColorBox.isChecked():
                argv.append("--forcecolor")
        for i in range(GUI.JobList.count()):
            currentJobs.append(str(GUI.JobList.item(i).text()))
        GUI.JobList.clear()
        for job in currentJobs:
            self.errors = False
            self.emit(QtCore.SIGNAL("addMessage"), '<b>Source:</b> ' + job, 'info')
            if str(GUI.FormatBox.currentText()) == 'CBZ':
                self.emit(QtCore.SIGNAL("addMessage"), 'Creating CBZ file...', 'info')
            else:
                self.emit(QtCore.SIGNAL("addMessage"), 'Creating EPUB file...', 'info')
            jobargv = list(argv)
            jobargv.append(job)
            try:
                outputPath = comic2ebook.main(jobargv, self)
                self.emit(QtCore.SIGNAL("hideProgressBar"))
            except UserWarning as warn:
                self.errors = True
                self.emit(QtCore.SIGNAL("addMessage"), str(warn), 'warning')
                self.emit(QtCore.SIGNAL("addMessage"), 'KCC failed to create output file!', 'warning')
            except Exception as err:
                self.errors = True
                type_, value_, traceback_ = sys.exc_info()
                self.emit(QtCore.SIGNAL("showDialog"), "Error during conversion %s:\n\n%s\n\nTraceback:\n%s"
                                                       % (jobargv[-1], str(err), traceback.format_tb(traceback_)))
                self.emit(QtCore.SIGNAL("addMessage"), 'KCC failed to create EPUB!', 'error')
            if not self.errors:
                if str(GUI.FormatBox.currentText()) == 'CBZ':
                    self.emit(QtCore.SIGNAL("addMessage"), 'Creating CBZ file... Done!', 'info', True)
                else:
                    self.emit(QtCore.SIGNAL("addMessage"), 'Creating EPUB file... Done!', 'info', True)
                if str(GUI.FormatBox.currentText()) == 'MOBI':
                    self.emit(QtCore.SIGNAL("addMessage"), 'Creating MOBI file...', 'info')
                    self.emit(QtCore.SIGNAL("progressBarTick"), 1)
                    try:
                        self.kindlegenErrorCode = 0
                        if os.path.getsize(outputPath) < 367001600:
                            output = Popen('kindlegen "' + outputPath + '"', stdout=PIPE, stderr=STDOUT, shell=True)
                            for line in output.stdout:
                                # ERROR: Generic error
                                if "Error(" in line:
                                    self.kindlegenErrorCode = 1
                                    self.kindlegenError = line
                                # ERROR: EPUB too big
                                if ":E23026:" in line:
                                    self.kindlegenErrorCode = 23026
                        else:
                            # ERROR: EPUB too big
                            self.kindlegenErrorCode = 23026
                    except:
                        # ERROR: Unknown generic error
                        self.kindlegenErrorCode = 1
                        continue
                    if self.kindlegenErrorCode == 0:
                        self.emit(QtCore.SIGNAL("addMessage"), 'Creating MOBI file... Done!', 'info', True)
                        self.emit(QtCore.SIGNAL("addMessage"), 'Removing SRCS header...', 'info')
                        os.remove(outputPath)
                        mobiPath = outputPath.replace('.epub', '.mobi')
                        shutil.move(mobiPath, mobiPath + '_tostrip')
                        try:
                            kindlestrip.main((mobiPath + '_tostrip', mobiPath))
                        except Exception:
                            self.errors = True
                        if not self.errors:
                            os.remove(mobiPath + '_tostrip')
                            self.emit(QtCore.SIGNAL("addMessage"), 'Removing SRCS header... Done!', 'info', True)
                        else:
                            shutil.move(mobiPath + '_tostrip', mobiPath)
                            self.emit(QtCore.SIGNAL("addMessage"),
                                      'KindleStrip failed to remove SRCS header!', 'warning')
                            self.emit(QtCore.SIGNAL("addMessage"),
                                      'MOBI file will work correctly but it will be highly oversized.', 'warning')
                    else:
                        epubSize = (os.path.getsize(outputPath))/1024/1024
                        os.remove(outputPath)
                        if os.path.exists(outputPath.replace('.epub', '.mobi')):
                            os.remove(outputPath.replace('.epub', '.mobi'))
                        self.emit(QtCore.SIGNAL("addMessage"), 'KindleGen failed to create MOBI!', 'error')
                        if self.kindlegenErrorCode == 1 and self.kindlegenError:
                            self.emit(QtCore.SIGNAL("showDialog"), "KindleGen error:\n\n" + self.kindlegenError)
                        if self.kindlegenErrorCode == 23026:
                            self.emit(QtCore.SIGNAL("addMessage"), 'Created EPUB file was too big.',
                                      'error')
                            self.emit(QtCore.SIGNAL("addMessage"), 'EPUB file: ' + str(epubSize) + 'MB.'
                                                                   ' Supported size: ~300MB.', 'error')
        self.emit(QtCore.SIGNAL("hideProgressBar"))
        self.parent.needClean = True
        self.emit(QtCore.SIGNAL("addMessage"), '<b>All jobs completed.</b>', 'info')
        self.emit(QtCore.SIGNAL("modeConvert"), True)


# noinspection PyBroadException
class Ui_KCC(object):
    def selectDir(self):
        # Dialog allow to select multiple directories but we can't parse that. QT Bug.
        if self.needClean:
            self.needClean = False
            GUI.JobList.clear()
        dname = QtGui.QFileDialog.getExistingDirectory(MainWindow, 'Select directory', self.lastPath)
        # Lame UTF-8 security measure
        try:
            str(dname)
        except Exception:
            QtGui.QMessageBox.critical(MainWindow, 'KCC Error', "Path cannot contain non-ASCII characters.",
                                       QtGui.QMessageBox.Ok)
            return
        if str(dname) != "":
            self.lastPath = os.path.abspath(os.path.join(str(dname), os.pardir))
            GUI.JobList.addItem(dname)

    def selectFile(self):
        if self.needClean:
            self.needClean = False
            GUI.JobList.clear()
        if self.UnRAR:
            fname = QtGui.QFileDialog.getOpenFileName(MainWindow, 'Select file', self.lastPath,
                                                      '*.cbz *.cbr *.zip *.rar *.pdf')
        else:
            fname = QtGui.QFileDialog.getOpenFileName(MainWindow, 'Select file', self.lastPath,
                                                      '*.cbz *.zip *.pdf')
        # Lame UTF-8 security measure
        try:
            str(fname)
        except Exception:
            QtGui.QMessageBox.critical(MainWindow, 'KCC Error', "Path cannot contain non-ASCII characters.",
                                       QtGui.QMessageBox.Ok)
            return
        if str(fname) != "":
            self.lastPath = os.path.abspath(os.path.join(str(fname), os.pardir))
            GUI.JobList.addItem(fname)

    def clearJobs(self):
        GUI.JobList.clear()

    def modeBasic(self):
        self.currentMode = 1
        MainWindow.setMinimumSize(QtCore.QSize(420, 270))
        MainWindow.setMaximumSize(QtCore.QSize(420, 270))
        MainWindow.resize(420, 270)
        GUI.BasicModeButton.setStyleSheet('font-weight:Bold;')
        GUI.AdvModeButton.setStyleSheet('font-weight:Normal;')
        GUI.FormatBox.setCurrentIndex(0)
        GUI.FormatBox.setEnabled(False)
        GUI.OptionsAdvanced.setEnabled(False)
        GUI.OptionsAdvancedGamma.setEnabled(False)
        GUI.OptionsExpert.setEnabled(False)
        GUI.ProcessingBox.hide()
        GUI.UpscaleBox.hide()
        GUI.NoRotateBox.hide()
        GUI.MangaBox.setEnabled(True)

    def modeAdvanced(self):
        self.currentMode = 2
        MainWindow.setMinimumSize(QtCore.QSize(420, 345))
        MainWindow.setMaximumSize(QtCore.QSize(420, 345))
        MainWindow.resize(420, 345)
        GUI.BasicModeButton.setStyleSheet('font-weight:Normal;')
        GUI.AdvModeButton.setStyleSheet('font-weight:Bold;')
        GUI.FormatBox.setEnabled(True)
        GUI.ProcessingBox.show()
        GUI.UpscaleBox.show()
        GUI.NoRotateBox.show()
        GUI.OptionsAdvancedGamma.setEnabled(True)
        GUI.OptionsAdvanced.setEnabled(True)
        GUI.OptionsExpert.setEnabled(False)
        GUI.MangaBox.setEnabled(True)

    def modeExpert(self, KFA=False):
        self.modeAdvanced()
        self.currentMode = 3
        MainWindow.setMinimumSize(QtCore.QSize(420, 380))
        MainWindow.setMaximumSize(QtCore.QSize(420, 380))
        MainWindow.resize(420, 380)
        GUI.OptionsExpert.setEnabled(True)
        if KFA:
            GUI.ColorBox.setCheckState(2)
            GUI.FormatBox.setCurrentIndex(0)
            GUI.FormatBox.setEnabled(False)
        else:
            GUI.FormatBox.setEnabled(True)
            GUI.MangaBox.setCheckState(0)
            GUI.MangaBox.setEnabled(False)

    def modeConvert(self, enable):
        if self.currentMode != 3:
            GUI.BasicModeButton.setEnabled(enable)
            GUI.AdvModeButton.setEnabled(enable)
        GUI.DirectoryButton.setEnabled(enable)
        GUI.ClearButton.setEnabled(enable)
        GUI.FileButton.setEnabled(enable)
        GUI.DeviceBox.setEnabled(enable)
        GUI.ConvertButton.setEnabled(enable)
        GUI.FormatBox.setEnabled(enable)
        GUI.OptionsBasic.setEnabled(enable)
        GUI.OptionsAdvanced.setEnabled(enable)
        GUI.OptionsAdvancedGamma.setEnabled(enable)
        GUI.OptionsExpert.setEnabled(enable)
        if enable:
            if self.currentMode == 1:
                self.modeBasic()
            elif self.currentMode == 2:
                self.modeAdvanced()
            elif self.currentMode == 3:
                self.modeExpert()

    def changeGamma(self, value):
        value = float(value)
        value = '%.2f' % (value/100)
        if float(value) <= 0.09:
            GUI.GammaLabel.setText('Gamma: Auto')
        else:
            GUI.GammaLabel.setText('Gamma: ' + str(value))
        self.GammaValue = value

    def toggleNoSplitRotate(self, value):
        if value:
            GUI.RotateBox.setEnabled(False)
            GUI.RotateBox.setChecked(False)
        else:
            GUI.RotateBox.setEnabled(True)

    def toggleUpscale(self, value):
        if value:
            GUI.StretchBox.setChecked(False)

    def toggleStretch(self, value):
        if value:
            GUI.UpscaleBox.setChecked(False)

    def changeDevice(self, value):
        if value == 12:
            GUI.BasicModeButton.setEnabled(False)
            GUI.AdvModeButton.setEnabled(False)
            self.addMessage('<a href="https://github.com/ciromattia/kcc/wiki/NonKindle-devices">'
                            'List of supported Non-Kindle devices</a>', 'info')
            self.modeExpert()
        elif value == 11:
            GUI.BasicModeButton.setEnabled(False)
            GUI.AdvModeButton.setEnabled(False)
            self.modeExpert(True)
        elif self.currentMode == 3:
            GUI.BasicModeButton.setEnabled(True)
            GUI.AdvModeButton.setEnabled(True)
            self.modeBasic()
        if value in [0, 1, 5, 6, 7, 8, 9, 12]:
            GUI.QualityBox.setCheckState(0)
            GUI.QualityBox.setEnabled(False)
        else:
            GUI.QualityBox.setEnabled(True)

    def stripTags(self, html):
        s = HTMLStripper()
        s.feed(html)
        return s.get_data()

    def addMessage(self, message, icon=None, replace=False):
        if icon:
            icon = eval('self.icons.' + icon)
            item = QtGui.QListWidgetItem(icon, '   ' + self.stripTags(message))
        else:
            item = QtGui.QListWidgetItem('   ' + self.stripTags(message))
        if replace:
            GUI.JobList.takeItem(GUI.JobList.count()-1)
        label = QtGui.QLabel(message)
        label.setOpenExternalLinks(True)
        if sys.platform == 'darwin':
            font = QtGui.QFont()
            font.setPointSize(11)
            label.setFont(font)
        item.setTextColor(QtGui.QColor("white"))
        GUI.JobList.addItem(item)
        GUI.JobList.setItemWidget(item, label)
        GUI.JobList.scrollToBottom()

    def showDialog(self, message):
        QtGui.QMessageBox.critical(MainWindow, 'KCC Error', message, QtGui.QMessageBox.Ok)

    def updateProgressbar(self, new=False, status=False):
        if new == "status":
            pass
            GUI.ProgressBar.setFormat(status)
        elif new:
            GUI.ProgressBar.setMaximum(new - 1)
            GUI.ProgressBar.reset()
            GUI.ProgressBar.show()
        else:
            GUI.ProgressBar.setValue(GUI.ProgressBar.value() + 1)

    def convertStart(self):
        if self.needClean:
            self.needClean = False
            GUI.JobList.clear()
        if GUI.JobList.count() == 0:
            self.addMessage('No files selected! Please choose files to convert.', 'error')
            self.needClean = True
            return
        if self.currentMode > 2 and (str(GUI.customWidth.text()) == '' or str(GUI.customHeight.text()) == ''):
            GUI.JobList.clear()
            self.addMessage('Target resolution is not set!', 'error')
            self.needClean = True
            return
        self.worker.start()

    def hideProgressBar(self):
        GUI.ProgressBar.hide()

    # noinspection PyUnusedLocal
    def saveSettings(self, event):
        self.settings.setValue('lastPath', self.lastPath)
        self.settings.setValue('lastDevice', GUI.DeviceBox.currentIndex())
        self.settings.setValue('currentFormat', GUI.FormatBox.currentIndex())
        self.settings.setValue('currentMode', self.currentMode)
        self.settings.setValue('options', QtCore.QVariant({'MangaBox': GUI.MangaBox.checkState(),
                                                           'RotateBox': GUI.RotateBox.checkState(),
                                                           'QualityBox': GUI.QualityBox.checkState(),
                                                           'ProcessingBox': GUI.ProcessingBox.checkState(),
                                                           'UpscaleBox': GUI.UpscaleBox.checkState(),
                                                           'NoRotateBox': GUI.NoRotateBox.checkState(),
                                                           'BorderBox': GUI.BorderBox.checkState(),
                                                           'StretchBox': GUI.StretchBox.checkState(),
                                                           'NoDitheringBox': GUI.NoDitheringBox.checkState(),
                                                           'ColorBox': GUI.ColorBox.checkState(),
                                                           'customWidth': GUI.customWidth.text(),
                                                           'customHeight': GUI.customHeight.text(),
                                                           'GammaSlider': float(self.GammaValue)*100}))
        self.settings.sync()

    def __init__(self, UI, KCC):
        global GUI, MainWindow
        GUI = UI
        MainWindow = KCC
        profiles = sorted(ProfileData.ProfileLabels.iterkeys())
        self.icons = Icons()
        self.settings = QtCore.QSettings('KindleComicConverter', 'KindleComicConverter')
        self.lastPath = self.settings.value('lastPath', '', type=str)
        self.lastDevice = self.settings.value('lastDevice', 10, type=int)
        self.currentMode = self.settings.value('currentMode', 1, type=int)
        self.currentFormat = self.settings.value('currentFormat', 0, type=int)
        self.options = self.settings.value('options', QtCore.QVariant({'GammaSlider': 0}))
        self.options = self.options.toPyObject()
        self.worker = WorkerThread(self)
        self.versionCheck = VersionThread(self)
        self.needClean = True

        self.addMessage('<b>Welcome!</b>', 'info')
        self.addMessage('<b>Remember:</b> All options have additional informations in tooltips.', 'info')
        if call('kindlegen', stdout=PIPE, stderr=STDOUT, shell=True) == 0:
            self.KindleGen = True
            formats = ['MOBI', 'EPUB', 'CBZ']
            versionCheck = Popen('kindlegen', stdout=PIPE, stderr=STDOUT, shell=True)
            for line in versionCheck.stdout:
                if "Amazon kindlegen" in line:
                    versionCheck = line.split('V')[1].split(' ')[0]
                    if tuple(map(int, (versionCheck.split(".")))) < tuple(map(int, ('2.9'.split(".")))):
                        self.addMessage('Your <a href="http://www.amazon.com/gp/feature.html?ie=UTF8&docId='
                                        '1000765211">kindlegen</a> is outdated! Creating MOBI might fail.'
                                        ' Please update <a href="http://www.amazon.com/gp/feature.html?ie=UTF8&docId='
                                        '1000765211">kindlegen</a> from Amazon\'s website.', 'warning')
                    break
        else:
            self.KindleGen = False
            formats = ['EPUB', 'CBZ']
            self.addMessage('Cannot find <a href="http://www.amazon.com/gp/feature.html?ie=UTF8&docId='
                            '1000765211">kindlegen</a> in PATH! MOBI creation will be disabled.', 'warning')
        rarExitCode = call('unrar', stdout=PIPE, stderr=STDOUT, shell=True)
        if rarExitCode == 0 or rarExitCode == 7:
            self.UnRAR = True
        else:
            self.UnRAR = False
            self.addMessage('Cannot find <a href="http://www.rarlab.com/rar_add.htm">UnRAR</a>!'
                            ' Processing of CBR/RAR files will be disabled.', 'warning')

        GUI.BasicModeButton.clicked.connect(self.modeBasic)
        GUI.AdvModeButton.clicked.connect(self.modeAdvanced)
        GUI.DirectoryButton.clicked.connect(self.selectDir)
        GUI.ClearButton.clicked.connect(self.clearJobs)
        GUI.FileButton.clicked.connect(self.selectFile)
        GUI.ConvertButton.clicked.connect(self.convertStart)
        GUI.GammaSlider.valueChanged.connect(self.changeGamma)
        GUI.NoRotateBox.stateChanged.connect(self.toggleNoSplitRotate)
        GUI.UpscaleBox.stateChanged.connect(self.toggleUpscale)
        GUI.StretchBox.stateChanged.connect(self.toggleStretch)
        GUI.DeviceBox.activated.connect(self.changeDevice)
        KCC.connect(self.worker, QtCore.SIGNAL("progressBarTick"), self.updateProgressbar)
        KCC.connect(self.worker, QtCore.SIGNAL("modeConvert"), self.modeConvert)
        KCC.connect(self.worker, QtCore.SIGNAL("addMessage"), self.addMessage)
        KCC.connect(self.worker, QtCore.SIGNAL("showDialog"), self.showDialog)
        KCC.connect(self.worker, QtCore.SIGNAL("hideProgressBar"), self.hideProgressBar)
        KCC.connect(self.versionCheck, QtCore.SIGNAL("addMessage"), self.addMessage)
        KCC.closeEvent = self.saveSettings

        for profile in profiles:
            if profile != "Other":
                GUI.DeviceBox.addItem(self.icons.deviceKindle, profile)
            else:
                GUI.DeviceBox.addItem(self.icons.deviceOther, profile)
        GUI.DeviceBox.setCurrentIndex(self.lastDevice)

        for f in formats:
            GUI.FormatBox.addItem(eval('self.icons.' + f + 'Format'), f)
        if self.currentFormat > GUI.FormatBox.count():
            GUI.FormatBox.setCurrentIndex(0)
            self.currentFormat = 0
        else:
            GUI.FormatBox.setCurrentIndex(self.currentFormat)

        for option in self.options:
            if str(option) == "customWidth":
                GUI.customWidth.setText(str(self.options[option]))
            elif str(option) == "customHeight":
                GUI.customHeight.setText(str(self.options[option]))
            elif str(option) == "GammaSlider":
                GUI.GammaSlider.setValue(int(self.options[option]))
                self.changeGamma(int(self.options[option]))
            else:
                eval('GUI.' + str(option)).setCheckState(self.options[option])
        if self.currentMode == 1:
            self.modeBasic()
        elif self.currentMode == 2:
            self.modeAdvanced()
        elif self.currentMode == 3:
            self.modeExpert()
        self.versionCheck.start()
        self.hideProgressBar()
        self.changeDevice(self.lastDevice)
