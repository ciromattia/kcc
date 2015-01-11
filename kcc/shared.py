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
#

__license__ = 'ISC'
__copyright__ = '2012-2015, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@iosphe.re>'
__docformat__ = 'restructuredtext en'

import os
from hashlib import md5
from html.parser import HTMLParser
from distutils.version import StrictVersion


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


def getImageFileName(imgfile):
    name, ext = os.path.splitext(imgfile)
    ext = ext.lower()
    if name.startswith('.') or (ext != '.png' and ext != '.jpg' and ext != '.jpeg' and ext != '.gif'):
        return None
    return [name, ext]


def walkLevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
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


# noinspection PyUnresolvedReferences
def dependencyCheck(level):
    missing = []
    if level > 2:
        try:
            from PyQt5.QtCore import qVersion as qtVersion
            if StrictVersion('5.2.0') > StrictVersion(qtVersion()):
                missing.append('PyQt 5.2.0+')
        except ImportError:
            missing.append('PyQt 5.2.0+')
    if level > 1:
        try:
            from psutil import __version__ as psutilVersion
            if StrictVersion('2.0.0') > StrictVersion(psutilVersion):
                missing.append('psutil 2.0.0+')
        except ImportError:
            missing.append('psutil 2.0.0+')
        try:
            from slugify import __version__ as slugifyVersion
            if StrictVersion('0.1.0') > StrictVersion(slugifyVersion):
                missing.append('python-slugify 0.1.0+')
        except ImportError:
            missing.append('python-slugify 0.1.0+')
    try:
        from PIL import PILLOW_VERSION as pillowVersion
        if StrictVersion('2.7.0') > StrictVersion(pillowVersion):
            missing.append('Pillow 2.7.0+')
    except ImportError:
        missing.append('Pillow 2.7.0+')
    if len(missing) > 0:
        try:
            import tkinter
            import tkinter.messagebox
            importRoot = tkinter.Tk()
            importRoot.withdraw()
            tkinter.messagebox.showerror('KCC - Error', 'ERROR: ' + ', '.join(missing) + ' is not installed!')
        except ImportError:
            print('ERROR: ' + ', '.join(missing) + ' is not installed!')
        exit(1)