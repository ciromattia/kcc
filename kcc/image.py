# Copyright (C) 2010  Alex Yatskov
# Copyright (C) 2011  Stanislav (proDOOMman) Kosolapov <prodoomman@gmail.com>
# Copyright (c) 2016  Alberto Planas <aplanas@gmail.com>
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2016 Pawel Jastrzebski <pawelj@iosphe.re>
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

import os
from io import BytesIO
from urllib.request import Request, urlopen
from urllib.parse import quote
from PIL import Image, ImageOps, ImageStat, ImageChops, ImageFilter
from .shared import md5Checksum
from . import __version__


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
        'K2': ("Kindle 2", (600, 670), Palette15, 1.8),
        'K3': ("Kindle", (600, 800), Palette16, 1.8),
        'K45': ("Kindle", (600, 800), Palette16, 1.8),
        'KDX': ("Kindle DX/DXG", (824, 1000), Palette16, 1.8),
        'KPW': ("Kindle Paperwhite 1/2", (758, 1024), Palette16, 1.8),
        'KV': ("Kindle Paperwhite 3/Voyage/Oasis", (1072, 1448), Palette16, 1.8),
        'KoMT': ("Kobo Mini/Touch", (600, 800), Palette16, 1.8),
        'KoG': ("Kobo Glo", (768, 1024), Palette16, 1.8),
        'KoGHD': ("Kobo Glo HD", (1072, 1448), Palette16, 1.8),
        'KoA': ("Kobo Aura", (758, 1024), Palette16, 1.8),
        'KoAHD': ("Kobo Aura HD", (1080, 1440), Palette16, 1.8),
        'KoAH2O': ("Kobo Aura H2O", (1080, 1430), Palette16, 1.8),
        'KoAO': ("Kobo Aura ONE", (1404, 1872), Palette16, 1.8),
        'OTHER': ("Other", (0, 0), Palette16, 1.8),
    }


class ComicPageParser:
    def __init__(self, source, options):
        self.opt = options
        self.source = source
        self.size = self.opt.profileData[1]
        self.payload = []
        self.image = Image.open(os.path.join(source[0], source[1])).convert('RGB')
        self.color = self.colorCheck()
        self.fill = self.fillCheck()
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
        # Only split if origin is not oriented the same as target
        if (width > height) != (dstwidth > dstheight) and not self.opt.webtoon:
            if self.opt.splitter != 1:
                if width > height:
                    # Source is landscape, so split by the width
                    leftbox = (0, 0, int(width / 2), height)
                    rightbox = (int(width / 2), 0, width, height)
                else:
                    # Source is portrait and target is landscape, so split by the height
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
                self.payload.append(['R', self.source, self.image.rotate(90, Image.BICUBIC, True),
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
    def __init__(self, mode, path, image, color, fill, options):
        self.opt = options
        _, self.size, self.palette, self.gamma = self.opt.profileData
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

    def saveToDir(self):
        try:
            flags = []
            if not self.opt.forcecolor and not self.opt.forcepng:
                self.image = self.image.convert('L')
            if self.rotated:
                flags.append('Rotated')
            if self.fill != 'white':
                flags.append('BlackFill')
            if self.opt.forcepng:
                self.targetPath += '.png'
                self.image.save(self.targetPath, 'PNG', optimize=1)
            else:
                self.targetPath += '.jpg'
                self.image.save(self.targetPath, 'JPEG', optimize=1, quality=80)
            return [md5Checksum(self.targetPath), flags, self.orgPath]
        except IOError:
            raise RuntimeError('Cannot save image.')

    def autocontrastImage(self):
        gamma = self.opt.gamma
        if gamma < 0.1:
            gamma = self.gamma
            if self.gamma != 1.0 and self.color:
                gamma = 1.0
        if gamma == 1.0:
            self.image = ImageOps.autocontrast(self.image)
        else:
            self.image = ImageOps.autocontrast(Image.eval(self.image, lambda a: 255 * (a / 255.) ** gamma))

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
        if self.image.size[0] <= self.size[0] and self.image.size[1] <= self.size[1]:
            method = Image.BICUBIC
        else:
            method = Image.LANCZOS
        if self.opt.stretch:
            self.image = self.image.resize(self.size, method)
        elif self.image.size[0] <= self.size[0] and self.image.size[1] <= self.size[1] and not self.opt.upscale:
            if self.opt.format == 'CBZ':
                borderw = int((self.size[0] - self.image.size[0]) / 2)
                borderh = int((self.size[1] - self.image.size[1]) / 2)
                self.image = ImageOps.expand(self.image, border=(borderw, borderh), fill=self.fill)
                if self.image.size[0] != self.size[0] or self.image.size[1] != self.size[1]:
                    self.image = ImageOps.fit(self.image, self.size, method=Image.BICUBIC, centering=(0.5, 0.5))
        else:
            if self.opt.format == 'CBZ':
                ratioDev = float(self.size[0]) / float(self.size[1])
                if (float(self.image.size[0]) / float(self.image.size[1])) < ratioDev:
                    diff = int(self.image.size[1] * ratioDev) - self.image.size[0]
                    self.image = ImageOps.expand(self.image, border=(int(diff / 2), 0), fill=self.fill)
                elif (float(self.image.size[0]) / float(self.image.size[1])) > ratioDev:
                    diff = int(self.image.size[0] / ratioDev) - self.image.size[1]
                    self.image = ImageOps.expand(self.image, border=(0, int(diff / 2)), fill=self.fill)
                self.image = ImageOps.fit(self.image, self.size, method=method, centering=(0.5, 0.5))
            else:
                hpercent = self.size[1] / float(self.image.size[1])
                wsize = int((float(self.image.size[0]) * float(hpercent)))
                self.image = self.image.resize((wsize, self.size[1]), method)
                if self.image.size[0] > self.size[0] or self.image.size[1] > self.size[1]:
                    self.image.thumbnail(self.size, Image.LANCZOS)

    def getBoundingBox(self, tmpImg):
        min_margin = [int(0.005 * i + 0.5) for i in tmpImg.size]
        max_margin = [int(0.1 * i + 0.5) for i in tmpImg.size]
        bbox = tmpImg.getbbox()
        bbox = (
            max(0, min(max_margin[0], bbox[0] - min_margin[0])),
            max(0, min(max_margin[1], bbox[1] - min_margin[1])),
            min(tmpImg.size[0],
                max(tmpImg.size[0] - max_margin[0], bbox[2] + min_margin[0])),
            min(tmpImg.size[1],
                max(tmpImg.size[1] - max_margin[1], bbox[3] + min_margin[1])),
        )
        return bbox

    def cropPageNumber(self, power):
        if self.fill != 'white':
            tmpImg = self.image.convert(mode='L')
        else:
            tmpImg = ImageOps.invert(self.image.convert(mode='L'))
        tmpImg = tmpImg.point(lambda x: x and 255)
        tmpImg = tmpImg.filter(ImageFilter.MinFilter(size=3))
        tmpImg = tmpImg.filter(ImageFilter.GaussianBlur(radius=5))
        tmpImg = tmpImg.point(lambda x: (x >= 16 * power) and x)
        self.image = self.image.crop(tmpImg.getbbox()) if tmpImg.getbbox() else self.image

    def cropMargin(self, power):
        if self.fill != 'white':
            tmpImg = self.image.convert(mode='L')
        else:
            tmpImg = ImageOps.invert(self.image.convert(mode='L'))
        tmpImg = tmpImg.filter(ImageFilter.GaussianBlur(radius=3))
        tmpImg = tmpImg.point(lambda x: (x >= 16 * power) and x)
        self.image = self.image.crop(self.getBoundingBox(tmpImg)) if tmpImg.getbbox() else self.image


class Cover:
    def __init__(self, source, target, opt, tomeNumber):
        self.options = opt
        self.source = source
        self.target = target
        if tomeNumber == 0:
            self.tomeNumber = 1
        else:
            self.tomeNumber = tomeNumber
        if self.tomeNumber in self.options.remoteCovers:
            try:
                source = urlopen(Request(quote(self.options.remoteCovers[self.tomeNumber]).replace('%3A', ':', 1),
                                         headers={'User-Agent': 'KindleComicConverter/' + __version__})).read()
                self.image = Image.open(BytesIO(source))
                self.processExternal()
            except Exception:
                self.image = Image.open(source)
                self.processInternal()
        else:
            self.image = Image.open(source)
            self.processInternal()

    def processInternal(self):
        self.image = self.image.convert('RGB')
        self.image = self.trim()
        self.save()

    def processExternal(self):
        self.image = self.image.convert('RGB')
        self.image.thumbnail(self.options.profileData[1], Image.LANCZOS)
        self.save()

    def trim(self):
        bg = Image.new(self.image.mode, self.image.size, self.image.getpixel((0, 0)))
        diff = ImageChops.difference(self.image, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        if bbox:
            return self.image.crop(bbox)
        else:
            return self.image

    def save(self):
        try:
            self.image.save(self.target, "JPEG", optimize=1, quality=80)
        except IOError:
            raise RuntimeError('Failed to process downloaded cover.')

    def saveToKindle(self, kindle, asin):
        self.image = self.image.resize((300, 470), Image.ANTIALIAS).convert('L')
        try:
            self.image.save(os.path.join(kindle.path.split('documents')[0], 'system', 'thumbnails',
                                         'thumbnail_' + asin + '_EBOK_portrait.jpg'), 'JPEG')
        except IOError:
            raise RuntimeError('Failed to upload cover.')
