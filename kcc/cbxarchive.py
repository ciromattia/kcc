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
import os
from zipfile import is_zipfile, ZipFile
from subprocess import STDOUT, PIPE
from psutil import Popen
from shutil import move, copy
from . import rarfile


class CBxArchive:
    def __init__(self, origFileName):
        self.origFileName = origFileName
        if is_zipfile(origFileName):
            self.compressor = 'zip'
        elif rarfile.is_rarfile(origFileName):
            self.compressor = 'rar'
        elif origFileName.endswith('.7z') or origFileName.endswith('.cb7'):
            self.compressor = '7z'
        else:
            self.compressor = None

    def isCbxFile(self):
        return self.compressor is not None

    def extractCBZ(self, targetdir):
        cbzFile = ZipFile(self.origFileName)
        filelist = []
        for f in cbzFile.namelist():
            if f.startswith('__MACOSX') or f.endswith('.DS_Store') or f.endswith('thumbs.db'):
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
        filelist = []
        for f in cbrFile.namelist():
            if f.startswith('__MACOSX') or f.endswith('.DS_Store') or f.endswith('thumbs.db'):
                pass  # skip MacOS special files
            elif f.endswith('/'):
                try:
                    os.makedirs(os.path.join(targetdir, f))
                except Exception:
                    pass  # the dir exists so we are going to extract the images only.
            else:
                filelist.append(f)
        cbrFile.extractall(targetdir, filelist)

    def extractCB7(self, targetdir):
        # Workaround for some wide UTF-8 + Popen abnormalities
        if sys.platform.startswith('darwin'):
            copy(self.origFileName, os.path.join(os.path.dirname(self.origFileName), 'TMP_KCC_TMP'))
            self.origFileName = os.path.join(os.path.dirname(self.origFileName), 'TMP_KCC_TMP')
        output = Popen('7za x "' + self.origFileName + '" -xr!__MACOSX -xr!.DS_Store -xr!thumbs.db -o"'
                       + targetdir + '"', stdout=PIPE, stderr=STDOUT, shell=True)
        extracted = False
        for line in output.stdout:
            if b"Everything is Ok" in line:
                extracted = True
        if sys.platform.startswith('darwin'):
            os.remove(self.origFileName)
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
                    os.replace(os.path.join(targetdir, adir[0], f), os.path.join(targetdir, adir[0], f + '-A'))
                    f += '-A'
                move(os.path.join(targetdir, adir[0], f), targetdir)
            os.rmdir(os.path.join(targetdir, adir[0]))
        return targetdir
