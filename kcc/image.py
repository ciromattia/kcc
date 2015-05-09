# Copyright (C) 2010  Alex Yatskov
# Copyright (C) 2011  Stanislav (proDOOMman) Kosolapov <prodoomman@gmail.com>
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2015 Pawel Jastrzebski <pawelj@iosphe.re>
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
from functools import reduce
from PIL import Image, ImageOps, ImageStat, ImageChops
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
        'K1': ("Kindle 1", (600, 670), Palette4, 1.8, (900, 1005)),
        'K2': ("Kindle 2", (600, 670), Palette15, 1.8, (900, 1005)),
        'K345': ("Kindle", (600, 800), Palette16, 1.8, (900, 1200)),
        'KDX': ("Kindle DX/DXG", (824, 1000), Palette16, 1.8, (1236, 1500)),
        'KPW': ("Kindle Paperwhite", (758, 1024), Palette16, 1.8, (1137, 1536)),
        'KV': ("Kindle Voyage", (1072, 1448), Palette16, 1.8, (1608, 2172)),
        'KFHD': ("K. Fire HD", (800, 1280), PalleteNull, 1.0, (1200, 1920)),
        'KFHDX': ("K. Fire HDX", (1200, 1920), PalleteNull, 1.0, (1800, 2880)),
        'KFHDX8': ("K. Fire HDX 8.9", (1600, 2560), PalleteNull, 1.0, (2400, 3840)),
        'KFA': ("Kindle for Android", (0, 0), PalleteNull, 1.0, (0, 0)),
        'KoMT': ("Kobo Mini/Touch", (600, 800), Palette16, 1.8, (900, 1200)),
        'KoG': ("Kobo Glo", (768, 1024), Palette16, 1.8, (1152, 1536)),
        'KoGHD': ("Kobo Glo HD", (1072, 1448), Palette16, 1.8, (1608, 2172)),
        'KoA': ("Kobo Aura", (758, 1024), Palette16, 1.8, (1137, 1536)),
        'KoAHD': ("Kobo Aura HD", (1080, 1440), Palette16, 1.8, (1620, 2160)),
        'KoAH2O': ("Kobo Aura H2O", (1080, 1430), Palette16, 1.8, (1620, 2145)),
        'OTHER': ("Other", (0, 0), Palette16, 1.8, (0, 0)),
    }


class ComicPage:
    def __init__(self, source, options, original=None):
        try:
            self.profile_label, self.size, self.palette, self.gamma, self.panelviewsize = options.profileData
        except KeyError:
            raise RuntimeError('Unexpected output device %s' % options.profileData)
        self.origFileName = source
        self.filename = os.path.basename(self.origFileName)
        self.image = Image.open(source)
        self.image = self.image.convert('RGB')
        self.opt = options
        if original:
            self.second = True
            self.rotated = original.rotated
            self.border = original.border
            self.noHPV = original.noHPV
            self.noVPV = original.noVPV
            self.noPV = original.noPV
            self.noHQ = original.noHQ
            self.fill = original.fill
            self.color = original.color
            if self.rotated:
                self.image = self.image.rotate(90, Image.BICUBIC, True)
            self.opt.quality = 0
        else:
            self.second = False
            self.rotated = None
            self.border = None
            self.noHPV = None
            self.noVPV = None
            self.noPV = None
            self.fill = None
            self.noHQ = False
            if options.webtoon:
                self.color = True
            else:
                self.color = self.isImageColor()

    def saveToDir(self, targetdir):
        try:
            flags = []
            filename = os.path.join(targetdir, os.path.splitext(self.filename)[0]) + '-KCC'
            if not self.opt.forcecolor and not self.opt.forcepng:
                self.image = self.image.convert('L')
            if self.rotated:
                flags.append('Rotated')
            if self.noPV:
                flags.append('NoPanelView')
            else:
                if self.noHPV:
                    flags.append('NoHorizontalPanelView')
                if self.noVPV:
                    flags.append('NoVerticalPanelView')
                if self.border:
                    flags.append('Margins-' + str(self.border[0]) + '-' + str(self.border[1]) + '-'
                                 + str(self.border[2]) + '-' + str(self.border[3]))
            if self.fill != 'white':
                flags.append('BlackFill')
            if self.opt.quality == 2:
                filename += '-HQ'
            if self.opt.forcepng:
                filename += '.png'
                self.image.save(filename, 'PNG', optimize=1)
            else:
                filename += '.jpg'
                self.image.save(filename, 'JPEG', optimize=1, quality=80)
            return [md5Checksum(filename), flags]
        except IOError as e:
            raise RuntimeError('Cannot write image in directory %s: %s' % (targetdir, e))

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

    def calculateBorder(self):
        if self.noPV:
            self.border = [0.0, 0.0, 0.0, 0.0]
            return
        if self.fill == 'white':
            border = ImageChops.invert(self.image).getbbox()
        else:
            border = self.image.getbbox()
        if self.opt.quality == 2:
            multiplier = 1.0
        else:
            multiplier = 1.5
        if border is not None:
            self.border = [round(float(border[0])/float(self.image.size[0])*150, 3),
                           round(float(border[1])/float(self.image.size[1])*150, 3),
                           round(float(self.image.size[0]-border[2])/float(self.image.size[0])*150, 3),
                           round(float(self.image.size[1]-border[3])/float(self.image.size[1])*150, 3)]
            if int((border[2] - border[0]) * multiplier) < self.size[0] + 10:
                self.noHPV = True
            if int((border[3] - border[1]) * multiplier) < self.size[1] + 10:
                self.noVPV = True
        else:
            self.border = [0.0, 0.0, 0.0, 0.0]
            self.noHPV = True
            self.noVPV = True

    def resizeImage(self):
        if self.opt.bordersColor:
            fill = self.opt.bordersColor
        else:
            fill = self.fill
        # Set target size
        if self.opt.quality == 0:
            size = (self.size[0], self.size[1])
        elif self.opt.quality == 1 and not self.opt.stretch and not self.opt.upscale and self.image.size[0] <=\
                self.size[0] and self.image.size[1] <= self.size[1]:
            size = (self.size[0], self.size[1])
        elif self.opt.quality == 1:
            # Forcing upscale to make sure that margins will be not too big
            if not self.opt.stretch:
                self.opt.upscale = True
            size = (self.panelviewsize[0], self.panelviewsize[1])
        elif self.opt.quality == 2 and not self.opt.stretch and not self.opt.upscale and self.image.size[0] <=\
                self.size[0] and self.image.size[1] <= self.size[1]:
            # HQ version will not be needed
            self.noHQ = True
            return
        else:
            size = (self.panelviewsize[0], self.panelviewsize[1])
        # If stretching is on - Resize without other considerations
        if self.opt.stretch:
            if self.image.size[0] <= size[0] and self.image.size[1] <= size[1]:
                method = Image.BICUBIC
            else:
                method = Image.LANCZOS
            self.image = self.image.resize(size, method)
            return
        # If image is smaller than target resolution and upscale is off - Just expand it by adding margins
        if self.image.size[0] <= size[0] and self.image.size[1] <= size[1] and not self.opt.upscale:
            borderw = int((size[0] - self.image.size[0]) / 2)
            borderh = int((size[1] - self.image.size[1]) / 2)
            # PV is disabled when source image is smaller than device screen and upscale is off
            if self.image.size[0] <= self.size[0] and self.image.size[1] <= self.size[1]:
                self.noPV = True
            self.image = ImageOps.expand(self.image, border=(borderw, borderh), fill=fill)
            # Border can't be float so sometimes image might be 1px too small/large
            if self.image.size[0] != size[0] or self.image.size[1] != size[1]:
                self.image = ImageOps.fit(self.image, size, method=Image.BICUBIC, centering=(0.5, 0.5))
            return
        # Otherwise - Upscale/Downscale
        ratioDev = float(size[0]) / float(size[1])
        if (float(self.image.size[0]) / float(self.image.size[1])) < ratioDev:
            diff = int(self.image.size[1] * ratioDev) - self.image.size[0]
            self.image = ImageOps.expand(self.image, border=(int(diff / 2), 0), fill=fill)
        elif (float(self.image.size[0]) / float(self.image.size[1])) > ratioDev:
            diff = int(self.image.size[0] / ratioDev) - self.image.size[1]
            self.image = ImageOps.expand(self.image, border=(0, int(diff / 2)), fill=fill)
        if self.image.size[0] <= size[0] and self.image.size[1] <= size[1]:
            method = Image.BICUBIC
        else:
            method = Image.LANCZOS
        self.image = ImageOps.fit(self.image, size, method=method, centering=(0.5, 0.5))
        return

    def splitPage(self, targetdir):
        width, height = self.image.size
        dstwidth, dstheight = self.size
        # Only split if origin is not oriented the same as target
        if (width > height) != (dstwidth > dstheight):
            if self.opt.rotate:
                self.image = self.image.rotate(90, Image.BICUBIC, True)
                self.rotated = True
                return None
            else:
                self.rotated = False
                if width > height:
                    # Source is landscape, so split by the width
                    leftbox = (0, 0, int(width / 2), height)
                    rightbox = (int(width / 2), 0, width, height)
                else:
                    # Source is portrait and target is landscape, so split by the height
                    leftbox = (0, 0, width, int(height / 2))
                    rightbox = (0, int(height / 2), width, height)
                filename = os.path.splitext(self.filename)[0]
                fileone = targetdir + '/' + filename + '-AAA.png'
                filetwo = targetdir + '/' + filename + '-BBB.png'
                try:
                    if self.opt.righttoleft:
                        pageone = self.image.crop(rightbox)
                        pagetwo = self.image.crop(leftbox)
                    else:
                        pageone = self.image.crop(leftbox)
                        pagetwo = self.image.crop(rightbox)
                    pageone.save(fileone, 'PNG', optimize=1)
                    pagetwo.save(filetwo, 'PNG', optimize=1)
                except IOError as e:
                    raise RuntimeError('Cannot write image in directory %s: %s' % (targetdir, e))
                return fileone, filetwo
        else:
            self.rotated = False
            return None

    def cutPageNumber(self):
        if ImageChops.invert(self.image).getbbox() is not None:
            widthImg, heightImg = self.image.size
            delta = 2
            diff = delta
            fixedThreshold = 5
            if ImageStat.Stat(self.image).var[0] < 2 * fixedThreshold:
                return self.image
            while ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg))).var[0] < fixedThreshold\
                    and diff < heightImg:
                diff += delta
            diff -= delta
            pageNumberCut1 = diff
            if diff < delta:
                diff = delta
            oldStat = ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg))).var[0]
            diff += delta
            while ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg))).var[0] - oldStat > 0\
                    and diff < heightImg // 4:
                oldStat = ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg))).var[0]
                diff += delta
            diff -= delta
            pageNumberCut2 = diff
            diff += delta
            oldStat = ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg,
                                                      heightImg - pageNumberCut2))).var[0]
            while ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg - pageNumberCut2))).var[0]\
                    < fixedThreshold + oldStat and diff < heightImg // 4:
                diff += delta
            diff -= delta
            pageNumberCut3 = diff
            delta = 5
            diff = delta
            while ImageStat.Stat(self.image.crop((0, heightImg - pageNumberCut2, diff, heightImg))).var[0]\
                    < fixedThreshold and diff < widthImg:
                diff += delta
            diff -= delta
            pageNumberX1 = diff
            diff = delta
            while ImageStat.Stat(self.image.crop((widthImg - diff, heightImg - pageNumberCut2,
                                                  widthImg, heightImg))).var[0] < fixedThreshold and diff < widthImg:
                diff += delta
            diff -= delta
            pageNumberX2 = widthImg - diff
            if pageNumberCut3 - pageNumberCut1 > 2 * delta\
                    and float(pageNumberX2 - pageNumberX1) / float(pageNumberCut2 - pageNumberCut1) <= 9.0\
                    and ImageStat.Stat(self.image.crop((0, heightImg - pageNumberCut3, widthImg, heightImg))).var[0]\
                    / ImageStat.Stat(self.image).var[0] < 0.1\
                    and pageNumberCut3 < heightImg / 4 - delta:
                diff = pageNumberCut3
            else:
                diff = pageNumberCut1
            self.image = self.image.crop((0, 0, widthImg, heightImg - diff))

    def cropWhiteSpace(self):
        if ImageChops.invert(self.image).getbbox() is not None:
            widthImg, heightImg = self.image.size
            delta = 10
            diff = delta
            fixedThreshold = 0.1
            # top
            while ImageStat.Stat(self.image.crop((0, 0, widthImg, diff))).var[0] < fixedThreshold and diff < heightImg:
                diff += delta
            diff -= delta
            self.image = self.image.crop((0, diff, widthImg, heightImg))
            widthImg, heightImg = self.image.size
            diff = delta
            # left
            while ImageStat.Stat(self.image.crop((0, 0, diff, heightImg))).var[0] < fixedThreshold and diff < widthImg:
                diff += delta
            diff -= delta
            self.image = self.image.crop((diff, 0, widthImg, heightImg))
            widthImg, heightImg = self.image.size
            diff = delta
            # down
            while ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg))).var[0] < fixedThreshold\
                    and diff < heightImg:
                diff += delta
            diff -= delta
            self.image = self.image.crop((0, 0, widthImg, heightImg - diff))
            widthImg, heightImg = self.image.size
            diff = delta
            # right
            while ImageStat.Stat(self.image.crop((widthImg - diff, 0, widthImg, heightImg))).var[0] < fixedThreshold\
                    and diff < widthImg:
                diff += delta
            diff -= delta
            self.image = self.image.crop((0, 0, widthImg - diff, heightImg))

    def getImageHistogram(self, image):
        histogram = image.histogram()
        if histogram[0] == 0:
            return -1
        elif histogram[255] == 0:
            return 1
        else:
            return 0

    def getImageFill(self):
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
                self.fill = 'white'
            elif surfaceW > surfaceB:
                self.fill = 'black'
        else:
            fill = 0
            startY = 0
            while startY < bw.size[1]:
                if startY + 5 > bw.size[1]:
                    startY = bw.size[1] - 5
                fill += self.getImageHistogram(bw.crop((0, startY, bw.size[0], startY+5)))
                startY += 5
            startX = 0
            while startX < bw.size[0]:
                if startX + 5 > bw.size[0]:
                    startX = bw.size[0] - 5
                fill += self.getImageHistogram(bw.crop((startX, 0, startX+5, bw.size[1])))
                startX += 5
            if fill > 0:
                self.fill = 'black'
            else:
                self.fill = 'white'

    def isImageColor(self):
        v = ImageStat.Stat(self.image).var
        isMonochromatic = reduce(lambda x, y: x and y < 0.005, v, True)
        if isMonochromatic:
            # Monochromatic
            return False
        else:
            if len(v) == 3:
                maxmin = abs(max(v) - min(v))
                if maxmin > 1000:
                    # Color
                    return True
                elif maxmin > 100:
                    # Probably color
                    return True
                else:
                    # Grayscale
                    return False
            elif len(v) == 1:
                # Black and white
                return False
            else:
                # Detection failed
                return False


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
            raise RuntimeError('Failed to save cover')
