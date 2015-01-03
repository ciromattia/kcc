#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2015 Pawel Jastrzebski <pawelj@iosphe.re>
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

__version__ = '4.3.1'
__license__ = 'ISC'
__copyright__ = '2012-2015, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@iosphe.re>'
__docformat__ = 'restructuredtext en'

import sys
if sys.version_info[0] != 3:
    print('ERROR: This is Python 3 script!')
    exit(1)

# OS specific PATH variable workarounds
import os
if sys.platform.startswith('darwin') and 'RESOURCEPATH' not in os.environ:
    os.environ['PATH'] = os.path.dirname(os.path.abspath(__file__)) + '/other/:' + os.environ['PATH']
elif sys.platform.startswith('win'):
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(os.path.abspath(sys.executable)))

        # Implementing dummy stdout and stderr for frozen Windows release
        class FakeSTD(object):
            def write(self, string):
                pass

            def flush(self):
                pass
        sys.stdout = FakeSTD()
        sys.stderr = FakeSTD()
    else:
        os.environ['PATH'] = os.path.dirname(os.path.abspath(__file__)) + '/other/;' + os.environ['PATH']
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

from kcc.shared import dependencyCheck
dependencyCheck(3)

from multiprocessing import freeze_support
from kcc import KCC_gui

if __name__ == "__main__":
    freeze_support()
    KCCAplication = KCC_gui.QApplicationMessaging(sys.argv)
    if KCCAplication.isRunning():
        if len(sys.argv) > 1:
            KCCAplication.sendMessage(sys.argv[1])
        else:
            KCCAplication.sendMessage('ARISE')
    else:
        KCCWindow = KCC_gui.QMainWindowKCC()
        KCCUI = KCC_gui.KCCGUI(KCCAplication, KCCWindow)
        if len(sys.argv) > 1:
            KCCUI.handleMessage(sys.argv[1])
        sys.exit(KCCAplication.exec_())
