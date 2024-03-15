# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2019 Pawel Jastrzebski <pawelj@iosphe.re>
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

import os
from random import choice
from string import ascii_uppercase, digits

# skip stray images a few pixels in size in some PDFs
# typical images are many thousands in length
# https://github.com/ciromattia/kcc/pull/546
STRAY_IMAGE_LENGTH_THRESHOLD = 300


class PdfJpgExtract:
    def __init__(self, fname):
        self.fname = fname
        self.filename = os.path.splitext(fname)
        self.path = self.filename[0] + "-KCC-" + ''.join(choice(ascii_uppercase + digits) for _ in range(3))

    def getPath(self):
        return self.path

    def extract(self):
        pdf = open(self.fname, "rb").read()
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
            i = iend

            if iend - istart < STRAY_IMAGE_LENGTH_THRESHOLD:
                continue

            jpg = pdf[istart:iend]
            jpgfile = open(self.path + "/jpg%d.jpg" % njpg, "wb")
            jpgfile.write(jpg)
            jpgfile.close()
            njpg += 1

        return self.path, njpg
