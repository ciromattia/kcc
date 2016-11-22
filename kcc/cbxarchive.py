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

import sys
import os
from zipfile import is_zipfile, ZipFile
from subprocess import STDOUT, PIPE
from psutil import Popen
from shutil import move, copy
try:
    from scandir import walk
except ImportError:
    walk = os.walk
from . import rarfile
from .shared import check7ZFile as is_7zfile, saferReplace, saferRemove


class CBxArchive:
    def __init__(self, origFileName):
        self.origFileName = origFileName
        if is_zipfile(origFileName):
            self.compressor = 'zip'
        elif rarfile.is_rarfile(origFileName):
            self.compressor = 'rar'
        elif is_7zfile(origFileName):
            self.compressor = '7z'
        else:
            self.compressor = None

    def isCbxFile(self):
        return self.compressor is not None

    def extractCBZ(self, targetdir):
        cbzFile = ZipFile(self.origFileName)
        filelist = []
        for f in cbzFile.namelist():
            if f.startswith('__MACOSX') or f.endswith('.DS_Store') or f.endswith('humbs.db'):
                pass    # skip MacOS special files
            elif f.endswith('/'):
                try:
                    os.makedirs(os.path.join(targetdir, f))
                except Exception:
                    pass  # the dir exists so we are going to extract the images only.
            else:
                filelist.append(f)
        cbzFile.extractall(targetdir, filelist)

    def extractCBR(self, targetdir):
        cbrFile = rarfile.RarFile(self.origFileName)
        cbrFile.extractall(targetdir)
        for root, dirnames, filenames in walk(targetdir):
            for filename in filenames:
                if filename.startswith('__MACOSX') or filename.endswith('.DS_Store') or filename.endswith('humbs.db'):
                    saferRemove(os.path.join(root, filename))

    def extractCB7(self, targetdir):
        # Workaround for some wide UTF-8 + Popen abnormalities
        if sys.platform.startswith('darwin'):
            copy(self.origFileName, os.path.join(os.path.dirname(self.origFileName), 'TMP_KCC_TMP'))
            self.origFileName = os.path.join(os.path.dirname(self.origFileName), 'TMP_KCC_TMP')
        output = Popen('7za x "' + self.origFileName + '" -xr!__MACOSX -xr!.DS_Store -xr!thumbs.db -xr!Thumbs.db -o"' +
                       targetdir + '"', stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
        extracted = False
        for line in output.stdout:
            if b"Everything is Ok" in line:
                extracted = True
        if sys.platform.startswith('darwin'):
            saferRemove(self.origFileName)
        if not extracted:
            raise OSError

    def extract(self, targetdir):
        if self.compressor == 'rar':
            self.extractCBR(targetdir)
        elif self.compressor == 'zip':
            self.extractCBZ(targetdir)
        elif self.compressor == '7z':
            self.extractCB7(targetdir)
        adir = os.listdir(targetdir)
        if 'ComicInfo.xml' in adir:
            adir.remove('ComicInfo.xml')
        if len(adir) == 1 and os.path.isdir(os.path.join(targetdir, adir[0])):
            for f in os.listdir(os.path.join(targetdir, adir[0])):
                # If directory names contain UTF-8 chars shutil.move can't clean up the mess alone
                if os.path.isdir(os.path.join(targetdir, f)):
                    saferReplace(os.path.join(targetdir, adir[0], f), os.path.join(targetdir, adir[0], f + '-A'))
                    f += '-A'
                move(os.path.join(targetdir, adir[0], f), targetdir)
            os.rmdir(os.path.join(targetdir, adir[0]))
        return targetdir
