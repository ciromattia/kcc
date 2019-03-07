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
#

import os
import sys
from . import __version__
from .shared import dependencyCheck


def start():
    dependencyCheck(3)
    from . import KCC_gui
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = "1"
    KCCAplication = KCC_gui.QApplicationMessaging(sys.argv)
    if KCCAplication.isRunning():
        for i in range(1, len(sys.argv)):
            KCCAplication.sendMessage(sys.argv[i])
        else:
            KCCAplication.sendMessage('ARISE')
    else:
        KCCWindow = KCC_gui.QMainWindowKCC()
        KCCUI = KCC_gui.KCCGUI(KCCAplication, KCCWindow)
        for i in range(1, len(sys.argv)):
            KCCUI.handleMessage(sys.argv[i])
        sys.exit(KCCAplication.exec_())


def startC2E():
    dependencyCheck(2)
    from .comic2ebook import main
    print('comic2ebook v' + __version__ + ' - Written by Ciro Mattia Gonano and Pawel Jastrzebski.')
    sys.exit(main(sys.argv[1:]))


def startC2P():
    dependencyCheck(1)
    from .comic2panel import main
    print('comic2panel v' + __version__ + ' - Written by Ciro Mattia Gonano and Pawel Jastrzebski.')
    sys.exit(main(sys.argv[1:]))
