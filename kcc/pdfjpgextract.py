# Copyright (c) 2012 Ciro Mattia Gonano <ciromattia@gmail.com>
#
# Based upon the code snippet by Ned Batchelder
# (http://nedbatchelder.com/blog/200712/extracting_jpgs_from_pdfs.html)
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


class PdfJpgExtract:
    def __init__(self, origFileName):
        self.origFileName = origFileName
        self.filename = os.path.splitext(origFileName)
        self.path = self.filename[0] + "-KCC-TMP"

    def getPath(self):
        return self.path

    def extract(self):
        pdf = file(self.origFileName, "rb").read()

        startmark = "\xff\xd8"
        startfix = 0
        endmark = "\xff\xd9"
        endfix = 2
        i = 0

        njpg = 0
        os.makedirs(self.path)
        while True:
            istream = pdf.find("stream", i)
            if istream < 0:
                break
            istart = pdf.find(startmark, istream, istream + 20)
            if istart < 0:
                i = istream + 20
                continue
            iend = pdf.find("endstream", istart)
            if iend < 0:
                raise Exception("Didn't find end of stream!")
            iend = pdf.find(endmark, iend - 20)
            if iend < 0:
                raise Exception("Didn't find end of JPG!")

            istart += startfix
            iend += endfix
            print "JPG %d from %d to %d" % (njpg, istart, iend)
            jpg = pdf[istart:iend]
            jpgfile = file(self.path + "/jpg%d.jpg" % njpg, "wb")
            jpgfile.write(jpg)
            jpgfile.close()

            njpg += 1
            i = iend
        return self.path, njpg
