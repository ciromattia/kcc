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
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import os
import zipfile
import rarfile


# noinspection PyBroadException
class CBxArchive:
    def __init__(self, origFileName):
        self.origFileName = origFileName
        if zipfile.is_zipfile(origFileName):
            self.compressor = 'zip'
        elif rarfile.is_rarfile(origFileName):
            self.compressor = 'rar'
        else:
            self.compressor = None

    def isCbxFile(self):
        return self.compressor is not None

    def extractCBZ(self, targetdir):
        cbzFile = zipfile.ZipFile(self.origFileName)
        filelist = []
        for f in cbzFile.namelist():
            if f.startswith('__MACOSX') or f.endswith('.DS_Store') or f.endswith('thumbs.db'):
                pass    # skip MacOS special files
            elif f.endswith('/'):
                try:
                    os.makedirs(os.path.join(targetdir, f))
                except:
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
                except:
                    pass  # the dir exists so we are going to extract the images only.
            else:
                filelist.append(f)
        cbrFile.extractall(targetdir, filelist)

    def extract(self, targetdir):
        print "\n" + targetdir + "\n"
        if self.compressor == 'rar':
            self.extractCBR(targetdir)
        elif self.compressor == 'zip':
            self.extractCBZ(targetdir)
        adir = os.listdir(targetdir)
        if len(adir) == 1 and os.path.isdir(os.path.join(targetdir, adir[0])):
            import shutil
            for f in os.listdir(os.path.join(targetdir, adir[0])):
                shutil.move(os.path.join(targetdir, adir[0], f), targetdir)
            os.rmdir(os.path.join(targetdir, adir[0]))
        return targetdir
