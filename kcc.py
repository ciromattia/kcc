#!/usr/bin/env python3
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

__version__ = '4.2'
__license__ = 'ISC'
__copyright__ = '2012-2014, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@iosphe.re>'
__docformat__ = 'restructuredtext en'

import sys
if sys.version_info[0] != 3:
    print('ERROR: This is Python 3 script!')
    exit(1)

# Dependency check
missing = []
try:
    # noinspection PyUnresolvedReferences
    from PyQt5 import QtCore, QtNetwork, QtWidgets
    if tuple(map(int, ('5.2.0'.split(".")))) > tuple(map(int, (QtCore.qVersion().split(".")))):
        missing.append('PyQt5 5.2.0+')
except ImportError:
    missing.append('PyQt5 5.2.0+')
try:
    # noinspection PyUnresolvedReferences
    import psutil
    if tuple(map(int, ('2.0.0'.split(".")))) > tuple(map(int, psutil.version_info)):
        missing.append('psutil 2.0.0+')
except ImportError:
    missing.append('psutil 2.0.0+')
try:
    # noinspection PyUnresolvedReferences
    import PIL
    if tuple(map(int, ('2.5.0'.split(".")))) > tuple(map(int, (PIL.PILLOW_VERSION.split(".")))):
        missing.append('Pillow 2.5.0+')
except ImportError:
    missing.append('Pillow 2.5.0+')
try:
    # noinspection PyUnresolvedReferences
    import slugify
except ImportError:
    missing.append('python-slugify')
if len(missing) > 0:
    try:
        # noinspection PyUnresolvedReferences
        import tkinter
        # noinspection PyUnresolvedReferences
        import tkinter.messagebox
        importRoot = tkinter.Tk()
        importRoot.withdraw()
        tkinter.messagebox.showerror('KCC - Error', 'ERROR: ' + ', '.join(missing) + ' is not installed!')
    except ImportError:
        print('ERROR: ' + ', '.join(missing) + ' is not installed!')
    exit(1)

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

        # Implementing dummy stdout and stderr for frozen Windows release
        class fakestd(object):
            def write(self, string):
                pass

            def flush(self):
                pass
        sys.stdout = fakestd()
        sys.stderr = fakestd()
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
            self._memory.create(1)
        self._key = 'KCC'
        self._timeout = 1000
        self._server = QtNetwork.QLocalServer(self)
        if not self.isRunning():
            # noinspection PyUnresolvedReferences
            self._server.newConnection.connect(self.handleMessage)
            self._server.listen(self._key)

    def shutdown(self):
        if self._memory.isAttached():
            self._memory.detach()
            self._server.close()

    def event(self, e):
        if e.type() == QtCore.QEvent.FileOpen:
            # noinspection PyArgumentList
            self.messageFromOtherInstance.emit(bytes(e.file(), 'UTF-8'))
            return True
        else:
            return QtWidgets.QApplication.event(self, e)

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
    modeConvert = QtCore.pyqtSignal(int)
    addMessage = QtCore.pyqtSignal(str, str, bool)
    addTrayMessage = QtCore.pyqtSignal(str, str)
    showDialog = QtCore.pyqtSignal(str, str)
    hideProgressBar = QtCore.pyqtSignal()
    forceShutdown = QtCore.pyqtSignal()
    dialogAnswer = QtCore.pyqtSignal(int)


if __name__ == "__main__":
    freeze_support()
    KCCAplication = QApplicationMessaging(sys.argv)
    if KCCAplication.isRunning():
        if len(sys.argv) > 1:
            KCCAplication.sendMessage(sys.argv[1])
            sys.exit(0)
        else:
            KCCAplication.sendMessage('ARISE')
            sys.exit(0)
    KCCWindow = QMainWindowKCC()
    KCCUI = KCC_gui.KCCGUI(KCCAplication, KCCWindow)
    if len(sys.argv) > 1:
        KCCUI.handleMessage(sys.argv[1])
    sys.exit(KCCAplication.exec_())
