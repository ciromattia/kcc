#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2013 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013 Pawel Jastrzebski <pawelj@vulturis.eu>
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

__version__ = '3.3'
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import os
import sys
import shutil
import traceback
import urllib2
import time
import comic2ebook
import kindlesplit
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
        self.conversionAlive = False
        self.errors = False
        self.kindlegenErrorCode = 0
        self.kindlegenError = None

    def __del__(self):
        self.wait()

    def sync(self):
        self.conversionAlive = self.parent.conversionAlive

    def clean(self):
        self.parent.needClean = True
        self.emit(QtCore.SIGNAL("hideProgressBar"))
        self.emit(QtCore.SIGNAL("addMessage"), '<b>Conversion interrupted.</b>', 'error')
        self.emit(QtCore.SIGNAL("modeConvert"), True)

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
            if GUI.NoRotateBox.isChecked():
                argv.append("--nosplitrotate")
            if GUI.UpscaleBox.checkState() == 1:
                argv.append("--stretch")
            elif GUI.UpscaleBox.checkState() == 2:
                argv.append("--upscale")
            if GUI.BorderBox.checkState() == 1:
                argv.append("--whiteborders")
            elif GUI.BorderBox.checkState() == 2:
                argv.append("--blackborders")
            if GUI.NoDitheringBox.isChecked():
                argv.append("--forcepng")
            if GUI.WebtoonBox.isChecked():
                argv.append("--webtoon")
            if float(self.parent.GammaValue) > 0.09:
                argv.append("--gamma=" + self.parent.GammaValue)
            if str(GUI.FormatBox.currentText()) == 'CBZ':
                argv.append("--cbz-output")
            if str(GUI.FormatBox.currentText()) == 'MOBI':
                argv.append("--batchsplit")
        if self.parent.currentMode > 2:
            argv.append("--customwidth=" + str(GUI.customWidth.text()))
            argv.append("--customheight=" + str(GUI.customHeight.text()))
            if GUI.ColorBox.isChecked():
                argv.append("--forcecolor")
        for i in range(GUI.JobList.count()):
            if GUI.JobList.item(i).icon().isNull():
                currentJobs.append(str(GUI.JobList.item(i).text()))
        GUI.JobList.clear()
        for job in currentJobs:
            time.sleep(0.5)
            if not self.conversionAlive:
                self.clean()
                return
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
                if not self.conversionAlive:
                    self.clean()
                    return
                else:
                    self.errors = True
                    self.emit(QtCore.SIGNAL("addMessage"), str(warn), 'warning')
                    self.emit(QtCore.SIGNAL("addMessage"), 'KCC failed to create output file!', 'warning')
            except Exception as err:
                self.errors = True
                type_, value_, traceback_ = sys.exc_info()
                self.emit(QtCore.SIGNAL("showDialog"), "Error during conversion %s:\n\n%s\n\nTraceback:\n%s"
                                                       % (jobargv[-1], str(err), traceback.format_tb(traceback_)))
                self.emit(QtCore.SIGNAL("addMessage"), 'KCC failed to create EPUB!', 'error')
            if not self.conversionAlive:
                for item in outputPath:
                    if os.path.exists(item):
                        os.remove(item)
                self.clean()
                return
            if not self.errors:
                if str(GUI.FormatBox.currentText()) == 'CBZ':
                    self.emit(QtCore.SIGNAL("addMessage"), 'Creating CBZ file... <b>Done!</b>', 'info', True)
                else:
                    self.emit(QtCore.SIGNAL("addMessage"), 'Creating EPUB file... <b>Done!</b>', 'info', True)
                if str(GUI.FormatBox.currentText()) == 'MOBI':
                    tomeNumber = 0
                    for item in outputPath:
                        tomeNumber += 1
                        if len(outputPath) > 1:
                            self.emit(QtCore.SIGNAL("addMessage"), 'Creating MOBI file (' + str(tomeNumber)
                                                                   + '/' + str(len(outputPath)) + ')...', 'info')
                        else:
                            self.emit(QtCore.SIGNAL("addMessage"), 'Creating MOBI file...', 'info')
                        self.emit(QtCore.SIGNAL("progressBarTick"), 1)
                        try:
                            self.kindlegenErrorCode = 0
                            if os.path.getsize(item) < 367001600:
                                output = Popen('kindlegen -locale en "' + item + '"', stdout=PIPE, stderr=STDOUT,
                                               shell=True)
                                for line in output.stdout:
                                    # ERROR: Generic error
                                    if "Error(" in line:
                                        self.kindlegenErrorCode = 1
                                        self.kindlegenError = line
                                    # ERROR: EPUB too big
                                    if ":E23026:" in line:
                                        self.kindlegenErrorCode = 23026
                                    if self.kindlegenErrorCode > 0:
                                        break
                            else:
                                # ERROR: EPUB too big
                                self.kindlegenErrorCode = 23026
                        except:
                            # ERROR: Unknown generic error
                            self.kindlegenErrorCode = 1
                            continue
                        if not self.conversionAlive:
                            for item in outputPath:
                                if os.path.exists(item):
                                    os.remove(item)
                                if os.path.exists(item.replace('.epub', '.mobi')):
                                    os.remove(item.replace('.epub', '.mobi'))
                            self.clean()
                            return
                        if self.kindlegenErrorCode == 0:
                            if len(outputPath) > 1:
                                self.emit(QtCore.SIGNAL("addMessage"), 'Creating MOBI file (' + str(tomeNumber) + '/'
                                                                       + str(len(outputPath)) + ')... <b>Done!</b>',
                                                                       'info',  True)
                            else:
                                self.emit(QtCore.SIGNAL("addMessage"), 'Creating MOBI file... <b>Done!</b>', 'info',
                                          True)
                            self.emit(QtCore.SIGNAL("addMessage"), 'Cleaning MOBI file...', 'info')
                            os.remove(item)
                            mobiPath = item.replace('.epub', '.mobi')
                            shutil.move(mobiPath, mobiPath + '_toclean')
                            try:
                                if profile in ['K345', 'KHD', 'KF', 'KFHD', 'KFHD8', 'KFHDX', 'KFHDX8', 'KFA']:
                                    newKindle = True
                                else:
                                    newKindle = False
                                mobisplit = kindlesplit.mobi_split(mobiPath + '_toclean', newKindle)
                                open(mobiPath, 'wb').write(mobisplit.getResult())
                            except Exception:
                                self.errors = True
                            if not self.errors:
                                os.remove(mobiPath + '_toclean')
                                self.emit(QtCore.SIGNAL("addMessage"), 'Cleaning MOBI file... <b>Done!</b>', 'info',
                                          True)
                            else:
                                os.remove(mobiPath + '_toclean')
                                os.remove(mobiPath)
                                self.emit(QtCore.SIGNAL("addMessage"),
                                          'KindleUnpack failed to clean MOBI file!', 'error')
                        else:
                            epubSize = (os.path.getsize(item))/1024/1024
                            os.remove(item)
                            if os.path.exists(item.replace('.epub', '.mobi')):
                                os.remove(item.replace('.epub', '.mobi'))
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
        if self.needClean:
            self.needClean = False
            GUI.JobList.clear()
        # Dirty, dirty way but OS native QFileDialogs don't support directory multiselect
        dirDialog = QtGui.QFileDialog(MainWindow, 'Select directory', self.lastPath)
        dirDialog.setFileMode(dirDialog.Directory)
        dirDialog.setOption(dirDialog.ShowDirsOnly, True)
        dirDialog.setOption(dirDialog.DontUseNativeDialog, True)
        l = dirDialog.findChild(QtGui.QListView, "listView")
        t = dirDialog.findChild(QtGui.QTreeView)
        if l:
            l.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        if t:
            t.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        if dirDialog.exec_() == 1:
            dnames = dirDialog.selectedFiles()
        else:
            dnames = ""
        # Lame UTF-8 security measure
        for dname in dnames:
            try:
                str(dname)
            except Exception:
                QtGui.QMessageBox.critical(MainWindow, 'KCC Error', "Path cannot contain non-ASCII characters.",
                                           QtGui.QMessageBox.Ok)
                return
            if str(dname) != "":
                if sys.platform == 'win32':
                    dname = dname.replace('/', '\\')
                self.lastPath = os.path.abspath(os.path.join(str(dname), os.pardir))
                GUI.JobList.addItem(dname)

    def selectFile(self):
        if self.needClean:
            self.needClean = False
            GUI.JobList.clear()
        if self.UnRAR:
            if self.sevenza:
                fnames = QtGui.QFileDialog.getOpenFileNames(MainWindow, 'Select file', self.lastPath,
                                                            '*.cbz *.cbr *.cb7 *.zip *.rar *.7z *.pdf')
            else:
                fnames = QtGui.QFileDialog.getOpenFileNames(MainWindow, 'Select file', self.lastPath,
                                                            '*.cbz *.cbr *.zip *.rar *.pdf')
        else:
            if self.sevenza:
                fnames = QtGui.QFileDialog.getOpenFileNames(MainWindow, 'Select file', self.lastPath,
                                                            '*.cbz *.cb7 *.zip *.7z *.pdf')
            else:
                fnames = QtGui.QFileDialog.getOpenFileNames(MainWindow, 'Select file', self.lastPath,
                                                            '*.cbz *.zip *.pdf')
        # Lame UTF-8 security measure
        for fname in fnames:
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
        GUI.NoRotateBox.setChecked(False)
        GUI.WebtoonBox.setChecked(False)
        GUI.ProcessingBox.setChecked(False)
        GUI.OptionsAdvanced.setEnabled(False)
        GUI.OptionsAdvancedGamma.setEnabled(False)
        GUI.OptionsExpert.setEnabled(False)
        GUI.ProcessingBox.hide()
        GUI.UpscaleBox.hide()
        GUI.NoRotateBox.hide()
        GUI.MangaBox.setEnabled(True)
        self.changeFormat()

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
            GUI.ColorBox.setChecked(True)
            GUI.FormatBox.setCurrentIndex(0)
            GUI.FormatBox.setEnabled(False)
        else:
            GUI.FormatBox.setEnabled(True)
            GUI.MangaBox.setChecked(False)
            GUI.MangaBox.setEnabled(False)

    def modeConvert(self, enable):
        if self.currentMode != 3:
            GUI.BasicModeButton.setEnabled(enable)
            GUI.AdvModeButton.setEnabled(enable)
        GUI.DirectoryButton.setEnabled(enable)
        GUI.ClearButton.setEnabled(enable)
        GUI.FileButton.setEnabled(enable)
        GUI.DeviceBox.setEnabled(enable)
        GUI.FormatBox.setEnabled(enable)
        GUI.OptionsBasic.setEnabled(enable)
        GUI.OptionsAdvanced.setEnabled(enable)
        GUI.OptionsAdvancedGamma.setEnabled(enable)
        GUI.OptionsExpert.setEnabled(enable)
        if enable:
            self.conversionAlive = False
            self.worker.sync()
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/Other/icons/convert.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            GUI.ConvertButton.setIcon(icon)
            GUI.ConvertButton.setText('Convert')
            GUI.ConvertButton.setEnabled(True)
            if self.currentMode == 1:
                self.modeBasic()
            elif self.currentMode == 2:
                self.modeAdvanced()
            elif self.currentMode == 3:
                self.modeExpert()
        else:
            self.conversionAlive = True
            self.worker.sync()
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/Other/icons/clear.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            GUI.ConvertButton.setIcon(icon)
            GUI.ConvertButton.setText('Abort')
            GUI.ConvertButton.setEnabled(True)

    def changeGamma(self, value):
        value = float(value)
        value = '%.2f' % (value/100)
        if float(value) <= 0.09:
            GUI.GammaLabel.setText('Gamma: Auto')
        else:
            GUI.GammaLabel.setText('Gamma: ' + str(value))
        self.GammaValue = value

    def toggleWebtoonBox(self, value):
        if value:
            GUI.NoRotateBox.setEnabled(False)
            GUI.NoRotateBox.setChecked(True)
            GUI.QualityBox.setEnabled(False)
            GUI.QualityBox.setChecked(False)
            GUI.MangaBox.setEnabled(False)
            GUI.MangaBox.setChecked(False)
            self.addMessage('If images will be too dark after conversion: Set <i>Gamma</i> to 1.0.', 'info')
        else:
            if not GUI.ProcessingBox.isChecked():
                GUI.NoRotateBox.setEnabled(True)
                GUI.QualityBox.setEnabled(True)
            GUI.MangaBox.setEnabled(True)
        self.changeDevice(GUI.DeviceBox.currentIndex(), False)
        self.changeFormat()

    def toggleNoSplitRotate(self, value):
        if value:
            GUI.RotateBox.setEnabled(False)
            GUI.RotateBox.setChecked(False)
        else:
            if not GUI.ProcessingBox.isChecked():
                GUI.RotateBox.setEnabled(True)
        self.changeDevice(GUI.DeviceBox.currentIndex(), False)
        self.changeFormat()

    def toggleProcessingBox(self, value):
        if value:
            GUI.RotateBox.setEnabled(False)
            GUI.RotateBox.setChecked(False)
            GUI.QualityBox.setEnabled(False)
            GUI.QualityBox.setChecked(False)
            GUI.UpscaleBox.setEnabled(False)
            GUI.UpscaleBox.setChecked(False)
            GUI.NoRotateBox.setEnabled(False)
            GUI.NoRotateBox.setChecked(False)
            GUI.BorderBox.setEnabled(False)
            GUI.BorderBox.setChecked(False)
            GUI.WebtoonBox.setEnabled(False)
            GUI.WebtoonBox.setChecked(False)
            GUI.NoDitheringBox.setEnabled(False)
            GUI.NoDitheringBox.setChecked(False)
            GUI.ColorBox.setEnabled(False)
            GUI.ColorBox.setChecked(False)
            GUI.GammaSlider.setEnabled(False)
            GUI.GammaLabel.setEnabled(False)
        else:
            GUI.RotateBox.setEnabled(True)
            GUI.QualityBox.setEnabled(True)
            GUI.UpscaleBox.setEnabled(True)
            GUI.NoRotateBox.setEnabled(True)
            GUI.BorderBox.setEnabled(True)
            GUI.WebtoonBox.setEnabled(True)
            GUI.NoDitheringBox.setEnabled(True)
            GUI.ColorBox.setEnabled(True)
            GUI.GammaSlider.setEnabled(True)
            GUI.GammaLabel.setEnabled(True)
        self.changeDevice(GUI.DeviceBox.currentIndex(), False)
        self.changeFormat()

    def changeDevice(self, value, showInfo=True):
        if value == 9:
            GUI.BasicModeButton.setEnabled(False)
            GUI.AdvModeButton.setEnabled(False)
            if showInfo:
                self.addMessage('<a href="https://github.com/ciromattia/kcc/wiki/NonKindle-devices">'
                                'List of supported Non-Kindle devices</a>', 'info')
            self.modeExpert()
        elif value == 8:
            GUI.BasicModeButton.setEnabled(False)
            GUI.AdvModeButton.setEnabled(False)
            self.modeExpert(True)
        elif self.currentMode == 3:
            GUI.BasicModeButton.setEnabled(True)
            GUI.AdvModeButton.setEnabled(True)
            self.modeBasic()
        if value in [9, 11, 12, 13, 14]:
            GUI.QualityBox.setChecked(False)
            GUI.QualityBox.setEnabled(False)
        else:
            if not GUI.WebtoonBox.isChecked() and not GUI.ProcessingBox.isChecked() \
                    and str(GUI.FormatBox.currentText()) != 'CBZ':
                GUI.QualityBox.setEnabled(True)
        if value in [3, 4, 5, 6, 8, 15]:
            GUI.NoDitheringBox.setChecked(False)
            GUI.NoDitheringBox.setEnabled(False)
        else:
            if not GUI.ProcessingBox.isChecked():
                GUI.NoDitheringBox.setEnabled(True)

    def changeFormat(self):
        if str(GUI.FormatBox.currentText()) == 'CBZ':
            GUI.QualityBox.setChecked(False)
            GUI.QualityBox.setEnabled(False)
        else:
            if not GUI.WebtoonBox.isChecked() and not GUI.ProcessingBox.isChecked():
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
        label.setStyleSheet('background-image:url('');background-color:rgba(255,0,0,0.5);')
        label.setOpenExternalLinks(True)
        if sys.platform == 'darwin':
            font = QtGui.QFont()
            font.setPointSize(11)
            label.setFont(font)
        item.setTextColor(QtGui.QColor('transparent'))
        GUI.JobList.addItem(item)
        GUI.JobList.setItemWidget(item, label)
        GUI.JobList.scrollToBottom()

    def showDialog(self, message):
        QtGui.QMessageBox.critical(MainWindow, 'KCC Error', message, QtGui.QMessageBox.Ok)

    def updateProgressbar(self, new=False, status=False):
        if new == "status":
            GUI.ProgressBar.setFormat(status)
        elif new:
            GUI.ProgressBar.setMaximum(new - 1)
            GUI.ProgressBar.reset()
            GUI.ProgressBar.show()
        else:
            GUI.ProgressBar.setValue(GUI.ProgressBar.value() + 1)

    def convertStart(self):
        if self.conversionAlive:
            GUI.ConvertButton.setEnabled(False)
            self.addMessage('Process will be interrupted. Please wait.', 'warning')
            self.conversionAlive = False
            self.worker.sync()
        else:
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

    def saveSettings(self, event):
        if self.conversionAlive:
            GUI.ConvertButton.setEnabled(False)
            self.addMessage('Process will be interrupted. Please wait.', 'warning')
            self.conversionAlive = False
            self.worker.sync()
            event.ignore()
        if not GUI.ConvertButton.isEnabled():
            event.ignore()
        self.settings.setValue('settingsVersion', __version__)
        self.settings.setValue('lastPath', self.lastPath)
        self.settings.setValue('lastDevice', GUI.DeviceBox.currentIndex())
        self.settings.setValue('currentFormat', GUI.FormatBox.currentIndex())
        self.settings.setValue('currentMode', self.currentMode)
        self.settings.setValue('firstStart', False)
        self.settings.setValue('options', QtCore.QVariant({'MangaBox': GUI.MangaBox.checkState(),
                                                           'RotateBox': GUI.RotateBox.checkState(),
                                                           'QualityBox': GUI.QualityBox.checkState(),
                                                           'ProcessingBox': GUI.ProcessingBox.checkState(),
                                                           'UpscaleBox': GUI.UpscaleBox.checkState(),
                                                           'NoRotateBox': GUI.NoRotateBox.checkState(),
                                                           'BorderBox': GUI.BorderBox.checkState(),
                                                           'WebtoonBox': GUI.WebtoonBox.checkState(),
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
        # User settings will be reverted to default ones if were created in one of the following versions
        # Empty string cover all versions before this system was implemented
        purgeSettingsVersions = ['']
        self.icons = Icons()
        self.settings = QtCore.QSettings('KindleComicConverter', 'KindleComicConverter')
        self.settingsVersion = self.settings.value('settingsVersion', '', type=str)
        if self.settingsVersion in purgeSettingsVersions:
            QtCore.QSettings.clear(self.settings)
            self.settingsVersion = self.settings.value('settingsVersion', '', type=str)
        self.lastPath = self.settings.value('lastPath', '', type=str)
        self.lastDevice = self.settings.value('lastDevice', 0, type=int)
        self.currentMode = self.settings.value('currentMode', 1, type=int)
        self.currentFormat = self.settings.value('currentFormat', 0, type=int)
        self.firstStart = self.settings.value('firstStart', True, type=bool)
        self.options = self.settings.value('options', QtCore.QVariant({'GammaSlider': 0}))
        self.options = self.options.toPyObject()
        self.worker = WorkerThread(self)
        self.versionCheck = VersionThread(self)
        self.conversionAlive = False
        self.needClean = True
        self.GammaValue = 1.0

        self.addMessage('<b>Welcome!</b>', 'info')
        self.addMessage('<b>Remember:</b> All options have additional informations in tooltips.', 'info')
        if self.firstStart:
            self.addMessage('Since you are using <b>KCC</b> for first time please see few '
                            '<a href="https://github.com/ciromattia/kcc#important-tips">important tips</a>.', 'info')
        if call('kindlegen -locale en', stdout=PIPE, stderr=STDOUT, shell=True) == 0:
            self.KindleGen = True
            formats = ['MOBI', 'EPUB', 'CBZ']
            versionCheck = Popen('kindlegen -locale en', stdout=PIPE, stderr=STDOUT, shell=True)
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
        sevenzaExitCode = call('7za', stdout=PIPE, stderr=STDOUT, shell=True)
        if sevenzaExitCode == 0 or sevenzaExitCode == 7:
            self.sevenza = True
        else:
            self.sevenza = False
            self.addMessage('Cannot find <a href="http://www.7-zip.org/download.html">7za</a>!'
                            ' Processing of CB7/7Z files will be disabled.', 'warning')

        GUI.BasicModeButton.clicked.connect(self.modeBasic)
        GUI.AdvModeButton.clicked.connect(self.modeAdvanced)
        GUI.DirectoryButton.clicked.connect(self.selectDir)
        GUI.ClearButton.clicked.connect(self.clearJobs)
        GUI.FileButton.clicked.connect(self.selectFile)
        GUI.ConvertButton.clicked.connect(self.convertStart)
        GUI.GammaSlider.valueChanged.connect(self.changeGamma)
        GUI.NoRotateBox.stateChanged.connect(self.toggleNoSplitRotate)
        GUI.WebtoonBox.stateChanged.connect(self.toggleWebtoonBox)
        GUI.ProcessingBox.stateChanged.connect(self.toggleProcessingBox)
        GUI.DeviceBox.activated.connect(self.changeDevice)
        GUI.FormatBox.activated.connect(self.changeFormat)
        KCC.connect(self.worker, QtCore.SIGNAL("progressBarTick"), self.updateProgressbar)
        KCC.connect(self.worker, QtCore.SIGNAL("modeConvert"), self.modeConvert)
        KCC.connect(self.worker, QtCore.SIGNAL("addMessage"), self.addMessage)
        KCC.connect(self.worker, QtCore.SIGNAL("showDialog"), self.showDialog)
        KCC.connect(self.worker, QtCore.SIGNAL("hideProgressBar"), self.hideProgressBar)
        KCC.connect(self.versionCheck, QtCore.SIGNAL("addMessage"), self.addMessage)
        KCC.closeEvent = self.saveSettings

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
        for profile in ProfileData.ProfileLabelsGUI:
            if profile == "Other":
                GUI.DeviceBox.addItem(self.icons.deviceOther, profile)
            elif profile == "Separator":
                GUI.DeviceBox.insertSeparator(GUI.DeviceBox.count()+1)
            else:
                GUI.DeviceBox.addItem(self.icons.deviceKindle, profile)
        if self.lastDevice > GUI.DeviceBox.count():
            GUI.DeviceBox.setCurrentIndex(0)
            self.lastDevice = 0
        else:
            GUI.DeviceBox.setCurrentIndex(self.lastDevice)

        if self.currentMode == 1:
            self.modeBasic()
        elif self.currentMode == 2:
            self.modeAdvanced()
        elif self.currentMode == 3:
            self.modeExpert()
        self.changeDevice(self.lastDevice)
        self.changeFormat()
        self.versionCheck.start()
        self.hideProgressBar()
        self.worker.sync()
