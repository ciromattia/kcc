# Copyright (C) 2010  Alex Yatskov
# Copyright (C) 2011  Stanislav (proDOOMman) Kosolapov <prodoomman@gmail.com>
# Copyright (C) 2012-2013  Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (C) 2013 Pawel Jastrzebski <pawelj@vulturis.eu>
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
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import os
from sys import platform
try:
    # noinspection PyUnresolvedReferences
    from PIL import Image, ImageOps, ImageStat, ImageChops
    if tuple(map(int, ('2.2.1'.split(".")))) > tuple(map(int, (Image.PILLOW_VERSION.split(".")))):
        print "ERROR: Pillow 2.2.1 or newer is required!"
        if platform.startswith('linux'):
            #noinspection PyUnresolvedReferences
            import Tkinter
            #noinspection PyUnresolvedReferences
            import tkMessageBox
            importRoot = Tkinter.Tk()
            importRoot.withdraw()
            tkMessageBox.showerror("KCC - Error", "Pillow 2.2.1 or newer is required!")
        exit(1)
except ImportError:
    print "ERROR: Pillow is not installed!"
    if platform.startswith('linux'):
        #noinspection PyUnresolvedReferences
        import Tkinter
        #noinspection PyUnresolvedReferences
        import tkMessageBox
        importRoot = Tkinter.Tk()
        importRoot.withdraw()
        tkMessageBox.showerror("KCC - Error", "Pillow 2.2.1 or newer is required!")
    exit(1)


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
        # Detect corrupted files - Phase 2
        try:
            self.origFileName = source
            self.filename = os.path.basename(self.origFileName)
            self.image = Image.open(source)
        except IOError:
            raise RuntimeError('Cannot read image file %s' % source)
        # Detect corrupted files - Phase 3
        try:
            self.image = Image.open(source)
            self.image.verify()
        except:
            raise RuntimeError('Image file %s is corrupted' % source)
        # Detect corrupted files - Phase 4
        try:
            self.image = Image.open(source)
            self.image.load()
        except:
            raise RuntimeError('Image file %s is corrupted' % source)
        self.image = Image.open(source)
        self.image = self.image.convert('RGB')
        self.rotated = None
        self.border = None
        self.noHPV = None
        self.noVPV = None
        if fill:
            self.fill = fill
        else:
            self.fill = None

    def saveToDir(self, targetdir, forcepng, color, wipe):
        try:
            suffix = ""
            if not color and not forcepng:
                self.image = self.image.convert('L')
            if self.rotated:
                suffix += "_kccrot"
            if wipe:
                os.remove(os.path.join(targetdir, self.filename))
            else:
                suffix += "_kcchq"
            if self.noHPV:
                suffix += "_kccnh"
            if self.noVPV:
                suffix += "_kccnv"
            if self.border:
                suffix += "_kccxl" + str(self.border[0]) + "_kccyu" + str(self.border[1]) + "_kccxr" +\
                          str(self.border[2]) + "_kccyd" + str(self.border[3])
            if forcepng:
                self.image.save(os.path.join(targetdir, os.path.splitext(self.filename)[0] + suffix + ".png"), "PNG",
                                optimize=1)
            else:
                self.image.save(os.path.join(targetdir, os.path.splitext(self.filename)[0] + suffix + ".jpg"), "JPEG",
                                optimize=1)
        except IOError as e:
            raise RuntimeError('Cannot write image in directory %s: %s' % (targetdir, e))

    def optimizeImage(self, gamma):
        if gamma < 0.1:
            gamma = self.gamma
            if self.gamma != 1.0 and self.isImageColor(self.image):
                gamma = 1.0
        if gamma == 1.0:
            self.image = ImageOps.autocontrast(self.image)
        else:
            self.image = ImageOps.autocontrast(Image.eval(self.image, lambda a: 255 * (a / 255.) ** gamma))

    def quantizeImage(self):
        colors = len(self.palette) / 3
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
        if self.fill == 'white':
            # This code trigger only when sourceImage is already saved. So we can break color quantization.
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
        else:
            size = (self.panelviewsize[0], self.panelviewsize[1])
        # If image is smaller than device resolution and upscale is off - Just expand it by adding margins
        if self.image.size[0] <= self.size[0] and self.image.size[1] <= self.size[1] and not upscale:
            borderw = (self.size[0] - self.image.size[0]) / 2
            borderh = (self.size[1] - self.image.size[1]) / 2
            self.image = ImageOps.expand(self.image, border=(borderw, borderh), fill=fill)
            return self.image
        # If stretching is on - Resize without other considerations
        if stretch:
            if self.image.size[0] <= size[0] and self.image.size[1] <= size[1]:
                method = Image.BICUBIC
            else:
                method = Image.ANTIALIAS
            self.image = self.image.resize(size, method)
            return self.image
        # Otherwise - Upscale/Downscale
        ratioDev = float(self.size[0]) / float(self.size[1])
        if (float(self.image.size[0]) / float(self.image.size[1])) < ratioDev:
            diff = int(self.image.size[1] * ratioDev) - self.image.size[0]
            self.image = ImageOps.expand(self.image, border=(diff / 2, 0), fill=fill)
        elif (float(self.image.size[0]) / float(self.image.size[1])) > ratioDev:
            diff = int(self.image.size[0] / ratioDev) - self.image.size[1]
            self.image = ImageOps.expand(self.image, border=(0, diff / 2), fill=fill)
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
                    leftbox = (0, 0, width / 2, height)
                    rightbox = (width / 2, 0, width, height)
                else:
                    # Source is portrait and target is landscape, so split by the height
                    leftbox = (0, 0, width, height / 2)
                    rightbox = (0, height / 2, width, height)
                filename = os.path.splitext(self.filename)
                fileone = targetdir + '/' + filename[0] + '_kcca' + filename[1]
                filetwo = targetdir + '/' + filename[0] + '_kccb' + filename[1]
                try:
                    if righttoleft:
                        pageone = self.image.crop(rightbox)
                        pagetwo = self.image.crop(leftbox)
                    else:
                        pageone = self.image.crop(leftbox)
                        pagetwo = self.image.crop(rightbox)
                    pageone.save(fileone)
                    pagetwo.save(filetwo)
                    os.remove(self.origFileName)
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
                    and diff < heightImg / 4:
                oldStat = ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg))).var[0]
                diff += delta
            diff -= delta
            pageNumberCut2 = diff
            diff += delta
            oldStat = ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg,
                                                      heightImg - pageNumberCut2))).var[0]
            while ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg - pageNumberCut2))).var[0]\
                    < fixedThreshold + oldStat and diff < heightImg / 4:
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
        for i in range(253, 256):
            white += RBGW[i]
        for i in range(3):
            black += RBGW[i]
        if black > pixelCount*0.5 and white == 0:
            return 1
        elif white > pixelCount*0.5 and black == 0:
            return -1
        else:
            return False

    def getImageFill(self):
        fill = 0
        # Search fom horizontal solid lines
        startY = 0
        stopY = 4
        searching = True
        while stopY <= self.image.size[1]:
            checkSolid = self.getImageHistogram(self.image.crop((0, startY, self.image.size[0], stopY)))
            if checkSolid:
                fill += checkSolid
            startY = stopY + 1
            stopY = startY + 4
            if stopY > self.image.size[1] and searching:
                startY = self.image.size[1] - 4
                stopY = self.image.size[1]
                searching = False
        # Search fom vertical solid lines
        startX = 0
        stopX = 4
        searching = True
        while stopX <= self.image.size[0]:
            checkSolid = self.getImageHistogram(self.image.crop((startX, 0, stopX, self.image.size[1])))
            if checkSolid:
                fill += checkSolid
            startX = stopX + 1
            stopX = startX + 4
            if stopX > self.image.size[0] and searching:
                startX = self.image.size[0] - 4
                stopX = self.image.size[0]
                searching = False
        if fill > 0:
            self.fill = 'black'
        else:
            self.fill = 'white'

    def isImageColor(self, image):
        v = ImageStat.Stat(image).var
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
