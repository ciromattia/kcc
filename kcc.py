#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2014 Pawel Jastrzebski <pawelj@vulturis.eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__license__ = 'GPL-3'
__copyright__ = '2012-2014, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import sys
if sys.version_info[0] != 3:
    print('ERROR: This is Python 3 script!')
    exit(1)

# Dependiences check
missing = []
try:
    # noinspection PyUnresolvedReferences
    from PyQt5 import QtCore, QtGui, QtNetwork, QtWidgets
except ImportError:
    missing.append('PyQt5')
try:
    # noinspection PyUnresolvedReferences
    from psutil import virtual_memory, Popen
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
            self._server.newConnection.connect(self.handleMessage)
            self._server.listen(self._key)

    def __del__(self):
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
