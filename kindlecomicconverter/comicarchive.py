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

import os
import platform
import subprocess
import distro
from shutil import move
from subprocess import STDOUT, PIPE
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from .shared import subprocess_run_silent

EXTRACTION_ERROR = 'Failed to extract archive. Try extracting file outside of KCC.'


class ComicArchive:
    def __init__(self, filepath):
        self.filepath = filepath
        self.type = None
        if not os.path.isfile(self.filepath):
            raise OSError('File not found.')
        process = subprocess_run_silent(['7z', 'l', '-y', '-p1', self.filepath], stderr=STDOUT, stdout=PIPE)
        for line in process.stdout.splitlines():
            if b'Type =' in line:
                self.type = line.rstrip().decode().split(' = ')[1].upper()
                break
        if process.returncode != 0 and distro.id() == 'fedora':
            process = subprocess_run_silent(['unrar', 'l', '-y', '-p1', self.filepath], stderr=STDOUT, stdout=PIPE)
            for line in process.stdout.splitlines():
                if b'Details: ' in line:
                    self.type = line.rstrip().decode().split(' ')[1].upper()
                    break
            if process.returncode != 0:
                raise OSError(EXTRACTION_ERROR)

    def extract(self, targetdir):
        if not os.path.isdir(targetdir):
            raise OSError('Target directory doesn\'t exist.')
        process = subprocess_run_silent(['7z', 'x', '-y', '-xr!__MACOSX', '-xr!.DS_Store', '-xr!thumbs.db', '-xr!Thumbs.db', '-o' + targetdir, self.filepath],
                                 stdout=PIPE, stderr=STDOUT)
        if process.returncode != 0 and distro.id() == 'fedora':
            process = subprocess_run_silent(['unrar', 'x', '-y', '-x__MACOSX', '-x.DS_Store', '-xthumbs.db', '-xThumbs.db', self.filepath, targetdir] 
                    , stdout=PIPE, stderr=STDOUT)
            if process.returncode != 0:
                raise OSError(EXTRACTION_ERROR)
        elif process.returncode != 0 and platform.system() == 'Darwin':
            process = subprocess_run_silent(['unar', self.filepath, '-f', '-o', targetdir], 
                stdout=PIPE, stderr=STDOUT)
        elif process.returncode != 0:
            raise OSError(EXTRACTION_ERROR)
        tdir = os.listdir(targetdir)
        if 'ComicInfo.xml' in tdir:
            tdir.remove('ComicInfo.xml')
        return targetdir

    def addFile(self, sourcefile):
        if self.type in ['RAR', 'RAR5']:
            raise NotImplementedError
        process = subprocess_run_silent(['7z', 'a', '-y', self.filepath, sourcefile],
                        stdout=PIPE, stderr=STDOUT)
        if process.returncode != 0:
            raise OSError('Failed to add the file.')

    def extractMetadata(self):
        process = subprocess_run_silent(['7z', 'x', '-y', '-so', self.filepath, 'ComicInfo.xml'],
                        stdout=PIPE, stderr=STDOUT)
        if process.returncode != 0:
            raise OSError(EXTRACTION_ERROR)
        try:
            return parseString(process.stdout)
        except ExpatError:
            return None
