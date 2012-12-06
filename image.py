# Copyright (C) 2010  Alex Yatskov
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
from PIL import Image, ImageDraw

class ImageFlags:
    Orient = 1 << 0
    Resize = 1 << 1
    Frame = 1 << 2
    Quantize = 1 << 3
    Stretch = 1 << 4


class KindleData:
    Palette4 = [
        0x00, 0x00, 0x00,
        0x55, 0x55, 0x55,
        0xaa, 0xaa, 0xaa,
        0xff, 0xff, 0xff
    ]

    Palette15a = [
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

    Palette15b = [
        0x00, 0x00, 0x00,
        0x11, 0x11, 0x11,
        0x22, 0x22, 0x22,
        0x33, 0x33, 0x33,
        0x44, 0x44, 0x44,
        0x55, 0x55, 0x55,
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
        'K1': ((600, 800), Palette4),
        'K2': ((600, 800), Palette15a),
        'K3': ((600, 800), Palette15a),
        'K4': ((600, 800), Palette15b),
        'KHD': ((758, 1024), Palette15b),
        'KDX': ((824, 1200), Palette15a)
    }

class ComicPage:
    def __init__(self,source,device):
        try:
            self.size, self.palette = KindleData.Profiles[device]
        except KeyError:
            raise RuntimeError('Unexpected output device %s' % device)
        try:
            self.origFileName = source
            self.image = Image.open(source)
        except IOError:
            raise RuntimeError('Cannot read image file %s' % source)
        self.image = self.image.convert('RGB')

    def saveToDir(self,targetdir):
        filename = os.path.basename(self.origFileName)
        print "Saving to " + targetdir + '/' + filename
        try:
            self.image = self.image.convert('L')    # convert to grayscale
            self.image.save(targetdir + '/' + filename,"JPEG")
        except IOError as e:
            raise RuntimeError('Cannot write image in directory %s: %s' %(targetdir,e))

    def quantizeImage(self):
        colors = len(self.palette) / 3
        if colors < 256:
            palette = self.palette + self.palette[:3] * (256 - colors)
        palImg = Image.new('P', (1, 1))
        palImg.putpalette(palette)
        self.image = self.image.quantize(palette=palImg)

    def stretchImage(self):
        widthDev, heightDev = self.size
        self.image = self.image.resize((widthDev, heightDev), Image.ANTIALIAS)

    def resizeImage(self):
        widthDev, heightDev = self.size
        widthImg, heightImg = self.image.size
        if widthImg <= widthDev and heightImg <= heightDev:
            return self.image
        ratioImg = float(widthImg) / float(heightImg)
        ratioWidth = float(widthImg) / float(widthDev)
        ratioHeight = float(heightImg) / float(heightDev)
        if ratioWidth > ratioHeight:
            widthImg = widthDev
            heightImg = int(widthDev / ratioImg)
        elif ratioWidth < ratioHeight:
            heightImg = heightDev
            widthImg = int(heightDev * ratioImg)
        else:
            widthImg, heightImg = self.size
        self.image = self.image.resize((widthImg, heightImg), Image.ANTIALIAS)

    def orientImage(self):
        widthDev, heightDev = self.size
        widthImg, heightImg = self.image.size
        if (widthImg > heightImg) != (widthDev > heightDev):
            self.image =  self.image.rotate(90, Image.BICUBIC, True)

    def splitPage(self, targetdir, righttoleft=False):
        width, height = self.image.size
        dstwidth, dstheight = self.size
        print "Image is %d x %d" % (width,height)
        # only split if origin is not oriented the same as target
        if (width > height) != (dstwidth > dstheight):
            if (width > height):
                # source is landscape, so split by the width
                leftbox = (0, 0, width/2, height)
                rightbox = (width/2, 0, width, height)
            else:
                # source is portrait and target is landscape, so split by the height
                leftbox = (0, 0, width, height/2)
                rightbox = (0, height/2, width, height)
            filename = os.path.splitext(os.path.basename(self.origFileName))
            fileone = targetdir + '/' + filename[0] + '-1' + filename[1]
            filetwo = targetdir + '/' + filename[0] + '-2' + filename[1]
            try:
                if (righttoleft == True):
                    pageone = self.image.crop(rightbox)
                    pagetwo = self.image.crop(leftbox)
                else:
                    pageone = self.image.crop(leftbox)
                    pagetwo = self.image.crop(rightbox)
                pageone.save(fileone)
                pagetwo.save(filetwo)
                os.remove(self.origFileName)
            except IOError as e:
                raise RuntimeError('Cannot write image in directory %s: %s' %(targetdir,e))
            return (fileone,filetwo)
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

# for debug purposes (this file is not meant to be called directly
if __name__ == "__main__":
    import sys
    imgfile = sys.argv[1]
    img = ComicPage(imgfile, "KHD")
    pages = img.splitPage('temp/',False)
    if (pages != None):
        print "%s, %s" % pages
    sys.exit(0)
    img.orientImage()
    img.resizeImage()
    img.frameImage()
    img.quantizeImage()
    img.saveToDir("temp/")
    sys.exit(0)
