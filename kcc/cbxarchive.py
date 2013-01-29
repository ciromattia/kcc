# Copyright (c) 2012 Ciro Mattia Gonano <ciromattia@gmail.com>
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
__license__   = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>'
__docformat__ = 'restructuredtext en'

import os

class CBxArchive:
    def __init__(self, origFileName):
        self.cbxexts = ['.zip','.cbz','.rar','.cbr']
        self.origFileName = origFileName
        self.filename = os.path.splitext(origFileName)

    def isCbxFile(self):
        return self.filename[1].lower() in self.cbxexts

    def extractCBZ(self,targetdir):
        try:
            from zipfile import ZipFile
        except ImportError:
            self.cbzFile = None
        cbzFile = ZipFile(self.origFileName)
        for f in cbzFile.namelist():
            if f.startswith('__MACOSX') or f.endswith('.DS_Store'):
                pass # skip MacOS special files
            elif f.endswith('/'):
                try:
                    os.makedirs(os.path.join(targetdir,f))
                except:
                    pass #the dir exists so we are going to extract the images only.
            else:
                cbzFile.extract(f, targetdir)

    def extractCBR(self,targetdir):
        try:
            import rarfile
        except ImportError:
            self.cbrFile = None
            return
        cbrFile = rarfile.RarFile(self.origFileName)
        for f in cbrFile.namelist():
            if f.startswith('__MACOSX') or f.endswith('.DS_Store'):
                pass # skip MacOS special files
            elif f.endswith('/'):
                try:
                    os.makedirs(os.path.join(targetdir,f))
                except:
                    pass #the dir exists so we are going to extract the images only.
            else:
                cbrFile.extract(f, targetdir)

    def extract(self,targetdir):
        if '.cbr' == self.filename[1].lower() or '.rar' == self.filename[1].lower():
            self.extractCBR(targetdir)
        elif '.cbz' == self.filename[1].lower() or '.zip' == self.filename[1].lower():
            self.extractCBZ(targetdir)
        dir = os.listdir(targetdir)
        if len(dir) == 1 and os.path.isdir(os.path.join(targetdir,dir[0])):
            import shutil
            for f in os.listdir(os.path.join(targetdir,dir[0])):
                shutil.move(os.path.join(targetdir,dir[0],f),targetdir)
            os.rmdir(os.path.join(targetdir,dir[0]))
        return targetdir
