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
#

__license__ = 'ISC'
__copyright__ = '2012-2014, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@iosphe.re>'
__docformat__ = 'restructuredtext en'

import os
from hashlib import md5


def getImageFileName(imgfile):
    filename = os.path.splitext(imgfile)
    if filename[0].startswith('.') or\
            (filename[1].lower() != '.png' and
             filename[1].lower() != '.jpg' and
             filename[1].lower() != '.gif' and
             filename[1].lower() != '.tif' and
             filename[1].lower() != '.tiff' and
             filename[1].lower() != '.bmp' and
             filename[1].lower() != '.jpeg'):
        return None
    return filename


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
