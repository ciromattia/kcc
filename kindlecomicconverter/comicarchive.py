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
from psutil import Popen
from shutil import move
from subprocess import STDOUT, PIPE
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError


class ComicArchive:
    def __init__(self, filepath):
        self.filepath = filepath
        self.type = None
        if not os.path.isfile(self.filepath):
            raise OSError('File not found.')
        process = Popen('7z l -y -p1 "' + self.filepath + '"', stderr=STDOUT, stdout=PIPE, stdin=PIPE, shell=True)
        for line in process.stdout:
            if b'Type =' in line:
                self.type = line.rstrip().decode().split(' = ')[1].upper()
                break
        process.communicate()
        if process.returncode != 0:
            raise OSError('Archive is corrupted or encrypted.')
        elif self.type not in ['7Z', 'RAR', 'RAR5', 'ZIP']:
            raise OSError('Unsupported archive format.')

    def extract(self, targetdir):
        if not os.path.isdir(targetdir):
            raise OSError('Target directory don\'t exist.')
        process = Popen('7z x -y -xr!__MACOSX -xr!.DS_Store -xr!thumbs.db -xr!Thumbs.db -o"' + targetdir + '" "' +
                        self.filepath + '"', stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
        process.communicate()
        if process.returncode != 0:
            raise OSError('Failed to extract archive.')
        tdir = os.listdir(targetdir)
        if 'ComicInfo.xml' in tdir:
            tdir.remove('ComicInfo.xml')
        if len(tdir) == 1 and os.path.isdir(os.path.join(targetdir, tdir[0])):
            for f in os.listdir(os.path.join(targetdir, tdir[0])):
                move(os.path.join(targetdir, tdir[0], f), targetdir)
            os.rmdir(os.path.join(targetdir, tdir[0]))
        return targetdir

    def addFile(self, sourcefile):
        if self.type in ['RAR', 'RAR5']:
            raise NotImplementedError
        process = Popen('7z a -y "' + self.filepath + '" "' + sourcefile + '"',
                        stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
        process.communicate()
        if process.returncode != 0:
            raise OSError('Failed to add the file.')

    def extractMetadata(self):
        process = Popen('7z x -y -so "' + self.filepath + '" ComicInfo.xml',
                        stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
        xml = process.communicate()
        if process.returncode != 0:
            raise OSError('Failed to extract archive.')
        try:
            return parseString(xml[0])
        except ExpatError:
            return None
