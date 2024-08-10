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

from functools import cached_property
import os
import platform
import distro
from subprocess import STDOUT, PIPE, CalledProcessError
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from .shared import subprocess_run

EXTRACTION_ERROR = 'Failed to extract archive. Try extracting file outside of KCC.'


class ComicArchive:
    def __init__(self, filepath):
        self.filepath = filepath
        if not os.path.isfile(self.filepath):
            raise OSError('File not found.')

    @cached_property
    def type(self):    
        extraction_commands = [
            ['7z', 'l', '-y', '-p1', self.filepath],
        ]

        if distro.id() == 'fedora':
            extraction_commands.append(
                ['unrar', 'l', '-y', '-p1', self.filepath],
            )

        for cmd in extraction_commands:
            try:
                process = subprocess_run(cmd, capture_output=True, check=True)
                for line in process.stdout.splitlines():
                    if b'Type =' in line:
                        return line.rstrip().decode().split(' = ')[1].upper()
            except FileNotFoundError:
                pass
            except CalledProcessError:
                pass

        raise OSError(EXTRACTION_ERROR)

    def extract(self, targetdir):
        if not os.path.isdir(targetdir):
            raise OSError('Target directory doesn\'t exist.')

        missing = []

        extraction_commands = [
            ['tar', '-xf', self.filepath, '-C', targetdir],
            ['7z', 'x', '-y', '-xr!__MACOSX', '-xr!.DS_Store', '-xr!thumbs.db', '-xr!Thumbs.db', '-o' + targetdir, self.filepath],
        ]

        if platform.system() == 'Darwin':
            extraction_commands.append(
                ['unar', self.filepath, '-f', '-o', targetdir]
            )

        if distro.id() == 'fedora':
            extraction_commands.append(
                ['unrar', 'x', '-y', '-x__MACOSX', '-x.DS_Store', '-xthumbs.db', '-xThumbs.db', self.filepath, targetdir]
            )
        
        for cmd in extraction_commands:
            try:
                subprocess_run(cmd, capture_output=True, check=True)
                return targetdir
            except FileNotFoundError:
                missing.append(cmd[0])
            except CalledProcessError:
                pass
        
        if missing:
            raise OSError(f'Extraction failed, install <a href="https://github.com/ciromattia/kcc#7-zip">specialized extraction software.</a>  ')
        else:
            raise OSError(EXTRACTION_ERROR)

    def addFile(self, sourcefile):
        if self.type in ['RAR', 'RAR5']:
            raise NotImplementedError
        process = subprocess_run(['7z', 'a', '-y', self.filepath, sourcefile],
                        stdout=PIPE, stderr=STDOUT)
        if process.returncode != 0:
            raise OSError('Failed to add the file.')

    def extractMetadata(self):
        process = subprocess_run(['7z', 'x', '-y', '-so', self.filepath, 'ComicInfo.xml'],
                        stdout=PIPE, stderr=STDOUT)
        if process.returncode != 0:
            raise OSError(EXTRACTION_ERROR)
        try:
            return parseString(process.stdout)
        except ExpatError:
            return None
