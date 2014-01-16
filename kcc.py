#!/usr/bin/env python3
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

__version__ = '4.0'
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

# Dependiences check
missing = []
try:
    # noinspection PyUnresolvedReferences
    from PyQt5 import QtCore, QtGui, QtNetwork, QtWidgets
except ImportError:
    missing.append('PyQt5')
try:
    # noinspection PyUnresolvedReferences
    from psutil import TOTAL_PHYMEM, Popen
except ImportError:
    missing.append('psutil')
try:
    # noinspection PyUnresolvedReferences
    from slugify import slugify
except ImportError:
    missing.append('python-slugify')
try:
    # noinspection PyUnresolvedReferences
    from PIL import Image, ImageOps, ImageStat, ImageChops
    if tuple(map(int, ('2.3.0'.split(".")))) > tuple(map(int, (Image.PILLOW_VERSION.split(".")))):
        missing.append('Pillow 2.3.0+')
except ImportError:
    missing.append('Pillow 2.3.0+')
if len(missing) > 0:
    print('ERROR: ' + ', '.join(missing) + ' is not installed!')
    import tkinter
    import tkinter.messagebox
    importRoot = tkinter.Tk()
    importRoot.withdraw()
    tkinter.messagebox.showerror('KCC - Error', 'ERROR: ' + ', '.join(missing) + ' is not installed!')
    exit(1)

import sys
import os
from multiprocessing import freeze_support
from kcc import KCC_gui

# OS specific PATH variable workarounds
if sys.platform.startswith('darwin'):
    if 'RESOURCEPATH' in os.environ:
        os.environ['PATH'] = os.environ['RESOURCEPATH'] + ':' + os.environ['PATH']
    else:
        os.environ['PATH'] = os.path.dirname(os.path.abspath(__file__)) + '/other/:' + os.environ['PATH']
elif sys.platform.startswith('win'):
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(os.path.abspath(sys.executable)))
    else:
        os.environ['PATH'] = os.path.dirname(os.path.abspath(__file__)) + '/other/;' + os.environ['PATH']
        os.chdir(os.path.dirname(os.path.abspath(__file__)))


# Implementing detection of already running KCC instance and forwarding argv to it
class QApplicationMessaging(QtWidgets.QApplication):
    messageFromOtherInstance = QtCore.pyqtSignal(bytes)

    def __init__(self, argv):
        QtWidgets.QApplication.__init__(self, argv)
        self._memory = QtCore.QSharedMemory(self)
        self._memory.setKey('KCC')
        if self._memory.attach():
            self._running = True
        else:
            self._running = False
            if not self._memory.create(1):
                raise RuntimeError(self._memory.errorString().toLocal8Bit().data())
        self._key = 'KCC'
        self._timeout = 1000
        self._server = QtNetwork.QLocalServer(self)
        if not self.isRunning():
            self._server.newConnection.connect(self.handleMessage)
            self._server.listen(self._key)

    def isRunning(self):
        return self._running

    def handleMessage(self):
        socket = self._server.nextPendingConnection()
        if socket.waitForReadyRead(self._timeout):
            self.messageFromOtherInstance.emit(socket.readAll().data())

    def sendMessage(self, message):
        if self.isRunning():
            socket = QtNetwork.QLocalSocket(self)
            socket.connectToServer(self._key, QtCore.QIODevice.WriteOnly)
            if not socket.waitForConnected(self._timeout):
                return False
            # noinspection PyArgumentList
            socket.write(bytes(message, 'UTF-8'))
            if not socket.waitForBytesWritten(self._timeout):
                return False
            socket.disconnectFromServer()
            return True
        return False


# Adding signals to QMainWindow
class QMainWindowKCC(QtWidgets.QMainWindow):
    progressBarTick = QtCore.pyqtSignal(str)
    modeConvert = QtCore.pyqtSignal(bool)
    addMessage = QtCore.pyqtSignal(str, str, bool)
    addTrayMessage = QtCore.pyqtSignal(str, str)
    showDialog = QtCore.pyqtSignal(str)
    hideProgressBar = QtCore.pyqtSignal()


if __name__ == "__main__":
    freeze_support()
    KCCAplication = QApplicationMessaging(sys.argv)
    if KCCAplication.isRunning():
        if len(sys.argv) > 1:
            KCCAplication.sendMessage(sys.argv[1])
            sys.exit(0)
        else:
            messageBox = QtWidgets.QMessageBox()
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(':/Icon/icons/comic2ebook.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            messageBox.setWindowIcon(icon)
            QtWidgets.QMessageBox.critical(messageBox, 'KCC - Error', 'KCC is already running!',
                                           QtWidgets.QMessageBox.Ok)
            sys.exit(1)
    KCCWindow = QMainWindowKCC()
    KCCUI = KCC_gui.KCCGUI(KCCAplication, KCCWindow)
    if len(sys.argv) > 1:
        KCCUI.handleMessage(sys.argv[1])
    sys.exit(KCCAplication.exec_())
