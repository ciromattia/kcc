# Copyright (C) 2010  Alex Yatskov
# Copyright (C) 2011  Stanislav (proDOOMman) Kosolapov <prodoomman@gmail.com>
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2014 Pawel Jastrzebski <pawelj@vulturis.eu>
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

__license__ = 'ISC'
__copyright__ = '2012-2014, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import os
from functools import reduce
from PIL import Image, ImageOps, ImageStat, ImageChops
from .shared import md5Checksum


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
        'KHD': ("Kindle Paperwhite", (758, 1024), Palette16, 1.8, (1137, 1536)),
        'KDX': ("Kindle DX/DXG", (824, 1000), Palette16, 1.8, (1236, 1500)),
        'KF': ("Kindle Fire", (600, 1024), PalleteNull, 1.0, (900, 1536)),
        'KFHD': ("K. Fire HD 7\"", (800, 1280), PalleteNull, 1.0, (1200, 1920)),
        'KFHD8': ("K. Fire HD 8.9\"", (1200, 1920), PalleteNull, 1.0, (1800, 2880)),
        'KFHDX': ("K. Fire HDX 7\"", (1200, 1920), PalleteNull, 1.0, (1800, 2880)),
        'KFHDX8': ("K. Fire HDX 8.9\"", (1600, 2560), PalleteNull, 1.0, (2400, 3840)),
        'KoMT': ("Kobo Mini/Touch", (600, 800), Palette16, 1.8, (900, 1200)),
        'KoG': ("Kobo Glow", (768, 1024), Palette16, 1.8, (1152, 1536)),
        'KoA': ("Kobo Aura", (758, 1024), Palette16, 1.8, (1137, 1536)),
        'KoAHD': ("Kobo Aura HD", (1080, 1440), Palette16, 1.8, (1620, 2160)),
        'KFA': ("Kindle for Android", (0, 0), PalleteNull, 1.0, (0, 0)),
        'OTHER': ("Other", (0, 0), Palette16, 1.8, (0, 0)),
    }


class ComicPage:
    def __init__(self, source, device, fill=None):
        try:
            self.profile_label, self.size, self.palette, self.gamma, self.panelviewsize = device
        except KeyError:
            raise RuntimeError('Unexpected output device %s' % device)
        self.origFileName = source
        self.filename = os.path.basename(self.origFileName)
        self.image = Image.open(source)
        self.image = self.image.convert('RGB')
        self.color = self.isImageColor()
        self.rotated = None
        self.border = None
        self.noHPV = None
        self.noVPV = None
        self.noPV = None
        self.purge = False
        self.hq = False
        if fill:
            self.fill = fill
        else:
            self.fill = None

    def saveToDir(self, targetdir, forcepng, color):
        try:
            if not self.purge:
                flags = []
                filename = os.path.join(targetdir, os.path.splitext(self.filename)[0]) + '-KCC'
                if not color and not forcepng:
                    self.image = self.image.convert('L')
                if self.rotated:
                    flags.append('Rotated')
                if self.hq:
                    flags.append('HighQuality')
                    filename += '-HQ'
                if self.noPV:
                    flags.append('NoPanelView')
                else:
                    if self.noHPV:
                        flags.append('NoHorizontalPanelView')
                    if self.noVPV:
                        flags.append('NoVerticalPanelView')
                    if self.border:
                        flags.append("Margins-" + str(self.border[0]) + "-" + str(self.border[1]) + "-"
                                     + str(self.border[2]) + "-" + str(self.border[3]))
                if forcepng:
                    filename += ".png"
                    self.image.save(filename,  "PNG", optimize=1)
                else:
                    filename += ".jpg"
                    self.image.save(filename, "JPEG", optimize=1)
                return [md5Checksum(filename), flags]
            else:
                return None
        except IOError as e:
            raise RuntimeError('Cannot write image in directory %s: %s' % (targetdir, e))

    def optimizeImage(self, gamma):
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

    def calculateBorderPercent(self, x, img, isWidth):
        if isWidth:
            return int(round(float(x)/float(img.image.size[0]), 4) * 10000 * 1.5)
        else:
            return int(round(float(x)/float(img.image.size[1]), 4) * 10000 * 1.5)

    def calculateBorder(self, sourceImage, isHQ=False):
        if (isHQ and sourceImage.purge) or self.noPV:
            self.border = [0, 0, 0, 0]
            self.noPV = True
            return
        if self.fill == 'white':
            # Only already saved files can have P mode. So we can break color quantization.
            if sourceImage.image.mode == 'P':
                sourceImage.image = sourceImage.image.convert('RGB')
            border = ImageChops.invert(sourceImage.image).getbbox()
        else:
            border = sourceImage.image.getbbox()
        if border is not None:
            if isHQ:
                multiplier = 1.0
            else:
                multiplier = 1.5
            self.border = [self.calculateBorderPercent(border[0], sourceImage, True),
                           self.calculateBorderPercent(border[1], sourceImage, False),
                           self.calculateBorderPercent((sourceImage.image.size[0] - border[2]), sourceImage, True),
                           self.calculateBorderPercent((sourceImage.image.size[1] - border[3]), sourceImage, False)]
            if int((border[2] - border[0]) * multiplier) < self.size[0]:
                self.noHPV = True
            if int((border[3] - border[1]) * multiplier) < self.size[1]:
                self.noVPV = True
        else:
            self.border = [0, 0, 0, 0]
            self.noHPV = True
            self.noVPV = True

    def resizeImage(self, upscale=False, stretch=False, bordersColor=None, qualityMode=0):
        if bordersColor:
            fill = bordersColor
        else:
            fill = self.fill
        # Set target size
        if qualityMode == 0:
            size = (self.size[0], self.size[1])
        elif qualityMode == 1 and not stretch and not upscale and self.image.size[0] <=\
                self.size[0] and self.image.size[1] <= self.size[1]:
            size = (self.size[0], self.size[1])
        elif qualityMode == 1:
            size = (self.panelviewsize[0], self.panelviewsize[1])
        elif qualityMode == 2 and not stretch and not upscale and self.image.size[0] <=\
                self.size[0] and self.image.size[1] <= self.size[1]:
            self.purge = True
            return self.image
        else:
            self.hq = True
            size = (self.panelviewsize[0], self.panelviewsize[1])
        # If stretching is on - Resize without other considerations
        if stretch:
            if self.image.size[0] <= size[0] and self.image.size[1] <= size[1]:
                method = Image.BICUBIC
            else:
                method = Image.ANTIALIAS
            self.image = self.image.resize(size, method)
            return self.image
        # If image is smaller than target resolution and upscale is off - Just expand it by adding margins
        if self.image.size[0] <= size[0] and self.image.size[1] <= size[1] and not upscale:
            borderw = int((size[0] - self.image.size[0]) / 2)
            borderh = int((size[1] - self.image.size[1]) / 2)
            # PV is disabled when source image is smaller than device screen and upscale is off
            if self.image.size[0] <= self.size[0] and self.image.size[1] <= self.size[1]:
                self.noPV = True
            self.image = ImageOps.expand(self.image, border=(borderw, borderh), fill=fill)
            # Border can't be float so sometimes image might be 1px too small/large
            if self.image.size[0] != size[0] or self.image.size[1] != size[1]:
                self.image = ImageOps.fit(self.image, size, method=Image.BICUBIC, centering=(0.5, 0.5))
            return self.image
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
            method = Image.ANTIALIAS
        self.image = ImageOps.fit(self.image, size, method=method, centering=(0.5, 0.5))
        return self.image

    def splitPage(self, targetdir, righttoleft=False, rotate=False):
        width, height = self.image.size
        dstwidth, dstheight = self.size
        # Only split if origin is not oriented the same as target
        if (width > height) != (dstwidth > dstheight):
            if rotate:
                self.image = self.image.rotate(90)
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
                filename = os.path.splitext(self.filename)
                fileone = targetdir + '/' + filename[0] + '-A' + filename[1]
                filetwo = targetdir + '/' + filename[0] + '-B' + filename[1]
                try:
                    if righttoleft:
                        pageone = self.image.crop(rightbox)
                        pagetwo = self.image.crop(leftbox)
                    else:
                        pageone = self.image.crop(leftbox)
                        pagetwo = self.image.crop(rightbox)
                    pageone.save(fileone)
                    pagetwo.save(filetwo)
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
        return self.image

    def cropWhiteSpace(self, threshold):
        if ImageChops.invert(self.image).getbbox() is not None:
            widthImg, heightImg = self.image.size
            delta = 10
            diff = delta
            # top
            while ImageStat.Stat(self.image.crop((0, 0, widthImg, diff))).var[0] < threshold and diff < heightImg:
                diff += delta
            diff -= delta
            self.image = self.image.crop((0, diff, widthImg, heightImg))
            widthImg, heightImg = self.image.size
            diff = delta
            # left
            while ImageStat.Stat(self.image.crop((0, 0, diff, heightImg))).var[0] < threshold and diff < widthImg:
                diff += delta
            diff -= delta
            self.image = self.image.crop((diff, 0, widthImg, heightImg))
            widthImg, heightImg = self.image.size
            diff = delta
            # down
            while ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg))).var[0] < threshold\
                    and diff < heightImg:
                diff += delta
            diff -= delta
            self.image = self.image.crop((0, 0, widthImg, heightImg - diff))
            widthImg, heightImg = self.image.size
            diff = delta
            # right
            while ImageStat.Stat(self.image.crop((widthImg - diff, 0, widthImg, heightImg))).var[0] < threshold\
                    and diff < widthImg:
                diff += delta
            diff -= delta
            self.image = self.image.crop((0, 0, widthImg - diff, heightImg))
        return self.image

    def getImageHistogram(self, image):
        histogram = image.histogram()
        RBGW = []
        pixelCount = 0
        for i in range(256):
            pixelCount += histogram[i] + histogram[256 + i] + histogram[512 + i]
            RBGW.append(histogram[i] + histogram[256 + i] + histogram[512 + i])
        white = 0
        black = 0
        for i in range(251, 256):
            white += RBGW[i]
        for i in range(5):
            black += RBGW[i]
        if black > pixelCount*0.8 and white == 0:
            return 1
        elif white > pixelCount*0.8 and black == 0:
            return -1
        else:
            return False

    def getImageFill(self, webtoon):
        if not webtoon and self.color:
            self.fill = 'black'
            return
        fill = 0
        if not webtoon and not self.rotated:
            # Search for horizontal solid lines
            startY = 0
            while startY < self.image.size[1]:
                if startY + 5 > self.image.size[1]:
                    startY = self.image.size[1] - 5
                checkSolid = self.getImageHistogram(self.image.crop((0, startY, self.image.size[0], startY+5)))
                if checkSolid:
                    fill += checkSolid
                startY += 5
        else:
            # Search for vertical solid lines
            startX = 0
            while startX < self.image.size[0]:
                if startX + 5 > self.image.size[0]:
                    startX = self.image.size[0] - 5
                checkSolid = self.getImageHistogram(self.image.crop((startX, 0, startX+5, self.image.size[1])))
                if checkSolid:
                    fill += checkSolid
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
