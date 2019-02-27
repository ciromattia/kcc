# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2018 Pawel Jastrzebski <pawelj@iosphe.re>
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

import PyPDF4
import PIL
import piexif

class PdfJpgExtract:
    def __init__(self, fname):
        self.fname = fname

    @staticmethod
    def _save_image_from_page(pdf_page, basename):
        ''' based on PyPDF4/Scripts/pdf-image-extractor.py '''

        angle = pdf_page.get("/Rotate", 0)

        fname = basename

        if '/XObject' not in pdf_page['/Resources']:
            return

        xObject = pdf_page['/Resources']['/XObject'].getObject()

        for obj in xObject:

            if xObject[obj]['/Subtype'] != '/Image':
                continue

            size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
            data = xObject[obj].getData()

            if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                mode = 'RGB'
            else:
                mode = 'P'

            if '/Filter' in xObject[obj]:
                if xObject[obj]['/Filter'] == '/FlateDecode':
                    fname += '.png'
                    img = PIL.Image.frombytes(mode, size, data)
                    img.save(fname)
                    img.close()
                    break
                elif xObject[obj]['/Filter'] == '/DCTDecode':
                    fname += '.jpg'
                    img = open(fname, 'wb')
                    img.write(data)
                    img.close()
                    break
                elif xObject[obj]['/Filter'] == '/JPXDecode':
                    fname += 'jp2'
                    img = open(fname, 'wb')
                    img.write(data)
                    img.close()
                    break
                elif xObject[obj]['/Filter'] == '/CCITTFaxDecode':
                    fname += '.tiff'
                    img = open(fname, 'wb')
                    img.write(data)
                    img.close()
                    break
            else:
                fname += '.png'
                img = PIL.Image.frombytes(mode, size, data)
                img.save(fname)
                img.close()
                break
        else:
            ''' can't find image in pdf page '''
            return

        img = PIL.Image.open(fname)

        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
        else:
            exif_dict = {}

        angle_orientation_map = {
            0: 1,
            90: 6,
            180: 3,
            270: 8,
        }

        if '0th' not in exif_dict:
            exif_dict['0th'] = {}

        exif_dict['0th'][piexif.ImageIFD.Orientation] = angle_orientation_map[angle]

        exif_bytes = piexif.dump(exif_dict)

        img.save(fname, exif = exif_bytes)
        img.close()

        return True

    def extract(self, targetdir):

        with open(self.fname, 'rb') as fp:
            pdf = PyPDF4.PdfFileReader(fp)

            nimg = 0

            for page_num in range(pdf.getNumPages()):
                page = pdf.getPage(page_num)
                base_fname = targetdir + '/img-%04d'% nimg

                if self._save_image_from_page(page, base_fname):
                    nimg += 1

        return targetdir, nimg

