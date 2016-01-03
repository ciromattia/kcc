# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2016 Pawel Jastrzebski <pawelj@iosphe.re>
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

import os
import sys
from urllib.parse import unquote
from urllib.request import urlopen, urlretrieve, Request
from time import sleep, time
from datetime import datetime
from shutil import move
from subprocess import STDOUT, PIPE
from PyQt5 import QtGui, QtCore, QtWidgets, QtNetwork
from xml.dom.minidom import parse, Document
from psutil import Popen, Process
from copy import copy
from distutils.version import StrictVersion
from xml.sax.saxutils import escape
from platform import platform
from .shared import md5Checksum, HTMLStripper, sanitizeTrace
from . import __version__
from . import comic2ebook
from . import metadata
from . import kindle
if sys.platform.startswith('darwin'):
    from . import KCC_ui_osx as KCC_ui
elif sys.platform.startswith('linux'):
    from . import KCC_ui_linux as KCC_ui
else:
    from . import KCC_ui
if sys.platform.startswith('darwin'):
    from . import KCC_MetaEditor_ui_osx as KCC_MetaEditor_ui
elif sys.platform.startswith('linux'):
    from . import KCC_MetaEditor_ui_linux as KCC_MetaEditor_ui
else:
    from . import KCC_MetaEditor_ui


class QApplicationMessaging(QtWidgets.QApplication):
    messageFromOtherInstance = QtCore.pyqtSignal(bytes)

    def __init__(self, argv):
        QtWidgets.QApplication.__init__(self, argv)
        self._key = 'KCC'
        self._timeout = 1000
        self._locked = False
        socket = QtNetwork.QLocalSocket(self)
        socket.connectToServer(self._key, QtCore.QIODevice.WriteOnly)
        if not socket.waitForConnected(self._timeout):
            self._server = QtNetwork.QLocalServer(self)
            self._server.newConnection.connect(self.handleMessage)
            self._server.listen(self._key)
        else:
            self._locked = True
        socket.disconnectFromServer()

    def __del__(self):
        if not self._locked:
            self._server.close()

    def event(self, e):
        if e.type() == QtCore.QEvent.FileOpen:
            self.messageFromOtherInstance.emit(bytes(e.file(), 'UTF-8'))
            return True
        else:
            return QtWidgets.QApplication.event(self, e)

    def isRunning(self):
        return self._locked

    def handleMessage(self):
        socket = self._server.nextPendingConnection()
        if socket.waitForReadyRead(self._timeout):
            self.messageFromOtherInstance.emit(socket.readAll().data())

    def sendMessage(self, message):
        socket = QtNetwork.QLocalSocket(self)
        socket.connectToServer(self._key, QtCore.QIODevice.WriteOnly)
        socket.waitForConnected(self._timeout)
        socket.write(bytes(message, 'UTF-8'))
        socket.waitForBytesWritten(self._timeout)
        socket.disconnectFromServer()


class QMainWindowKCC(QtWidgets.QMainWindow):
    progressBarTick = QtCore.pyqtSignal(str)
    modeConvert = QtCore.pyqtSignal(int)
    addMessage = QtCore.pyqtSignal(str, str, bool)
    addTrayMessage = QtCore.pyqtSignal(str, str)
    showDialog = QtCore.pyqtSignal(str, str)
    hideProgressBar = QtCore.pyqtSignal()
    forceShutdown = QtCore.pyqtSignal()


class Icons:
    def __init__(self):
        self.deviceKindle = QtGui.QIcon()
        self.deviceKindle.addPixmap(QtGui.QPixmap(":/Devices/icons/Kindle.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.deviceKobo = QtGui.QIcon()
        self.deviceKobo.addPixmap(QtGui.QPixmap(":/Devices/icons/Kobo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
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

        self.programIcon = QtGui.QIcon()
        self.programIcon.addPixmap(QtGui.QPixmap(":/Icon/icons/comic2ebook.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)


class VersionThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.newVersion = ''
        self.md5 = ''
        self.barProgress = 0
        self.answer = None

    def __del__(self):
        self.wait()

    def run(self):
        try:
            XML = parse(urlopen(Request('https://kcc.iosphe.re/Version/',
                                        headers={'User-Agent': 'KindleComicConverter/' + __version__})))
        except Exception:
            return
        latestVersion = XML.childNodes[0].getElementsByTagName('LatestVersion')[0].childNodes[0].toxml()
        if StrictVersion(latestVersion) > StrictVersion(__version__):
            if sys.platform.startswith('win'):
                self.newVersion = latestVersion
                self.md5 = XML.childNodes[0].getElementsByTagName('MD5')[0].childNodes[0].toxml()
                MW.showDialog.emit('<b>New version released!</b> <a href="https://github.com/ciromattia/kcc/releases/">'
                                   'See changelog.</a><br/><br/>Installed version: ' + __version__ +
                                   '<br/>Current version: ' + latestVersion +
                                   '<br/><br/>Would you like to start automatic update?', 'question')
                self.getNewVersion()
            else:
                MW.addMessage.emit('<a href="https://kcc.iosphe.re/">'
                                   '<b>New version is available!</b></a> '
                                   '(<a href="https://github.com/ciromattia/kcc/releases/">'
                                   'Changelog</a>)', 'warning', False)

    def setAnswer(self, dialogAnswer):
        self.answer = dialogAnswer

    def getNewVersion(self):
        while self.answer is None:
            sleep(1)
        if self.answer == QtWidgets.QMessageBox.Yes:
            try:
                MW.modeConvert.emit(-1)
                MW.progressBarTick.emit('Downloading update')
                path = urlretrieve('https://kcc.iosphe.re/Windows/KindleComicConverter_win_' +
                                   self.newVersion + '.exe', reporthook=self.getNewVersionTick)
                if self.md5 != md5Checksum(path[0]):
                    raise Exception
                move(path[0], path[0] + '.exe')
                MW.hideProgressBar.emit()
                MW.modeConvert.emit(1)
                Popen(path[0] + '.exe  /SP- /silent /noicons', stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
                MW.forceShutdown.emit()
            except Exception:
                MW.addMessage.emit('Failed to download update!', 'warning', False)
                MW.hideProgressBar.emit()
                MW.modeConvert.emit(1)

    def getNewVersionTick(self, size, blockSize, totalSize):
        progress = int((size / (totalSize // blockSize)) * 100)
        if size == 0:
            MW.progressBarTick.emit('100')
        if progress > self.barProgress:
            self.barProgress = progress
            MW.progressBarTick.emit('tick')


class ProgressThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.running = False
        self.content = None
        self.progress = 0

    def __del__(self):
        self.wait()

    def run(self):
        self.running = True
        while self.running:
            sleep(1)
            if self.content and GUI.conversionAlive:
                MW.addMessage.emit(self.content + self.progress * '.', 'info', True)
                self.progress += 1
                if self.progress == 4:
                    self.progress = 0

    def stop(self):
        self.running = False


class WorkerThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.conversionAlive = False
        self.errors = False
        self.kindlegenErrorCode = [0]
        self.workerOutput = []
        self.progressBarTick = MW.progressBarTick
        self.addMessage = MW.addMessage

    def __del__(self):
        self.wait()

    def sync(self):
        self.conversionAlive = GUI.conversionAlive

    def clean(self):
        GUI.progress.content = ''
        GUI.progress.stop()
        GUI.needClean = True
        MW.hideProgressBar.emit()
        MW.addMessage.emit('<b>Conversion interrupted.</b>', 'error', False)
        MW.addTrayMessage.emit('Conversion interrupted.', 'Critical')
        MW.modeConvert.emit(1)

    def run(self):
        MW.modeConvert.emit(0)

        parser = comic2ebook.makeParser()
        options, _ = parser.parse_args()
        argv = ''
        currentJobs = []

        options.profile = GUI.profiles[str(GUI.DeviceBox.currentText())]['Label']
        options.format = str(GUI.FormatBox.currentText()).replace('/AZW3', '')
        if GUI.MangaBox.isChecked():
            options.righttoleft = True
        if GUI.RotateBox.checkState() == 1:
            options.splitter = 2
        elif GUI.RotateBox.checkState() == 2:
            options.splitter = 1
        if GUI.QualityBox.isChecked():
            options.hqmode = True
        if GUI.WebtoonBox.isChecked():
            options.webtoon = True
        if GUI.UpscaleBox.checkState() == 1:
            options.stretch = True
        elif GUI.UpscaleBox.checkState() == 2:
            options.upscale = True
        if GUI.GammaBox.isChecked() and float(GUI.GammaValue) > 0.09:
            options.gamma = float(GUI.GammaValue)
        if GUI.BorderBox.checkState() == 1:
            options.white_borders = True
        elif GUI.BorderBox.checkState() == 2:
            options.black_borders = True
        if GUI.NoDitheringBox.isChecked():
            options.forcepng = True
        if GUI.ColorBox.isChecked():
            options.forcecolor = True
        if GUI.currentMode > 2:
            options.customwidth = str(GUI.customWidth.text())
            options.customheight = str(GUI.customHeight.text())

        for i in range(GUI.JobList.count()):
            # Make sure that we don't consider any system message as job to do
            if GUI.JobList.item(i).icon().isNull():
                currentJobs.append(str(GUI.JobList.item(i).text()))
        GUI.JobList.clear()
        for job in currentJobs:
            sleep(0.5)
            if not self.conversionAlive:
                self.clean()
                return
            self.errors = False
            MW.addMessage.emit('<b>Source:</b> ' + job, 'info', False)
            if str(GUI.FormatBox.currentText()) == 'CBZ':
                MW.addMessage.emit('Creating CBZ files', 'info', False)
                GUI.progress.content = 'Creating CBZ files'
            else:
                MW.addMessage.emit('Creating EPUB files', 'info', False)
                GUI.progress.content = 'Creating EPUB files'
            jobargv = list(argv)
            jobargv.append(job)
            try:
                comic2ebook.options = copy(options)
                comic2ebook.checkOptions()
                outputPath = comic2ebook.makeBook(job, self)
                MW.hideProgressBar.emit()
            except UserWarning as warn:
                if not self.conversionAlive:
                    self.clean()
                    return
                else:
                    GUI.progress.content = ''
                    self.errors = True
                    MW.addMessage.emit(str(warn), 'warning', False)
                    MW.addMessage.emit('Error during conversion! Please consult '
                                       '<a href="https://github.com/ciromattia/kcc/wiki/Error-messages">wiki</a> '
                                       'for more details.', 'error', False)
                    MW.addTrayMessage.emit('Error during conversion!', 'Critical')
            except Exception as err:
                GUI.progress.content = ''
                self.errors = True
                _, _, traceback = sys.exc_info()
                MW.showDialog.emit("Error during conversion %s:\n\n%s\n\nTraceback:\n%s"
                                   % (jobargv[-1], str(err), sanitizeTrace(traceback)), 'error')
                MW.addMessage.emit('Error during conversion! Please consult '
                                   '<a href="https://github.com/ciromattia/kcc/wiki/Error-messages">wiki</a> '
                                   'for more details.', 'error', False)
                MW.addTrayMessage.emit('Error during conversion!', 'Critical')
            if not self.conversionAlive:
                for item in outputPath:
                    if os.path.exists(item):
                        os.remove(item)
                self.clean()
                return
            if not self.errors:
                GUI.progress.content = ''
                if str(GUI.FormatBox.currentText()) == 'CBZ':
                    MW.addMessage.emit('Creating CBZ files... <b>Done!</b>', 'info', True)
                else:
                    MW.addMessage.emit('Creating EPUB files... <b>Done!</b>', 'info', True)
                if str(GUI.FormatBox.currentText()) == 'MOBI/AZW3':
                    MW.progressBarTick.emit('Creating MOBI files')
                    MW.progressBarTick.emit(str(len(outputPath) * 2 + 1))
                    MW.progressBarTick.emit('tick')
                    MW.addMessage.emit('Creating MOBI files', 'info', False)
                    GUI.progress.content = 'Creating MOBI files'
                    work = []
                    for item in outputPath:
                        work.append([item])
                    self.workerOutput = comic2ebook.makeMOBI(work, self)
                    self.kindlegenErrorCode = [0]
                    for errors in self.workerOutput:
                        if errors[0] != 0:
                            self.kindlegenErrorCode = errors
                            break
                    if not self.conversionAlive:
                        for item in outputPath:
                            if os.path.exists(item):
                                os.remove(item)
                            if os.path.exists(item.replace('.epub', '.mobi')):
                                os.remove(item.replace('.epub', '.mobi'))
                        self.clean()
                        return
                    if self.kindlegenErrorCode[0] == 0:
                        GUI.progress.content = ''
                        MW.addMessage.emit('Creating MOBI files... <b>Done!</b>', 'info', True)
                        MW.addMessage.emit('Processing MOBI files', 'info', False)
                        GUI.progress.content = 'Processing MOBI files'
                        self.workerOutput = []
                        for item in outputPath:
                            self.workerOutput.append(comic2ebook.makeMOBIFix(
                                item, comic2ebook.options.covers[outputPath.index(item)][1]))
                            MW.progressBarTick.emit('tick')
                        for success in self.workerOutput:
                            if not success[0]:
                                self.errors = True
                                break
                        if not self.errors:
                            for item in outputPath:
                                GUI.progress.content = ''
                                mobiPath = item.replace('.epub', '.mobi')
                                os.remove(mobiPath + '_toclean')
                                if GUI.targetDirectory and GUI.targetDirectory != os.path.dirname(mobiPath):
                                    try:
                                        move(mobiPath, GUI.targetDirectory)
                                    except Exception:
                                        pass
                            MW.addMessage.emit('Processing MOBI files... <b>Done!</b>', 'info', True)
                            k = kindle.Kindle()
                            if k.path and k.coverSupport:
                                for item in outputPath:
                                    comic2ebook.options.covers[outputPath.index(item)][0].saveToKindle(
                                        k, comic2ebook.options.covers[outputPath.index(item)][1])
                                MW.addMessage.emit('Kindle detected. Uploading covers...', 'info', False)
                        else:
                            GUI.progress.content = ''
                            for item in outputPath:
                                mobiPath = item.replace('.epub', '.mobi')
                                if os.path.exists(mobiPath):
                                    os.remove(mobiPath)
                                if os.path.exists(mobiPath + '_toclean'):
                                    os.remove(mobiPath + '_toclean')
                            MW.addMessage.emit('Failed to process MOBI file!', 'error', False)
                            MW.addTrayMessage.emit('Failed to process MOBI file!', 'Critical')
                    else:
                        GUI.progress.content = ''
                        epubSize = (os.path.getsize(self.kindlegenErrorCode[2])) // 1024 // 1024
                        for item in outputPath:
                            if os.path.exists(item):
                                os.remove(item)
                            if os.path.exists(item.replace('.epub', '.mobi')):
                                os.remove(item.replace('.epub', '.mobi'))
                        MW.addMessage.emit('KindleGen failed to create MOBI!', 'error', False)
                        MW.addTrayMessage.emit('KindleGen failed to create MOBI!', 'Critical')
                        if self.kindlegenErrorCode[0] == 1 and self.kindlegenErrorCode[1] != '':
                            MW.showDialog.emit("KindleGen error:\n\n" + self.kindlegenErrorCode[1], 'error')
                        if self.kindlegenErrorCode[0] == 23026:
                            MW.addMessage.emit('Created EPUB file was too big.', 'error', False)
                            MW.addMessage.emit('EPUB file: ' + str(epubSize) + 'MB. Supported size: ~350MB.', 'error',
                                               False)
                else:
                    for item in outputPath:
                        if GUI.targetDirectory and GUI.targetDirectory != os.path.dirname(item):
                            try:
                                move(item, GUI.targetDirectory)
                            except Exception:
                                pass
        GUI.progress.content = ''
        GUI.progress.stop()
        MW.hideProgressBar.emit()
        GUI.needClean = True
        if not self.errors:
            MW.addMessage.emit('<b>All jobs completed.</b>', 'info', False)
            MW.addTrayMessage.emit('All jobs completed.', 'Information')
        MW.modeConvert.emit(1)


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        if self.isSystemTrayAvailable():
            QtWidgets.QSystemTrayIcon.__init__(self, GUI.icons.programIcon, MW)
            self.activated.connect(self.catchClicks)

    def catchClicks(self):
        MW.showNormal()
        MW.raise_()
        MW.activateWindow()

    def addTrayMessage(self, message, icon):
        icon = eval('QtWidgets.QSystemTrayIcon.' + icon)
        if self.supportsMessages() and not MW.isActiveWindow():
            self.showMessage('Kindle Comic Converter', message, icon)


class KCCGUI(KCC_ui.Ui_KCC):
    def selectDir(self):
        if self.needClean:
            self.needClean = False
            GUI.JobList.clear()
        dname = QtWidgets.QFileDialog.getExistingDirectory(MW, 'Select directory', self.lastPath)
        if dname != '':
            if sys.platform.startswith('win'):
                dname = dname.replace('/', '\\')
            self.lastPath = os.path.abspath(os.path.join(dname, os.pardir))
            GUI.JobList.addItem(dname)
            GUI.JobList.scrollToBottom()

    def selectFile(self):
        if self.needClean:
            self.needClean = False
            GUI.JobList.clear()
        if self.UnRAR:
            if self.sevenza:
                fnames = QtWidgets.QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                                'Comic (*.cbz *.cbr *.cb7 *.zip *.rar *.7z *.pdf)')
            else:
                fnames = QtWidgets.QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                                'Comic (*.cbz *.cbr *.zip *.rar *.pdf)')
        else:
            if self.sevenza:
                fnames = QtWidgets.QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                                'Comic (*.cbz *.cb7 *.zip *.7z *.pdf)')
            else:
                fnames = QtWidgets.QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                                'Comic (*.cbz *.zip *.pdf)')
        for fname in fnames[0]:
            if fname != '':
                if sys.platform.startswith('win'):
                    fname = fname.replace('/', '\\')
                self.lastPath = os.path.abspath(os.path.join(fname, os.pardir))
                GUI.JobList.addItem(fname)
                GUI.JobList.scrollToBottom()

    def selectFileMetaEditor(self):
        if self.UnRAR:
            if self.sevenza:
                fname = QtWidgets.QFileDialog.getOpenFileName(MW, 'Select file', self.lastPath,
                                                              'Comic (*.cbz *.cbr *.cb7)')
            else:
                fname = QtWidgets.QFileDialog.getOpenFileName(MW, 'Select file', self.lastPath,
                                                              'Comic (*.cbz *.cbr)')
        else:
            if self.sevenza:
                fname = QtWidgets.QFileDialog.getOpenFileName(MW, 'Select file', self.lastPath,
                                                              'Comic (*.cbz *.cb7)')
            else:
                fname = QtWidgets.QFileDialog.getOpenFileName(MW, 'Select file', self.lastPath,
                                                              'Comic (*.cbz)')
        if fname[0] != '':
            if sys.platform.startswith('win'):
                fname = fname[0].replace('/', '\\')
            else:
                fname = fname[0]
            self.lastPath = os.path.abspath(os.path.join(fname, os.pardir))
            try:
                self.editor.loadData(fname)
            except Exception as err:
                _, _, traceback = sys.exc_info()
                self.showDialog("Failed to parse metadata!\n\n%s\n\nTraceback:\n%s"
                                % (str(err), sanitizeTrace(traceback)), 'error')
            else:
                self.editor.ui.exec_()

    def clearJobs(self):
        GUI.JobList.clear()

    # noinspection PyCallByClass,PyTypeChecker,PyArgumentList
    def openWiki(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/ciromattia/kcc/wiki'))

    def modeChange(self, mode):
        if mode == 1:
            self.currentMode = 1
            MW.setMaximumSize(QtCore.QSize(420, 335))
            MW.setMinimumSize(QtCore.QSize(420, 335))
            MW.resize(420, 335)
            GUI.OptionsGamma.setVisible(False)
            GUI.OptionsCustom.setVisible(False)
        elif mode == 2:
            self.currentMode = 2
            MW.setMaximumSize(QtCore.QSize(420, 365))
            MW.setMinimumSize(QtCore.QSize(420, 365))
            MW.resize(420, 365)
            GUI.OptionsGamma.setVisible(True)
            GUI.OptionsCustom.setVisible(False)
        elif mode == 3:
            self.currentMode = 3
            MW.setMaximumSize(QtCore.QSize(420, 390))
            MW.setMinimumSize(QtCore.QSize(420, 390))
            MW.resize(420, 390)
            GUI.OptionsGamma.setVisible(True)
            GUI.OptionsCustom.setVisible(True)

    def modeConvert(self, enable):
        if enable < 1:
            status = False
        else:
            status = True
        GUI.EditorButton.setEnabled(status)
        GUI.WikiButton.setEnabled(status)
        GUI.FormatBox.setEnabled(status)
        GUI.DirectoryButton.setEnabled(status)
        GUI.ClearButton.setEnabled(status)
        GUI.FileButton.setEnabled(status)
        GUI.DeviceBox.setEnabled(status)
        GUI.Options.setEnabled(status)
        GUI.OptionsGamma.setEnabled(status)
        GUI.OptionsCustom.setEnabled(status)
        GUI.ConvertButton.setEnabled(True)
        if enable == 1:
            self.conversionAlive = False
            self.worker.sync()
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/Other/icons/convert.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            GUI.ConvertButton.setIcon(icon)
            GUI.ConvertButton.setText('Convert')
            GUI.Form.setAcceptDrops(True)
        elif enable == 0:
            self.conversionAlive = True
            self.worker.sync()
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/Other/icons/clear.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            GUI.ConvertButton.setIcon(icon)
            GUI.ConvertButton.setText('Abort')
            GUI.Form.setAcceptDrops(False)
        elif enable == -1:
            self.conversionAlive = True
            self.worker.sync()
            GUI.ConvertButton.setEnabled(False)
            GUI.Form.setAcceptDrops(False)

    def toggleGammaBox(self, value):
        if value:
            if self.currentMode != 3:
                self.modeChange(2)
        else:
            if self.currentMode != 3:
                self.modeChange(1)

    def toggleWebtoonBox(self, value):
        if value:
            GUI.QualityBox.setEnabled(False)
            GUI.QualityBox.setChecked(False)
            GUI.MangaBox.setEnabled(False)
            GUI.MangaBox.setChecked(False)
            GUI.RotateBox.setEnabled(False)
            GUI.RotateBox.setChecked(False)
            GUI.UpscaleBox.setEnabled(False)
            GUI.UpscaleBox.setChecked(True)
        else:
            GUI.QualityBox.setEnabled(True)
            GUI.MangaBox.setEnabled(True)
            GUI.RotateBox.setEnabled(True)
            GUI.UpscaleBox.setEnabled(True)

    def changeGamma(self, value):
        value = float(value)
        value = '%.2f' % (value / 100)
        if float(value) <= 0.09:
            GUI.GammaLabel.setText('Gamma: Auto')
        else:
            GUI.GammaLabel.setText('Gamma: ' + str(value))
        self.GammaValue = value

    def changeDevice(self):
        profile = GUI.profiles[str(GUI.DeviceBox.currentText())]
        if profile['ForceExpert']:
            self.modeChange(3)
        elif GUI.GammaBox.isChecked():
            self.modeChange(2)
        else:
            self.modeChange(1)
        self.changeFormat()
        GUI.GammaSlider.setValue(0)
        self.changeGamma(0)
        GUI.QualityBox.setEnabled(profile['Quality'])
        if not profile['Quality']:
            GUI.QualityBox.setChecked(False)
        if profile['DefaultUpscale']:
            GUI.UpscaleBox.setChecked(True)
        if str(GUI.DeviceBox.currentText()) == 'Other':
            self.addMessage('<a href="https://github.com/ciromattia/kcc/wiki/NonKindle-devices">'
                            'List of supported Non-Kindle devices.</a>', 'info')

    def changeFormat(self, outputFormat=None):
        profile = GUI.profiles[str(GUI.DeviceBox.currentText())]
        if outputFormat is not None:
            GUI.FormatBox.setCurrentIndex(outputFormat)
        else:
            GUI.FormatBox.setCurrentIndex(profile['DefaultFormat'])
        GUI.QualityBox.setEnabled(profile['Quality'])

    def stripTags(self, html):
        s = HTMLStripper()
        s.feed(html)
        return s.get_data()

    def addMessage(self, message, icon, replace=False):
        if icon != '':
            icon = eval('self.icons.' + icon)
            item = QtWidgets.QListWidgetItem(icon, '    ' + self.stripTags(message))
        else:
            item = QtWidgets.QListWidgetItem('    ' + self.stripTags(message))
        if replace:
            GUI.JobList.takeItem(GUI.JobList.count() - 1)
        # Due to lack of HTML support in QListWidgetItem we overlay text field with QLabel
        # We still fill original text field with transparent content to trigger creation of horizontal scrollbar
        item.setForeground(QtGui.QColor('transparent'))
        label = QtWidgets.QLabel(message)
        label.setStyleSheet('background-image:url('');background-color:rgba(0,0,0,0);')
        label.setOpenExternalLinks(True)
        font = QtGui.QFont()
        font.setPointSize(self.listFontSize)
        label.setFont(font)
        GUI.JobList.addItem(item)
        GUI.JobList.setItemWidget(item, label)
        GUI.JobList.scrollToBottom()

    def showDialog(self, message, kind):
        if kind == 'error':
            QtWidgets.QMessageBox.critical(MW, 'KCC - Error', message, QtWidgets.QMessageBox.Ok)
            try:
                doc = Document()
                root = doc.createElement('KCCErrorReport')
                doc.appendChild(root)
                main = doc.createElement('Timestamp')
                root.appendChild(main)
                text = doc.createTextNode(datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S'))
                main.appendChild(text)
                main = doc.createElement('OS')
                root.appendChild(main)
                text = doc.createTextNode(platform())
                main.appendChild(text)
                main = doc.createElement('Version')
                root.appendChild(main)
                text = doc.createTextNode(__version__)
                main.appendChild(text)
                main = doc.createElement('Error')
                root.appendChild(main)
                text = doc.createTextNode(message)
                main.appendChild(text)
                urlopen(Request(url='https://kcc.iosphe.re/ErrorHandle/', data=doc.toxml(encoding='utf-8'),
                                headers={'Content-Type': 'application/xml',
                                         'User-Agent': 'KindleComicConverter/' + __version__}))
            except:
                pass
        elif kind == 'question':
            GUI.versionCheck.setAnswer(QtWidgets.QMessageBox.question(MW, 'KCC - Question', message,
                                                                          QtWidgets.QMessageBox.Yes,
                                                                          QtWidgets.QMessageBox.No))

    def updateProgressbar(self, command):
        if command == 'tick':
            GUI.ProgressBar.setValue(GUI.ProgressBar.value() + 1)
        elif command.isdigit():
            GUI.ProgressBar.setMaximum(int(command) - 1)
            GUI.EditorButton.hide()
            GUI.WikiButton.hide()
            GUI.ProgressBar.reset()
            GUI.ProgressBar.show()
        else:
            GUI.ProgressBar.setFormat(command)

    def convertStart(self):
        if self.conversionAlive:
            GUI.ConvertButton.setEnabled(False)
            self.addMessage('Process will be interrupted. Please wait.', 'warning')
            self.conversionAlive = False
            self.worker.sync()
        else:
            # noinspection PyArgumentList
            if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                dname = QtWidgets.QFileDialog.getExistingDirectory(MW, 'Select output directory', self.lastPath)
                if dname != '':
                    if sys.platform.startswith('win'):
                        dname = dname.replace('/', '\\')
                    GUI.targetDirectory = dname
                else:
                    GUI.targetDirectory = ''
            else:
                GUI.targetDirectory = ''
            self.progress.start()
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
            if str(GUI.FormatBox.currentText()) == 'MOBI/AZW3' and not self.kindleGen:
                self.detectKindleGen()
                if not self.kindleGen:
                    GUI.JobList.clear()
                    self.addMessage('Cannot find <a href="http://www.amazon.com/gp/feature.html?ie=UTF8&docId='
                                    '1000765211"><b>KindleGen</b></a>! MOBI conversion is unavailable!', 'error')
                    if sys.platform.startswith('win'):
                        self.addMessage('Download it and place EXE in KCC directory.', 'error')
                    elif sys.platform.startswith('darwin'):
                        self.addMessage('Install it using <a href="http://brew.sh/">Brew</a>.', 'error')
                    else:
                        self.addMessage('Download it and place executable in /usr/local/bin directory.', 'error')
                    self.needClean = True
                    return
            self.worker.start()

    def hideProgressBar(self):
        GUI.ProgressBar.hide()
        GUI.EditorButton.show()
        GUI.WikiButton.show()

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
        self.settings.setValue('startNumber', self.startNumber + 1)
        self.settings.setValue('options', {'MangaBox': GUI.MangaBox.checkState(),
                                           'RotateBox': GUI.RotateBox.checkState(),
                                           'QualityBox': GUI.QualityBox.checkState(),
                                           'GammaBox': GUI.GammaBox.checkState(),
                                           'UpscaleBox': GUI.UpscaleBox.checkState(),
                                           'BorderBox': GUI.BorderBox.checkState(),
                                           'WebtoonBox': GUI.WebtoonBox.checkState(),
                                           'NoDitheringBox': GUI.NoDitheringBox.checkState(),
                                           'ColorBox': GUI.ColorBox.checkState(),
                                           'customWidth': GUI.customWidth.text(),
                                           'customHeight': GUI.customHeight.text(),
                                           'GammaSlider': float(self.GammaValue) * 100})
        self.settings.sync()
        self.tray.hide()

    def handleMessage(self, message):
        MW.raise_()
        MW.activateWindow()
        if type(message) is bytes:
            message = message.decode('UTF-8')
        if not self.conversionAlive and message != 'ARISE':
            if self.needClean:
                self.needClean = False
                GUI.JobList.clear()
            if self.UnRAR:
                if self.sevenza:
                    formats = ['.cbz', '.cbr', '.cb7', '.zip', '.rar', '.7z', '.pdf']
                else:
                    formats = ['.cbz', '.cbr', '.zip', '.rar', '.pdf']
            else:
                if self.sevenza:
                    formats = ['.cbz', '.cb7', '.zip', '.7z', '.pdf']
                else:
                    formats = ['.cbz', '.zip', '.pdf']
            if os.path.isdir(message):
                GUI.JobList.addItem(message)
                GUI.JobList.scrollToBottom()
            elif os.path.isfile(message):
                extension = os.path.splitext(message)
                if extension[1].lower() in formats:
                    GUI.JobList.addItem(message)
                    GUI.JobList.scrollToBottom()
                else:
                    self.addMessage('This file type is unsupported!', 'error')

    def dragAndDrop(self, e):
        e.accept()

    def dragAndDropAccepted(self, e):
        for message in e.mimeData().urls():
            message = unquote(message.toString().replace('file:///', ''))
            if sys.platform.startswith('win'):
                message = message.replace('/', '\\')
            else:
                message = '/' + message
                if message[-1] == '/':
                    message = message[:-1]
            self.handleMessage(message)

    def forceShutdown(self):
        self.saveSettings(None)
        sys.exit(0)

    def detectKindleGen(self, startup=False):
        if not sys.platform.startswith('win'):
            try:
                os.chmod('/usr/local/bin/kindlegen', 0o755)
            except Exception:
                pass
        kindleGenExitCode = Popen('kindlegen -locale en', stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
        if kindleGenExitCode.wait() == 0:
            self.kindleGen = True
            versionCheck = Popen('kindlegen -locale en', stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
            for line in versionCheck.stdout:
                line = line.decode("utf-8")
                if 'Amazon kindlegen' in line:
                    versionCheck = line.split('V')[1].split(' ')[0]
                    if StrictVersion(versionCheck) < StrictVersion('2.9'):
                        self.addMessage('Your <a href="http://www.amazon.com/gp/feature.html?ie=UTF8&docId='
                                        '1000765211">KindleGen</a> is outdated! MOBI conversion might fail.', 'warning')
                    break
        else:
            self.kindleGen = False
            if startup:
                self.addMessage('Cannot find <a href="http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211">'
                                '<b>KindleGen</b></a>! MOBI conversion will be unavailable!', 'error')
                if sys.platform.startswith('win'):
                    self.addMessage('Download it and place EXE in KCC directory.', 'error')
                elif sys.platform.startswith('darwin'):
                    self.addMessage('Install it using <a href="http://brew.sh/">Brew</a>.', 'error')
                else:
                    self.addMessage('Download it and place executable in /usr/local/bin directory.', 'error')

    # noinspection PyArgumentList
    def __init__(self, KCCAplication, KCCWindow):
        global APP, MW, GUI
        APP = KCCAplication
        MW = KCCWindow
        GUI = self
        self.setupUi(MW)
        self.editor = KCCGUI_MetaEditor()
        self.icons = Icons()
        self.settings = QtCore.QSettings('KindleComicConverter', 'KindleComicConverter')
        self.settingsVersion = self.settings.value('settingsVersion', '', type=str)
        self.lastPath = self.settings.value('lastPath', '', type=str)
        self.lastDevice = self.settings.value('lastDevice', 0, type=int)
        self.currentFormat = self.settings.value('currentFormat', 0, type=int)
        self.startNumber = self.settings.value('startNumber', 0, type=int)
        self.options = self.settings.value('options', {'GammaSlider': 0})
        self.worker = WorkerThread()
        self.versionCheck = VersionThread()
        self.progress = ProgressThread()
        self.tray = SystemTrayIcon()
        self.conversionAlive = False
        self.needClean = True
        self.kindleGen = False
        self.GammaValue = 1.0
        self.currentMode = 1
        self.targetDirectory = ''
        if sys.platform.startswith('darwin'):
            self.listFontSize = 11
            self.statusBarFontSize = 10
            self.statusBarStyle = 'QLabel{padding-top:2px;padding-bottom:3px;}'
            self.ProgressBar.setStyleSheet('QProgressBar{font-size:13px;text-align:center;'
                                           'border:2px solid grey;border-radius:5px;}'
                                           'QProgressBar::chunk{background-color:steelblue;width:20px;}')
        elif sys.platform.startswith('linux'):
            self.listFontSize = 8
            self.statusBarFontSize = 8
            self.statusBarStyle = 'QLabel{padding-top:3px;padding-bottom:3px;}'
            self.statusBar.setStyleSheet('QStatusBar::item{border:0px;border-top:2px solid #C2C7CB;}')
        else:
            self.listFontSize = 9
            self.statusBarFontSize = 8
            self.statusBarStyle = 'QLabel{padding-top:3px;padding-bottom:3px}'
            self.statusBar.setStyleSheet('QStatusBar::item{border:0px;border-top:2px solid #C2C7CB;}')
            # Decrease priority to increase system responsiveness during conversion
            from psutil import BELOW_NORMAL_PRIORITY_CLASS
            self.p = Process(os.getpid())
            self.p.nice(BELOW_NORMAL_PRIORITY_CLASS)
            self.p.ionice(1)

        self.profiles = {
            "K. PW 3/Voyage": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 0,
                               'DefaultUpscale': True, 'Label': 'KV'},
            "Kindle PW 1/2": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 0,
                              'DefaultUpscale': False, 'Label': 'KPW'},
            "Kindle": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 0,
                       'DefaultUpscale': False, 'Label': 'K345'},
            "Kindle DX/DXG": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 2,
                              'DefaultUpscale': False, 'Label': 'KDX'},
            "Kobo Mini/Touch": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 1,
                                'DefaultUpscale': False, 'Label': 'KoMT'},
            "Kobo Glo": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 1,
                         'DefaultUpscale': False, 'Label': 'KoG'},
            "Kobo Glo HD": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 1,
                            'DefaultUpscale': False, 'Label': 'KoGHD'},
            "Kobo Aura": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 1,
                          'DefaultUpscale': False, 'Label': 'KoA'},
            "Kobo Aura HD": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 1,
                             'DefaultUpscale': True, 'Label': 'KoAHD'},
            "Kobo Aura H2O": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 1,
                              'DefaultUpscale': True, 'Label': 'KoAH2O'},
            "Other": {'Quality': False, 'ForceExpert': True, 'DefaultFormat': 1,
                      'DefaultUpscale': False, 'Label': 'OTHER'},
            "Kindle 1": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 0,
                         'DefaultUpscale': False, 'Label': 'K1'},
            "Kindle 2": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 0,
                         'DefaultUpscale': False, 'Label': 'K2'}
        }
        profilesGUI = [
            "K. PW 3/Voyage",
            "Kindle PW 1/2",
            "Kindle",
            "Separator",
            "Kobo Mini/Touch",
            "Kobo Glo",
            "Kobo Glo HD",
            "Kobo Aura",
            "Kobo Aura HD",
            "Kobo Aura H2O",
            "Separator",
            "Other",
            "Separator",
            "Kindle 1",
            "Kindle 2",
            "Kindle DX/DXG",
        ]

        statusBarLabel = QtWidgets.QLabel('<b><a href="https://kcc.iosphe.re/">HOMEPAGE</a> - <a href="https://github.'
                                          'com/ciromattia/kcc/blob/master/README.md#issues--new-features--donations">DO'
                                          'NATE</a> - <a href="http://www.mobileread.com/forums/showthread.php?t=207461'
                                          '">FORUM</a></b>')
        statusBarLabel.setAlignment(QtCore.Qt.AlignCenter)
        statusBarLabel.setStyleSheet(self.statusBarStyle)
        statusBarLabel.setOpenExternalLinks(True)
        statusBarLabelFont = QtGui.QFont()
        statusBarLabelFont.setPointSize(self.statusBarFontSize)
        statusBarLabel.setFont(statusBarLabelFont)
        GUI.statusBar.addPermanentWidget(statusBarLabel, 1)

        self.addMessage('<b>Welcome!</b>', 'info')
        self.addMessage('<b>Remember:</b> All options have additional informations in tooltips.', 'info')
        if self.startNumber < 5:
            self.addMessage('Since you are new user of <b>KCC</b> please see few '
                            '<a href="https://github.com/ciromattia/kcc/wiki/Important-tips">important tips</a>.',
                            'info')
        rarExitCode = Popen('unrar', stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
        rarExitCode = rarExitCode.wait()
        if rarExitCode == 0 or rarExitCode == 7:
            self.UnRAR = True
        else:
            self.UnRAR = False
            self.addMessage('Cannot find <a href="http://www.rarlab.com/rar_add.htm">UnRAR</a>!'
                            ' Processing of CBR/RAR files will be disabled.', 'warning')
        sevenzaExitCode = Popen('7za', stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
        sevenzaExitCode = sevenzaExitCode.wait()
        if sevenzaExitCode == 0 or sevenzaExitCode == 7:
            self.sevenza = True
        else:
            self.sevenza = False
            self.addMessage('Cannot find <a href="http://www.7-zip.org/download.html">7za</a>!'
                            ' Processing of CB7/7Z files will be disabled.', 'warning')
        self.detectKindleGen(True)

        APP.messageFromOtherInstance.connect(self.handleMessage)
        GUI.DirectoryButton.clicked.connect(self.selectDir)
        GUI.ClearButton.clicked.connect(self.clearJobs)
        GUI.FileButton.clicked.connect(self.selectFile)
        GUI.EditorButton.clicked.connect(self.selectFileMetaEditor)
        GUI.WikiButton.clicked.connect(self.openWiki)
        GUI.ConvertButton.clicked.connect(self.convertStart)
        GUI.GammaSlider.valueChanged.connect(self.changeGamma)
        GUI.GammaBox.stateChanged.connect(self.toggleGammaBox)
        GUI.WebtoonBox.stateChanged.connect(self.toggleWebtoonBox)
        GUI.DeviceBox.activated.connect(self.changeDevice)
        GUI.FormatBox.activated.connect(self.changeFormat)
        MW.progressBarTick.connect(self.updateProgressbar)
        MW.modeConvert.connect(self.modeConvert)
        MW.addMessage.connect(self.addMessage)
        MW.showDialog.connect(self.showDialog)
        MW.hideProgressBar.connect(self.hideProgressBar)
        MW.forceShutdown.connect(self.forceShutdown)
        MW.closeEvent = self.saveSettings
        MW.addTrayMessage.connect(self.tray.addTrayMessage)

        GUI.Form.setAcceptDrops(True)
        GUI.Form.dragEnterEvent = self.dragAndDrop
        GUI.Form.dropEvent = self.dragAndDropAccepted

        self.modeChange(1)
        for profile in profilesGUI:
            if profile == "Other":
                GUI.DeviceBox.addItem(self.icons.deviceOther, profile)
            elif profile == "Separator":
                GUI.DeviceBox.insertSeparator(GUI.DeviceBox.count() + 1)
            elif 'Ko' in profile:
                GUI.DeviceBox.addItem(self.icons.deviceKobo, profile)
            else:
                GUI.DeviceBox.addItem(self.icons.deviceKindle, profile)
        for f in ['MOBI/AZW3', 'EPUB', 'CBZ']:
            GUI.FormatBox.addItem(eval('self.icons.' + f.replace('/AZW3', '') + 'Format'), f)
        if self.lastDevice > GUI.DeviceBox.count():
            self.lastDevice = 0
        if profilesGUI[self.lastDevice] == "Separator":
            self.lastDevice = 0
        if self.currentFormat > GUI.FormatBox.count():
            self.currentFormat = 0
        GUI.DeviceBox.setCurrentIndex(self.lastDevice)
        self.changeDevice()
        if self.currentFormat != self.profiles[str(GUI.DeviceBox.currentText())]['DefaultFormat']:
            self.changeFormat(self.currentFormat)
        for option in self.options:
            if str(option) == "customWidth":
                GUI.customWidth.setText(str(self.options[option]))
            elif str(option) == "customHeight":
                GUI.customHeight.setText(str(self.options[option]))
            elif str(option) == "GammaSlider":
                if GUI.GammaSlider.isEnabled():
                    GUI.GammaSlider.setValue(int(self.options[option]))
                    self.changeGamma(int(self.options[option]))
            else:
                try:
                    if eval('GUI.' + str(option)).isEnabled():
                        eval('GUI.' + str(option)).setCheckState(self.options[option])
                except AttributeError:
                    pass
        self.hideProgressBar()
        self.worker.sync()
        self.versionCheck.start()
        self.tray.show()

        # Linux hack as PyQt 5.5 not hit mainstream distributions yet
        if sys.platform.startswith('linux') and StrictVersion(QtCore.qVersion()) > StrictVersion('5.4.9'):
            self.JobList.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
            self.JobList.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        MW.setWindowTitle("Kindle Comic Converter " + __version__)
        MW.show()
        MW.raise_()


class KCCGUI_MetaEditor(KCC_MetaEditor_ui.Ui_MetaEditorDialog):
    def loadData(self, file):
        self.parser = metadata.MetadataParser(file)
        if self.parser.compressor == 'rar':
            self.EditorFrame.setEnabled(False)
            self.OKButton.setEnabled(False)
            self.StatusLabel.setText('CBR metadata are read-only.')
        else:
            self.EditorFrame.setEnabled(True)
            self.OKButton.setEnabled(True)
            self.StatusLabel.setText('Separate authors with a comma.')
        for field in (self.SeriesLine, self.VolumeLine, self.NumberLine, self.MUidLine):
            field.setText(self.parser.data[field.objectName()[:-4]])
        for field in (self.WriterLine, self.PencillerLine, self.InkerLine, self.ColoristLine):
            field.setText(', '.join(self.parser.data[field.objectName()[:-4] + 's']))
        if self.SeriesLine.text() == '':
            self.SeriesLine.setText(file.split('\\')[-1].split('/')[-1].split('.')[0])

    def saveData(self):
        for field in (self.VolumeLine, self.NumberLine, self.MUidLine):
            if field.text().isnumeric() or self.cleanData(field.text()) == '':
                self.parser.data[field.objectName()[:-4]] = self.cleanData(field.text())
            else:
                self.StatusLabel.setText(field.objectName()[:-4] + ' field must be a number.')
                break
        else:
            self.parser.data['Series'] = self.cleanData(self.SeriesLine.text())
            for field in (self.WriterLine, self.PencillerLine, self.InkerLine, self.ColoristLine):
                values = self.cleanData(field.text()).split(',')
                tmpData = []
                for value in values:
                    if self.cleanData(value) != '':
                        tmpData.append(self.cleanData(value))
                self.parser.data[field.objectName()[:-4] + 's'] = tmpData
            try:
                self.parser.saveXML()
            except Exception as err:
                _, _, traceback = sys.exc_info()
                GUI.showDialog("Failed to save metadata!\n\n%s\n\nTraceback:\n%s"
                               % (str(err), sanitizeTrace(traceback)), 'error')
            self.ui.close()

    def cleanData(self, s):
        return escape(s.strip())

    def __init__(self):
        self.ui = QtWidgets.QDialog()
        self.parser = None
        self.setupUi(self.ui)
        self.ui.setWindowFlags(self.ui.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.OKButton.clicked.connect(self.saveData)
        self.CancelButton.clicked.connect(self.ui.close)
