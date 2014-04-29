# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2014 Pawel Jastrzebski <pawelj@vulturis.eu>
#
# Based upon the code snippet by Ned Batchelder
# (http://nedbatchelder.com/blog/200712/extracting_jpgs_from_pdfs.html)
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

import os
from random import choice
from string import ascii_uppercase, digits


class PdfJpgExtract:
    def __init__(self, origFileName):
        self.origFileName = origFileName
        self.filename = os.path.splitext(origFileName)
        # noinspection PyUnusedLocal
        self.path = self.filename[0] + "-KCC-TMP-" + ''.join(choice(ascii_uppercase + digits) for x in range(3))

    def getPath(self):
        return self.path

    def extract(self):
        pdf = open(self.origFileName, "rb").read()
        startmark = b"\xff\xd8"
        startfix = 0
        endmark = b"\xff\xd9"
        endfix = 2
        i = 0
        njpg = 0
        os.makedirs(self.path)
        while True:
            istream = pdf.find(b"stream", i)
            if istream < 0:
                break
            istart = pdf.find(startmark, istream, istream + 20)
            if istart < 0:
                i = istream + 20
                continue
            iend = pdf.find(b"endstream", istart)
            if iend < 0:
                raise Exception("Didn't find end of stream!")
            iend = pdf.find(endmark, iend - 20)
            if iend < 0:
                raise Exception("Didn't find end of JPG!")
            istart += startfix
            iend += endfix
            jpg = pdf[istart:iend]
            jpgfile = open(self.path + "/jpg%d.jpg" % njpg, "wb")
            jpgfile.write(jpg)
            jpgfile.close()
            njpg += 1
            i = iend
        return self.path, njpg
