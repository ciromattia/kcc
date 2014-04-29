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

from multiprocessing import freeze_support
from kcc.comic2ebook import main, Copyright

if __name__ == "__main__":
    freeze_support()
    Copyright()
    main(sys.argv[1:])
    sys.exit(0)