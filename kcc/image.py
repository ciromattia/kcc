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
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>'
__docformat__ = 'restructuredtext en'

import os
from PIL import Image, ImageOps, ImageDraw, ImageStat


class ImageFlags:
    Orient = 1 << 0
    Resize = 1 << 1
    Frame = 1 << 2
    Quantize = 1 << 3
    Stretch = 1 << 4


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
        'K1': ("Kindle", (600, 800), Palette4),
        'K2': ("Kindle 2", (600, 800), Palette15),
        'K3': ("Kindle 3/Keyboard", (600, 800), Palette16),
        'K4': ("Kindle 4/NT/Touch", (600, 800), Palette16),
        'KHD': ("Kindle Paperwhite", (758, 1024), Palette16),
        'KDX': ("Kindle DX", (824, 1200), Palette15),
        'KDXG': ("Kindle DXG", (824, 1200), Palette16)
    }
    
    ProfileLabels = {
        "Kindle": 'K1',
        "Kindle 2": 'K2',
        "Kindle 3/Keyboard": 'K3',
        "Kindle 4/NT/Touch": 'K4',
        "Kindle Paperwhite": 'KHD',
        "Kindle DX": 'KDX',
        "Kindle DXG": 'KDXG'
    }


class ComicPage:
    def __init__(self, source, device):
        try:
            self.profile_label, self.size, self.palette = ProfileData.Profiles[device]
        except KeyError:
            raise RuntimeError('Unexpected output device %s' % device)
        try:
            self.origFileName = source
            self.image = Image.open(source)
        except IOError:
            raise RuntimeError('Cannot read image file %s' % source)
        self.image = self.image.convert('RGB')

    def saveToDir(self, targetdir):
        filename = os.path.basename(self.origFileName)
        try:
            self.image = self.image.convert('L')    # convert to grayscale
            self.image.save(os.path.join(targetdir, filename), "JPEG")
        except IOError as e:
            raise RuntimeError('Cannot write image in directory %s: %s' % (targetdir, e))

    def optimizeImage(self):
        self.image = ImageOps.autocontrast(self.image)

    def quantizeImage(self):
        colors = len(self.palette) / 3
        if colors < 256:
            self.palette += self.palette[:3] * (256 - colors)
        palImg = Image.new('P', (1, 1))
        palImg.putpalette(self.palette)
        self.image = self.image.quantize(palette=palImg)

    def resizeImage(self, upscale=False, stretch=False, black_borders=False):
        method = Image.ANTIALIAS
        if black_borders:
            fill = 'black'
        else:
            fill = 'white'
        if self.image.size[0] <= self.size[0] and self.image.size[1] <= self.size[1]:
            if not upscale:
                # do not upscale but center image in a device-sized image
                borderw = (self.size[0] - self.image.size[0]) / 2
                borderh = (self.size[1] - self.image.size[1]) / 2
                self.image = ImageOps.expand(self.image, border=(borderw, borderh), fill=fill)
                return self.image
            else:
                method = Image.NEAREST

        if stretch:  # if stretching call directly resize() without other considerations.
            self.image = self.image.resize(self.size, method)
            return self.image

        ratioDev = float(self.size[0]) / float(self.size[1])
        if (float(self.image.size[0]) / float(self.image.size[1])) < ratioDev:
            diff = int(self.image.size[1] * ratioDev) - self.image.size[0]
            self.image = ImageOps.expand(self.image, border=(diff / 2, 0), fill=fill)
        elif (float(self.image.size[0]) / float(self.image.size[1])) > ratioDev:
            diff = int(self.image.size[0] / ratioDev) - self.image.size[1]
            self.image = ImageOps.expand(self.image, border=(0, diff / 2), fill=fill)
        self.image = ImageOps.fit(self.image, self.size, method=method, centering=(0.5, 0.5))
        return self.image

    def splitPage(self, targetdir, righttoleft=False, rotate=False):
        width, height = self.image.size
        dstwidth, dstheight = self.size
        #print "Image is %d x %d" % (width,height)
        # only split if origin is not oriented the same as target
        if (width > height) != (dstwidth > dstheight):
			if rotate:
				self.image = self.image.rotate(90)
				return None
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
				fileone = targetdir + '/' + filename[0] + '-1' + filename[1]
				filetwo = targetdir + '/' + filename[0] + '-2' + filename[1]
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

    def frameImage(self):
        foreground = tuple(self.palette[:3])
        background = tuple(self.palette[-3:])
        widthDev, heightDev = self.size
        widthImg, heightImg = self.image.size
        pastePt = (
            max(0, (widthDev - widthImg) / 2),
            max(0, (heightDev - heightImg) / 2)
        )
        corner1 = (
            pastePt[0] - 1,
            pastePt[1] - 1
        )
        corner2 = (
            pastePt[0] + widthImg + 1,
            pastePt[1] + heightImg + 1
        )
        imageBg = Image.new(self.image.mode, self.size, background)
        imageBg.paste(self.image, pastePt)
        draw = ImageDraw.Draw(imageBg)
        draw.rectangle([corner1, corner2], outline=foreground)
        self.image = imageBg

    def cutPageNumber(self):
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
        oldStat = ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg - pageNumberCut2))).var[0]
        while ImageStat.Stat(self.image.crop((0, heightImg - diff, widthImg, heightImg - pageNumberCut2))).var[0]\
                < fixedThreshold + oldStat and diff < heightImg / 4:
            diff += delta
        diff -= delta
        pageNumberCut3 = diff
        delta = 5
        diff = delta
        while ImageStat.Stat(self.image.crop((0, heightImg - pageNumberCut2, diff, heightImg))).var[0] < fixedThreshold\
                and diff < widthImg:
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

    def addProgressbar(self, file_number, files_totalnumber, size, howoften):
        if file_number // howoften != float(file_number) / howoften:
            return self.image
        white = (255, 255, 255)
        black = (0, 0, 0)
        widthDev, heightDev = size
        widthImg, heightImg = self.image.size
        pastePt = (
            max(0, (widthDev - widthImg) / 2),
            max(0, (heightDev - heightImg) / 2)
        )
        imageBg = Image.new('RGB', size, white)
        imageBg.paste(self.image, pastePt)
        self.image = imageBg
        widthImg, heightImg = self.image.size
        draw = ImageDraw.Draw(self.image)
        #Black rectangle
        draw.rectangle([(0, heightImg - 3), (widthImg, heightImg)], outline=black, fill=black)
        #White rectangle
        draw.rectangle([(widthImg * file_number / files_totalnumber, heightImg - 3), (widthImg - 1, heightImg)],
                       outline=black, fill=white)
        #Making notches
        for i in range(1, 10):
            if i <= (10 * file_number / files_totalnumber):
                notch_colour = white  # White
            else:
                notch_colour = black  # Black
            draw.line([(widthImg * float(i) / 10, heightImg - 3), (widthImg * float(i) / 10, heightImg)],
                      fill=notch_colour)
            #The 50%
            if i == 5:
                draw.rectangle([(widthImg / 2 - 1, heightImg - 5), (widthImg / 2 + 1, heightImg)],
                               outline=black, fill=notch_colour)
        return self.image
