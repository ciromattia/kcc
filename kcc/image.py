# Copyright (C) 2010  Alex Yatskov
# Copyright (C) 2011  Stanislav (proDOOMman) Kosolapov <prodoomman@gmail.com>
# Copyright (C) 2012-2013  Ciro Mattia Gonano <ciromattia@gmail.com>
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
try:
    # noinspection PyUnresolvedReferences
    from PIL import Image, ImageOps, ImageStat, ImageChops
except ImportError:
    print "ERROR: Pillow is not installed!"
    exit(1)


class ProfileData:
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

    Profiles = {
        'K1': ("Kindle 1", (600, 800), Palette4, 1.8, (900, 1200)),
        'K2': ("Kindle 2", (600, 800), Palette15, 1.8, (900, 1200)),
        'K3': ("Kindle Keyboard", (600, 800), Palette16, 1.8, (900, 1200)),
        'K4NT': ("Kindle Non-Touch", (600, 800), Palette16, 1.8, (900, 1200)),
        'K4T': ("Kindle Touch", (600, 800), Palette16, 1.8, (900, 1200)),
        'KHD': ("Kindle Paperwhite", (758, 1024), Palette16, 1.8, (1137, 1536)),
        'KDX': ("Kindle DX", (824, 1200), Palette15, 1.8, (1236, 1800)),
        'KDXG': ("Kindle DXG", (824, 1200), Palette16, 1.8, (1236, 1800)),
        'KF': ("Kindle Fire", (600, 1024), Palette16, 1.0, (900, 1536)),
        'KFHD': ("Kindle Fire HD 7\"", (800, 1280), Palette16, 1.0, (1200, 1920)),
        'KFHD8': ("Kindle Fire HD 8.9\"", (1200, 1920), Palette16, 1.0, (1800, 2880)),
        'KFA': ("Kindle for Android", (0, 0), Palette16, 1.0, (0, 0)),
        'OTHER': ("Other", (0, 0), Palette16, 1.8, (0, 0)),
    }

    ProfileLabels = {
        "Kindle 1": 'K1',
        "Kindle 2": 'K2',
        "Kindle 3/Keyboard": 'K3',
        "Kindle 4/Non-Touch": 'K4NT',
        "Kindle 4/Touch": 'K4T',
        "Kindle Paperwhite": 'KHD',
        "Kindle DX": 'KDX',
        "Kindle DXG": 'KDXG',
        "Kindle Fire": 'KF',
        "Kindle Fire HD 7\"": 'KFHD',
        "Kindle Fire HD 8.9\"": 'KFHD8',
        "Kindle for Android": 'KFA',
        "Other": 'OTHER'
    }


class ComicPage:
    def __init__(self, source, device):
        try:
            self.profile_label, self.size, self.palette, self.gamma, self.panelviewsize = device
        except KeyError:
            raise RuntimeError('Unexpected output device %s' % device)
        # Detect corrupted files - Phase 2
        try:
            self.origFileName = source
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

    def saveToDir(self, targetdir, forcepng, color, wipe, suffix=None):
        filename = os.path.basename(self.origFileName)
        try:
            if not color:
                self.image = self.image.convert('L')    # convert to grayscale
            if suffix == "R":
                suffix = "_kccrotated"
            else:
                suffix = ""
            if wipe:
                os.remove(os.path.join(targetdir, filename))
            else:
                suffix += "_kcchq"
            if forcepng:
                self.image.save(os.path.join(targetdir, os.path.splitext(filename)[0] + suffix + ".png"), "PNG")
            else:
                self.image.save(os.path.join(targetdir, os.path.splitext(filename)[0] + suffix + ".jpg"), "JPEG")
        except IOError as e:
            raise RuntimeError('Cannot write image in directory %s: %s' % (targetdir, e))

    def optimizeImage(self, gamma):
        if gamma < 0.1:
            gamma = self.gamma
        if gamma == 1.0:
            self.image = ImageOps.autocontrast(self.image)
        else:
            self.image = ImageOps.autocontrast(Image.eval(self.image, lambda a: 255 * (a / 255.) ** gamma))

    def quantizeImage(self):
        self.image = self.image.convert('L')    # convert to grayscale
        self.image = self.image.convert("RGB")    # convert back to RGB
        colors = len(self.palette) / 3
        if colors < 256:
            self.palette += self.palette[:3] * (256 - colors)
        palImg = Image.new('P', (1, 1))
        palImg.putpalette(self.palette)
        self.image = self.image.quantize(palette=palImg)

    def resizeImage(self, upscale=False, stretch=False, black_borders=False, isSplit=False, toRight=False,
                    landscapeMode=False, qualityMode=0):
        method = Image.ANTIALIAS
        if black_borders:
            fill = 'black'
        else:
            fill = 'white'
        if qualityMode == 0:
            size = (self.size[0], self.size[1])
        else:
            size = (self.panelviewsize[0], self.panelviewsize[1])
        # Kindle Paperwhite/Touch - Force upscale of splited pages to increase readability
        if isSplit and landscapeMode:
            upscale = True
        if self.image.size[0] <= self.size[0] and self.image.size[1] <= self.size[1]:
            if not upscale:
                borderw = (self.size[0] - self.image.size[0]) / 2
                borderh = (self.size[1] - self.image.size[1]) / 2
                self.image = ImageOps.expand(self.image, border=(borderw, borderh), fill=fill)
                return self.image
            else:
                method = Image.BILINEAR
        if stretch:  # if stretching call directly resize() without other considerations.
            self.image = self.image.resize(size, method)
            return self.image
        ratioDev = float(self.size[0]) / float(self.size[1])
        if (float(self.image.size[0]) / float(self.image.size[1])) < ratioDev:
            if isSplit and landscapeMode:
                diff = int(self.image.size[1] * ratioDev) - self.image.size[0]
                self.image = ImageOps.expand(self.image, border=(diff / 2, 0), fill=fill)
                tempImg = Image.new(self.image.mode, (self.image.size[0] + diff, self.image.size[1]), fill)
                if toRight:
                    tempImg.paste(self.image, (diff, 0))
                else:
                    tempImg.paste(self.image, (0, 0))
                self.image = tempImg
            else:
                diff = int(self.image.size[1] * ratioDev) - self.image.size[0]
                self.image = ImageOps.expand(self.image, border=(diff / 2, 0), fill=fill)
        elif (float(self.image.size[0]) / float(self.image.size[1])) > ratioDev:
            diff = int(self.image.size[0] / ratioDev) - self.image.size[1]
            self.image = ImageOps.expand(self.image, border=(0, diff / 2), fill=fill)
        self.image = ImageOps.fit(self.image, size, method=method, centering=(0.5, 0.5))
        return self.image

    def splitPage(self, targetdir, righttoleft=False, rotate=False):
        width, height = self.image.size
        dstwidth, dstheight = self.size
        #print "Image is %d x %d" % (width,height)
        # only split if origin is not oriented the same as target
        if (width > height) != (dstwidth > dstheight):
            if rotate:
                self.image = self.image.rotate(90)
                return "R"
            else:
                if width > height:
                    # source is landscape, so split by the width
                    leftbox = (0, 0, width / 2, height)
                    rightbox = (width / 2, 0, width, height)
                else:
                    # source is portrait and target is landscape, so split by the height
                    leftbox = (0, 0, width, height / 2)
                    rightbox = (0, height / 2, width, height)
                filename = os.path.splitext(os.path.basename(self.origFileName))
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
            #    print "Top crop: %s"%diff
            self.image = self.image.crop((0, diff, widthImg, heightImg))
            widthImg, heightImg = self.image.size
            diff = delta
            # left
            while ImageStat.Stat(self.image.crop((0, 0, diff, heightImg))).var[0] < threshold and diff < widthImg:
                diff += delta
            diff -= delta
            #    print "Left crop: %s"%diff
            self.image = self.image.crop((diff, 0, widthImg, heightImg))
            widthImg, heightImg = self.image.size
            diff = delta
            # down
            while ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg))).var[0] < threshold\
                    and diff < heightImg:
                diff += delta
            diff -= delta
            #    print "Down crop: %s"%diff
            self.image = self.image.crop((0, 0, widthImg, heightImg - diff))
            widthImg, heightImg = self.image.size
            diff = delta
            # right
            while ImageStat.Stat(self.image.crop((widthImg - diff, 0, widthImg, heightImg))).var[0] < threshold\
                    and diff < widthImg:
                diff += delta
            diff -= delta
            #    print "Right crop: %s"%diff
            self.image = self.image.crop((0, 0, widthImg - diff, heightImg))
            #    print "New size: %sx%s"%(self.image.size[0],self.image.size[1])
        return self.image