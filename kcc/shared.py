# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2016 Pawel Jastrzebski <pawelj@iosphe.re>
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
from sys import version_info
from hashlib import md5
from html.parser import HTMLParser
from distutils.version import StrictVersion
from time import sleep
from shutil import rmtree, copy
from tempfile import mkdtemp
from zipfile import ZipFile, ZIP_DEFLATED
from re import split
from traceback import format_tb
try:
    from scandir import walk
except ImportError:
    walk = os.walk


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
    for root, dirs, files in walk(some_dir):
        dirs, files = walkSort(dirs, files)
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]


def md5Checksum(filePath):
    with open(filePath, 'rb') as fh:
        m = md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()


def check7ZFile(filePath):
    with open(filePath, 'rb') as fh:
        header = fh.read(6)
    return header == b"7z\xbc\xaf'\x1c"


def saferReplace(old, new):
    for x in range(30):
        try:
            os.replace(old, new)
        except PermissionError:
            sleep(1)
        else:
            break
    else:
        raise PermissionError("Failed to move the file.")


def saferRemove(target):
    for x in range(30):
        try:
            os.remove(target)
        except PermissionError:
            sleep(1)
        else:
            break
    else:
        raise PermissionError("Failed to remove the file.")


def removeFromZIP(zipfname, *filenames):
    tempdir = mkdtemp('', 'KCC-')
    try:
        tempname = os.path.join(tempdir, 'KCC.zip')
        with ZipFile(zipfname, 'r') as zipread:
            with ZipFile(tempname, 'w', compression=ZIP_DEFLATED) as zipwrite:
                for item in zipread.infolist():
                    if item.filename not in filenames:
                        zipwrite.writestr(item, zipread.read(item.filename))
        for x in range(30):
            try:
                copy(tempname, zipfname)
            except PermissionError:
                sleep(1)
            else:
                break
        else:
            raise PermissionError
    finally:
        rmtree(tempdir, True)


def sanitizeTrace(traceback):
    return ''.join(format_tb(traceback))\
        .replace('C:/Users/Pawel/Documents/Projekty/KCC/', '')\
        .replace('C:/Python35/', '')\
        .replace('c:/python35/', '')\
        .replace('C:\\Users\\Pawel\\Documents\\Projekty\\KCC\\', '')\
        .replace('C:\\Python35\\', '')\
        .replace('c:\\python35\\', '')


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
            missing.append('raven 5.13.0+')
    if level > 1:
        try:
            from psutil import __version__ as psutilVersion
            if StrictVersion('4.1.0') > StrictVersion(psutilVersion):
                missing.append('psutil 4.1.0+')
        except ImportError:
            missing.append('psutil 4.1.0+')
        try:
            from slugify import __version__ as slugifyVersion
            if StrictVersion('1.2.0') > StrictVersion(slugifyVersion):
                missing.append('python-slugify 1.2.0+')
        except ImportError:
            missing.append('python-slugify 1.2.0+')
    try:
        from PIL import PILLOW_VERSION as pillowVersion
        if StrictVersion('3.2.0') > StrictVersion(pillowVersion):
            missing.append('Pillow 3.2.0+')
    except ImportError:
        missing.append('Pillow 3.2.0+')
    if version_info[1] < 5:
        try:
            from scandir import __version__ as scandirVersion
            if StrictVersion('1.2') > StrictVersion(scandirVersion):
                missing.append('scandir 1.2+')
        except ImportError:
            missing.append('scandir 1.2+')
    if len(missing) > 0:
        print('ERROR: ' + ', '.join(missing) + ' is not installed!')
        exit(1)
