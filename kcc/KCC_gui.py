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

__version__ = '3.6'
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import os
import sys
import traceback
import urllib2
import socket
import comic2ebook
import kindlesplit
from string import split
from time import sleep
from shutil import move
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from image import ProfileData
from subprocess import STDOUT, PIPE
from PyQt4 import QtGui, QtCore
from xml.dom.minidom import parse
from HTMLParser import HTMLParser
from KCC_rc_web import WebContent
try:
    #noinspection PyUnresolvedReferences
    from psutil import TOTAL_PHYMEM, Popen
except ImportError:
    print "ERROR: Psutil is not installed!"
    if sys.platform.startswith('linux'):
        import Tkinter
        import tkMessageBox
        importRoot = Tkinter.Tk()
        importRoot.withdraw()
        tkMessageBox.showerror("KCC - Error", "Psutil is not installed!")
    exit(1)
if sys.platform.startswith('darwin'):
    import KCC_ui_osx as KCC_ui
elif sys.platform.startswith('linux'):
    import KCC_ui_linux as KCC_ui
else:
    import KCC_ui


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
    #noinspection PyAttributeOutsideInit
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
                self.wfile.write('<!DOCTYPE html>\n'
                                 '<html lang="en">\n'
                                 '<head><meta charset="utf-8">\n'
                                 '<link href="' + GUI.webContent.favicon + '" rel="icon" type="image/x-icon" />\n'
                                 '<title>Kindle Comic Converter</title>\n'
                                 '</head>\n'
                                 '<body>\n'
                                 '<div style="text-align: center; font-size:25px">\n'
                                 '<p style="font-size:50px">- <img style="vertical-align: middle" '
                                 'alt="KCC Logo" src="' + GUI.webContent.logo + '" /> -</p>\n')
                if len(GUI.completedWork) > 0 and not GUI.conversionAlive:
                    for key in sorted(GUI.completedWork.iterkeys()):
                        self.wfile.write('<p><a href="' + key + '">' + split(key, '.')[0] + '</a></p>\n')
                else:
                    self.wfile.write('<p style="font-weight: bold">No downloads are available.<br/>'
                                     'Convert some files and refresh this page.</p>\n')
                self.wfile.write('</div>\n'
                                 '</body>\n'
                                 '</html>\n')
            elif sendReply:
                outputFile = GUI.completedWork[urllib2.unquote(self.path[1:])].decode('utf-8')
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
            lIP = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1][0]
        except StandardError:
            # Sadly it can fail on some Linux configurations
            lIP = None
        try:
            self.server = WebServerThreaded(('', 4242), WebServerHandler)
            self.running = True
            if lIP:
                self.emit(QtCore.SIGNAL("addMessage"), '<b><a href="http://' + lIP +
                                                       ':4242/">Content server</a></b> started.', 'info')
            else:
                self.emit(QtCore.SIGNAL("addMessage"), '<b>Content server</b> started on port 4242.', 'info')
            while self.running:
                self.server.handle_request()
        except StandardError:
            self.emit(QtCore.SIGNAL("addMessage"), '<b>Content server</b> failed to start!', 'error')

    def stop(self):
        self.running = False


class VersionThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        try:
            XML = urllib2.urlopen('http://kcc.vulturis.eu/Version.php')
            XML = parse(XML)
        except StandardError:
            return
        latestVersion = XML.childNodes[0].getElementsByTagName('latest')[0].childNodes[0].toxml()
        if tuple(map(int, (latestVersion.split(".")))) > tuple(map(int, (__version__.split(".")))):
            self.emit(QtCore.SIGNAL("addMessage"), '<a href="http://kcc.vulturis.eu/">'
                                                   '<b>New version is available!</b></a> '
                                                   '(<a href="https://github.com/ciromattia/kcc/releases/">'
                                                   'Changelog</a>)', 'warning')


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
            if self.content:
                self.emit(QtCore.SIGNAL("addMessage"), self.content + self.progress * '.', 'info', True)
                self.progress += 1
                if self.progress == 4:
                    self.progress = 0

    def stop(self):
        self.running = False


class WorkerSignals(QtCore.QObject):
    result = QtCore.pyqtSignal(list)


class KindleGenThread(QtCore.QRunnable):
    def __init__(self, batch):
        super(KindleGenThread, self).__init__()
        self.signals = WorkerSignals()
        self.work = batch

    def run(self):
        kindlegenErrorCode = 0
        kindlegenError = ''
        try:
            if os.path.getsize(self.work) < 367001600:
                output = Popen('kindlegen -locale en "' + self.work.encode(sys.getfilesystemencoding()) + '"',
                               stdout=PIPE, stderr=STDOUT, shell=True)
                for line in output.stdout:
                    # ERROR: Generic error
                    if "Error(" in line:
                        kindlegenErrorCode = 1
                        kindlegenError = line
                    # ERROR: EPUB too big
                    if ":E23026:" in line:
                        kindlegenErrorCode = 23026
                    if kindlegenErrorCode > 0:
                        break
            else:
                # ERROR: EPUB too big
                kindlegenErrorCode = 23026
            self.signals.result.emit([kindlegenErrorCode, kindlegenError, self.work])
        except StandardError:
            # ERROR: Unknown generic error
            kindlegenErrorCode = 1
            self.signals.result.emit([kindlegenErrorCode, kindlegenError, self.work])


class KindleUnpackThread(QtCore.QRunnable):
    def __init__(self, batch):
        super(KindleUnpackThread, self).__init__()
        self.signals = WorkerSignals()
        self.work = batch

    def run(self):
        item = self.work[0]
        profile = self.work[1]
        os.remove(item)
        mobiPath = item.replace('.epub', '.mobi')
        move(mobiPath, mobiPath + '_toclean')
        try:
            # MOBI file produced by KindleGen is hybrid. KF8 + M7 + Source header
            # KindleSplit is removing redundant data as we need only KF8 part for new Kindle models
            if profile in ['K345', 'KHD', 'KF', 'KFHD', 'KFHD8', 'KFHDX', 'KFHDX8', 'KFA']:
                newKindle = True
            else:
                newKindle = False
            mobisplit = kindlesplit.mobi_split(mobiPath + '_toclean', newKindle)
            open(mobiPath, 'wb').write(mobisplit.getResult())
            self.signals.result.emit([True])
        except StandardError:
            self.signals.result.emit([False])


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
        availableMemory = TOTAL_PHYMEM/1000000000
        if availableMemory <= 2:
            self.threadNumber = 1
        elif 2 < availableMemory <= 4:
            self.threadNumber = 2
        else:
            self.threadNumber = 4
        # Let's make sure that we don't use too many threads
        if self.threadNumber > QtCore.QThread.idealThreadCount():
            self.threadNumber = QtCore.QThread.idealThreadCount()

    def __del__(self):
        self.wait()

    def sync(self):
        self.conversionAlive = GUI.conversionAlive

    def clean(self):
        GUI.progress.content = ''
        GUI.progress.stop()
        GUI.needClean = True
        self.emit(QtCore.SIGNAL("hideProgressBar"))
        self.emit(QtCore.SIGNAL("addMessage"), '<b>Conversion interrupted.</b>', 'error')
        self.emit(QtCore.SIGNAL("addTrayMessage"), 'Conversion interrupted.', 'Critical')
        self.emit(QtCore.SIGNAL("modeConvert"), True)

    def addResult(self, output):
        self.emit(QtCore.SIGNAL("progressBarTick"))
        self.workerOutput.append(output)

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
        if GUI.currentMode == 1:
            if profile in ['KFHD', 'KFHD8', 'KFHDX', 'KFHDX8']:
                argv.append("--upscale")
        if GUI.currentMode > 1:
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
            if float(GUI.GammaValue) > 0.09:
                # noinspection PyTypeChecker
                argv.append("--gamma=" + GUI.GammaValue)
            if str(GUI.FormatBox.currentText()) == 'CBZ':
                argv.append("--cbz-output")
            if str(GUI.FormatBox.currentText()) == 'MOBI':
                argv.append("--batchsplit")
        if GUI.currentMode > 2:
            argv.append("--customwidth=" + str(GUI.customWidth.text()))
            argv.append("--customheight=" + str(GUI.customHeight.text()))
            if GUI.ColorBox.isChecked():
                argv.append("--forcecolor")
        for i in range(GUI.JobList.count()):
            # Make sure that we don't consider any system message as job to do
            if GUI.JobList.item(i).icon().isNull():
                currentJobs.append(unicode(GUI.JobList.item(i).text()))
        GUI.JobList.clear()
        for job in currentJobs:
            sleep(0.5)
            if not self.conversionAlive:
                self.clean()
                return
            self.errors = False
            self.emit(QtCore.SIGNAL("addMessage"), '<b>Source:</b> ' + job, 'info')
            if str(GUI.FormatBox.currentText()) == 'CBZ':
                self.emit(QtCore.SIGNAL("addMessage"), 'Creating CBZ files', 'info')
                GUI.progress.content = 'Creating CBZ files'
            else:
                self.emit(QtCore.SIGNAL("addMessage"), 'Creating EPUB files', 'info')
                GUI.progress.content = 'Creating EPUB files'
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
                    GUI.progress.content = ''
                    self.errors = True
                    self.emit(QtCore.SIGNAL("addMessage"), str(warn), 'warning')
                    self.emit(QtCore.SIGNAL("addMessage"), 'Failed to create output file!', 'warning')
                    self.emit(QtCore.SIGNAL("addTrayMessage"), 'Failed to create output file!', 'Critical')
            except Exception as err:
                GUI.progress.content = ''
                self.errors = True
                type_, value_, traceback_ = sys.exc_info()
                self.emit(QtCore.SIGNAL("showDialog"), "Error during conversion %s:\n\n%s\n\nTraceback:\n%s"
                                                       % (jobargv[-1], str(err), traceback.format_tb(traceback_)))
                self.emit(QtCore.SIGNAL("addMessage"), 'Failed to create EPUB!', 'error')
                self.emit(QtCore.SIGNAL("addTrayMessage"), 'Failed to create EPUB!', 'Critical')
            if not self.conversionAlive:
                for item in outputPath:
                    if os.path.exists(item):
                        os.remove(item)
                self.clean()
                return
            if not self.errors:
                GUI.progress.content = ''
                if str(GUI.FormatBox.currentText()) == 'CBZ':
                    self.emit(QtCore.SIGNAL("addMessage"), 'Creating CBZ files... <b>Done!</b>', 'info', True)
                else:
                    self.emit(QtCore.SIGNAL("addMessage"), 'Creating EPUB files... <b>Done!</b>', 'info', True)
                if str(GUI.FormatBox.currentText()) == 'MOBI':
                    self.emit(QtCore.SIGNAL("progressBarTick"), 'status', 'Creating MOBI files')
                    self.emit(QtCore.SIGNAL("progressBarTick"), len(outputPath)*2+1)
                    self.emit(QtCore.SIGNAL("progressBarTick"))
                    self.emit(QtCore.SIGNAL("addMessage"), 'Creating MOBI files', 'info')
                    GUI.progress.content = 'Creating MOBI files'
                    self.workerOutput = []
                    # Number of KindleGen threads depends on the size of RAM
                    self.pool.setMaxThreadCount(self.threadNumber)
                    for item in outputPath:
                        worker = KindleGenThread(item)
                        worker.signals.result.connect(self.addResult)
                        self.pool.start(worker)
                    self.pool.waitForDone()
                    sleep(0.5)
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
                        self.emit(QtCore.SIGNAL("addMessage"), 'Creating MOBI files... <b>Done!</b>', 'info', True)
                        self.emit(QtCore.SIGNAL("addMessage"), 'Cleaning MOBI files', 'info')
                        GUI.progress.content = 'Cleaning MOBI files'
                        self.workerOutput = []
                        # Multithreading KindleUnpack in current form is a waste of resources.
                        # Unless we higly optimise KindleUnpack or drop 32bit support this will not change.
                        self.pool.setMaxThreadCount(1)
                        for item in outputPath:
                            worker = KindleUnpackThread([item, profile])
                            worker.signals.result.connect(self.addResult)
                            self.pool.start(worker)
                        self.pool.waitForDone()
                        sleep(0.5)
                        for success in self.workerOutput:
                            if not success:
                                self.errors = True
                                break
                        if not self.errors:
                            for item in outputPath:
                                GUI.progress.content = ''
                                mobiPath = item.replace('.epub', '.mobi')
                                os.remove(mobiPath + '_toclean')
                                GUI.completedWork[os.path.basename(mobiPath).encode('utf-8')] = \
                                    mobiPath.encode('utf-8')
                                self.emit(QtCore.SIGNAL("addMessage"), 'Cleaning MOBI files... <b>Done!</b>', 'info',
                                          True)
                        else:
                            GUI.progress.content = ''
                            for item in outputPath:
                                mobiPath = item.replace('.epub', '.mobi')
                                if os.path.exists(mobiPath):
                                    os.remove(mobiPath)
                                if os.path.exists(mobiPath + '_toclean'):
                                    os.remove(mobiPath + '_toclean')
                            self.emit(QtCore.SIGNAL("addMessage"), 'KindleUnpack failed to clean MOBI file!', 'error')
                            self.emit(QtCore.SIGNAL("addTrayMessage"), 'KindleUnpack failed to clean MOBI file!',
                                      'Critical')
                    else:
                        GUI.progress.content = ''
                        epubSize = (os.path.getsize(self.kindlegenErrorCode[2]))/1024/1024
                        for item in outputPath:
                            if os.path.exists(item):
                                os.remove(item)
                            if os.path.exists(item.replace('.epub', '.mobi')):
                                os.remove(item.replace('.epub', '.mobi'))
                        self.emit(QtCore.SIGNAL("addMessage"), 'KindleGen failed to create MOBI!', 'error')
                        self.emit(QtCore.SIGNAL("addTrayMessage"), 'KindleGen failed to create MOBI!', 'Critical')
                        if self.kindlegenErrorCode[0] == 1 and self.kindlegenErrorCode[1] != '':
                            self.emit(QtCore.SIGNAL("showDialog"), "KindleGen error:\n\n" +
                                                                   self.self.kindlegenErrorCode[1])
                        if self.kindlegenErrorCode[0] == 23026:
                            self.emit(QtCore.SIGNAL("addMessage"), 'Created EPUB file was too big.',
                                      'error')
                            self.emit(QtCore.SIGNAL("addMessage"), 'EPUB file: ' + str(epubSize) + 'MB.'
                                                                   ' Supported size: ~300MB.', 'error')
                else:
                    for item in outputPath:
                        GUI.completedWork[os.path.basename(item).encode('utf-8')] = item.encode('utf-8')
        GUI.progress.content = ''
        GUI.progress.stop()
        self.emit(QtCore.SIGNAL("hideProgressBar"))
        GUI.needClean = True
        self.emit(QtCore.SIGNAL("addMessage"), '<b>All jobs completed.</b>', 'info')
        self.emit(QtCore.SIGNAL("addTrayMessage"), 'All jobs completed.', 'Information')
        self.emit(QtCore.SIGNAL("modeConvert"), True)


class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self):
        if not sys.platform.startswith('darwin') and self.isSystemTrayAvailable():
            QtGui.QSystemTrayIcon.__init__(self, GUI.icons.programIcon, MW)
            self.activated.connect(self.catchClicks)

    def catchClicks(self):
        MW.showNormal()
        MW.raise_()
        MW.activateWindow()

    def addTrayMessage(self, message, icon):
        if not sys.platform.startswith('darwin'):
            icon = eval('QtGui.QSystemTrayIcon.' + icon)
            if self.supportsMessages() and not MW.isActiveWindow():
                self.showMessage('Kindle Comic Converter', message, icon)


class KCCGUI(KCC_ui.Ui_KCC):
    def selectDir(self):
        if self.needClean:
            self.needClean = False
            GUI.JobList.clear()
        # Dirty, dirty way but OS native QFileDialogs don't support directory multiselect
        dirDialog = QtGui.QFileDialog(MW, 'Select directory', self.lastPath)
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
        for dname in dnames:
            if unicode(dname) != "":
                if sys.platform == 'win32':
                    dname = dname.replace('/', '\\')
                self.lastPath = os.path.abspath(os.path.join(unicode(dname), os.pardir))
                GUI.JobList.addItem(dname)
        MW.setFocus()

    def selectFile(self):
        if self.needClean:
            self.needClean = False
            GUI.JobList.clear()
        if self.UnRAR:
            if self.sevenza:
                fnames = QtGui.QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                            '*.cbz *.cbr *.cb7 *.zip *.rar *.7z *.pdf')
            else:
                fnames = QtGui.QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                            '*.cbz *.cbr *.zip *.rar *.pdf')
        else:
            if self.sevenza:
                fnames = QtGui.QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                            '*.cbz *.cb7 *.zip *.7z *.pdf')
            else:
                fnames = QtGui.QFileDialog.getOpenFileNames(MW, 'Select file', self.lastPath,
                                                            '*.cbz *.zip *.pdf')
        for fname in fnames:
            if unicode(fname) != "":
                self.lastPath = os.path.abspath(os.path.join(unicode(fname), os.pardir))
                GUI.JobList.addItem(fname)

    def clearJobs(self):
        GUI.JobList.clear()

    def modeBasic(self):
        self.currentMode = 1
        if sys.platform.startswith('darwin'):
            MW.setMinimumSize(QtCore.QSize(420, 291))
            MW.setMaximumSize(QtCore.QSize(420, 291))
            MW.resize(420, 291)
        else:
            MW.setMinimumSize(QtCore.QSize(420, 287))
            MW.setMaximumSize(QtCore.QSize(420, 287))
            MW.resize(420, 287)
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
        MW.setMinimumSize(QtCore.QSize(420, 365))
        MW.setMaximumSize(QtCore.QSize(420, 365))
        MW.resize(420, 365)
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
        MW.setMinimumSize(QtCore.QSize(420, 397))
        MW.setMaximumSize(QtCore.QSize(420, 397))
        MW.resize(420, 397)
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
        if value in [9, 11, 12, 13]:
            GUI.QualityBox.setChecked(False)
            GUI.QualityBox.setEnabled(False)
            self.QualityBoxDisabled = True
        if value in [4, 5, 6, 7]:
            if GUI.UpscaleBox.isEnabled():
                GUI.UpscaleBox.setChecked(True)
        else:
            if not GUI.WebtoonBox.isChecked() and not GUI.ProcessingBox.isChecked() \
                    and str(GUI.FormatBox.currentText()) != 'CBZ' and value not in [9, 11, 12, 13]:
                GUI.QualityBox.setEnabled(True)
                self.QualityBoxDisabled = False

    def changeFormat(self):
        if str(GUI.FormatBox.currentText()) == 'CBZ':
            GUI.QualityBox.setChecked(False)
            GUI.QualityBox.setEnabled(False)
        else:
            if not GUI.WebtoonBox.isChecked() and not GUI.ProcessingBox.isChecked() and not self.QualityBoxDisabled:
                GUI.QualityBox.setEnabled(True)

    def stripTags(self, html):
        s = HTMLStripper()
        s.feed(html)
        return s.get_data()

    def addMessage(self, message, icon=None, replace=False):
        if icon:
            icon = eval('self.icons.' + icon)
            item = QtGui.QListWidgetItem(icon, '    ' + self.stripTags(message))
        else:
            item = QtGui.QListWidgetItem('    ' + self.stripTags(message))
        if replace:
            GUI.JobList.takeItem(GUI.JobList.count()-1)
        # Due to lack of HTML support in QListWidgetItem we overlay text field with QLabel
        # We still fill original text field with transparent content to trigger creation of horizontal scrollbar
        item.setTextColor(QtGui.QColor('transparent'))
        label = QtGui.QLabel(message)
        label.setStyleSheet('background-image:url('');background-color:rgba(255,0,0,0.5);')
        label.setOpenExternalLinks(True)
        font = QtGui.QFont()
        font.setPointSize(self.listFontSize)
        label.setFont(font)
        GUI.JobList.addItem(item)
        GUI.JobList.setItemWidget(item, label)
        GUI.JobList.scrollToBottom()

    def showDialog(self, message):
        QtGui.QMessageBox.critical(MW, 'KCC - Error', message, QtGui.QMessageBox.Ok)

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

    def handleMessage(self, message):
        MW.raise_()
        MW.activateWindow()
        if not self.conversionAlive:
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
        self.webContent = WebContent()
        self.tray = SystemTrayIcon()
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
        self.worker = WorkerThread()
        self.versionCheck = VersionThread()
        self.contentServer = WebServerThread()
        self.progress = ProgressThread()
        self.conversionAlive = False
        self.needClean = True
        self.QualityBoxDisabled = False
        self.GammaValue = 1.0
        self.completedWork = {}
        if sys.platform.startswith('darwin'):
            self.listFontSize = 11
            self.statusBarFontSize = 10
            self.statusBarStyle = 'QLabel{padding-top:5px;padding-bottom:5px;border-top:2px solid #C2C7CB}'
        elif sys.platform.startswith('linux'):
            self.listFontSize = 8
            self.statusBarFontSize = 8
            self.statusBarStyle = 'QLabel{padding-top:5px;padding-bottom:3px;border-top:2px solid #C2C7CB}'
            self.tray.show()
        else:
            self.listFontSize = 9
            self.statusBarFontSize = 8
            self.statusBarStyle = 'QLabel{padding-top:3px;padding-bottom:3px;border-top:2px solid #C2C7CB}'
            self.tray.show()

        statusBarLabel = QtGui.QLabel('<b><a href="http://kcc.vulturis.eu/">HOMEPAGE</a> - <a href="https://github.com/'
                                      'ciromattia/kcc/blob/master/README.md#issues--new-features--donations">DONATE</a>'
                                      ' - <a href="https://github.com/ciromattia/kcc/blob/master/README.md#kcc">README<'
                                      '/a> - <a href="https://github.com/ciromattia/kcc/wiki">WIKI</a></b>')
        statusBarLabel.setAlignment(QtCore.Qt.AlignCenter)
        statusBarLabel.setStyleSheet(self.statusBarStyle)
        statusBarLabel.setOpenExternalLinks(True)
        statusBarLabelFont = QtGui.QFont()
        statusBarLabelFont.setPointSize(self.statusBarFontSize)
        statusBarLabel.setFont(statusBarLabelFont)
        GUI.statusBar.addPermanentWidget(statusBarLabel, 1)

        self.addMessage('<b>Welcome!</b>', 'info')
        self.addMessage('<b>Remember:</b> All options have additional informations in tooltips.', 'info')
        if self.firstStart:
            self.addMessage('Since you are using <b>KCC</b> for first time please see few '
                            '<a href="https://github.com/ciromattia/kcc#important-tips">important tips</a>.', 'info')
        kindleGenExitCode = Popen('kindlegen -locale en', stdout=PIPE, stderr=STDOUT, shell=True)
        if kindleGenExitCode.wait() == 0:
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

        APP.connect(APP, QtCore.SIGNAL('messageFromOtherInstance'), self.handleMessage)
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
        MW.connect(self.worker, QtCore.SIGNAL("progressBarTick"), self.updateProgressbar)
        MW.connect(self.worker, QtCore.SIGNAL("modeConvert"), self.modeConvert)
        MW.connect(self.worker, QtCore.SIGNAL("addMessage"), self.addMessage)
        MW.connect(self.worker, QtCore.SIGNAL("addTrayMessage"), self.tray.addTrayMessage)
        MW.connect(self.worker, QtCore.SIGNAL("showDialog"), self.showDialog)
        MW.connect(self.worker, QtCore.SIGNAL("hideProgressBar"), self.hideProgressBar)
        MW.connect(self.versionCheck, QtCore.SIGNAL("addMessage"), self.addMessage)
        MW.connect(self.contentServer, QtCore.SIGNAL("addMessage"), self.addMessage)
        MW.connect(self.progress, QtCore.SIGNAL("addMessage"), self.addMessage)
        MW.closeEvent = self.saveSettings

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
        self.contentServer.start()
        self.hideProgressBar()
        self.worker.sync()
        MW.setWindowTitle("Kindle Comic Converter " + __version__)
        MW.show()
        MW.raise_()
