# -*- coding: utf-8 -*-
#
# Copyright (C) 2010  Alex Yatskov
# Copyright (C) 2011  Stanislav (proDOOMman) Kosolapov <prodoomman@gmail.com>
# Copyright (c) 2016  Alberto Planas <aplanas@gmail.com>
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2019 Pawel Jastrzebski <pawelj@iosphe.re>
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
import io
import os
import mozjpeg_lossless_optimization
from PIL import Image, ImageOps, ImageStat, ImageChops, ImageFilter
from .shared import md5Checksum
from .page_number_crop_alg import get_bbox_crop_margin_page_number, get_bbox_crop_margin

AUTO_CROP_THRESHOLD = 0.015


class ProfileData:
    def __init__(self):
        pass

    Palette4 = [
        0x00, 0x00, 0x00,
        0x55, 0x55, 0x55,
        0xaa, 0xaa, 0xaa,
        0xff, 0xff, 0xff
    ]

    Palette15 = [
        0x00, 0x00, 0x00,
        0x11, 0x11, 0x11,
        0x22, 0x22, 0x22,
        0x33, 0x33, 0x33,
        0x44, 0x44, 0x44,
        0x55, 0x55, 0x55,
        0x66, 0x66, 0x66,
        0x77, 0x77, 0x77,
        0x88, 0x88, 0x88,
        0x99, 0x99, 0x99,
        0xaa, 0xaa, 0xaa,
        0xbb, 0xbb, 0xbb,
        0xcc, 0xcc, 0xcc,
        0xdd, 0xdd, 0xdd,
        0xff, 0xff, 0xff,
    ]

    Palette16 = [
        0x00, 0x00, 0x00,
        0x11, 0x11, 0x11,
        0x22, 0x22, 0x22,
        0x33, 0x33, 0x33,
        0x44, 0x44, 0x44,
        0x55, 0x55, 0x55,
        0x66, 0x66, 0x66,
        0x77, 0x77, 0x77,
        0x88, 0x88, 0x88,
        0x99, 0x99, 0x99,
        0xaa, 0xaa, 0xaa,
        0xbb, 0xbb, 0xbb,
        0xcc, 0xcc, 0xcc,
        0xdd, 0xdd, 0xdd,
        0xee, 0xee, 0xee,
        0xff, 0xff, 0xff,
    ]

    PalleteNull = [
    ]

    Profiles = {
        'K1': ("Kindle 1", (600, 670), Palette4, 1.8),
        'K11': ("Kindle 11", (1072, 1448), Palette16, 1.8),
        'K2': ("Kindle 2", (600, 670), Palette15, 1.8),
        'K34': ("Kindle Keyboard/Touch", (600, 800), Palette16, 1.8),
        'K578': ("Kindle", (600, 800), Palette16, 1.8),
        'KDX': ("Kindle DX/DXG", (824, 1000), Palette16, 1.8),
        'KPW': ("Kindle Paperwhite 1/2", (758, 1024), Palette16, 1.8),
        'KV': ("Kindle Paperwhite 3/4/Voyage/Oasis", (1072, 1448), Palette16, 1.8),
        'KPW5': ("Kindle Paperwhite 5/Signature Edition", (1236, 1648), Palette16, 1.8),
        'KO': ("Kindle Oasis 2/3", (1264, 1680), Palette16, 1.8),
        'KS': ("Kindle Scribe", (1860, 2480), Palette16, 1.8),
        'KoMT': ("Kobo Mini/Touch", (600, 800), Palette16, 1.8),
        'KoG': ("Kobo Glo", (768, 1024), Palette16, 1.8),
        'KoGHD': ("Kobo Glo HD", (1072, 1448), Palette16, 1.8),
        'KoA': ("Kobo Aura", (758, 1024), Palette16, 1.8),
        'KoAHD': ("Kobo Aura HD", (1080, 1440), Palette16, 1.8),
        'KoAH2O': ("Kobo Aura H2O", (1080, 1430), Palette16, 1.8),
        'KoAO': ("Kobo Aura ONE", (1404, 1872), Palette16, 1.8),
        'KoN': ("Kobo Nia", (758, 1024), Palette16, 1.8),
        'KoC': ("Kobo Clara HD/Kobo Clara 2E", (1072, 1448), Palette16, 1.8),
        'KoCC': ("Kobo Clara Colour", (1072, 1448), Palette16, 1.8),
        'KoL': ("Kobo Libra H2O/Kobo Libra 2", (1264, 1680), Palette16, 1.8),
        'KoLC': ("Kobo Libra Colour", (1264, 1680), Palette16, 1.8),
        'KoF': ("Kobo Forma", (1440, 1920), Palette16, 1.8),
        'KoS': ("Kobo Sage", (1440, 1920), Palette16, 1.8),
        'KoE': ("Kobo Elipsa", (1404, 1872), Palette16, 1.8),
        'OTHER': ("Other", (0, 0), Palette16, 1.8),
    }


class ComicPageParser:
    def __init__(self, source, options):
        Image.MAX_IMAGE_PIXELS = int(2048 * 2048 * 2048 // 4 // 3)
        self.opt = options
        self.source = source
        self.size = self.opt.profileData[1]
        self.payload = []
        self.image = Image.open(os.path.join(source[0], source[1])).convert('RGB')
        self.color = self.colorCheck()
        self.fill = self.fillCheck()
        # backwards compatibility for Pillow >9.1.0
        if not hasattr(Image, 'Resampling'):
            Image.Resampling = Image
        self.splitCheck()

    def getImageHistogram(self, image):
        histogram = image.histogram()
        if histogram[0] == 0:
            return -1
        elif histogram[255] == 0:
            return 1
        else:
            return 0

    def splitCheck(self):
        width, height = self.image.size
        dstwidth, dstheight = self.size
        if self.opt.maximizestrips:
            leftbox = (0, 0, int(width / 2), height)
            rightbox = (int(width / 2), 0, width, height)
            if self.opt.righttoleft:
                pageone = self.image.crop(rightbox)
                pagetwo = self.image.crop(leftbox)
            else:
                pageone = self.image.crop(leftbox)
                pagetwo = self.image.crop(rightbox)
            new_image = Image.new("RGB", (int(width / 2), int(height*2)))
            new_image.paste(pageone, (0, 0))
            new_image.paste(pagetwo, (0, height))
            self.payload.append(['N', self.source, new_image, self.color, self.fill])
        elif (width > height) != (dstwidth > dstheight) and width <= dstheight and height <= dstwidth \
                and not self.opt.webtoon and self.opt.splitter == 1:
            self.payload.append(['R', self.source, self.image.rotate(90, Image.Resampling.BICUBIC, True), self.color, self.fill])
        elif (width > height) != (dstwidth > dstheight) and not self.opt.webtoon:
            if self.opt.splitter != 1:
                if width > height:
                    leftbox = (0, 0, int(width / 2), height)
                    rightbox = (int(width / 2), 0, width, height)
                else:
                    leftbox = (0, 0, width, int(height / 2))
                    rightbox = (0, int(height / 2), width, height)
                if self.opt.righttoleft:
                    pageone = self.image.crop(rightbox)
                    pagetwo = self.image.crop(leftbox)
                else:
                    pageone = self.image.crop(leftbox)
                    pagetwo = self.image.crop(rightbox)
                self.payload.append(['S1', self.source, pageone, self.color, self.fill])
                self.payload.append(['S2', self.source, pagetwo, self.color, self.fill])
            if self.opt.splitter > 0:
                self.payload.append(['R', self.source, self.image.rotate(90, Image.Resampling.BICUBIC, True),
                                    self.color, self.fill])
        else:
            self.payload.append(['N', self.source, self.image, self.color, self.fill])

    def colorCheck(self):
        if self.opt.webtoon:
            return True
        else:
            img = self.image.copy()
            bands = img.getbands()
            if bands == ('R', 'G', 'B') or bands == ('R', 'G', 'B', 'A'):
                thumb = img.resize((40, 40))
                SSE, bias = 0, [0, 0, 0]
                bias = ImageStat.Stat(thumb).mean[:3]
                bias = [b - sum(bias) / 3 for b in bias]
                for pixel in thumb.getdata():
                    mu = sum(pixel) / 3
                    SSE += sum((pixel[i] - mu - bias[i]) * (pixel[i] - mu - bias[i]) for i in [0, 1, 2])
                MSE = float(SSE) / (40 * 40)
                if MSE > 22:
                    return True
                else:
                    return False
            else:
                return False

    def fillCheck(self):
        if self.opt.bordersColor:
            return self.opt.bordersColor
        else:
            bw = self.image.convert('L').point(lambda x: 0 if x < 128 else 255, '1')
            imageBoxA = bw.getbbox()
            imageBoxB = ImageChops.invert(bw).getbbox()
            if imageBoxA is None or imageBoxB is None:
                surfaceB, surfaceW = 0, 0
                diff = 0
            else:
                surfaceB = (imageBoxA[2] - imageBoxA[0]) * (imageBoxA[3] - imageBoxA[1])
                surfaceW = (imageBoxB[2] - imageBoxB[0]) * (imageBoxB[3] - imageBoxB[1])
                diff = ((max(surfaceB, surfaceW) - min(surfaceB, surfaceW)) / min(surfaceB, surfaceW)) * 100
            if diff > 0.5:
                if surfaceW < surfaceB:
                    return 'white'
                elif surfaceW > surfaceB:
                    return 'black'
            else:
                fill = 0
                startY = 0
                while startY < bw.size[1]:
                    if startY + 5 > bw.size[1]:
                        startY = bw.size[1] - 5
                    fill += self.getImageHistogram(bw.crop((0, startY, bw.size[0], startY + 5)))
                    startY += 5
                startX = 0
                while startX < bw.size[0]:
                    if startX + 5 > bw.size[0]:
                        startX = bw.size[0] - 5
                    fill += self.getImageHistogram(bw.crop((startX, 0, startX + 5, bw.size[1])))
                    startX += 5
                if fill > 0:
                    return 'black'
                else:
                    return 'white'


class ComicPage:
    def __init__(self, options, mode, path, image, color, fill):
        self.opt = options
        _, self.size, self.palette, self.gamma = self.opt.profileData
        if self.opt.hq:
            self.size = (int(self.size[0] * 1.5), int(self.size[1] * 1.5))
        self.kindle_scribe_azw3 = (options.profile == 'KS') and (options.format in ('MOBI', 'EPUB'))
        self.image = image
        self.color = color
        self.fill = fill
        self.rotated = False
        self.orgPath = os.path.join(path[0], path[1])
        if 'N' in mode:
            self.targetPath = os.path.join(path[0], os.path.splitext(path[1])[0]) + '-KCC'
        elif 'R' in mode:
            self.targetPath = os.path.join(path[0], os.path.splitext(path[1])[0]) + '-KCC-A'
            self.rotated = True
        elif 'S1' in mode:
            self.targetPath = os.path.join(path[0], os.path.splitext(path[1])[0]) + '-KCC-B'
        elif 'S2' in mode:
            self.targetPath = os.path.join(path[0], os.path.splitext(path[1])[0]) + '-KCC-C'
        # backwards compatibility for Pillow >9.1.0
        if not hasattr(Image, 'Resampling'):
            Image.Resampling = Image

    def saveToDir(self):
        try:
            flags = []
            if not self.opt.forcecolor and not self.opt.forcepng:
                self.image = self.image.convert('L')
            if self.rotated:
                flags.append('Rotated')
            if self.fill != 'white':
                flags.append('BlackBackground')
            if self.opt.forcepng:
                self.image.info["transparency"] = None
                self.targetPath += '.png'
                self.image.save(self.targetPath, 'PNG', optimize=1)
            else:
                self.targetPath += '.jpg'
                if self.opt.mozjpeg:
                    with io.BytesIO() as output:
                        self.image.save(output, format="JPEG", optimize=1, quality=85)
                        input_jpeg_bytes = output.getvalue()
                        output_jpeg_bytes = mozjpeg_lossless_optimization.optimize(input_jpeg_bytes)
                        with open(self.targetPath, "wb") as output_jpeg_file:
                            output_jpeg_file.write(output_jpeg_bytes)
                else:
                    self.image.save(self.targetPath, 'JPEG', optimize=1, quality=85)
            return [md5Checksum(self.targetPath), flags, self.orgPath]
        except IOError as err:
            raise RuntimeError('Cannot save image. ' + str(err))

    def autocontrastImage(self):
        gamma = self.opt.gamma
        if gamma < 0.1:
            gamma = self.gamma
            if self.gamma != 1.0 and self.color:
                gamma = 1.0
        if gamma == 1.0:
            self.image = ImageOps.autocontrast(self.image)
        else:
            self.image = ImageOps.autocontrast(Image.eval(self.image, lambda a: int(255 * (a / 255.) ** gamma)))

    def quantizeImage(self):
        colors = len(self.palette) // 3
        if colors < 256:
            self.palette += self.palette[:3] * (256 - colors)
        palImg = Image.new('P', (1, 1))
        palImg.putpalette(self.palette)
        self.image = self.image.convert('L')
        self.image = self.image.convert('RGB')
        # Quantize is deprecated but new function call it internally anyway...
        self.image = self.image.quantize(palette=palImg)

    def resizeImage(self):
        # kindle scribe conversion to mobi is limited in resolution by kindlegen, same with send to kindle and epub
        if self.kindle_scribe_azw3:
            self.size = (1440, 1920)
        ratio_device = float(self.size[1]) / float(self.size[0])
        ratio_image = float(self.image.size[1]) / float(self.image.size[0])
        method = self.resize_method()
        if self.opt.stretch:
            self.image = self.image.resize(self.size, method)
        elif method == Image.Resampling.BICUBIC and not self.opt.upscale:
            if self.opt.format == 'CBZ' or self.opt.kfx:
                borderw = int((self.size[0] - self.image.size[0]) / 2)
                borderh = int((self.size[1] - self.image.size[1]) / 2)
                self.image = ImageOps.expand(self.image, border=(borderw, borderh), fill=self.fill)
                if self.image.size[0] != self.size[0] or self.image.size[1] != self.size[1]:
                    self.image = ImageOps.fit(self.image, self.size, method=method)
        else: # if image bigger than device resolution or smaller with upscaling
            if abs(ratio_image - ratio_device) < AUTO_CROP_THRESHOLD:
                self.image = ImageOps.fit(self.image, self.size, method=method)
            elif self.opt.format == 'CBZ' or self.opt.kfx:
                self.image = ImageOps.pad(self.image, self.size, method=method, color=self.fill)
            else:
                if self.kindle_scribe_azw3:
                    self.size = (1860, 1920)
                self.image = ImageOps.contain(self.image, self.size, method=method)

    def resize_method(self):
        if self.image.size[0] <= self.size[0] and self.image.size[1] <= self.size[1]:
            return Image.Resampling.BICUBIC
        else:
            return Image.Resampling.LANCZOS

    def maybeCrop(self, box, minimum):
        box_area = (box[2] - box[0]) * (box[3] - box[1])
        image_area = self.image.size[0] * self.image.size[1]
        if (box_area / image_area) >= minimum:
            self.image = self.image.crop(box)

    def cropPageNumber(self, power, minimum):
        bbox = get_bbox_crop_margin_page_number(self.image, power, self.fill)
        
        if bbox:
            self.maybeCrop(bbox, minimum)

    def cropMargin(self, power, minimum):
        bbox = get_bbox_crop_margin(self.image, power, self.fill)
        
        if bbox:
            self.maybeCrop(bbox, minimum)


class Cover:
    def __init__(self, source, target, opt, tomeid):
        self.options = opt
        self.source = source
        self.target = target
        if tomeid == 0:
            self.tomeid = 1
        else:
            self.tomeid = tomeid
        self.image = Image.open(source)
        # backwards compatibility for Pillow >9.1.0
        if not hasattr(Image, 'Resampling'):
            Image.Resampling = Image
        self.process()

    def process(self):
        self.image = self.image.convert('RGB')
        self.image = ImageOps.autocontrast(self.image)
        if not self.options.forcecolor:
            self.image = self.image.convert('L')
        self.image.thumbnail(self.options.profileData[1], Image.Resampling.LANCZOS)
        self.save()

    def save(self):
        try:
            self.image.save(self.target, "JPEG", optimize=1, quality=85)
        except IOError:
            raise RuntimeError('Failed to save cover.')

    def saveToKindle(self, kindle, asin):
        self.image = self.image.resize((300, 470), Image.Resampling.LANCZOS)
        try:
            self.image.save(os.path.join(kindle.path.split('documents')[0], 'system', 'thumbnails',
                                         'thumbnail_' + asin + '_EBOK_portrait.jpg'), 'JPEG', optimize=1, quality=85)
        except IOError:
            raise RuntimeError('Failed to upload cover.')
