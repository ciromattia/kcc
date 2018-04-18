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
#

import os
from hashlib import md5
from html.parser import HTMLParser
from distutils.version import StrictVersion
from shutil import rmtree, copy
from tempfile import mkdtemp
from zipfile import ZipFile, ZIP_DEFLATED
from re import split
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
    if name.startswith('.') or (ext != '.png' and ext != '.jpg' and ext != '.jpeg' and ext != '.gif'):
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


def md5Checksum(fpath):
    with open(fpath, 'rb') as fh:
        m = md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()


def check7ZFile(fpath):
    with open(fpath, 'rb') as fh:
        header = fh.read(6)
    return header == b"7z\xbc\xaf'\x1c"


def removeFromZIP(zipfname, *filenames):
    tempdir = mkdtemp('', 'KCC-')
    try:
        tempname = os.path.join(tempdir, 'KCC.zip')
        with ZipFile(zipfname, 'r') as zipread:
            with ZipFile(tempname, 'w', compression=ZIP_DEFLATED) as zipwrite:
                for item in zipread.infolist():
                    if item.filename not in filenames:
                        zipwrite.writestr(item, zipread.read(item.filename))
        copy(tempname, zipfname)
    finally:
        rmtree(tempdir, True)


def sanitizeTrace(traceback):
    return ''.join(format_tb(traceback))\
        .replace('C:/projects/kcc/', '') \
        .replace('c:/projects/kcc/', '') \
        .replace('C:/python36-x64/', '')\
        .replace('c:/python36-x64/', '')\
        .replace('C:\\projects\\kcc\\', '') \
        .replace('c:\\projects\\kcc\\', '') \
        .replace('C:\\python36-x64\\', '')\
        .replace('c:\\python36-x64\\', '')


def dependencyCheck(level):
    missing = []
    if level > 2:
        try:
            from PyQt5.QtCore import qVersion as qtVersion
            if StrictVersion('5.6.0') > StrictVersion(qtVersion()):
                missing.append('PyQt 5.6.0+')
        except ImportError:
            missing.append('PyQt 5.6.0+')
        try:
            import raven
        except ImportError:
            missing.append('raven 6.0.0+')
    if level > 1:
        try:
            from psutil import __version__ as psutilVersion
            if StrictVersion('5.0.0') > StrictVersion(psutilVersion):
                missing.append('psutil 5.0.0+')
        except ImportError:
            missing.append('psutil 5.0.0+')
        try:
            from slugify import __version__ as slugifyVersion
            if StrictVersion('1.2.1') > StrictVersion(slugifyVersion):
                missing.append('python-slugify 1.2.1+')
        except ImportError:
            missing.append('python-slugify 1.2.1+')
    try:
        from PIL import __version__ as pillowVersion
        if StrictVersion('4.0.0') > StrictVersion(pillowVersion):
            missing.append('Pillow 4.0.0+')
    except ImportError:
        missing.append('Pillow 4.0.0+')
    if len(missing) > 0:
        print('ERROR: ' + ', '.join(missing) + ' is not installed!')
        exit(1)
