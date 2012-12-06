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
__version__ = '1.0'

import os

class CBxArchive:
    def __init__(self, origFileName):
        self.cbxexts = ['.zip','.cbz','.rar','.cbr']
        self.origFileName = origFileName
        self.filename = os.path.splitext(origFileName)
        self.path = self.filename[0]

    def isCbxFile(self):
        result = (self.filename[1].lower() in self.cbxexts)
        if result == True:
            return result
        return False

    def getPath(self):
        return self.path

    def extractCBZ(self):
        try:
            from zipfile import ZipFile
        except ImportError:
            self.cbzFile = None
        cbzFile = ZipFile(self.origFileName)
        for f in cbzFile.namelist():
            if (f.startswith('__MACOSX') or f.endswith('.DS_Store')):
                pass # skip MacOS special files
            elif f.endswith('/'):
                try:
                    os.makedirs(self.path+'/'+f)
                except:
                    pass #the dir exists so we are going to extract the images only.
            else:
                cbzFile.extract(f, self.path)

    def extractCBR(self):
        try:
            import rarfile
        except ImportError:
            self.cbrFile = None
        cbrFile = rarfile.RarFile(self.origFileName)
        for f in cbrFile.namelist():
            if (f.startswith('__MACOSX') or f.endswith('.DS_Store')):
                pass # skip MacOS special files
            elif f.endswith('/'):
                try:
                    os.makedirs(self.path+'/'+f)
                except:
                    pass #the dir exists so we are going to extract the images only.
            else:
                cbrFile.extract(f, self.path)

    def extract(self):
        if ('.cbr' == self.filename[1].lower() or '.rar' == self.filename[1].lower()):
            self.extractCBR()
        elif ('.cbz' == self.filename[1].lower() or '.zip' == self.filename[1].lower()):
            self.extractCBZ()
        dir = os.listdir(self.path)
        if (len(dir) == 1):
            import shutil
            for f in os.listdir(self.path + "/" + dir[0]):
                shutil.move(self.path + "/" + dir[0] + "/" + f,self.path)
            os.rmdir(self.path + "/" + dir[0])
