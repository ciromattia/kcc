# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2014 Pawel Jastrzebski <pawelj@iosphe.re>
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

__version__ = '4.0.2'
__license__ = 'ISC'
__copyright__ = '2012-2014, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@iosphe.re>'
__docformat__ = 'restructuredtext en'

import os
import sys
from urllib.parse import unquote
from urllib.request import urlopen, urlretrieve
from socket import gethostbyname_ex, gethostname
from traceback import format_tb
from time import sleep
from shutil import move
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from subprocess import STDOUT, PIPE
from PyQt5 import QtGui, QtCore, QtWidgets
from xml.dom.minidom import parse
from html.parser import HTMLParser
from psutil import virtual_memory, Popen, Process
from uuid import uuid4
from .shared import md5Checksum
from . import comic2ebook
from . import dualmetafix
from . import KCC_rc_web
if sys.platform.startswith('darwin'):
    from . import KCC_ui_osx as KCC_ui
elif sys.platform.startswith('linux'):
    from . import KCC_ui_linux as KCC_ui
else:
    from . import KCC_ui


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


class HTMLStripper(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


class WebServerHandler(BaseHTTPRequestHandler):
    # noinspection PyAttributeOutsideInit, PyArgumentList
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        try:
            sendReply = False
            mimetype = None
            if self.path.endswith('.mobi'):
                mimetype = 'application/x-mobipocket-ebook'
                sendReply = True
            if self.path.endswith('.epub'):
                mimetype = 'application/epub+zip'
                sendReply = True
            if self.path.endswith('.cbz'):
                mimetype = 'application/x-cbz'
                sendReply = True
            if self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes('<!DOCTYPE html>\n'
                                 '<html lang="en">\n'
                                 '<head><meta charset="utf-8">\n'
                                 '<link href="' + GUI.webContent.favicon + '" rel="icon" type="image/x-icon" />\n'
                                 '<title>Kindle Comic Converter</title>\n'
                                 '</head>\n'
                                 '<body>\n'
                                 '<div style="text-align: center; font-size:25px">\n'
                                 '<p style="font-size:50px">- <img style="vertical-align: middle" '
                                 'alt="KCC Logo" src="' + GUI.webContent.logo + '" /> -</p>\n', 'UTF-8'))
                if len(GUI.completedWork) > 0 and not GUI.conversionAlive:
                    for key in sorted(GUI.completedWork.keys()):
                        self.wfile.write(bytes('<p><a href="' + key + '">' + key.split('.')[0] + '</a></p>\n', 'UTF-8'))
                else:
                    self.wfile.write(bytes('<p style="font-weight: bold">No downloads are available.<br/>'
                                     'Convert some files and refresh this page.</p>\n', 'UTF-8'))
                self.wfile.write(bytes('</div>\n'
                                 '</body>\n'
                                 '</html>\n', 'UTF-8'))
            elif sendReply:
                outputFile = GUI.completedWork[unquote(self.path[1:])]
                fp = open(outputFile, 'rb')
                self.send_response(200)
                self.send_header('Content-type', mimetype)
                self.send_header('Content-Length', os.path.getsize(outputFile))
                self.end_headers()
                while True:
                    chunk = fp.read(8192)
                    if not chunk:
                        fp.close()
                        break
                    self.wfile.write(chunk)
            return
        except (IOError, LookupError):
            self.send_error(404, 'File Not Found: %s' % self.path)


class WebServerThreaded(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


class WebServerThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.server = None
        self.running = False

    def __del__(self):
        self.wait()

    def run(self):
        try:
            # Sweet cross-platform one-liner to get LAN ip address
            lIP = [ip for ip in gethostbyname_ex(gethostname())[2] if not ip.startswith("127.")][:1][0]
        except Exception:
            # Sadly it can fail on some Linux configurations
            lIP = None
        try:
            self.server = WebServerThreaded(('', 4242), WebServerHandler)
            self.running = True
            if lIP:
                MW.addMessage.emit('<b><a href="http://' + str(lIP) + ':4242/">Content server</a></b> started.', 'info',
                                   False)
            else:
                MW.addMessage.emit('<b>Content server</b> started on port 4242.', 'info', False)
            while self.running:
                self.server.handle_request()
        except Exception:
            MW.addMessage.emit('<b>Content server</b> failed to start!', 'error', False)

    def stop(self):
        self.running = False


class VersionThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.newVersion = ''
        self.md5 = ''

    def __del__(self):
        self.wait()

    def run(self):
        try:
            sleep(1)
            XML = urlopen('http://kcc.iosphe.re/Version.php')
            XML = parse(XML)
        except Exception:
            return
        latestVersion = XML.childNodes[0].getElementsByTagName('latest')[0].childNodes[0].toxml()
        if tuple(map(int, (latestVersion.split(".")))) > tuple(map(int, (__version__.split(".")))):
            if sys.platform.startswith('win'):
                self.newVersion = latestVersion
                self.md5 = XML.childNodes[0].getElementsByTagName('WindowsMD5')[0].childNodes[0].toxml()
                MW.showDialog.emit('<b>New version released!</b> <a href="https://github.com/ciromattia/kcc/releases/">'
                                   'See changelog.</a><<br/><br/>Installed version: ' + __version__ +
                                   '<br/>Current version: ' + latestVersion +
                                   '<br/><br/>Would you like to start automatic update?', 'question')
            else:
                MW.addMessage.emit('<a href="http://kcc.iosphe.re/">'
                                   '<b>New version is available!</b></a> '
                                   '(<a href="https://github.com/ciromattia/kcc/releases/">'
                                   'Changelog</a>)', 'warning', False)

    def getNewVersion(self, dialogAnswer):
        if dialogAnswer == QtWidgets.QMessageBox.Yes:
            try:
                MW.modeConvert.emit(-1)
                MW.progressBarTick.emit('Downloading update')
                path = urlretrieve('http://kcc.iosphe.re/Windows/KindleComicConverter_win_'
                                   + self.newVersion + '.exe', reporthook=self.getNewVersionTick)
                if self.md5 != md5Checksum(path[0]):
                    raise Exception
                move(path[0], path[0] + '.exe')
                MW.hideProgressBar.emit()
                MW.modeConvert.emit(1)
                Popen(path[0] + '.exe  /SP- /silent /noicons')
                MW.forceShutdown.emit()
            except Exception:
                MW.addMessage.emit('Failed to download update!', 'warning', False)
                MW.hideProgressBar.emit()
                MW.modeConvert.emit(1)

    def getNewVersionTick(self, size, blockSize, totalSize):
        if size == 0:
            MW.progressBarTick.emit(str(int(totalSize / blockSize)))
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


class WorkerSignals(QtCore.QObject):
    result = QtCore.pyqtSignal(list)


class DualMetaFixThread(QtCore.QRunnable):
    def __init__(self, batch):
        super(DualMetaFixThread, self).__init__()
        self.signals = WorkerSignals()
        self.work = batch

    def run(self):
        item = self.work
        os.remove(item)
        mobiPath = item.replace('.epub', '.mobi')
        move(mobiPath, mobiPath + '_toclean')
        try:
            # noinspection PyArgumentList
            dualmetafix.DualMobiMetaFix(mobiPath + '_toclean', mobiPath, bytes(str(uuid4()), 'UTF-8'))
            self.signals.result.emit([True])
        except Exception as err:
            self.signals.result.emit([False, format(err)])


class WorkerThread(QtCore.QThread):
    #noinspection PyArgumentList
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.pool = QtCore.QThreadPool()
        self.conversionAlive = False
        self.errors = False
        self.kindlegenErrorCode = [0]
        self.workerOutput = []
        # Let's make sure that we don't fill the memory
        availableMemory = virtual_memory().total/1000000000
        if availableMemory <= 2:
            self.threadNumber = 1
        elif 2 < availableMemory <= 4:
            self.threadNumber = 2
        else:
            self.threadNumber = 4
        # Let's make sure that we don't use too many threads
        if self.threadNumber > QtCore.QThread.idealThreadCount():
            self.threadNumber = QtCore.QThread.idealThreadCount()
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

    def addResult(self, output):
        MW.progressBarTick.emit('tick')
        self.workerOutput.append(output)

    def run(self):
        MW.modeConvert.emit(0)

        parser = comic2ebook.makeParser()
        options, _ = parser.parse_args()

        profile = GUI.profiles[str(GUI.DeviceBox.currentText())]['Label']
        options.profile = profile
        argv = ''
        currentJobs = []

        # Basic mode settings
        if GUI.MangaBox.isChecked():
            options.righttoleft = True
        if GUI.RotateBox.isChecked():
            options.roate = True
        if GUI.QualityBox.checkState() == 1:
            options.quality = 1
        elif GUI.QualityBox.checkState() == 2:
            options.quality = 2
        if str(GUI.FormatBox.currentText()) == 'CBZ':
            options.cbzoutput = True
        if GUI.currentMode == 1:
            if profile in ['KFHD', 'KFHD8', 'KFHDX', 'KFHDX8']:
                options.upscale = True

        # Advanced mode settings
        if GUI.currentMode > 1:
            if GUI.ProcessingBox.isChecked():
                options.imgproc = False
            if GUI.NoRotateBox.isChecked():
                options.nosplitrotate = True
            if GUI.UpscaleBox.checkState() == 1:
                options.stretch = True
            elif GUI.UpscaleBox.checkState() == 2:
                options.upscale = True
            if GUI.BorderBox.checkState() == 1:
                options.white_borders = True
            elif GUI.BorderBox.checkState() == 2:
                options.black_borders = True
            if GUI.NoDitheringBox.isChecked():
                options.forcepng = True
            if GUI.WebtoonBox.isChecked():
                options.webtoon = True
            if float(GUI.GammaValue) > 0.09:
                # noinspection PyTypeChecker
                options.gamma = float(GUI.GammaValue)
            if str(GUI.FormatBox.currentText()) == 'MOBI':
                options.batchsplit = True

        # Other/custom settings.
        if GUI.currentMode > 2:
            options.customwidth = str(GUI.customWidth.text())
            options.customheight = str(GUI.customHeight.text())
            if GUI.ColorBox.isChecked():
                options.forcecolor = True

        comic2ebook.options = options
        comic2ebook.checkOptions()

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
                    MW.addMessage.emit('Failed to create output file!', 'error', False)
                    MW.addTrayMessage.emit('Failed to create output file!', 'Critical')
            except Exception as err:
                GUI.progress.content = ''
                self.errors = True
                _, _, traceback = sys.exc_info()
                MW.showDialog.emit("Error during conversion %s:\n\n%s\n\nTraceback:\n%s"
                                   % (jobargv[-1], str(err), "".join(format_tb(traceback))), 'error')
                MW.addMessage.emit('Failed to create EPUB!', 'error', False)
                MW.addTrayMessage.emit('Failed to create EPUB!', 'Critical')
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
                if str(GUI.FormatBox.currentText()) == 'MOBI':
                    MW.progressBarTick.emit('Creating MOBI files')
                    MW.progressBarTick.emit(str(len(outputPath)*2+1))
                    MW.progressBarTick.emit('tick')
                    MW.addMessage.emit('Creating MOBI files', 'info', False)
                    GUI.progress.content = 'Creating MOBI files'
                    self.workerOutput = []
                    # Number of KindleGen threads depends on the size of RAM
                    self.pool.setMaxThreadCount(self.threadNumber)

                    self.workerOutput = comic2ebook.batchConvert(outputPath)

                    self.kindlegenErrorCode = [0]
                    for errors in self.workerOutput:
                        if errors[0] != 0:
                            self.kindlegenErrorCode = errors
                            break
                    if not self.conversionAlive:
                        for item in outputPath:
                            if os.path.exists(item):
                                os.remove(item)
                            sleep(1)
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
                        # DualMetaFix is very fast and there is not reason to use multithreading.
                        self.pool.setMaxThreadCount(1)
                        for item in outputPath:
                            worker = DualMetaFixThread(item)
                            worker.signals.result.connect(self.addResult)
                            self.pool.start(worker)
                        self.pool.waitForDone()
                        sleep(0.5)
                        for success in self.workerOutput:
                            if not success[0]:
                                self.errors = True
                                break
                        if not self.errors:
                            for item in outputPath:
                                GUI.progress.content = ''
                                mobiPath = item.replace('.epub', '.mobi')
                                os.remove(mobiPath + '_toclean')
                                if GUI.targetDirectory and GUI.targetDirectory != os.path.split(mobiPath)[0]:
                                    try:
                                        move(mobiPath, GUI.targetDirectory)
                                        mobiPath = os.path.join(GUI.targetDirectory, os.path.basename(mobiPath))
                                    except Exception:
                                        pass
                                GUI.completedWork[os.path.basename(mobiPath)] = mobiPath
                            MW.addMessage.emit('Processing MOBI files... <b>Done!</b>', 'info', True)
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
                        epubSize = (os.path.getsize(self.kindlegenErrorCode[2]))//1024//1024
                        for item in outputPath:
                            if os.path.exists(item):
                                os.remove(item)
                            sleep(1)
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
                        if GUI.targetDirectory and GUI.targetDirectory != os.path.split(item)[0]:
                            try:
                                move(item, GUI.targetDirectory)
                                item = os.path.join(GUI.targetDirectory, os.path.basename(item))
                            except Exception:
                                pass
                        GUI.completedWork[os.path.basename(item)] = item
        GUI.progress.content = ''
        GUI.progress.stop()
        MW.hideProgressBar.emit()
        GUI.needClean = True
        MW.addMessage.emit('<b>All jobs completed.</b>', 'info', False)
        MW.addTrayMessage.emit('All jobs completed.', 'Information')
        MW.modeConvert.emit(1)


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self):
        if self.isSystemTrayAvailable():
            QtWidgets.QSystemTrayIcon.__init__(self, GUI.icons.programIcon, MW)
            # noinspection PyUnresolvedReferences
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

    def clearJobs(self):
        GUI.JobList.clear()

    def modeBasic(self):
        self.currentMode = 1
        if sys.platform.startswith('darwin'):
            MW.setMaximumSize(QtCore.QSize(420, 291))
            MW.setMinimumSize(QtCore.QSize(420, 291))
            MW.resize(420, 291)
        else:
            MW.setMaximumSize(QtCore.QSize(420, 287))
            MW.setMinimumSize(QtCore.QSize(420, 287))
            MW.resize(420, 287)
        GUI.BasicModeButton.setEnabled(True)
        GUI.AdvModeButton.setEnabled(True)
        GUI.BasicModeButton.setStyleSheet('font-weight:Bold;')
        GUI.AdvModeButton.setStyleSheet('font-weight:Normal;')
        GUI.FormatBox.setEnabled(False)
        GUI.OptionsBasic.setEnabled(True)
        GUI.OptionsBasic.setVisible(True)
        GUI.MangaBox.setChecked(False)
        GUI.RotateBox.setChecked(False)
        GUI.QualityBox.setChecked(False)
        GUI.OptionsAdvanced.setEnabled(False)
        GUI.OptionsAdvanced.setVisible(False)
        GUI.ProcessingBox.setChecked(False)
        GUI.UpscaleBox.setChecked(False)
        GUI.NoRotateBox.setChecked(False)
        GUI.BorderBox.setChecked(False)
        GUI.WebtoonBox.setChecked(False)
        GUI.NoDitheringBox.setChecked(False)
        GUI.OptionsAdvancedGamma.setEnabled(False)
        GUI.OptionsAdvancedGamma.setVisible(False)
        GUI.OptionsExpert.setEnabled(False)
        GUI.OptionsExpert.setVisible(False)
        GUI.ColorBox.setChecked(False)

    def modeAdvanced(self):
        self.currentMode = 2
        MW.setMaximumSize(QtCore.QSize(420, 365))
        MW.setMinimumSize(QtCore.QSize(420, 365))
        MW.resize(420, 365)
        GUI.BasicModeButton.setEnabled(True)
        GUI.AdvModeButton.setEnabled(True)
        GUI.BasicModeButton.setStyleSheet('font-weight:Normal;')
        GUI.AdvModeButton.setStyleSheet('font-weight:Bold;')
        GUI.FormatBox.setEnabled(True)
        GUI.OptionsBasic.setEnabled(True)
        GUI.OptionsBasic.setVisible(True)
        GUI.MangaBox.setChecked(False)
        GUI.RotateBox.setChecked(False)
        GUI.QualityBox.setChecked(False)
        GUI.OptionsAdvanced.setEnabled(True)
        GUI.OptionsAdvanced.setVisible(True)
        GUI.ProcessingBox.setChecked(False)
        GUI.UpscaleBox.setChecked(False)
        GUI.NoRotateBox.setChecked(False)
        GUI.BorderBox.setChecked(False)
        GUI.WebtoonBox.setChecked(False)
        GUI.NoDitheringBox.setChecked(False)
        GUI.OptionsAdvancedGamma.setEnabled(True)
        GUI.OptionsAdvancedGamma.setVisible(True)
        GUI.OptionsExpert.setEnabled(True)
        GUI.OptionsExpert.setVisible(True)
        GUI.ColorBox.setChecked(False)

    def modeExpert(self):
        self.currentMode = 3
        MW.setMaximumSize(QtCore.QSize(420, 397))
        MW.setMinimumSize(QtCore.QSize(420, 397))
        MW.resize(420, 397)
        GUI.BasicModeButton.setEnabled(False)
        GUI.AdvModeButton.setEnabled(False)
        GUI.BasicModeButton.setStyleSheet('font-weight:Normal;')
        GUI.AdvModeButton.setStyleSheet('font-weight:Normal;')
        GUI.FormatBox.setEnabled(True)
        GUI.OptionsBasic.setEnabled(True)
        GUI.OptionsBasic.setVisible(True)
        GUI.MangaBox.setChecked(False)
        GUI.RotateBox.setChecked(False)
        GUI.QualityBox.setChecked(False)
        GUI.OptionsAdvanced.setEnabled(True)
        GUI.OptionsAdvanced.setVisible(True)
        GUI.ProcessingBox.setChecked(False)
        GUI.UpscaleBox.setChecked(False)
        GUI.NoRotateBox.setChecked(False)
        GUI.BorderBox.setChecked(False)
        GUI.WebtoonBox.setChecked(False)
        GUI.NoDitheringBox.setChecked(False)
        GUI.OptionsAdvancedGamma.setEnabled(True)
        GUI.OptionsAdvancedGamma.setVisible(True)
        GUI.OptionsExpert.setEnabled(True)
        GUI.OptionsExpert.setVisible(True)
        GUI.ColorBox.setChecked(False)

    def modeConvert(self, enable):
        if enable < 1:
            status = False
        else:
            status = True
        if self.currentMode != 3:
            GUI.BasicModeButton.setEnabled(status)
            GUI.AdvModeButton.setEnabled(status)
        if self.currentMode != 1:
            GUI.FormatBox.setEnabled(status)
        GUI.DirectoryButton.setEnabled(status)
        GUI.ClearButton.setEnabled(status)
        GUI.FileButton.setEnabled(status)
        GUI.DeviceBox.setEnabled(status)
        GUI.OptionsBasic.setEnabled(status)
        GUI.OptionsAdvanced.setEnabled(status)
        GUI.OptionsAdvancedGamma.setEnabled(status)
        GUI.OptionsExpert.setEnabled(status)
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

    def toggleWebtoonBox(self, value):
        if value:
            GUI.NoRotateBox.setEnabled(False)
            GUI.NoRotateBox.setChecked(True)
            GUI.QualityBox.setEnabled(False)
            GUI.QualityBox.setChecked(False)
            GUI.MangaBox.setEnabled(False)
            GUI.MangaBox.setChecked(False)
        else:
            if not GUI.ProcessingBox.isChecked():
                GUI.NoRotateBox.setEnabled(True)
                GUI.QualityBox.setEnabled(True)
            GUI.MangaBox.setEnabled(True)

    def toggleNoSplitRotate(self, value):
        if value:
            GUI.RotateBox.setEnabled(False)
            GUI.RotateBox.setChecked(False)
        else:
            if not GUI.ProcessingBox.isChecked():
                GUI.RotateBox.setEnabled(True)

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
            GUI.UpscaleBox.setEnabled(True)
            GUI.NoRotateBox.setEnabled(True)
            GUI.BorderBox.setEnabled(True)
            GUI.WebtoonBox.setEnabled(True)
            GUI.NoDitheringBox.setEnabled(True)
            GUI.ColorBox.setEnabled(True)
            GUI.GammaSlider.setEnabled(True)
            GUI.GammaLabel.setEnabled(True)
            if GUI.profiles[str(GUI.DeviceBox.currentText())]['Quality']:
                GUI.QualityBox.setEnabled(True)

    def toggleQualityBox(self, value):
        if value == 2 and 'Kobo' in str(GUI.DeviceBox.currentText()):
            self.addMessage('Kobo devices can\'t use ultra quality mode!', 'warning')
            GUI.QualityBox.setCheckState(0)

    def changeGamma(self, value):
        value = float(value)
        value = '%.2f' % (value/100)
        if float(value) <= 0.09:
            GUI.GammaLabel.setText('Gamma: Auto')
        else:
            GUI.GammaLabel.setText('Gamma: ' + str(value))
        self.GammaValue = value

    def changeDevice(self):
        if self.currentMode == 1:
            self.modeBasic()
        elif self.currentMode == 2:
            self.modeAdvanced()
        elif self.currentMode == 3:
            self.modeExpert()
        profile = GUI.profiles[str(GUI.DeviceBox.currentText())]
        if profile['ForceExpert']:
            self.modeExpert()
            GUI.BasicModeButton.setEnabled(False)
            GUI.AdvModeButton.setEnabled(False)
        else:
            GUI.BasicModeButton.setEnabled(True)
            GUI.AdvModeButton.setEnabled(True)
            if self.currentMode == 3:
                self.modeBasic()
        self.changeFormat()
        GUI.GammaSlider.setValue(0)
        self.changeGamma(0)
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
            if GUI.FormatBox.count() == 3:
                GUI.FormatBox.setCurrentIndex(profile['DefaultFormat'])
            else:
                if profile['DefaultFormat'] != 0:
                    tmpFormat = profile['DefaultFormat'] - 1
                else:
                    tmpFormat = 0
                GUI.FormatBox.setCurrentIndex(tmpFormat)
        if GUI.WebtoonBox.isChecked():
            GUI.MangaBox.setEnabled(False)
            GUI.QualityBox.setEnabled(False)
            GUI.MangaBox.setChecked(False)
            GUI.QualityBox.setChecked(False)
        else:
            GUI.QualityBox.setEnabled(profile['Quality'])
            if not profile['Quality']:
                GUI.QualityBox.setChecked(False)
        if GUI.ProcessingBox.isChecked():
            GUI.QualityBox.setEnabled(False)
            GUI.QualityBox.setChecked(False)

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
            GUI.JobList.takeItem(GUI.JobList.count()-1)
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
        elif kind == 'question':
            dialogResponse = QtWidgets.QMessageBox.question(MW, 'KCC - Question', message,
                                                            QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            MW.dialogAnswer.emit(dialogResponse)

    def updateProgressbar(self, command):
        if command == 'tick':
            GUI.ProgressBar.setValue(GUI.ProgressBar.value() + 1)
        elif command.isdigit():
            GUI.ProgressBar.setMaximum(int(command) - 1)
            GUI.BasicModeButton.hide()
            GUI.AdvModeButton.hide()
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
            self.worker.start()

    def hideProgressBar(self):
        GUI.ProgressBar.hide()
        GUI.BasicModeButton.show()
        GUI.AdvModeButton.show()

    def saveSettings(self, event):
        if self.conversionAlive:
            GUI.ConvertButton.setEnabled(False)
            self.addMessage('Process will be interrupted. Please wait.', 'warning')
            self.conversionAlive = False
            self.worker.sync()
            event.ignore()
        if not GUI.ConvertButton.isEnabled():
            event.ignore()
        self.contentServer.stop()
        self.settings.setValue('settingsVersion', __version__)
        self.settings.setValue('lastPath', self.lastPath)
        self.settings.setValue('lastDevice', GUI.DeviceBox.currentIndex())
        self.settings.setValue('currentFormat', GUI.FormatBox.currentIndex())
        self.settings.setValue('currentMode', self.currentMode)
        self.settings.setValue('startNumber', self.startNumber + 1)
        self.settings.setValue('options', {'MangaBox': GUI.MangaBox.checkState(),
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
                                           'GammaSlider': float(self.GammaValue)*100})
        self.settings.sync()
        self.tray.hide()
        APP.shutdown()

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
            elif os.path.isfile(message):
                extension = os.path.splitext(message)
                if extension[1].lower() in formats:
                    GUI.JobList.addItem(message)
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

    # noinspection PyArgumentList
    def __init__(self, KCCAplication, KCCWindow):
        global APP, MW, GUI
        APP = KCCAplication
        MW = KCCWindow
        GUI = self
        self.setupUi(MW)
        # User settings will be reverted to default ones if were created in one of the following versions
        # Empty string cover all versions before this system was implemented
        purgeSettingsVersions = ['']
        self.icons = Icons()
        self.webContent = KCC_rc_web.WebContent()
        self.settings = QtCore.QSettings('KindleComicConverter', 'KindleComicConverter')
        self.settingsVersion = self.settings.value('settingsVersion', '', type=str)
        if self.settingsVersion in purgeSettingsVersions:
            QtCore.QSettings.clear(self.settings)
            self.settingsVersion = self.settings.value('settingsVersion', '', type=str)
        self.lastPath = self.settings.value('lastPath', '', type=str)
        self.lastDevice = self.settings.value('lastDevice', 0, type=int)
        self.currentMode = self.settings.value('currentMode', 1, type=int)
        self.currentFormat = self.settings.value('currentFormat', 0, type=int)
        self.startNumber = self.settings.value('startNumber', 0, type=int)
        self.options = self.settings.value('options', {'GammaSlider': 0})
        self.worker = WorkerThread()
        self.versionCheck = VersionThread()
        self.contentServer = WebServerThread()
        self.progress = ProgressThread()
        self.tray = SystemTrayIcon()
        self.conversionAlive = False
        self.needClean = True
        self.GammaValue = 1.0
        self.completedWork = {}
        self.targetDirectory = ''
        if sys.platform.startswith('darwin'):
            self.listFontSize = 11
            self.statusBarFontSize = 10
            self.statusBarStyle = 'QLabel{padding-top:2px;padding-bottom:3px;}'
            self.ProgressBar.setStyleSheet('QProgressBar{padding-top:5px;text-align:center;}')
        elif sys.platform.startswith('linux'):
            self.listFontSize = 8
            self.statusBarFontSize = 8
            self.statusBarStyle = 'QLabel{padding-top:5px;padding-bottom:3px;}'
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
            "Kindle Paperwhite": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 0,
                                  'DefaultUpscale': False, 'Label': 'KHD'},
            "Kindle": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 0,
                       'DefaultUpscale': False, 'Label': 'K345'},
            "Kindle DX/DXG": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 0,
                              'DefaultUpscale': False, 'Label': 'KDX'},
            "Kindle Fire": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 0,
                            'DefaultUpscale': False, 'Label': 'KF'},
            "K. Fire HD 7\"": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 0,
                               'DefaultUpscale': True, 'Label': 'KFHD'},
            "K. Fire HD 8.9\"": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 0,
                                 'DefaultUpscale': True, 'Label': 'KFHD8'},
            "K. Fire HDX 7\"": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 0,
                                'DefaultUpscale': True, 'Label': 'KFHDX'},
            "K. Fire HDX 8.9\"": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 0,
                                  'DefaultUpscale': True, 'Label': 'KFHDX8'},
            "Kobo Mini/Touch": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 2,
                                'DefaultUpscale': False, 'Label': 'KoMT'},
            "Kobo Glow": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 2,
                          'DefaultUpscale': False, 'Label': 'KoG'},
            "Kobo Aura": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 2,
                          'DefaultUpscale': False, 'Label': 'KoA'},
            "Kobo Aura HD": {'Quality': True, 'ForceExpert': False, 'DefaultFormat': 2,
                             'DefaultUpscale': False, 'Label': 'KoAHD'},
            "Other": {'Quality': False, 'ForceExpert': True, 'DefaultFormat': 1,
                      'DefaultUpscale': False, 'Label': 'OTHER'},
            "Kindle for Android": {'Quality': False, 'ForceExpert': True, 'DefaultFormat': 0,
                                   'DefaultUpscale': False, 'Label': 'KFA'},
            "Kindle 1": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 0,
                         'DefaultUpscale': False, 'Label': 'K1'},
            "Kindle 2": {'Quality': False, 'ForceExpert': False, 'DefaultFormat': 0,
                         'DefaultUpscale': False, 'Label': 'K2'}
        }
        profilesGUI = [
            "Kindle Paperwhite",
            "Kindle",
            "Kindle DX/DXG",
            "Separator",
            "Kindle Fire",
            "K. Fire HD 7\"",
            "K. Fire HD 8.9\"",
            "K. Fire HDX 7\"",
            "K. Fire HDX 8.9\"",
            "Separator",
            "Kobo Mini/Touch",
            "Kobo Glow",
            "Kobo Aura",
            "Kobo Aura HD",
            "Separator",
            "Other",
            "Separator",
            "Kindle for Android",
            "Kindle 1",
            "Kindle 2",
        ]

        statusBarLabel = QtWidgets.QLabel('<b><a href="http://kcc.iosphe.re/">HOMEPAGE</a> - <a href="https://github.'
                                          'com/ciromattia/kcc/blob/master/README.md#issues--new-features--donations">DO'
                                          'NATE</a> - <a href="https://github.com/ciromattia/kcc/wiki">WIKI</a> - <a hr'
                                          'ef="http://www.mobileread.com/forums/showthread.php?t=207461">FORUM</a></b>')
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
        kindleGenExitCode = Popen('kindlegen -locale en', stdout=PIPE, stderr=STDOUT, shell=True)
        if kindleGenExitCode.wait() == 0:
            self.KindleGen = True
            formats = ['MOBI', 'EPUB', 'CBZ']
            versionCheck = Popen('kindlegen -locale en', stdout=PIPE, stderr=STDOUT, shell=True)
            for line in versionCheck.stdout:
                line = line.decode("utf-8")
                if 'Amazon kindlegen' in line:
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
            if sys.platform.startswith('win'):
                self.addMessage('Cannot find <a href="http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211">'
                                'kindlegen</a> in KCC directory! MOBI creation will be disabled.', 'warning')
            else:
                self.addMessage('Cannot find <a href="http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211">'
                                'kindlegen</a> in PATH! MOBI creation will be disabled.', 'warning')
        rarExitCode = Popen('unrar', stdout=PIPE, stderr=STDOUT, shell=True)
        rarExitCode = rarExitCode.wait()
        if rarExitCode == 0 or rarExitCode == 7:
            self.UnRAR = True
        else:
            self.UnRAR = False
            self.addMessage('Cannot find <a href="http://www.rarlab.com/rar_add.htm">UnRAR</a>!'
                            ' Processing of CBR/RAR files will be disabled.', 'warning')
        sevenzaExitCode = Popen('7za', stdout=PIPE, stderr=STDOUT, shell=True)
        sevenzaExitCode = sevenzaExitCode.wait()
        if sevenzaExitCode == 0 or sevenzaExitCode == 7:
            self.sevenza = True
        else:
            self.sevenza = False
            self.addMessage('Cannot find <a href="http://www.7-zip.org/download.html">7za</a>!'
                            ' Processing of CB7/7Z files will be disabled.', 'warning')

        APP.messageFromOtherInstance.connect(self.handleMessage)
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
        GUI.QualityBox.stateChanged.connect(self.toggleQualityBox)
        GUI.DeviceBox.activated.connect(self.changeDevice)
        GUI.FormatBox.activated.connect(self.changeFormat)
        MW.progressBarTick.connect(self.updateProgressbar)
        MW.modeConvert.connect(self.modeConvert)
        MW.addMessage.connect(self.addMessage)
        MW.showDialog.connect(self.showDialog)
        MW.hideProgressBar.connect(self.hideProgressBar)
        MW.forceShutdown.connect(self.forceShutdown)
        MW.dialogAnswer.connect(self.versionCheck.getNewVersion)
        MW.closeEvent = self.saveSettings
        MW.addTrayMessage.connect(self.tray.addTrayMessage)

        GUI.Form.setAcceptDrops(True)
        GUI.Form.dragEnterEvent = self.dragAndDrop
        GUI.Form.dropEvent = self.dragAndDropAccepted

        for profile in profilesGUI:
            if profile == "Other":
                GUI.DeviceBox.addItem(self.icons.deviceOther, profile)
            elif profile == "Separator":
                GUI.DeviceBox.insertSeparator(GUI.DeviceBox.count()+1)
            elif 'Ko' in profile:
                GUI.DeviceBox.addItem(self.icons.deviceKobo, profile)
            else:
                GUI.DeviceBox.addItem(self.icons.deviceKindle, profile)
        for f in formats:
            GUI.FormatBox.addItem(eval('self.icons.' + f + 'Format'), f)
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
                if eval('GUI.' + str(option)).isEnabled():
                    eval('GUI.' + str(option)).setCheckState(self.options[option])
        self.hideProgressBar()
        self.worker.sync()
        self.versionCheck.start()
        self.contentServer.start()
        self.tray.show()
        MW.setWindowTitle("Kindle Comic Converter " + __version__)
        MW.show()
        MW.raise_()
