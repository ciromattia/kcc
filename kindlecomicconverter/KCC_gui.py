# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2019 Pawel Jastrzebski <pawelj@iosphe.re>
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
import re
import sys
from urllib.parse import unquote
from time import sleep
from shutil import move, rmtree
from subprocess import STDOUT, PIPE

import requests
# noinspection PyUnresolvedReferences
from PySide6 import QtGui, QtCore, QtWidgets, QtNetwork
from PySide6.QtCore import Qt
from xml.sax.saxutils import escape
from psutil import Process
from copy import copy
from distutils.version import StrictVersion
from raven import Client
from tempfile import gettempdir

from .shared import HTMLStripper, sanitizeTrace, walkLevel, subprocess_run
from . import __version__
from . import comic2ebook
from . import metadata
from . import kindle
from . import KCC_ui
from . import KCC_ui_editor


class QApplicationMessaging(QtWidgets.QApplication):
    messageFromOtherInstance = QtCore.Signal(bytes)

    def __init__(self, argv):
        QtWidgets.QApplication.__init__(self, argv)
        self._key = 'KCC'
        self._timeout = 1000
        self._locked = False
        socket = QtNetwork.QLocalSocket(self)
        socket.connectToServer(self._key, QtCore.QIODeviceBase.OpenModeFlag.WriteOnly)
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
        if e.type() == QtCore.QEvent.Type.FileOpen:
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
        socket.connectToServer(self._key, QtCore.QIODeviceBase.OpenModeFlag.WriteOnly)
        socket.waitForConnected(self._timeout)
        socket.write(bytes(message, 'UTF-8'))
        socket.waitForBytesWritten(self._timeout)
        socket.disconnectFromServer()


class QMainWindowKCC(QtWidgets.QMainWindow):
    progressBarTick = QtCore.Signal(str)
    modeConvert = QtCore.Signal(int)
    addMessage = QtCore.Signal(str, str, bool)
    addTrayMessage = QtCore.Signal(str, str)
    showDialog = QtCore.Signal(str, str)
    hideProgressBar = QtCore.Signal()
    forceShutdown = QtCore.Signal()


class Icons:
    def __init__(self):
        self.deviceKindle = QtGui.QIcon()
        self.deviceKindle.addPixmap(QtGui.QPixmap(":/Devices/icons/Kindle.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.deviceKobo = QtGui.QIcon()
        self.deviceKobo.addPixmap(QtGui.QPixmap(":/Devices/icons/Kobo.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.deviceOther = QtGui.QIcon()
        self.deviceOther.addPixmap(QtGui.QPixmap(":/Devices/icons/Other.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        self.MOBIFormat = QtGui.QIcon()
        self.MOBIFormat.addPixmap(QtGui.QPixmap(":/Formats/icons/MOBI.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.CBZFormat = QtGui.QIcon()
        self.CBZFormat.addPixmap(QtGui.QPixmap(":/Formats/icons/CBZ.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.EPUBFormat = QtGui.QIcon()
        self.EPUBFormat.addPixmap(QtGui.QPixmap(":/Formats/icons/EPUB.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        self.info = QtGui.QIcon()
        self.info.addPixmap(QtGui.QPixmap(":/Status/icons/info.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.warning = QtGui.QIcon()
        self.warning.addPixmap(QtGui.QPixmap(":/Status/icons/warning.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.error = QtGui.QIcon()
        self.error.addPixmap(QtGui.QPixmap(":/Status/icons/error.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        self.programIcon = QtGui.QIcon()
        self.programIcon.addPixmap(QtGui.QPixmap(":/Icon/icons/comic2ebook.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)


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
            json_parser = requests.get("https://api.github.com/repos/ciromattia/kcc/releases/latest").json()

            html_url = json_parser["html_url"]
            latest_version = json_parser["tag_name"]
            latest_version = re.sub(r'^v', "", latest_version)

            if ("b" not in __version__ and StrictVersion(latest_version) > StrictVersion(__version__)) \
                    or ("b" in __version__
                        and StrictVersion(latest_version) >= StrictVersion(re.sub(r'b.*', '', __version__))):
                MW.addMessage.emit('<a href="' + html_url + '"><b>The new version is available!</b></a>', 'warning',
                                   False)
        except Exception:
            return

    def setAnswer(self, dialoganswer):
        self.answer = dialoganswer


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

    # noinspection PyUnboundLocalVariable
    def run(self):
        MW.modeConvert.emit(0)

        parser = comic2ebook.makeParser()
        options = parser.parse_args()
        argv = ''
        currentJobs = []

        options.profile = GUI.profiles[str(GUI.deviceBox.currentText())]['Label']
        gui_current_format = GUI.formats[str(GUI.formatBox.currentText())]['format']
        options.format = gui_current_format
        if GUI.mangaBox.isChecked():
            options.righttoleft = True
        if GUI.rotateBox.checkState() == Qt.CheckState.PartiallyChecked:
            options.splitter = 2
        elif GUI.rotateBox.checkState() == Qt.CheckState.Checked:
            options.splitter = 1
        if GUI.qualityBox.checkState() == Qt.CheckState.PartiallyChecked:
            options.autoscale = True
        elif GUI.qualityBox.checkState() == Qt.CheckState.Checked:
            options.hq = True
        if GUI.webtoonBox.isChecked():
            options.webtoon = True
        if GUI.upscaleBox.checkState() == Qt.CheckState.PartiallyChecked:
            options.stretch = True
        elif GUI.upscaleBox.checkState() == Qt.CheckState.Checked:
            options.upscale = True
        if GUI.gammaBox.isChecked() and float(GUI.gammaValue) > 0.09:
            options.gamma = float(GUI.gammaValue)
        options.cropping = GUI.croppingBox.checkState().value
        if GUI.croppingBox.checkState() != Qt.CheckState.Unchecked:
            options.croppingp = float(GUI.croppingPowerValue)
        if GUI.borderBox.checkState() == Qt.CheckState.PartiallyChecked:
            options.white_borders = True
        elif GUI.borderBox.checkState() == Qt.CheckState.Checked:
            options.black_borders = True
        if GUI.outputSplit.isChecked():
            options.batchsplit = 2
        if GUI.colorBox.isChecked():
            options.forcecolor = True
        if GUI.maximizeStrips.isChecked():
            options.maximizestrips = True
        if GUI.disableProcessingBox.isChecked():
            options.noprocessing = True
        if GUI.deleteBox.isChecked():
            options.delete = True
        if GUI.dedupeCoverBox.isChecked():
            options.dedupecover = True
        if GUI.mozJpegBox.checkState() == Qt.CheckState.PartiallyChecked:
            options.forcepng = True
        elif GUI.mozJpegBox.checkState() == Qt.CheckState.Checked:
            options.mozjpeg = True
        if GUI.currentMode > 2:
            options.customwidth = str(GUI.widthBox.value())
            options.customheight = str(GUI.heightBox.value())
        if GUI.targetDirectory != '':
            options.output = GUI.targetDirectory

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
            if gui_current_format == 'CBZ':
                MW.addMessage.emit('Creating CBZ files', 'info', False)
                GUI.progress.content = 'Creating CBZ files'
            else:
                MW.addMessage.emit('Creating EPUB files', 'info', False)
                GUI.progress.content = 'Creating EPUB files'
            jobargv = list(argv)
            jobargv.append(job)
            try:
                comic2ebook.options = comic2ebook.checkOptions(copy(options))
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
                            os.remove(item)
                self.clean()
                return
            if not self.errors:
                GUI.progress.content = ''
                if gui_current_format == 'CBZ':
                    MW.addMessage.emit('Creating CBZ files... <b>Done!</b>', 'info', True)
                else:
                    MW.addMessage.emit('Creating EPUB files... <b>Done!</b>', 'info', True)
                if 'MOBI' in gui_current_format:
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
                                MW.addMessage.emit('Kindle detected. Uploading covers... <b>Done!</b>', 'info', False)
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
            self.setIcon(GUI.icons.programIcon)
            self.activated.connect(self.catchClicks)

    def catchClicks(self):
        MW.showNormal()
        MW.raise_()
        MW.activateWindow()

    def addTrayMessage(self, message, icon):
        icon = getattr(QtWidgets.QSystemTrayIcon.MessageIcon, icon)
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
        if self.tar or self.sevenzip:
            fnames = QtWidgets.QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                            'Comic (*.cbz *.cbr *.cb7 *.zip *.rar *.7z *.pdf);;All (*.*)')
        else:
            fnames = QtWidgets.QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                            'Comic (*.pdf);;All (*.*)')
        for fname in fnames[0]:
            if fname != '':
                if sys.platform.startswith('win'):
                    fname = fname.replace('/', '\\')
                self.lastPath = os.path.abspath(os.path.join(fname, os.pardir))
                GUI.jobList.addItem(fname)
                GUI.jobList.scrollToBottom()

    def selectFileMetaEditor(self):
        sname = ''
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            dname = QtWidgets.QFileDialog.getExistingDirectory(MW, 'Select directory', self.lastPath)
            if dname != '':
                sname = os.path.join(dname, 'ComicInfo.xml')
                if sys.platform.startswith('win'):
                    sname = sname.replace('/', '\\')
                self.lastPath = os.path.abspath(sname)
        else:
            if self.sevenzip:
                fname = QtWidgets.QFileDialog.getOpenFileName(MW, 'Select file', self.lastPath,
                                                              'Comic (*.cbz *.cbr *.cb7)')
            else:
                fname = ['']
                self.showDialog("Editor is disabled due to a lack of 7z.", 'error')
                self.addMessage('<a href="https://github.com/ciromattia/kcc#7-zip">Install 7z (link)</a>'
                ' to enable metadata editing.', 'warning')
            if fname[0] != '':
                if sys.platform.startswith('win'):
                    sname = fname[0].replace('/', '\\')
                else:
                    sname = fname[0]
                self.lastPath = os.path.abspath(os.path.join(sname, os.pardir))
        if sname != '':
            try:
                self.editor.loadData(sname)
            except Exception as err:
                _, _, traceback = sys.exc_info()
                GUI.sentry.captureException()
                self.showDialog("Failed to parse metadata!\n\n%s\n\nTraceback:\n%s"
                                % (str(err), sanitizeTrace(traceback)), 'error')
            else:
                self.editor.ui.exec_()

    def clearJobs(self):
        GUI.jobList.clear()

    def openWiki(self):
        # noinspection PyCallByClass
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
            icon.addPixmap(QtGui.QPixmap(":/Other/icons/convert.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            GUI.convertButton.setIcon(icon)
            GUI.convertButton.setText('Convert')
            GUI.centralWidget.setAcceptDrops(True)
        elif enable == 0:
            self.conversionAlive = True
            self.worker.sync()
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/Other/icons/clear.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
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

    def togglecroppingBox(self, value):
        if value:
            GUI.croppingWidget.setVisible(True)
        else:
            GUI.croppingWidget.setVisible(False)
            self.changeCroppingPower(100)  # 1.0

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

    def togglequalityBox(self, value):
        profile = GUI.profiles[str(GUI.deviceBox.currentText())]
        if value == 2:
            if profile['Label'] in ['KV', 'KO']:
                self.addMessage('This option is intended for older Kindle models.', 'warning')
                self.addMessage('On this device, quality improvement will be negligible.', 'warning')
            GUI.upscaleBox.setEnabled(False)
            GUI.upscaleBox.setChecked(True)
        else:
            GUI.upscaleBox.setEnabled(True)
            GUI.upscaleBox.setChecked(profile['DefaultUpscale'])

    def changeGamma(self, value):
        valueRaw = int(5 * round(float(value) / 5))
        value = '%.2f' % (float(valueRaw) / 100)
        if float(value) <= 0.09:
            GUI.gammaLabel.setText('Gamma: Auto')
        else:
            GUI.gammaLabel.setText('Gamma: ' + str(value))
        GUI.gammaSlider.setValue(valueRaw)
        self.gammaValue = value

    def changeCroppingPower(self, value):
        valueRaw = int(5 * round(float(value) / 5))
        value = '%.2f' % (float(valueRaw) / 100)
        GUI.croppingPowerLabel.setText('Cropping Power: ' + str(value))
        GUI.croppingPowerSlider.setValue(valueRaw)
        self.croppingPowerValue = value

    def changeDevice(self):
        profile = GUI.profiles[str(GUI.deviceBox.currentText())]
        if profile['ForceExpert']:
            self.modeChange(3)
        elif GUI.gammaBox.isChecked():
            self.modeChange(2)
        else:
            self.modeChange(1)
        GUI.colorBox.setChecked(profile['ForceColor'])
        self.changeFormat()
        GUI.gammaSlider.setValue(0)
        self.changeGamma(0)
        if not GUI.webtoonBox.isChecked():
            GUI.qualityBox.setEnabled(profile['PVOptions'])
        GUI.upscaleBox.setChecked(profile['DefaultUpscale'])
        GUI.mangaBox.setChecked(True)
        if not profile['PVOptions']:
            GUI.qualityBox.setChecked(False)
        if str(GUI.deviceBox.currentText()) == 'Other':
            self.addMessage('<a href="https://github.com/ciromattia/kcc/wiki/NonKindle-devices">'
                            'List of supported Non-Kindle devices.</a>', 'info')

    def changeFormat(self, outputformat=None):
        profile = GUI.profiles[str(GUI.deviceBox.currentText())]
        if outputformat is not None:
            GUI.formatBox.setCurrentIndex(outputformat)
        else:
            GUI.formatBox.setCurrentIndex(profile['DefaultFormat'])
        if not GUI.webtoonBox.isChecked():
            GUI.qualityBox.setEnabled(profile['PVOptions'])
        if GUI.formats[str(GUI.formatBox.currentText())]['format'] == 'MOBI':
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
            icon = getattr(self.icons, icon)
            item = QtWidgets.QListWidgetItem(icon, '   ' + self.stripTags(message))
        else:
            item = QtWidgets.QListWidgetItem('   ' + self.stripTags(message))
        if replace:
            GUI.jobList.takeItem(GUI.jobList.count() - 1)
        # Due to lack of HTML support in QListWidgetItem we overlay text field with QLabel
        # We still fill original text field with transparent content to trigger creation of horizontal scrollbar
        item.setForeground(QtGui.QColor('transparent'))
        label = QtWidgets.QLabel(message)
        label.setStyleSheet('background-image:url('');background-color:rgba(0,0,0,0);color:rgb(0,0,0);')
        label.setOpenExternalLinks(True)
        GUI.jobList.addItem(item)
        GUI.jobList.setItemWidget(item, label)
        GUI.jobList.scrollToBottom()

    def showDialog(self, message, kind):
        if kind == 'error':
            QtWidgets.QMessageBox.critical(MW, 'KCC - Error', message, QtWidgets.QMessageBox.StandardButton.Ok)
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
            self.addMessage('The process will be interrupted. Please wait.', 'warning')
            self.conversionAlive = False
            self.worker.sync()
        else:
            if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier:
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
            if 'MOBI' in GUI.formats[str(GUI.formatBox.currentText())]['format'] and not self.kindleGen:
                self.detectKindleGen()
                if not self.kindleGen:
                    GUI.jobList.clear()
                    self.display_kindlegen_missing()
                    self.needClean = True
                    return
            self.worker.start()

    def display_kindlegen_missing(self):
        self.addMessage(
            '<a href="https://github.com/ciromattia/kcc#kindlegen"><b>Install KindleGen (link)</b></a> to enable MOBI conversion for Kindles!',
            'error'
        )

    def saveSettings(self, event):
        if self.conversionAlive:
            GUI.convertButton.setEnabled(False)
            self.addMessage('The process will be interrupted. Please wait.', 'warning')
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
        self.settings.setValue('options', {'mangaBox': GUI.mangaBox.checkState().value,
                                           'rotateBox': GUI.rotateBox.checkState().value,
                                           'qualityBox': GUI.qualityBox.checkState().value,
                                           'gammaBox': GUI.gammaBox.checkState().value,
                                           'croppingBox': GUI.croppingBox.checkState().value,
                                           'croppingPowerSlider': float(self.croppingPowerValue) * 100,
                                           'upscaleBox': GUI.upscaleBox.checkState().value,
                                           'borderBox': GUI.borderBox.checkState().value,
                                           'webtoonBox': GUI.webtoonBox.checkState().value,
                                           'outputSplit': GUI.outputSplit.checkState().value,
                                           'colorBox': GUI.colorBox.checkState().value,
                                           'disableProcessingBox': GUI.disableProcessingBox.checkState().value,
                                           'mozJpegBox': GUI.mozJpegBox.checkState().value,
                                           'widthBox': GUI.widthBox.value(),
                                           'heightBox': GUI.heightBox.value(),
                                           'deleteBox': GUI.deleteBox.checkState().value,
                                           'dedupeCoverBox': GUI.dedupeCoverBox.checkState().value,
                                           'maximizeStrips': GUI.maximizeStrips.checkState().value,
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
            formats = ['.pdf']
            if self.tar or self.sevenzip:
                formats.extend(['.cb7', '.7z', '.cbz', '.zip', '.cbr', '.rar'])
            if os.path.isdir(message):
                GUI.jobList.addItem(message)
                GUI.jobList.scrollToBottom()
            elif os.path.isfile(message):
                extension = os.path.splitext(message)
                if extension[1].lower() in formats:
                    GUI.jobList.addItem(message)
                    GUI.jobList.scrollToBottom()
                else:
                    self.addMessage('Unsupported file type for ' + message, 'error')

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
        try:
            versionCheck = subprocess_run(['kindlegen', '-locale', 'en'], stdout=PIPE, stderr=STDOUT, encoding='UTF-8')
            self.kindleGen = True
            for line in versionCheck.stdout.splitlines():
                if 'Amazon kindlegen' in line:
                    versionCheck = line.split('V')[1].split(' ')[0]
                    if StrictVersion(versionCheck) < StrictVersion('2.9'):
                        self.addMessage('Your <a href="https://www.amazon.com/b?node=23496309011">KindleGen</a>'
                                        ' is outdated! MOBI conversion might fail.', 'warning')
                    break
        except FileNotFoundError:
            self.kindleGen = False
            if startup:
                self.display_kindlegen_missing()

    def __init__(self, kccapp, kccwindow):
        global APP, MW, GUI
        APP = kccapp
        MW = kccwindow
        GUI = self
        self.setupUi(MW)
        self.editor = KCCGUI_MetaEditor()
        self.icons = Icons()
        self.settings = QtCore.QSettings('ciromattia', 'kcc')
        self.settingsVersion = self.settings.value('settingsVersion', '', type=str)
        self.lastPath = self.settings.value('lastPath', '', type=str)
        self.lastDevice = self.settings.value('lastDevice', 0, type=int)
        self.currentFormat = self.settings.value('currentFormat', 0, type=int)
        self.startNumber = self.settings.value('startNumber', 0, type=int)
        self.windowSize = self.settings.value('windowSize', '0x0', type=str)
        self.options = self.settings.value('options', {'gammaSlider': 0, 'croppingBox': 2, 'croppingPowerSlider': 100})
        self.worker = WorkerThread()
        self.versionCheck = VersionThread()
        self.progress = ProgressThread()
        self.tray = SystemTrayIcon()
        self.conversionAlive = False
        self.needClean = True
        self.kindleGen = False
        self.gammaValue = 1.0
        self.croppingPowerValue = 1.0
        self.currentMode = 1
        self.targetDirectory = ''
        self.sentry = Client(release=__version__)
        if sys.platform.startswith('win'):
            # noinspection PyUnresolvedReferences
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
                getattr(GUI, element).setMinimumSize(QtCore.QSize(0, 0))
            GUI.gridLayout.setContentsMargins(-1, -1, -1, -1)
            for element in ['gridLayout_2', 'gridLayout_3', 'gridLayout_4', 'horizontalLayout', 'horizontalLayout_2']:
                getattr(GUI, element).setContentsMargins(-1, 0, -1, 0)
            if self.windowSize == '0x0':
                MW.resize(500, 500)

        self.formats = {  # text, icon, data/option_format
            "MOBI/AZW3": {'icon': 'MOBI', 'format': 'MOBI'},
            "EPUB": {'icon': 'EPUB', 'format': 'EPUB'},
            "CBZ": {'icon': 'CBZ', 'format': 'CBZ'},
            "EPUB (Calibre KFX)": {'icon': 'EPUB', 'format': 'KFX'},
            "MOBI + EPUB": {'icon': 'MOBI', 'format': 'MOBI+EPUB'},
            "EPUB (200MB limit)": {'icon': 'EPUB', 'format': 'EPUB-200MB'}
        }


        self.profiles = {
            "Kindle Oasis 9/10": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                                 'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KO'},
            "Kindle Oasis 8": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                             'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KV'},
            "Kindle Voyage": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                              'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KV'},
            "Kindle Scribe": {
                'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0, 'DefaultUpscale': False, 'ForceColor': False, 'Label': 'KS',
            },
            "Kindle 11": {
                'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0, 'DefaultUpscale': True, 'ForceColor': False, 'Label': 'K11',
            },
            "Kindle PW 11": {
                'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0, 'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KPW5',
            },
            "Kindle PW 7/10": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                              'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KV'},
            "Kindle PW 5/6": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                              'DefaultUpscale': False, 'ForceColor': False, 'Label': 'KPW'},
            "Kindle 4/5/7/8/10": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                       'DefaultUpscale': False, 'ForceColor': False, 'Label': 'K578'},
            "Kindle DX": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 2,
                              'DefaultUpscale': False, 'ForceColor': False, 'Label': 'KDX'},
            "Kobo Mini/Touch": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                                'DefaultUpscale': False, 'ForceColor': False, 'Label': 'KoMT'},
            "Kobo Glo": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                         'DefaultUpscale': False, 'ForceColor': False, 'Label': 'KoG'},
            "Kobo Glo HD": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                            'DefaultUpscale': False, 'ForceColor': False, 'Label': 'KoGHD'},
            "Kobo Aura": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                          'DefaultUpscale': False, 'ForceColor': False, 'Label': 'KoA'},
            "Kobo Aura HD": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                             'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KoAHD'},
            "Kobo Aura H2O": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                              'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KoAH2O'},
            "Kobo Aura ONE": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                              'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KoAO'},
            "Kobo Clara HD": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                              'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KoC'},
            "Kobo Libra H2O": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                               'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KoL'},
            "Kobo Forma": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1,
                           'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KoF'},
            "Kindle 1": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 0,
                         'DefaultUpscale': False, 'ForceColor': False, 'Label': 'K1'},
            "Kindle 2": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 0,
                         'DefaultUpscale': False, 'ForceColor': False, 'Label': 'K2'},
            "Kindle Keyboard": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 0,
                                'DefaultUpscale': False, 'ForceColor': False, 'Label': 'K34'},
            "Kindle Touch": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 0,
                             'DefaultUpscale': False, 'ForceColor': False, 'Label': 'K34'},
            "Kobo Nia": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1, 'DefaultUpscale': True, 'ForceColor': False,
                         'Label': 'KoN'},
            "Kobo Clara 2E": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1, 'DefaultUpscale': True, 'ForceColor': False,
                              'Label': 'KoC'},
            "Kobo Clara Colour": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1, 'DefaultUpscale': True, 'ForceColor': True,
                              'Label': 'KoCC'},
            "Kobo Libra 2": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1, 'DefaultUpscale': True, 'ForceColor': False,
                             'Label': 'KoL'},
            "Kobo Libra Colour": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1, 'DefaultUpscale': True, 'ForceColor': True,
                             'Label': 'KoLC'},
            "Kobo Sage": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1, 'DefaultUpscale': True, 'ForceColor': False,
                          'Label': 'KoS'},
            "Kobo Elipsa": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 1, 'DefaultUpscale': True, 'ForceColor': False,
                            'Label': 'KoE'},
            "Other": {'PVOptions': False, 'ForceExpert': True, 'DefaultFormat': 1, 'DefaultUpscale': False, 'ForceColor': False,
                      'Label': 'OTHER'},
        }
        profilesGUI = [
            "Kindle Scribe",
            "Kindle 11",
            "Kindle PW 11",
            "Kindle Oasis 9/10",
            "Separator",
            "Kobo Clara 2E",
            "Kobo Clara Colour",
            "Kobo Sage",
            "Kobo Libra 2",
            "Kobo Libra Colour",
            "Kobo Elipsa",
            "Kobo Nia",
            "Separator",
            "Other",
            "Separator",
            "Kindle Oasis 8",
            "Kindle PW 7/10",
            "Kindle Voyage",
            "Kindle PW 5/6",
            "Kindle 4/5/7/8/10",
            "Kindle Touch",
            "Kindle Keyboard",
            "Kindle DX",
            "Kindle 2",
            "Kindle 1",
            "Separator",
            "Kobo Aura",
            "Kobo Aura ONE",
            "Kobo Aura H2O",
            "Kobo Aura HD",
            "Kobo Clara HD",
            "Kobo Forma",
            "Kobo Glo HD",
            "Kobo Glo",
            "Kobo Libra H2O",
            "Kobo Mini/Touch",
        ]

        statusBarLabel = QtWidgets.QLabel('<b><a href="https://kcc.iosphe.re/">HOMEPAGE</a> - <a href="https://github.'
                                          'com/ciromattia/kcc/blob/master/README.md#issues--new-features--donations">DO'
                                          'NATE</a> - <a href="http://www.mobileread.com/forums/showthread.php?t=207461'
                                          '">FORUM</a></b>')
        statusBarLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        statusBarLabel.setOpenExternalLinks(True)
        GUI.statusBar.addPermanentWidget(statusBarLabel, 1)

        self.addMessage('<b>Welcome!</b>', 'info')
        self.addMessage('<b>Remember:</b> All options have additional information in tooltips.', 'info')
        if self.startNumber < 5:
            self.addMessage('Since you are a new user of <b>KCC</b> please see few '
                            '<a href="https://github.com/ciromattia/kcc/wiki/Important-tips">important tips</a>.',
                            'info')
        try:
            subprocess_run(['tar'], stdout=PIPE, stderr=STDOUT)
            self.tar = True
        except FileNotFoundError:
            self.tar = False
        try:
            subprocess_run(['7z'], stdout=PIPE, stderr=STDOUT)
            self.sevenzip = True
        except FileNotFoundError:
            self.sevenzip = False
            if not self.tar:
                self.addMessage('<a href="https://github.com/ciromattia/kcc#7-zip">Install 7z (link)</a>'
                                ' to enable CBZ/CBR/ZIP/etc processing.', 'warning')
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
        GUI.croppingBox.stateChanged.connect(self.togglecroppingBox)
        GUI.croppingPowerSlider.valueChanged.connect(self.changeCroppingPower)
        GUI.webtoonBox.stateChanged.connect(self.togglewebtoonBox)
        GUI.qualityBox.stateChanged.connect(self.togglequalityBox)
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
        for f in self.formats:
            GUI.formatBox.addItem(getattr(self.icons, self.formats[f]['icon'] + 'Format'), f)
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
            elif str(option) == "croppingPowerSlider":
                if GUI.croppingPowerSlider.isEnabled():
                    GUI.croppingPowerSlider.setValue(int(self.options[option]))
                    self.changeCroppingPower(int(self.options[option]))
            else:
                try:
                    if getattr(GUI, option).isEnabled():
                        getattr(GUI, option).setCheckState(Qt.CheckState(self.options[option]))
                except AttributeError:
                    pass
        self.worker.sync()
        self.versionCheck.start()
        self.tray.show()

        # Cleanup unfinished conversion
        for root, dirs, _ in walkLevel(gettempdir(), 0):
            for tempdir in dirs:
                if tempdir.startswith('KCC-'):
                    rmtree(os.path.join(root, tempdir), True)

        if self.windowSize != '0x0':
            x, y = self.windowSize.split('x')
            MW.resize(int(x), int(y))
        MW.setWindowTitle("Kindle Comic Converter " + __version__)
        MW.show()
        MW.raise_()


class KCCGUI_MetaEditor(KCC_ui_editor.Ui_editorDialog):
    def loadData(self, file):
        self.parser = metadata.MetadataParser(file)
        if self.parser.format in ['RAR', 'RAR5']:
            self.editorWidget.setEnabled(False)
            self.okButton.setEnabled(False)
            self.statusLabel.setText('CBR metadata are read-only.')
        else:
            self.editorWidget.setEnabled(True)
            self.okButton.setEnabled(True)
            self.statusLabel.setText('Separate authors with a comma.')
        for field in (self.seriesLine, self.volumeLine, self.numberLine):
            field.setText(self.parser.data[field.objectName().capitalize()[:-4]])
        for field in (self.writerLine, self.pencillerLine, self.inkerLine, self.coloristLine):
            field.setText(', '.join(self.parser.data[field.objectName().capitalize()[:-4] + 's']))
        if self.seriesLine.text() == '':
            if file.endswith('.xml'):
                self.seriesLine.setText(file.split('\\')[-2])
            else:
                self.seriesLine.setText(file.split('\\')[-1].split('/')[-1].split('.')[0])

    def saveData(self):
        for field in (self.volumeLine, self.numberLine):
            if field.text().isnumeric() or self.cleanData(field.text()) == '':
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
        self.ui.setWindowFlags(self.ui.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        self.okButton.clicked.connect(self.saveData)
        self.cancelButton.clicked.connect(self.ui.close)
        if sys.platform.startswith('linux'):
            self.ui.resize(450, 260)
            self.ui.setMinimumSize(QtCore.QSize(450, 260))
        elif sys.platform.startswith('darwin'):
            self.ui.resize(450, 310)
            self.ui.setMinimumSize(QtCore.QSize(450, 310))
