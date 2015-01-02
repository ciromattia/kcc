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

__version__ = '4.3.1'
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
    import PIL
    if tuple(map(int, ('2.7.0'.split(".")))) > tuple(map(int, (PIL.PILLOW_VERSION.split(".")))):
        missing.append('Pillow 2.7.0+')
except ImportError:
    missing.append('Pillow 2.7.0+')
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

from multiprocessing import freeze_support
from kcc.comic2panel import main

if __name__ == "__main__":
    freeze_support()
    print(('comic2ebook v%(__version__)s. Written by Ciro Mattia Gonano and Pawel Jastrzebski.' % globals()))
    main(sys.argv[1:])
    sys.exit(0)