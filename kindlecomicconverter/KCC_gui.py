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

from datetime import datetime, timezone
import itertools
from pathlib import Path
from PySide6.QtCore import (QSize, QUrl, Qt, Signal, QIODeviceBase, QEvent, QThread, QSettings)
from PySide6.QtGui import (QColor, QIcon, QPixmap, QDesktopServices)
from PySide6.QtWidgets import (QApplication, QLabel, QListWidgetItem, QMainWindow, QSystemTrayIcon, QFileDialog, QMessageBox, QDialog)
from PySide6.QtNetwork import (QLocalSocket, QLocalServer)

import os
import re
import sys
from urllib.parse import unquote
from time import sleep
from shutil import move, rmtree
from subprocess import STDOUT, PIPE, CalledProcessError

import requests
from xml.sax.saxutils import escape
from psutil import Process
from copy import copy
from packaging.version import Version
from raven import Client
from tempfile import gettempdir

from .shared import HTMLStripper, sanitizeTrace, walkLevel, subprocess_run
from .comicarchive import SEVENZIP, available_archive_tools
from . import __version__
from . import comic2ebook
from . import metadata
from . import kindle
from . import KCC_ui
from . import KCC_ui_editor


class QApplicationMessaging(QApplication):
    messageFromOtherInstance = Signal(bytes)

    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self._key = 'KCC'
        self._timeout = 1000
        self._locked = False
        socket = QLocalSocket(self)
        socket.connectToServer(self._key, QIODeviceBase.OpenModeFlag.WriteOnly)
        if not socket.waitForConnected(self._timeout):
            self._server = QLocalServer(self)
            self._server.newConnection.connect(self.handleMessage)
            self._server.listen(self._key)
        else:
            self._locked = True
        socket.disconnectFromServer()

    def __del__(self):
        if not self._locked:
            self._server.close()

    def event(self, e):
        if e.type() == QEvent.Type.FileOpen:
            self.messageFromOtherInstance.emit(bytes(e.file(), 'UTF-8'))
            return True
        else:
            return QApplication.event(self, e)

    def isRunning(self):
        return self._locked

    def handleMessage(self):
        socket = self._server.nextPendingConnection()
        if socket.waitForReadyRead(self._timeout):
            self.messageFromOtherInstance.emit(socket.readAll().data())

    def sendMessage(self, message):
        socket = QLocalSocket(self)
        socket.connectToServer(self._key, QIODeviceBase.OpenModeFlag.WriteOnly)
        socket.waitForConnected(self._timeout)
        socket.write(bytes(message, 'UTF-8'))
        socket.waitForBytesWritten(self._timeout)
        socket.disconnectFromServer()


class QMainWindowKCC(QMainWindow):
    progressBarTick = Signal(str)
    modeConvert = Signal(int)
    addMessage = Signal(str, str, bool)
    addTrayMessage = Signal(str, str)
    showDialog = Signal(str, str)
    hideProgressBar = Signal()
    forceShutdown = Signal()


class Icons:
    def __init__(self):
        self.deviceKindle = QIcon()
        self.deviceKindle.addPixmap(QPixmap(":/Devices/icons/Kindle.png"), QIcon.Mode.Normal, QIcon.State.Off)
        self.deviceKobo = QIcon()
        self.deviceKobo.addPixmap(QPixmap(":/Devices/icons/Kobo.png"), QIcon.Mode.Normal, QIcon.State.Off)
        self.deviceRmk = QIcon()
        self.deviceRmk.addPixmap(QPixmap(":/Devices/icons/Rmk.png"), QIcon.Mode.Normal, QIcon.State.Off)
        self.deviceOther = QIcon()
        self.deviceOther.addPixmap(QPixmap(":/Devices/icons/Other.png"), QIcon.Mode.Normal, QIcon.State.Off)

        self.MOBIFormat = QIcon()
        self.MOBIFormat.addPixmap(QPixmap(":/Formats/icons/MOBI.png"), QIcon.Mode.Normal, QIcon.State.Off)
        self.CBZFormat = QIcon()
        self.CBZFormat.addPixmap(QPixmap(":/Formats/icons/CBZ.png"), QIcon.Mode.Normal, QIcon.State.Off)
        self.EPUBFormat = QIcon()
        self.EPUBFormat.addPixmap(QPixmap(":/Formats/icons/EPUB.png"), QIcon.Mode.Normal, QIcon.State.Off)
        self.KFXFormat = QIcon()
        self.KFXFormat.addPixmap(QPixmap(":/Formats/icons/KFX.png"), QIcon.Mode.Normal, QIcon.State.Off)

        self.info = QIcon()
        self.info.addPixmap(QPixmap(":/Status/icons/info.png"), QIcon.Mode.Normal, QIcon.State.Off)
        self.warning = QIcon()
        self.warning.addPixmap(QPixmap(":/Status/icons/warning.png"), QIcon.Mode.Normal, QIcon.State.Off)
        self.error = QIcon()
        self.error.addPixmap(QPixmap(":/Status/icons/error.png"), QIcon.Mode.Normal, QIcon.State.Off)

        self.programIcon = QIcon()
        self.programIcon.addPixmap(QPixmap(":/Icon/icons/comic2ebook.png"), QIcon.Mode.Normal, QIcon.State.Off)

        self.kofi = QIcon()
        self.kofi.addPixmap(QPixmap(":/Brand/icons/kofi_symbol.png"), QIcon.Mode.Normal, QIcon.State.Off)
        
        self.humble = QIcon()
        self.humble.addPixmap(QPixmap(":/Brand/icons/Humble_H-Red.png"), QIcon.Mode.Normal, QIcon.State.Off)

        self.bindle = QIcon()
        self.bindle.addPixmap(QPixmap(":/Brand/icons/Bindle_Red.png"), QIcon.Mode.Normal, QIcon.State.Off)


class VersionThread(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.newVersion = ''
        self.md5 = ''
        self.barProgress = 0
        self.answer = None

    def __del__(self):
        self.wait()

    def run(self):
        try:
            # unauthenticated API requests limit is 60 req/hour
            if getattr(sys, 'frozen', False):
                json_parser = requests.get("https://api.github.com/repos/ciromattia/kcc/releases/latest").json()

                html_url = json_parser["html_url"]
                latest_version = json_parser["tag_name"]
                latest_version = re.sub(r'^v', "", latest_version)

                if ("b" not in __version__ and Version(latest_version) > Version(__version__)) \
                        or ("b" in __version__
                            and Version(latest_version) >= Version(re.sub(r'b.*', '', __version__))):
                    MW.addMessage.emit('<a href="' + html_url + '"><b>The new version is available!</b></a>', 'warning',
                                    False)
        except Exception:
            pass
        
        try:
            announcements = requests.get('https://api.github.com/repos/axu2/kcc-messages/contents/links.json',
                                       headers={
                                           'Accept': 'application/vnd.github.raw+json',
                                           'X-GitHub-Api-Version': '2022-11-28'}).json()
            for category, payloads in announcements.items():
                for payload in payloads:
                    expiration = datetime.fromisoformat(payload['expiration'])
                    if expiration < datetime.now(timezone.utc):
                        continue
                    delta = expiration - datetime.now(timezone.utc)
                    time_left = f"{delta.days} day(s) left"
                    icon = 'info'
                    if category == 'humbleMangaBundles':
                        icon = 'humble'
                    if category == 'humbleComicBundles':
                        icon = 'bindle'
                    if category == 'kofi':
                        icon = 'kofi'
                    message = f"<b>{payload.get('name')}</b>"
                    if payload.get('link'):
                        message = '<a href="{}"><b>{}</b></a>'.format(payload.get('link'), payload.get('name'))
                    if payload.get('showDeadline'):
                        message += f': {time_left}'
                    if category == 'humbleBundles':
                        message += ' [referral]'
                    MW.addMessage.emit(message, icon , False)
        except Exception as e:
            print(e)


    def setAnswer(self, dialoganswer):
        self.answer = dialoganswer


class ProgressThread(QThread):
    def __init__(self):
        QThread.__init__(self)
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


class WorkerThread(QThread):
    def __init__(self):
        QThread.__init__(self)
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
        if GUI.autoLevelBox.isChecked():
            options.autolevel = True
        if GUI.autocontrastBox.checkState() == Qt.CheckState.PartiallyChecked:
            options.noautocontrast = True
        elif GUI.autocontrastBox.checkState() == Qt.CheckState.Checked:
            options.colorautocontrast = True
        if GUI.croppingBox.isChecked():
            if GUI.croppingBox.checkState() == Qt.CheckState.PartiallyChecked:
                options.cropping = 1
            else:
                options.cropping = 2
        else:
            options.cropping = 0
        if GUI.croppingBox.checkState() != Qt.CheckState.Unchecked:
            options.croppingp = float(GUI.croppingPowerValue)
            options.preservemargin = GUI.preserveMarginBox.value()
        if GUI.interPanelCropBox.isChecked():
            if GUI.interPanelCropBox.checkState() == Qt.CheckState.PartiallyChecked:
                options.interpanelcrop = 1
            else:
                options.interpanelcrop = 2
        else:
            options.interpanelcrop = 0
        if GUI.borderBox.checkState() == Qt.CheckState.PartiallyChecked:
            options.white_borders = True
        elif GUI.borderBox.checkState() == Qt.CheckState.Checked:
            options.black_borders = True
        if GUI.outputSplit.isChecked():
            options.batchsplit = 2
        if GUI.colorBox.isChecked():
            options.forcecolor = True
        if GUI.eraseRainbowBox.isChecked():
            options.eraserainbow = True
        if GUI.maximizeStrips.isChecked():
            options.maximizestrips = True
        if GUI.disableProcessingBox.isChecked():
            options.noprocessing = True
        if GUI.metadataTitleBox.checkState() == Qt.CheckState.PartiallyChecked:
            options.metadatatitle = 1
        elif GUI.metadataTitleBox.checkState() == Qt.CheckState.Checked:
            options.metadatatitle = 2
        if GUI.deleteBox.isChecked():
            options.delete = True
        if GUI.spreadShiftBox.isChecked():
            options.spreadshift = True
        if GUI.fileFusionBox.isChecked():
            options.filefusion = True
        else:
            options.filefusion = False
        if GUI.noRotateBox.isChecked():
            options.norotate = True
        if GUI.rotateFirstBox.isChecked():
            options.rotatefirst = True
        if GUI.mozJpegBox.checkState() == Qt.CheckState.PartiallyChecked:
            options.forcepng = True
        elif GUI.mozJpegBox.checkState() == Qt.CheckState.Checked:
            options.mozjpeg = True
        if GUI.currentMode > 2:
            options.customwidth = str(GUI.widthBox.value())
            options.customheight = str(GUI.heightBox.value())
        if GUI.targetDirectory != '':
            options.output = GUI.targetDirectory
        if GUI.titleEdit.text():
            options.title = str(GUI.titleEdit.text())
        if GUI.authorEdit.text():
            options.author = str(GUI.authorEdit.text())
        if GUI.chunkSizeCheckBox.isChecked():
            options.targetsize = int(GUI.chunkSizeBox.value())

        for i in range(GUI.jobList.count()):
            # Make sure that we don't consider any system message as job to do
            if GUI.jobList.item(i).icon().isNull():
                currentJobs.append(str(GUI.jobList.item(i).text()))
        GUI.jobList.clear()
        if options.filefusion:
            bookDir = []
            MW.addMessage.emit('Attempting file fusion', 'info', False)
            for job in currentJobs:
                bookDir.append(job)
            try:
                comic2ebook.options = comic2ebook.checkOptions(copy(options))
                currentJobs.clear()
                currentJobs.append(comic2ebook.makeFusion(bookDir))
                MW.addMessage.emit('Created fusion at ' + currentJobs[0], 'info', False)
            except Exception as e:
                print('Fusion Failed. ' + str(e))
                MW.addMessage.emit('Fusion Failed. ' + str(e), 'error', True)
        elif len(currentJobs) > 1 and options.title != 'defaulttitle':
            currentJobs.clear()
            error_message = 'Process Failed. Custom title can\'t be set when processing more than 1 source.\nDid you forget to check fusion?'
            print(error_message)
            MW.addMessage.emit(error_message, 'error', True)
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
            elif gui_current_format == 'PDF':
                MW.addMessage.emit('Creating PDF files', 'info', False)
                GUI.progress.content = 'Creating PDF files'
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
                MW.showDialog.emit("Error during conversion %s:\n\n%s\n\nTraceback:\n%s"
                                   % (jobargv[-1], str(err), sanitizeTrace(traceback)), 'error')
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
                elif gui_current_format == 'PDF':
                    MW.addMessage.emit('Creating PDF files... <b>Done!</b>', 'info', True)
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
                            k = kindle.Kindle(options.profile)
                            if k.path and k.coverSupport:
                                for item in outputPath:
                                    cover = comic2ebook.options.covers[outputPath.index(item)][0]
                                    if cover:
                                        cover.saveToKindle(
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
                            MW.addMessage.emit('Created EPUB file was too big. Weird file structure?', 'error', False)
                            MW.addMessage.emit('EPUB file: ' + str(epubSize) + 'MB. Supported size: ~350MB.', 'error',
                                               False)
                        if self.kindlegenErrorCode[0] == 3221226505:
                            MW.addMessage.emit('Unknown Windows error. Possibly filepath too long?', 'error', False)
                else:
                    for item in outputPath:
                        if GUI.targetDirectory and GUI.targetDirectory != os.path.dirname(item):
                            try:
                                move(item, GUI.targetDirectory)
                            except Exception:
                                pass
        if options.filefusion:
            for path in currentJobs:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    rmtree(path, True)
        GUI.progress.content = ''
        GUI.progress.stop()
        MW.hideProgressBar.emit()
        GUI.needClean = True
        if not self.errors:
            MW.addMessage.emit('<b>All jobs completed.</b>', 'info', False)
            MW.addTrayMessage.emit('All jobs completed.', 'Information')
        MW.modeConvert.emit(1)


class SystemTrayIcon(QSystemTrayIcon):
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
        icon = getattr(QSystemTrayIcon.MessageIcon, icon)
        if self.supportsMessages() and not MW.isActiveWindow():
            self.showMessage('Kindle Comic Converter', message, icon)


class KCCGUI(KCC_ui.Ui_mainWindow):
    def selectDefaultOutputFolder(self):
        dname = QFileDialog.getExistingDirectory(MW, 'Select default output folder', self.defaultOutputFolder)
        if self.is_directory_on_kindle(dname):
            return
        if dname != '':
            if sys.platform.startswith('win'):
                dname = dname.replace('/', '\\')
            GUI.defaultOutputFolder = dname

    def is_directory_on_kindle(self, dname):
        path = Path(dname)
        for parent in itertools.chain([path], path.parents):
            if parent.name == 'documents' and parent.parent.joinpath('system').joinpath('thumbnails').is_dir():
                self.addMessage("Cannot select Kindle as output directory", 'error')
                return True

    def selectOutputFolder(self):
        dname = QFileDialog.getExistingDirectory(MW, 'Select output directory', self.lastPath)
        if self.is_directory_on_kindle(dname):
            return
        if dname != '':
            if sys.platform.startswith('win'):
                dname = dname.replace('/', '\\')
            GUI.targetDirectory = dname
        else:
            GUI.targetDirectory = ''
        return GUI.targetDirectory

    def selectFile(self):
        if self.needClean:
            self.needClean = False
            GUI.jobList.clear()
        if self.tar or self.sevenzip:
            fnames = QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                            'Comic (*.cbz *.cbr *.cb7 *.zip *.rar *.7z *.pdf);;All (*.*)')
        else:
            fnames = QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                            'Comic (*.pdf);;All (*.*)')
        for fname in fnames[0]:
            if fname != '':
                if sys.platform.startswith('win'):
                    fname = fname.replace('/', '\\')
                self.lastPath = os.path.abspath(os.path.join(fname, os.pardir))
                GUI.jobList.addItem(fname)
                GUI.jobList.scrollToBottom()

    def selectFileMetaEditor(self, sname):
        if not sname:
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                dname = QFileDialog.getExistingDirectory(MW, 'Select directory', self.lastPath)
                if dname != '':
                    sname = os.path.join(dname, 'ComicInfo.xml')
                    self.lastPath = os.path.dirname(sname)
            else:
                if self.sevenzip:
                    fname = QFileDialog.getOpenFileName(MW, 'Select file', self.lastPath,
                                                                  'Comic (*.cbz *.cbr *.cb7)')
                else:
                    fname = ['']
                    self.showDialog("Editor is disabled due to a lack of 7z.", 'error')
                    self.addMessage('<a href="https://github.com/ciromattia/kcc#7-zip">Install 7z (link)</a>'
                    ' to enable metadata editing.', 'warning')
                if fname[0] != '':
                    sname = fname[0]
                    self.lastPath = os.path.abspath(os.path.join(sname, os.pardir))
        if sname:
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
        QDesktopServices.openUrl(QUrl('https://github.com/ciromattia/kcc/wiki'))

    def openKofi(self):
        # noinspection PyCallByClass
        QDesktopServices.openUrl(QUrl('https://ko-fi.com/eink_dude'))

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
        GUI.defaultOutputFolderButton.setEnabled(status)
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
            icon = QIcon()
            icon.addPixmap(QPixmap(":/Other/icons/convert.png"), QIcon.Mode.Normal, QIcon.State.Off)
            GUI.convertButton.setIcon(icon)
            GUI.convertButton.setText('Convert')
            GUI.centralWidget.setAcceptDrops(True)
        elif enable == 0:
            self.conversionAlive = True
            self.worker.sync()
            icon = QIcon()
            icon.addPixmap(QPixmap(":/Other/icons/clear.png"), QIcon.Mode.Normal, QIcon.State.Off)
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
            self.addMessage('You can choose a taller device profile to get taller cuts in webtoon mode.', 'info')
            self.addMessage('Try reading webtoon panels side by side in landscape!', 'info')
            GUI.qualityBox.setEnabled(False)
            GUI.qualityBox.setChecked(False)
            GUI.mangaBox.setEnabled(False)
            GUI.mangaBox.setChecked(False)
            GUI.rotateBox.setEnabled(False)
            GUI.rotateBox.setChecked(False)
            GUI.borderBox.setEnabled(False)
            GUI.borderBox.setCheckState(Qt.CheckState.PartiallyChecked)
            GUI.upscaleBox.setEnabled(False)
            GUI.upscaleBox.setChecked(False)
            GUI.croppingBox.setEnabled(False)
            GUI.croppingBox.setChecked(False)
            GUI.interPanelCropBox.setEnabled(False)
            GUI.interPanelCropBox.setChecked(False)
            GUI.autoLevelBox.setEnabled(False)
            GUI.autoLevelBox.setChecked(False)
            GUI.autocontrastBox.setEnabled(False)
            GUI.autocontrastBox.setChecked(False)
        else:
            profile = GUI.profiles[str(GUI.deviceBox.currentText())]
            if profile['PVOptions']:
                GUI.qualityBox.setEnabled(True)
            GUI.mangaBox.setEnabled(True)
            GUI.rotateBox.setEnabled(True)
            GUI.borderBox.setEnabled(True)
            profile = GUI.profiles[str(GUI.deviceBox.currentText())]
            if profile['Label'] != 'KS':
                GUI.upscaleBox.setEnabled(True)
            GUI.croppingBox.setEnabled(True)
            GUI.interPanelCropBox.setEnabled(True)
            GUI.autoLevelBox.setEnabled(True)
            GUI.autocontrastBox.setEnabled(True)
            GUI.autocontrastBox.setChecked(True)


    def togglequalityBox(self, value):
        profile = GUI.profiles[str(GUI.deviceBox.currentText())]
        if value == 2:
            if profile['Label'] not in ('K57', 'KPW', 'K810') :
                self.addMessage('This option is intended for older Kindle models.', 'warning')
                self.addMessage('On this device, there will be conversion speed and quality issues.', 'warning')
                self.addMessage('Use the Kindle Scribe profile if you want higher resolution when zooming.', 'warning')
            GUI.upscaleBox.setEnabled(False)
            GUI.upscaleBox.setChecked(True)
        else:
            GUI.upscaleBox.setEnabled(True)
            GUI.upscaleBox.setChecked(profile['DefaultUpscale'])

    def toggleImageFormatBox(self, value):
        profile = GUI.profiles[str(GUI.deviceBox.currentText())]
        if value == 1:
            if profile['Label'] == 'KS':
                current_format = GUI.formats[str(GUI.formatBox.currentText())]['format']
                for bad_format in ('MOBI', 'EPUB'):
                    if bad_format in current_format:
                        self.addMessage('Scribe PNG MOBI/EPUB has a lot of problems like blank pages/sections. Use JPG instead.', 'warning')
                        break

    def togglechunkSizeCheckBox(self, value):
        GUI.chunkSizeWidget.setVisible(value)

    def toggletitleEdit(self, value):
        if value:
            self.metadataTitleBox.setChecked(False)

    def togglefileFusionBox(self, value):
        if value:
            GUI.metadataTitleBox.setChecked(False)
            GUI.metadataTitleBox.setEnabled(False)
        else:
            GUI.metadataTitleBox.setEnabled(True)

    def togglemetadataTitleBox(self, value):
        if value:
            GUI.titleEdit.setText(None)

    def editSourceMetadata(self, item):
        if item.icon().isNull():
            sname = item.text()
            if os.path.isdir(sname):
                sname = os.path.join(sname, "ComicInfo.xml")
            self.selectFileMetaEditor(sname)

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
        if not GUI.webtoonBox.isChecked():
            GUI.qualityBox.setEnabled(profile['PVOptions'])
        GUI.upscaleBox.setChecked(profile['DefaultUpscale'])
        if profile['Label'] == 'KS':
            GUI.upscaleBox.setDisabled(True)
        else:
            if not GUI.webtoonBox.isChecked():
                GUI.upscaleBox.setEnabled(True)
        if profile['Label'] == 'KCS':
            current_format = GUI.formats[str(GUI.formatBox.currentText())]['format']
            for bad_format in ('MOBI', 'EPUB'):
                if bad_format in current_format:
                    self.addMessage('Colorsoft MOBI/EPUB can have blank pages. Just go back a few pages, exit, and reenter book.', 'info')
                    break
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
        if (GUI.formats[str(GUI.formatBox.currentText())]['format'] == 'EPUB-200MB' or
            GUI.formats[str(GUI.formatBox.currentText())]['format'] == 'MOBI+EPUB-200MB'):
            GUI.chunkSizeCheckBox.setEnabled(False)
            GUI.chunkSizeCheckBox.setChecked(False)
        elif not GUI.webtoonBox.isChecked():
            GUI.chunkSizeCheckBox.setEnabled(True)
        if GUI.formats[str(GUI.formatBox.currentText())]['format'] in ('CBZ', 'PDF') and not GUI.webtoonBox.isChecked():
            self.addMessage("Partially check W/B Margins if you don't want KCC to extend the image margins.", 'info')   

    def stripTags(self, html):
        s = HTMLStripper()
        s.feed(html)
        return s.get_data()

    def addMessage(self, message, icon, replace=False):
        if icon != '':
            icon = getattr(self.icons, icon)
            item = QListWidgetItem(icon, '   ' + self.stripTags(message))
        else:
            item = QListWidgetItem('   ' + self.stripTags(message))
        if replace:
            GUI.jobList.takeItem(GUI.jobList.count() - 1)
        # Due to lack of HTML support in QListWidgetItem we overlay text field with QLabel
        # We still fill original text field with transparent content to trigger creation of horizontal scrollbar
        item.setForeground(QColor('transparent'))
        label = QLabel(message)
        label.setOpenExternalLinks(True)
        GUI.jobList.addItem(item)
        GUI.jobList.setItemWidget(item, label)
        GUI.jobList.scrollToBottom()

    def showDialog(self, message, kind):
        if kind == 'error':
            QMessageBox.critical(MW, 'KCC - Error', message, QMessageBox.StandardButton.Ok)
        elif kind == 'question':
            GUI.versionCheck.setAnswer(QMessageBox.question(MW, 'KCC - Question', message,
                                                                      QMessageBox.Yes,
                                                                      QMessageBox.No))

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
            if QApplication.keyboardModifiers() == Qt.KeyboardModifier.ShiftModifier:
                if not self.selectOutputFolder():
                    return
            elif GUI.defaultOutputFolderBox.isChecked():
                self.targetDirectory = self.defaultOutputFolder
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
            if GUI.defaultOutputFolderBox.checkState() == Qt.CheckState.PartiallyChecked:
                parent = Path(self.jobList.item(0).text()).parent
                target_path = parent.joinpath(f"{parent.name}")
                if not target_path.exists():
                    target_path.mkdir()
                self.targetDirectory = str(target_path)
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
        self.settings.setValue('defaultOutputFolder', self.defaultOutputFolder)
        self.settings.setValue('lastDevice', GUI.deviceBox.currentIndex())
        self.settings.setValue('currentFormat', GUI.formatBox.currentIndex())
        self.settings.setValue('startNumber', self.startNumber + 1)
        self.settings.setValue('windowSize', str(MW.size().width()) + 'x' + str(MW.size().height()))
        self.settings.setValue('options', {'mangaBox': GUI.mangaBox.checkState(),
                                           'rotateBox': GUI.rotateBox.checkState(),
                                           'qualityBox': GUI.qualityBox.checkState(),
                                           'gammaBox': GUI.gammaBox.checkState(),
                                           'autoLevelBox': GUI.autoLevelBox.checkState(),
                                           'autocontrastBox': GUI.autocontrastBox.checkState(),
                                           'croppingBox': GUI.croppingBox.checkState(),
                                           'croppingPowerSlider': float(self.croppingPowerValue) * 100,
                                           'preserveMarginBox': self.preserveMarginBox.value(),
                                           'interPanelCropBox': GUI.interPanelCropBox.checkState(),
                                           'upscaleBox': GUI.upscaleBox.checkState(),
                                           'borderBox': GUI.borderBox.checkState(),
                                           'webtoonBox': GUI.webtoonBox.checkState(),
                                           'outputSplit': GUI.outputSplit.checkState(),
                                           'colorBox': GUI.colorBox.checkState(),
                                           'eraseRainbowBox': GUI.eraseRainbowBox.checkState(),
                                           'disableProcessingBox': GUI.disableProcessingBox.checkState(),
                                           'metadataTitleBox': GUI.metadataTitleBox.checkState(),
                                           'mozJpegBox': GUI.mozJpegBox.checkState(),
                                           'widthBox': GUI.widthBox.value(),
                                           'heightBox': GUI.heightBox.value(),
                                           'deleteBox': GUI.deleteBox.checkState(),
                                           'spreadShiftBox': GUI.spreadShiftBox.checkState(),
                                           'fileFusionBox': GUI.fileFusionBox.checkState(),
                                           'defaultOutputFolderBox': GUI.defaultOutputFolderBox.checkState(),
                                           'noRotateBox': GUI.noRotateBox.checkState(),
                                           'rotateFirstBox': GUI.rotateFirstBox.checkState(),
                                           'maximizeStrips': GUI.maximizeStrips.checkState(),
                                           'gammaSlider': float(self.gammaValue) * 100,
                                           'chunkSizeCheckBox': GUI.chunkSizeCheckBox.checkState(),
                                           'chunkSizeBox': GUI.chunkSizeBox.value()})
        self.settings.sync()
        self.tray.hide()

    def handleMessage(self, message):
        MW.raise_()
        MW.activateWindow()
        if type(message) is bytes:
            message = message.decode('UTF-8')
        if not self.conversionAlive and message != 'ARISE' and not GUI.jobList.findItems(message, Qt.MatchFlag.MatchExactly):
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
        GUI.jobList.sortItems()

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
            versionCheck = subprocess_run(['kindlegen', '-locale', 'en'], stdout=PIPE, stderr=STDOUT, encoding='UTF-8', errors='ignore', check=True)
            self.kindleGen = True
            for line in versionCheck.stdout.splitlines():
                if 'Amazon kindlegen' in line:
                    versionCheck = line.split('V')[1].split(' ')[0]
                    if Version(versionCheck) < Version('2.9'):
                        self.addMessage('Your <a href="https://www.amazon.com/b?node=23496309011">KindleGen</a>'
                                        ' is outdated! MOBI conversion might fail.', 'warning')
                    break
        except (FileNotFoundError, CalledProcessError):
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
        self.settings = QSettings('ciromattia', 'kcc9')
        self.settingsVersion = self.settings.value('settingsVersion', '', type=str)
        self.lastPath = self.settings.value('lastPath', '', type=str)
        self.defaultOutputFolder = str(self.settings.value('defaultOutputFolder', '', type=str))
        if not os.path.exists(self.defaultOutputFolder):
            self.defaultOutputFolder = ''
        self.lastDevice = self.settings.value('lastDevice', 0, type=int)
        self.currentFormat = self.settings.value('currentFormat', 0, type=int)
        self.startNumber = self.settings.value('startNumber', 0, type=int)
        self.windowSize = self.settings.value('windowSize', '0x0', type=str)
        default_options = {'gammaSlider': 0, 'croppingBox': 2, 'croppingPowerSlider': 100}
        try:
            self.options = self.settings.value('options', default_options)
        except Exception:
            self.options = default_options
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
            for element in ['editorButton', 'wikiButton', 'defaultOutputFolderButton', 'clearButton', 'fileButton', 'deviceBox',
                            'convertButton', 'formatBox']:
                getattr(GUI, element).setMinimumSize(QSize(0, 0))
            GUI.gridLayout.setContentsMargins(-1, -1, -1, -1)
            for element in ['gridLayout_2', 'gridLayout_3', 'gridLayout_4', 'horizontalLayout', 'horizontalLayout_2']:
                getattr(GUI, element).setContentsMargins(-1, 0, -1, 0)
            if self.windowSize == '0x0':
                MW.resize(500, 500)

        self.formats = {  # text, icon, data/option_format
            "MOBI/AZW3": {'icon': 'MOBI', 'format': 'MOBI'},
            "EPUB": {'icon': 'EPUB', 'format': 'EPUB'},
            "CBZ": {'icon': 'CBZ', 'format': 'CBZ'},
            "PDF": {'icon': 'EPUB', 'format': 'PDF'},
            "KFX (does not work)": {'icon': 'KFX', 'format': 'KFX'},
            "MOBI + EPUB": {'icon': 'MOBI', 'format': 'MOBI+EPUB'},
            "EPUB (200MB limit)": {'icon': 'EPUB', 'format': 'EPUB-200MB'},
            "MOBI + EPUB (200MB limit)": {'icon': 'MOBI', 'format': 'MOBI+EPUB-200MB'},
        }


        self.profiles = {
            "Kindle Oasis 9/10": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                                 'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KO'},
            "Kindle 8/10": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                       'DefaultUpscale': False, 'ForceColor': False, 'Label': 'K810'},
            "Kindle Oasis 8": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                             'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KPW34'},
            "Kindle Voyage": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                              'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KV'},
            "Kindle Scribe": {
                'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0, 'DefaultUpscale': False, 'ForceColor': False, 'Label': 'KS',
            },
            "Kindle 11": {
                'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0, 'DefaultUpscale': True, 'ForceColor': False, 'Label': 'K11',
            },
            "Kindle Paperwhite 11": {
                'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0, 'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KPW5',
            },
            "Kindle Paperwhite 12": {
                'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0, 'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KO',
            },
            "Kindle Colorsoft": {
                'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0, 'DefaultUpscale': True, 'ForceColor': True, 'Label': 'KCS',
            },
            "Kindle Paperwhite 7/10": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                              'DefaultUpscale': True, 'ForceColor': False, 'Label': 'KPW34'},
            "Kindle Paperwhite 5/6": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                              'DefaultUpscale': False, 'ForceColor': False, 'Label': 'KPW'},
            "Kindle 4/5/7": {'PVOptions': True, 'ForceExpert': False, 'DefaultFormat': 0,
                       'DefaultUpscale': False, 'ForceColor': False, 'Label': 'K57'},
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
            "reMarkable 1": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 3, 'DefaultUpscale': True, 'ForceColor': False,
                             'Label': 'Rmk1'},
            "reMarkable 2": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 3, 'DefaultUpscale': True, 'ForceColor': False,
                             'Label': 'Rmk2'},
            "reMarkable Paper Pro": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 3, 'DefaultUpscale': True, 'ForceColor': True,
                             'Label': 'RmkPP'},
            "reMarkable Paper Pro Move": {'PVOptions': False, 'ForceExpert': False, 'DefaultFormat': 3, 'DefaultUpscale': True, 'ForceColor': True,
                             'Label': 'RmkPPMove'},
            "Other": {'PVOptions': False, 'ForceExpert': True, 'DefaultFormat': 1, 'DefaultUpscale': False, 'ForceColor': False,
                      'Label': 'OTHER'},
        }
        profilesGUI = [
            "Kindle Colorsoft",
            "Kindle Paperwhite 12",
            "Kindle Scribe",
            "Kindle Paperwhite 11",
            "Kindle 11",
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
            "reMarkable 1",
            "reMarkable 2",
            "reMarkable Paper Pro",
            "reMarkable Paper Pro Move",
            "Separator",
            "Other",
            "Separator",
            "Kindle 8/10",
            "Kindle Oasis 8",
            "Kindle Paperwhite 7/10",
            "Kindle Voyage",
            "Kindle Paperwhite 5/6",
            "Kindle 4/5/7",
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

        link_dict = {
            'README': "https://github.com/ciromattia/kcc?tab=readme-ov-file#kcc",
            'FAQ': "https://github.com/ciromattia/kcc/blob/master/README.md#faq",
            'YOUTUBE': "https://youtu.be/IR2Fhcm9658?si=Z-2zzLaUFjmaEbrj",
            'COMMISSIONS': "https://github.com/ciromattia/kcc?tab=readme-ov-file#commissions",
            'DONATE': "https://github.com/ciromattia/kcc/blob/master/README.md#issues--new-features--donations",
            'FORUM': "http://www.mobileread.com/forums/showthread.php?t=207461",
            'DISCORD': "https://discord.com/invite/qj7wpnUHav",
        }

        link_html_list = [f'<a href="{v}">{k}</a>' for k, v in link_dict.items()]
        statusBarLabel = QLabel(f'<b>{" - ".join(link_html_list)}</b>')
        statusBarLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        statusBarLabel.setOpenExternalLinks(True)
        GUI.statusBar.addPermanentWidget(statusBarLabel, 1)

        self.addMessage('<b>Tip:</b> Hover mouse over options to see additional information in tooltips.', 'info')
        self.addMessage('<b>Tip:</b> You can drag and drop image folders or comic files/archives into this window to convert.', 'info')
        if self.startNumber < 5:
            self.addMessage('Since you are a new user of <b>KCC</b> please see few '
                            '<a href="https://github.com/ciromattia/kcc/wiki/Important-tips">important tips</a>.',
                            'info')
        
        self.tar = 'tar' in available_archive_tools()
        self.sevenzip = SEVENZIP in available_archive_tools()
        if not any([self.tar, self.sevenzip]):
            self.addMessage('<a href="https://github.com/ciromattia/kcc#7-zip">Install 7z (link)</a>'
                            ' to enable CBZ/CBR/ZIP/etc processing.', 'warning')
        self.detectKindleGen(True)

        APP.messageFromOtherInstance.connect(self.handleMessage)
        GUI.defaultOutputFolderButton.clicked.connect(self.selectDefaultOutputFolder)
        GUI.clearButton.clicked.connect(self.clearJobs)
        GUI.fileButton.clicked.connect(self.selectFile)
        GUI.editorButton.clicked.connect(self.selectFileMetaEditor)
        GUI.wikiButton.clicked.connect(self.openWiki)
        GUI.kofiButton.clicked.connect(self.openKofi)
        GUI.convertButton.clicked.connect(self.convertStart)
        GUI.gammaSlider.valueChanged.connect(self.changeGamma)
        GUI.gammaBox.stateChanged.connect(self.togglegammaBox)
        GUI.croppingBox.stateChanged.connect(self.togglecroppingBox)
        GUI.croppingPowerSlider.valueChanged.connect(self.changeCroppingPower)
        GUI.webtoonBox.stateChanged.connect(self.togglewebtoonBox)
        GUI.qualityBox.stateChanged.connect(self.togglequalityBox)
        GUI.mozJpegBox.stateChanged.connect(self.toggleImageFormatBox)
        GUI.chunkSizeCheckBox.stateChanged.connect(self.togglechunkSizeCheckBox)
        GUI.deviceBox.activated.connect(self.changeDevice)
        GUI.formatBox.activated.connect(self.changeFormat)
        GUI.titleEdit.textChanged.connect(self.toggletitleEdit)
        GUI.fileFusionBox.stateChanged.connect(self.togglefileFusionBox)
        GUI.metadataTitleBox.stateChanged.connect(self.togglemetadataTitleBox)
        GUI.jobList.itemDoubleClicked.connect(self.editSourceMetadata)
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
            elif 'reM' in profile:
                GUI.deviceBox.addItem(self.icons.deviceRmk, profile)
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
                    GUI.preserveMarginBox.setValue(self.options.get('preserveMarginBox', 0))
            elif str(option) == "chunkSizeBox":
                GUI.chunkSizeBox.setValue(int(self.options[option]))
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
        for field in (self.seriesLine, self.volumeLine, self.numberLine, self.titleLine):
            field.setText(self.parser.data[field.objectName().capitalize()[:-4]])
        for field in (self.writerLine, self.pencillerLine, self.inkerLine, self.coloristLine):
            field.setText(', '.join(self.parser.data[field.objectName().capitalize()[:-4] + 's']))
        for field in (self.seriesLine, self.titleLine):
            if field.text() == '':
                path = Path(file)
                if file.endswith('.xml'):
                    field.setText(path.parent.name)
                else:
                    field.setText(path.stem)

    def saveData(self):
        for field in (self.volumeLine, self.numberLine):
            if field.text().isnumeric() or self.cleanData(field.text()) == '':
                self.parser.data[field.objectName().capitalize()[:-4]] = self.cleanData(field.text())
            else:
                self.statusLabel.setText(field.objectName().capitalize()[:-4] + ' field must be a number.')
                break
        else:
            for field in (self.seriesLine, self.titleLine):
                self.parser.data[field.objectName().capitalize()[:-4]] = self.cleanData(field.text())
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
        self.ui = QDialog()
        self.parser = None
        self.setupUi(self.ui)
        self.ui.setWindowFlags(self.ui.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.okButton.clicked.connect(self.saveData)
        self.cancelButton.clicked.connect(self.ui.close)
        if sys.platform.startswith('linux'):
            self.ui.resize(450, 260)
            self.ui.setMinimumSize(QSize(450, 260))
        elif sys.platform.startswith('darwin'):
            self.ui.resize(450, 310)
            self.ui.setMinimumSize(QSize(450, 310))
