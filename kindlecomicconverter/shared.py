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

from functools import lru_cache
import os
from hashlib import md5
from html.parser import HTMLParser
import subprocess
from packaging.version import Version
from re import split
import sys
from traceback import format_tb


class HTMLStripper(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

    def error(self, message):
        pass


def getImageFileName(imgfile):
    name, ext = os.path.splitext(imgfile)
    ext = ext.lower()
    if (name.startswith('.') and len(name) == 1):
        return None
    if name.startswith('._'):
        return None
    if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.jp2', '.j2k', '.jpx']:
        return None
    return [name, ext]


def walkSort(dirnames, filenames):
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in split('([0-9]+)', key)]
    dirnames.sort(key=lambda name: alphanum_key(name.lower()))
    filenames.sort(key=lambda name: alphanum_key(name.lower()))
    return dirnames, filenames


def walkLevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        dirs, files = walkSort(dirs, files)
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]



def sanitizeTrace(traceback):
    return ''.join(format_tb(traceback))\
        .replace('C:/projects/kcc/', '')\
        .replace('c:/projects/kcc/', '')\
        .replace('C:/python37-x64/', '')\
        .replace('c:/python37-x64/', '')\
        .replace('C:\\projects\\kcc\\', '')\
        .replace('c:\\projects\\kcc\\', '')\
        .replace('C:\\python37-x64\\', '')\
        .replace('c:\\python37-x64\\', '')


# noinspection PyUnresolvedReferences
def dependencyCheck(level):
    missing = []
    if level > 2:
        try:
            from PySide6.QtCore import qVersion as qtVersion
            if Version('6.5.1') > Version(qtVersion()):
                missing.append('PySide 6.5.1+')
        except ImportError:
            missing.append('PySide 6.5.1+')
        try:
            import raven
        except ImportError:
            missing.append('raven 6.0.0+')
    if level > 1:
        try:
            from psutil import __version__ as psutilVersion
            if Version('5.0.0') > Version(psutilVersion):
                missing.append('psutil 5.0.0+')
        except ImportError:
            missing.append('psutil 5.0.0+')
        try:
            from types import ModuleType
            from slugify import __version__ as slugifyVersion
            if isinstance(slugifyVersion, ModuleType):
                slugifyVersion = slugifyVersion.__version__
            if Version('1.2.1') > Version(slugifyVersion):
                missing.append('python-slugify 1.2.1+')
        except ImportError:
            missing.append('python-slugify 1.2.1+')
    try:
        from PIL import __version__ as pillowVersion
        if Version('5.2.0') > Version(pillowVersion):
            missing.append('Pillow 5.2.0+')
    except ImportError:
        missing.append('Pillow 5.2.0+')
    if len(missing) > 0:
        print('ERROR: ' + ', '.join(missing) + ' is not installed!')
        sys.exit(1)

@lru_cache
def available_archive_tools():
    available = []

    for tool in ['tar', '7z', 'unar', 'unrar']:
        try:
            subprocess_run([tool], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            available.append(tool)
        except FileNotFoundError:
            pass
    
    return available

def subprocess_run(command, **kwargs):
    if (os.name == 'nt'):
        kwargs.setdefault('creationflags', subprocess.CREATE_NO_WINDOW)
    return subprocess.run(command, **kwargs)
