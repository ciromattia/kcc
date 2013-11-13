#!/usr/bin/env python2
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

import sys
import os
try:
    #noinspection PyUnresolvedReferences
    from PyQt4 import QtCore, QtGui, QtNetwork
except ImportError:
    print "ERROR: PyQT4 is not installed!"
    if sys.platform.startswith('linux'):
        import Tkinter
        import tkMessageBox
        importRoot = Tkinter.Tk()
        importRoot.withdraw()
        tkMessageBox.showerror("KCC - Error", "PyQT4 is not installed!")
    exit(1)
from kcc import KCC_gui
from multiprocessing import freeze_support

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
class QApplicationMessaging(QtGui.QApplication):
    def __init__(self, argv):
        QtGui.QApplication.__init__(self, argv)
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
            self.emit(QtCore.SIGNAL('messageFromOtherInstance'), socket.readAll().data().decode('utf8'))

    def sendMessage(self, message):
        if self.isRunning():
            socket = QtNetwork.QLocalSocket(self)
            socket.connectToServer(self._key, QtCore.QIODevice.WriteOnly)
            if not socket.waitForConnected(self._timeout):
                return False
            socket.write(message.encode('utf8'))
            if not socket.waitForBytesWritten(self._timeout):
                return False
            socket.disconnectFromServer()
            return True
        return False

freeze_support()
KCCAplication = QApplicationMessaging(sys.argv)
if KCCAplication.isRunning():
    if len(sys.argv) > 1:
        KCCAplication.sendMessage(sys.argv[1].decode(sys.getfilesystemencoding()))
        sys.exit(0)
    else:
        messageBox = QtGui.QMessageBox()
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(':/Icon/icons/comic2ebook.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        messageBox.setWindowIcon(icon)
        QtGui.QMessageBox.critical(messageBox, 'KCC - Error', 'KCC is already running!', QtGui.QMessageBox.Ok)
        sys.exit(1)
KCCWindow = QtGui.QMainWindow()
KCCUI = KCC_gui.KCCGUI(KCCAplication, KCCWindow)
if len(sys.argv) > 1:
    KCCUI.handleMessage(sys.argv[1].decode(sys.getfilesystemencoding()))
sys.exit(KCCAplication.exec_())
