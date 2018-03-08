#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2018 Pawel Jastrzebski <pawelj@iosphe.re>
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

import sys
if sys.version_info[0] != 3:
    print('ERROR: This is Python 3 script!')
    exit(1)

# OS specific workarounds
import os
if sys.platform.startswith('darwin'):
    if getattr(sys, 'frozen', False):
        os.environ['PATH'] = os.path.dirname(os.path.abspath(sys.executable)) + \
            '/../Resources:/usr/local/bin:/usr/bin:/bin'
        os.system('defaults write com.kindlecomicconverter.KindleComicConverter ApplePersistenceIgnoreState YES')
        os.system('defaults write com.kindlecomicconverter.KindleComicConverter NSInitialToolTipDelay -int 1000')
    else:
        os.environ['PATH'] = os.path.dirname(os.path.abspath(__file__)) + '/other/osx/:' + os.environ['PATH']
elif sys.platform.startswith('win'):
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(os.path.abspath(sys.executable)))
    else:
        os.environ['PATH'] = os.path.dirname(os.path.abspath(__file__)) + '/other/windows/;' + os.environ['PATH']
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
# Load additional Sentry configuration
if getattr(sys, 'frozen', False):
    try:
        import kindlecomicconverter.sentry
    except ImportError:
        pass

from multiprocessing import freeze_support
from kindlecomicconverter.startup import start

if __name__ == "__main__":
    freeze_support()
    start()

