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
from time import sleep
from shutil import move
from subprocess import STDOUT, PIPE
from PyQt5 import QtGui, QtCore, QtWidgets, QtNetwork
from xml.dom.minidom import parse
from psutil import Popen, Process
from copy import copy
from distutils.version import StrictVersion
from xml.sax.saxutils import escape
from raven import Client
from .shared import md5Checksum, HTMLStripper, sanitizeTrace, saferRemove
from . import __version__
from . import comic2ebook
from . import metadata
from . import kindle
from . import KCC_ui
from . import KCC_ui_editor


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

        options.profile = GUI.profiles[str(GUI.deviceBox.currentText())]['Label']
        options.format = str(GUI.formatBox.currentText()).replace('/AZW3', '')
        if GUI.mangaBox.isChecked():
            options.righttoleft = True
        if GUI.rotateBox.checkState() == 1:
            options.splitter = 2
        elif GUI.rotateBox.checkState() == 2:
            options.splitter = 1
        if GUI.qualityBox.isChecked():
            options.autoscale = True
        if GUI.webtoonBox.isChecked():
            options.webtoon = True
        if GUI.upscaleBox.checkState() == 1:
            options.stretch = True
        elif GUI.upscaleBox.checkState() == 2:
            options.upscale = True
        if GUI.gammaBox.isChecked() and float(GUI.gammaValue) > 0.09:
            options.gamma = float(GUI.gammaValue)
        if GUI.borderBox.checkState() == 1:
            options.white_borders = True
        elif GUI.borderBox.checkState() == 2:
            options.black_borders = True
        if GUI.outputSplit.isChecked():
            options.batchsplit = 2
        if GUI.colorBox.isChecked():
            options.forcecolor = True
        if GUI.currentMode > 2:
            options.customwidth = str(GUI.widthBox.value())
            options.customheight = str(GUI.heightBox.value())

        for i in range(GUI.jobList.count()):
            # Make sure that we don't consider any system message as job to do
            if GUI.jobList.item(i).icon().isNull():
                currentJobs.append(str(GUI.jobList.item(i).text()))
        GUI.jobList.clear()
        for job in currentJobs:
            sleep(0.5)
            if not self.conversionAlive:
                self.clean()
                return
            self.errors = False
            MW.addMessage.emit('<b>Source:</b> ' + job, 'info', False)
            if str(GUI.formatBox.currentText()) == 'CBZ':
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
                if len(err.args) == 1:
                    MW.showDialog.emit("Error during conversion %s:\n\n%s\n\nTraceback:\n%s"
                                       % (jobargv[-1], str(err), sanitizeTrace(traceback)), 'error')
                else:
                    MW.showDialog.emit("Error during conversion %s:\n\n%s\n\nTraceback:\n%s"
                                       % (jobargv[-1], str(err.args[0]), err.args[1]), 'error')
                    GUI.sentry.extra_context({'realTraceback': err.args[1]})
                if ' is corrupted.' not in str(err):
                    GUI.sentry.captureException()
                MW.addMessage.emit('Error during conversion! Please consult '
                                   '<a href="https://github.com/ciromattia/kcc/wiki/Error-messages">wiki</a> '
                                   'for more details.', 'error', False)
                MW.addTrayMessage.emit('Error during conversion!', 'Critical')
            if not self.conversionAlive:
                if 'outputPath' in locals():
                    for item in outputPath:
                        if os.path.exists(item):
                            saferRemove(item)
                self.clean()
                return
            if not self.errors:
                GUI.progress.content = ''
                if str(GUI.formatBox.currentText()) == 'CBZ':
                    MW.addMessage.emit('Creating CBZ files... <b>Done!</b>', 'info', True)
                else:
                    MW.addMessage.emit('Creating EPUB files... <b>Done!</b>', 'info', True)
                if str(GUI.formatBox.currentText()) == 'MOBI/AZW3':
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
                                saferRemove(item)
                            if os.path.exists(item.replace('.epub', '.mobi')):
                                saferRemove(item.replace('.epub', '.mobi'))
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
                                saferRemove(mobiPath + '_toclean')
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
                                MW.addMessage.emit('Kindle detected. Uploading covers... <b>Done!</b>', 'info', False)
                        else:
                            GUI.progress.content = ''
                            for item in outputPath:
                                mobiPath = item.replace('.epub', '.mobi')
                                if os.path.exists(mobiPath):
                                    saferRemove(mobiPath)
                                if os.path.exists(mobiPath + '_toclean'):
                                    saferRemove(mobiPath + '_toclean')
                            MW.addMessage.emit('Failed to process MOBI file!', 'error', False)
                            MW.addTrayMessage.emit('Failed to process MOBI file!', 'Critical')
                    else:
                        GUI.progress.content = ''
                        epubSize = (os.path.getsize(self.kindlegenErrorCode[2])) // 1024 // 1024
                        for item in outputPath:
                            if os.path.exists(item):
                                saferRemove(item)
                            if os.path.exists(item.replace('.epub', '.mobi')):
                                saferRemove(item.replace('.epub', '.mobi'))
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


class KCCGUI(KCC_ui.Ui_mainWindow):
    def selectDir(self):
        if self.needClean:
            self.needClean = False
            GUI.jobList.clear()
        dname = QtWidgets.QFileDialog.getExistingDirectory(MW, 'Select directory', self.lastPath)
        if dname != '':
            if sys.platform.startswith('win'):
                dname = dname.replace('/', '\\')
            self.lastPath = os.path.abspath(os.path.join(dname, os.pardir))
            GUI.jobList.addItem(dname)
            GUI.jobList.scrollToBottom()

    def selectFile(self):
        if self.needClean:
            self.needClean = False
            GUI.jobList.clear()
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
                GUI.jobList.addItem(fname)
                GUI.jobList.scrollToBottom()

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
                GUI.sentry.captureException()
                self.showDialog("Failed to parse metadata!\n\n%s\n\nTraceback:\n%s"
                                % (str(err), sanitizeTrace(traceback)), 'error')
            else:
                self.editor.ui.exec_()

    def clearJobs(self):
        GUI.jobList.clear()

    # noinspection PyCallByClass,PyTypeChecker
    def openWiki(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/ciromattia/kcc/wiki'))

    def modeChange(self, mode):
        if mode == 1:
            self.currentMode = 1
            GUI.gammaWidget.setVisible(False)
            GUI.customWidget.setVisible(False)
        elif mode == 2:
            self.currentMode = 2
            GUI.gammaWidget.setVisible(True)
            GUI.customWidget.setVisible(False)
        elif mode == 3:
            self.currentMode = 3
            GUI.gammaWidget.setVisible(True)
            GUI.customWidget.setVisible(True)

    def modeConvert(self, enable):
        if enable < 1:
            status = False
        else:
            status = True
        GUI.editorButton.setEnabled(status)
        GUI.wikiButton.setEnabled(status)
        GUI.deviceBox.setEnabled(status)
        GUI.directoryButton.setEnabled(status)
        GUI.clearButton.setEnabled(status)
        GUI.fileButton.setEnabled(status)
        GUI.formatBox.setEnabled(status)
        GUI.optionWidget.setEnabled(status)
        GUI.gammaWidget.setEnabled(status)
        GUI.customWidget.setEnabled(status)
        GUI.convertButton.setEnabled(True)
        if enable == 1:
            self.conversionAlive = False
            self.worker.sync()
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/Other/icons/convert.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            GUI.convertButton.setIcon(icon)
            GUI.convertButton.setText('Convert')
            GUI.centralWidget.setAcceptDrops(True)
        elif enable == 0:
            self.conversionAlive = True
            self.worker.sync()
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/Other/icons/clear.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            GUI.convertButton.setIcon(icon)
            GUI.convertButton.setText('Abort')
            GUI.centralWidget.setAcceptDrops(False)
        elif enable == -1:
            self.conversionAlive = True
            self.worker.sync()
            GUI.convertButton.setEnabled(False)
            GUI.centralWidget.setAcceptDrops(False)

    def togglegammaBox(self, value):
        if value:
            if self.currentMode != 3:
                self.modeChange(2)
        else:
            if self.currentMode != 3:
                self.modeChange(1)

    def togglewebtoonBox(self, value):
        if value:
            GUI.qualityBox.setEnabled(False)
            GUI.qualityBox.setChecked(False)
            GUI.mangaBox.setEnabled(False)
            GUI.mangaBox.setChecked(False)
            GUI.rotateBox.setEnabled(False)
            GUI.rotateBox.setChecked(False)
            GUI.upscaleBox.setEnabled(False)
            GUI.upscaleBox.setChecked(True)
        else:
            profile = GUI.profiles[str(GUI.deviceBox.currentText())]
            if profile['PVOptions']:
                GUI.qualityBox.setEnabled(True)
            GUI.mangaBox.setEnabled(True)
            GUI.rotateBox.setEnabled(True)
            GUI.upscaleBox.setEnabled(True)

    def changeGamma(self, value):
        valueRaw = int(5 * round(float(value) / 5))
        value = '%.2f' % (float(valueRaw) / 100)
        if float(value) <= 0.09:
            GUI.gammaLabel.setText('Gamma: Auto')
        else:
            GUI.gammaLabel.setText('Gamma: ' + str(value))
        GUI.gammaSlider.setValue(valueRaw)
        self.gammaValue = value

    def changeDevice(self):
        profile = GUI.profiles[str(GUI.deviceBox.currentText())]
        if profile['ForceExpert']:
            self.modeChange(3)
        elif GUI.gammaBox.isChecked():
            self.modeChange(2)
        else:
            self.modeChange(1)
        self.changeFormat()
        GUI.gammaSlider.setValue(0)
        self.changeGamma(0)
        GUI.qualityBox.setEnabled(profile['PVOptions'])
        GUI.upscaleBox.setChecked(profile['DefaultUpscale'])
        if not profile['PVOptions']:
            GUI.qualityBox.setChecked(False)
        if str(GUI.deviceBox.currentText()) == 'Other':
            self.addMessage('<a href="https://github.com/ciromattia/kcc/wiki/NonKindle-devices">'
                            'List of supported Non-Kindle devices.</a>', 'info')

    def changeFormat(self, outputFormat=None):
        profile = GUI.profiles[str(GUI.deviceBox.currentText())]
        if outputFormat is not None:
            GUI.formatBox.setCurrentIndex(outputFormat)
        else:
            GUI.formatBox.setCurrentIndex(profile['DefaultFormat'])
        GUI.qualityBox.setEnabled(profile['PVOptions'])
        if str(GUI.formatBox.currentText()) == 'MOBI/AZW3':
            GUI.outputSplit.setEnabled(True)
        else:
            GUI.outputSplit.setEnabled(False)
            GUI.outputSplit.setChecked(False)

    def stripTags(self, html):
        s = HTMLStripper()
        s.feed(html)
        return s.get_data()

    def addMessage(self, message, icon, replace=False):
        if icon != '':
            icon = eval('self.icons.' + icon)
            item = QtWidgets.QListWidgetItem(icon, '   ' + self.stripTags(message))
        else:
            item = QtWidgets.QListWidgetItem('   ' + self.stripTags(message))
        if replace:
            GUI.jobList.takeItem(GUI.jobList.count() - 1)
        # Due to lack of HTML support in QListWidgetItem we overlay text field with QLabel
        # We still fill original text field with transparent content to trigger creation of horizontal scrollbar
        item.setForeground(QtGui.QColor('transparent'))
        label = QtWidgets.QLabel(message)
        label.setStyleSheet('background-image:url('');background-color:rgba(0,0,0,0);')
        label.setOpenExternalLinks(True)
        GUI.jobList.addItem(item)
        GUI.jobList.setItemWidget(item, label)
        GUI.jobList.scrollToBottom()

    def showDialog(self, message, kind):
        if kind == 'error':
            QtWidgets.QMessageBox.critical(MW, 'KCC - Error', message, QtWidgets.QMessageBox.Ok)
        elif kind == 'question':
            GUI.versionCheck.setAnswer(QtWidgets.QMessageBox.question(MW, 'KCC - Question', message,
                                                                          QtWidgets.QMessageBox.Yes,
                                                                          QtWidgets.QMessageBox.No))

    def updateProgressbar(self, command):
        if command == 'tick':
            GUI.progressBar.setValue(GUI.progressBar.value() + 1)
        elif command.isdigit():
            GUI.progressBar.setMaximum(int(command) - 1)
            GUI.toolWidget.hide()
            GUI.progressBar.reset()
            GUI.progressBar.show()
        else:
            GUI.progressBar.setFormat(command)

    def hideProgressBar(self):
        GUI.progressBar.hide()
        GUI.toolWidget.show()

    def convertStart(self):
        if self.conversionAlive:
            GUI.convertButton.setEnabled(False)
            self.addMessage('Process will be interrupted. Please wait.', 'warning')
            self.conversionAlive = False
            self.worker.sync()
        else:
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
                GUI.jobList.clear()
            if GUI.jobList.count() == 0:
                self.addMessage('No files selected! Please choose files to convert.', 'error')
                self.needClean = True
                return
            if self.currentMode > 2 and (GUI.widthBox.value() == 0 or GUI.heightBox.value() == 0):
                GUI.jobList.clear()
                self.addMessage('Target resolution is not set!', 'error')
                self.needClean = True
                return
            if str(GUI.formatBox.currentText()) == 'MOBI/AZW3' and not self.kindleGen:
                self.detectKindleGen()
                if not self.kindleGen:
                    GUI.jobList.clear()
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

    def saveSettings(self, event):
        if self.conversionAlive:
            GUI.convertButton.setEnabled(False)
            self.addMessage('Process will be interrupted. Please wait.', 'warning')
            self.conversionAlive = False
            self.worker.sync()
            event.ignore()
        if not GUI.convertButton.isEnabled():
            event.ignore()
        self.settings.setValue('settingsVersion', __version__)
        self.settings.setValue('lastPath', self.lastPath)
        self.settings.setValue('lastDevice', GUI.deviceBox.currentIndex())
        self.settings.setValue('currentFormat', GUI.formatBox.currentIndex())
        self.settings.setValue('startNumber', self.startNumber + 1)
        self.settings.setValue('windowSize', str(MW.size().width()) + 'x' + str(MW.size().height()))
        self.settings.setValue('options', {'mangaBox': GUI.mangaBox.checkState(),
                                           'rotateBox': GUI.rotateBox.checkState(),
                                           'qualityBox': GUI.qualityBox.checkState(),
                                           'gammaBox': GUI.gammaBox.checkState(),
                                           'upscaleBox': GUI.upscaleBox.checkState(),
                                           'borderBox': GUI.borderBox.checkState(),
                                           'webtoonBox': GUI.webtoonBox.checkState(),
                                           'outputSplit': GUI.outputSplit.checkState(),
                                           'colorBox': GUI.colorBox.checkState(),
                                           'widthBox': GUI.widthBox.value(),
                                           'heightBox': GUI.heightBox.value(),
                                           'gammaSlider': float(self.gammaValue) * 100})
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
                GUI.jobList.clear()
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
                GUI.jobList.addItem(message)
                GUI.jobList.scrollToBottom()
            elif os.path.isfile(message):
                extension = os.path.splitext(message)
                if extension[1].lower() in formats:
                    GUI.jobList.addItem(message)
                    GUI.jobList.scrollToBottom()
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
        self.windowSize = self.settings.value('windowSize', '0x0', type=str)
        self.options = self.settings.value('options', {'gammaSlider': 0})
        self.worker = WorkerThread()
        self.versionCheck = VersionThread()
        self.progress = ProgressThread()
        self.tray = SystemTrayIcon()
        self.conversionAlive = False
        self.needClean = True
        self.kindleGen = False
        self.gammaValue = 1.0
        self.currentMode = 1
        self.targetDirectory = ''
        self.sentry = Client(release=__version__)
        if sys.platform.startswith('win'):
            from psutil import BELOW_NORMAL_PRIORITY_CLASS
            self.p = Process(os.getpid())
            self.p.nice(BELOW_NORMAL_PRIORITY_CLASS)
            self.p.ionice(1)
        elif sys.platform.startswith('linux'):
            APP.setStyle('fusion')
            if self.windowSize == '0x0':
                MW.resize(500, 500)
        elif sys.platform.startswith('darwin'):
            for element in ['editorButton', 'wikiButton', 'directoryButton', 'clearButton', 'fileButton', 'deviceBox',
                            'convertButton', 'formatBox']:
                eval('GUI.' + element).setMinimumSize(QtCore.QSize(0, 0))
            GUI.gridLayout.setContentsMargins(-1, -1, -1, -1)
            for element in ['gridLayout_2', 'gridLayout_3', 'gridLayout_4', 'horizontalLayout', 'horizontalLayout_2']:
                eval('GUI.' + element).setContentsMargins(-1, 0, -1, 0)
            if self.windowSize == '0x0':
                MW.resize(500, 500)

        self.profiles = {
            "Kindle Oasis": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                             'DefaultUpscale': True, 'Label': 'KV'},
            "Kindle Voyage": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                              'DefaultUpscale': True, 'Label': 'KV'},
            "Kindle PW 3": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                            'DefaultUpscale': True, 'Label': 'KV'},
            "Kindle PW 1/2": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                              'DefaultUpscale': False, 'Label': 'KPW'},
            "Kindle": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                       'DefaultUpscale': False, 'Label': 'K45'},
            "Kindle DX/DXG": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 2,
                              'DefaultUpscale': False, 'Label': 'KDX'},
            "Kobo Mini/Touch": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                                'DefaultUpscale': False, 'Label': 'KoMT'},
            "Kobo Glo": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                         'DefaultUpscale': False, 'Label': 'KoG'},
            "Kobo Glo HD": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                            'DefaultUpscale': False, 'Label': 'KoGHD'},
            "Kobo Aura": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                          'DefaultUpscale': False, 'Label': 'KoA'},
            "Kobo Aura HD": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                             'DefaultUpscale': True, 'Label': 'KoAHD'},
            "Kobo Aura H2O": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                              'DefaultUpscale': True, 'Label': 'KoAH2O'},
            "Kobo Aura ONE": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                              'DefaultUpscale': True, 'Label': 'KoAO'},
            "Other": {'PVOptions': False, 'ForceExpert': True, 'DefaultFormat': 1,
                      'DefaultUpscale': False, 'Label': 'OTHER'},
            "Kindle 1": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 0,
                         'DefaultUpscale': False, 'Label': 'K1'},
            "Kindle 2": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 0,
                         'DefaultUpscale': False, 'Label': 'K2'},
            "Kindle 3": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 0,
                         'DefaultUpscale': False, 'Label': 'K3'},
        }
        profilesGUI = [
            "Kindle Oasis",
            "Kindle Voyage",
            "Kindle PW 3",
            "Kindle PW 1/2",
            "Kindle",
            "Separator",
            "Kobo Aura ONE",
            "Kobo Aura H2O",
            "Kobo Aura HD",
            "Kobo Aura",
            "Kobo Glo HD",
            "Kobo Glo",
            "Kobo Mini/Touch",
            "Separator",
            "Other",
            "Separator",
            "Kindle DX/DXG",
            "Kindle 3",
            "Kindle 2",
            "Kindle 1",
        ]

        statusBarLabel = QtWidgets.QLabel('<b><a href="https://kcc.iosphe.re/">HOMEPAGE</a> - <a href="https://github.'
                                          'com/ciromattia/kcc/blob/master/README.md#issues--new-features--donations">DO'
                                          'NATE</a> - <a href="http://www.mobileread.com/forums/showthread.php?t=207461'
                                          '">FORUM</a></b>')
        statusBarLabel.setAlignment(QtCore.Qt.AlignCenter)
        statusBarLabel.setOpenExternalLinks(True)
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
        GUI.directoryButton.clicked.connect(self.selectDir)
        GUI.clearButton.clicked.connect(self.clearJobs)
        GUI.fileButton.clicked.connect(self.selectFile)
        GUI.editorButton.clicked.connect(self.selectFileMetaEditor)
        GUI.wikiButton.clicked.connect(self.openWiki)
        GUI.convertButton.clicked.connect(self.convertStart)
        GUI.gammaSlider.valueChanged.connect(self.changeGamma)
        GUI.gammaBox.stateChanged.connect(self.togglegammaBox)
        GUI.webtoonBox.stateChanged.connect(self.togglewebtoonBox)
        GUI.deviceBox.activated.connect(self.changeDevice)
        GUI.formatBox.activated.connect(self.changeFormat)
        MW.progressBarTick.connect(self.updateProgressbar)
        MW.modeConvert.connect(self.modeConvert)
        MW.addMessage.connect(self.addMessage)
        MW.showDialog.connect(self.showDialog)
        MW.hideProgressBar.connect(self.hideProgressBar)
        MW.forceShutdown.connect(self.forceShutdown)
        MW.closeEvent = self.saveSettings
        MW.addTrayMessage.connect(self.tray.addTrayMessage)

        GUI.centralWidget.setAcceptDrops(True)
        GUI.centralWidget.dragEnterEvent = self.dragAndDrop
        GUI.centralWidget.dropEvent = self.dragAndDropAccepted

        self.modeChange(1)
        for profile in profilesGUI:
            if profile == "Other":
                GUI.deviceBox.addItem(self.icons.deviceOther, profile)
            elif profile == "Separator":
                GUI.deviceBox.insertSeparator(GUI.deviceBox.count() + 1)
            elif 'Ko' in profile:
                GUI.deviceBox.addItem(self.icons.deviceKobo, profile)
            else:
                GUI.deviceBox.addItem(self.icons.deviceKindle, profile)
        for f in ['MOBI/AZW3', 'EPUB', 'CBZ']:
            GUI.formatBox.addItem(eval('self.icons.' + f.replace('/AZW3', '') + 'Format'), f)
        if self.lastDevice > GUI.deviceBox.count():
            self.lastDevice = 0
        if profilesGUI[self.lastDevice] == "Separator":
            self.lastDevice = 0
        if self.currentFormat > GUI.formatBox.count():
            self.currentFormat = 0
        GUI.deviceBox.setCurrentIndex(self.lastDevice)
        self.changeDevice()
        if self.currentFormat != self.profiles[str(GUI.deviceBox.currentText())]['DefaultFormat']:
            self.changeFormat(self.currentFormat)
        for option in self.options:
            if str(option) == "widthBox":
                GUI.widthBox.setValue(int(self.options[option]))
            elif str(option) == "heightBox":
                GUI.heightBox.setValue(int(self.options[option]))
            elif str(option) == "gammaSlider":
                if GUI.gammaSlider.isEnabled():
                    GUI.gammaSlider.setValue(int(self.options[option]))
                    self.changeGamma(int(self.options[option]))
            else:
                try:
                    if eval('GUI.' + str(option)).isEnabled():
                        eval('GUI.' + str(option)).setCheckState(self.options[option])
                except AttributeError:
                    pass
        self.worker.sync()
        self.versionCheck.start()
        self.tray.show()

        if self.windowSize != '0x0':
            x, y = self.windowSize.split('x')
            MW.resize(int(x), int(y))
        MW.setWindowTitle("Kindle Comic Converter " + __version__)
        MW.show()
        MW.raise_()


class KCCGUI_MetaEditor(KCC_ui_editor.Ui_editorDialog):
    def loadData(self, file):
        self.parser = metadata.MetadataParser(file)
        if self.parser.compressor == 'rar':
            self.editorWidget.setEnabled(False)
            self.okButton.setEnabled(False)
            self.statusLabel.setText('CBR metadata are read-only.')
        else:
            self.editorWidget.setEnabled(True)
            self.okButton.setEnabled(True)
            self.statusLabel.setText('Separate authors with a comma.')
        for field in (self.seriesLine, self.volumeLine, self.numberLine, self.muidLine):
            if field.objectName() == 'muidLine':
                field.setText(self.parser.data['MUid'])
            else:
                field.setText(self.parser.data[field.objectName().capitalize()[:-4]])
        for field in (self.writerLine, self.pencillerLine, self.inkerLine, self.coloristLine):
            field.setText(', '.join(self.parser.data[field.objectName().capitalize()[:-4] + 's']))
        if self.seriesLine.text() == '':
            self.seriesLine.setText(file.split('\\')[-1].split('/')[-1].split('.')[0])

    def saveData(self):
        for field in (self.volumeLine, self.numberLine, self.muidLine):
            if field.text().isnumeric() or self.cleanData(field.text()) == '':
                if field.objectName() == 'muidLine':
                    self.parser.data['MUid'] = self.cleanData(field.text())
                else:
                    self.parser.data[field.objectName().capitalize()[:-4]] = self.cleanData(field.text())
            else:
                self.statusLabel.setText(field.objectName().capitalize()[:-4] + ' field must be a number.')
                break
        else:
            self.parser.data['Series'] = self.cleanData(self.seriesLine.text())
            for field in (self.writerLine, self.pencillerLine, self.inkerLine, self.coloristLine):
                values = self.cleanData(field.text()).split(',')
                tmpData = []
                for value in values:
                    if self.cleanData(value) != '':
                        tmpData.append(self.cleanData(value))
                self.parser.data[field.objectName().capitalize()[:-4] + 's'] = tmpData
            try:
                self.parser.saveXML()
            except Exception as err:
                _, _, traceback = sys.exc_info()
                GUI.sentry.captureException()
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
        self.okButton.clicked.connect(self.saveData)
        self.cancelButton.clicked.connect(self.ui.close)
        if sys.platform.startswith('linux'):
            self.ui.resize(450, 260)
            self.ui.setMinimumSize(QtCore.QSize(450, 260))
        elif sys.platform.startswith('darwin'):
            self.ui.resize(450, 310)
            self.ui.setMinimumSize(QtCore.QSize(450, 310))
