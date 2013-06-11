#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Ciro Mattia Gonano <ciromattia@gmail.com>
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
#
__version__ = '3.0'
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import sys
import os
from PyQt4 import QtGui
from kcc import KCC_gui, KCC_ui
from multiprocessing import freeze_support

freeze_support()
if sys.platform == 'darwin':
    os.environ['PATH'] = '/usr/local/bin:' + os.environ['PATH']
app = QtGui.QApplication(sys.argv)
KCC = QtGui.QMainWindow()
ui = KCC_ui.Ui_KCC()
ui.setupUi(KCC)
gui = KCC_gui.Ui_KCC(ui, KCC)
KCC.setWindowTitle("Kindle Comic Converter " + __version__)
KCC.show()
sys.exit(app.exec_())
