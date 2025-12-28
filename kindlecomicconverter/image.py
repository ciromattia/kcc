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
import numpy as np
from pathlib import Path
from functools import cached_property
import mozjpeg_lossless_optimization
from PIL import Image, ImageOps, ImageFile, ImageChops, ImageDraw

from .rainbow_artifacts_eraser import erase_rainbow_artifacts
from .page_number_crop_alg import get_bbox_crop_margin_page_number, get_bbox_crop_margin
from .inter_panel_crop_alg import crop_empty_inter_panel

AUTO_CROP_THRESHOLD = 0.015
ImageFile.LOAD_TRUNCATED_IMAGES = True


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

    ProfilesKindleEBOK = {
    }

    ProfilesKindlePDOC = {
        'K1': ("Kindle 1", (600, 670), Palette4, 1.0),
        'K2': ("Kindle 2", (600, 670), Palette15, 1.0),
        'KDX': ("Kindle DX/DXG", (824, 1000), Palette16, 1.0),
        'K34': ("Kindle Keyboard/Touch", (600, 800), Palette16, 1.0),
        'K57': ("Kindle 5/7", (600, 800), Palette16, 1.0),
        'KPW': ("Kindle Paperwhite 1/2", (758, 1024), Palette16, 1.0),
        'KV': ("Kindle Voyage", (1072, 1448), Palette16, 1.0),
        'KPW34': ("Kindle Paperwhite 3/4/Oasis", (1072, 1448), Palette16, 1.0),
        'K810': ("Kindle 8/10", (600, 800), Palette16, 1.0),
        'KO': ("Kindle Oasis 2/3/Paperwhite 12", (1264, 1680), Palette16, 1.0),
        'K11': ("Kindle 11", (1072, 1448), Palette16, 1.0),
        'KPW5': ("Kindle Paperwhite 5/Signature Edition", (1236, 1648), Palette16, 1.0),
        'KS': ("Kindle Scribe 1/2", (1860, 2480), Palette16, 1.0),
        'KCS': ("Kindle Colorsoft", (1264, 1680), Palette16, 1.0),
        'KS3': ("Kindle Scribe 3", (1920, 2640), Palette16, 1.0),
        'KSCS': ("Kindle Scribe Colorsoft", (1920, 2640), Palette16, 1.0),
    }

    ProfilesKindle = {
        **ProfilesKindleEBOK,
        **ProfilesKindlePDOC
    }

    ProfilesKobo = {
        'KoMT': ("Kobo Mini/Touch", (600, 800), Palette16, 1.0),
        'KoG': ("Kobo Glo", (768, 1024), Palette16, 1.0),
        'KoGHD': ("Kobo Glo HD", (1072, 1448), Palette16, 1.0),
        'KoA': ("Kobo Aura", (758, 1024), Palette16, 1.0),
        'KoAHD': ("Kobo Aura HD", (1080, 1440), Palette16, 1.0),
        'KoAH2O': ("Kobo Aura H2O", (1080, 1430), Palette16, 1.0),
        'KoAO': ("Kobo Aura ONE", (1404, 1872), Palette16, 1.0),
        'KoN': ("Kobo Nia", (758, 1024), Palette16, 1.0),
        'KoC': ("Kobo Clara HD/Kobo Clara 2E", (1072, 1448), Palette16, 1.0),
        'KoCC': ("Kobo Clara Colour", (1072, 1448), Palette16, 1.0),
        'KoL': ("Kobo Libra H2O/Kobo Libra 2", (1264, 1680), Palette16, 1.0),
        'KoLC': ("Kobo Libra Colour", (1264, 1680), Palette16, 1.0),
        'KoF': ("Kobo Forma", (1440, 1920), Palette16, 1.0),
        'KoS': ("Kobo Sage", (1440, 1920), Palette16, 1.0),
        'KoE': ("Kobo Elipsa", (1404, 1872), Palette16, 1.0),
    }

    ProfilesRemarkable = {
        'Rmk1': ("reMarkable 1", (1404, 1872), Palette16, 1.0),
        'Rmk2': ("reMarkable 2", (1404, 1872), Palette16, 1.0),
        'RmkPP': ("reMarkable Paper Pro", (1620, 2160), Palette16, 1.0),
        'RmkPPMove': ("reMarkable Paper Pro Move", (954, 1696), Palette16, 1.0),
    }

    Profiles = {
        **ProfilesKindle,
        **ProfilesKobo,
        **ProfilesRemarkable,
        'OTHER': ("Other", (0, 0), Palette16, 1.0),
    }


class ComicPageParser:
    def __init__(self, source, options):
        Image.MAX_IMAGE_PIXELS = int(2048 * 2048 * 2048 // 4 // 3)
        self.opt = options
        self.source = source
        self.size = self.opt.profileData[1]
        self.payload = []

        # Detect corruption in source image, let caller catch any exceptions triggered.
        srcImgPath = os.path.join(source[0], source[1])
        Image.open(srcImgPath).verify()
        with Image.open(srcImgPath) as im:
            self.image = im.copy()

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
            self.payload.append(['N', self.source, new_image, self.fill])
        elif (width > height) != (dstwidth > dstheight) and width <= dstheight and height <= dstwidth \
                and not self.opt.webtoon and self.opt.splitter == 1:
            spread = self.image
            if not self.opt.norotate:
                spread = spread.rotate(90, Image.Resampling.BICUBIC, True)
            self.payload.append(['R', self.source, spread, self.fill])
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
                self.payload.append(['S1', self.source, pageone, self.fill])
                self.payload.append(['S2', self.source, pagetwo, self.fill])
            if self.opt.splitter > 0:
                spread = self.image
                if not self.opt.norotate:
                    spread = spread.rotate(90, Image.Resampling.BICUBIC, True)
                self.payload.append(['R', self.source, spread, self.fill])
        else:
            self.payload.append(['N', self.source, self.image, self.fill])

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
    def __init__(self, options, mode, path, image, fill):
        self.opt = options
        _, self.size, self.palette, self.gamma = self.opt.profileData
        if self.opt.hq:
            self.size = (int(self.size[0] * 1.5), int(self.size[1] * 1.5))
        self.original_color_mode = image.mode
        # TODO: color check earlier
        self.image = image.convert("RGB")
        self.fill = fill
        self.rotated = False
        self.orgPath = os.path.join(path[0], path[1])
        self.targetPathStart = os.path.join(path[0], os.path.splitext(path[1])[0])
        if 'N' in mode:
            self.targetPathOrder = '-kcc-x'
        elif 'R' in mode:
            self.targetPathOrder = '-kcc-a' if options.rotatefirst else '-kcc-d'
            if not options.norotate:
                self.rotated = True
        elif 'S1' in mode:
            self.targetPathOrder = '-kcc-b'
        elif 'S2' in mode:
            self.targetPathOrder = '-kcc-c'
        # backwards compatibility for Pillow >9.1.0
        if not hasattr(Image, 'Resampling'):
            Image.Resampling = Image

    @cached_property
    def color(self):
        if self.original_color_mode in ("L", "1"):
            return False
        if self.opt.webtoon:
            return True
        if self.calculate_color():
            return True
        return False
    
    # cut off pixels from both ends of the histogram to remove jpg compression artifacts
    # for better accuracy, you could split the image in half and analyze each half separately
    def histograms_cutoff(self, cb_hist, cr_hist, cutoff=(2, 2)):
        if cutoff == (0, 0):
            return cb_hist, cr_hist

        for h in cb_hist, cr_hist:
            # get number of pixels
            n = sum(h)
            # remove cutoff% pixels from the low end
            cut = int(n * cutoff[0] // 100)
            for lo in range(256):
                if cut > h[lo]:
                    cut = cut - h[lo]
                    h[lo] = 0
                else:
                    h[lo] -= cut
                    cut = 0
                if cut <= 0:
                    break
            # remove cutoff% samples from the high end
            cut = int(n * cutoff[1] // 100)
            for hi in range(255, -1, -1):
                if cut > h[hi]:
                    cut = cut - h[hi]
                    h[hi] = 0
                else:
                    h[hi] -= cut
                    cut = 0
                if cut <= 0:
                    break
        return cb_hist, cr_hist

    def color_precision(self, cb_hist_original, cr_hist_original, cutoff, diff_threshold):
        cb_hist, cr_hist = self.histograms_cutoff(cb_hist_original.copy(), cr_hist_original.copy(), cutoff)

        cb_nonzero = [i for i, e in enumerate(cb_hist) if e]
        cr_nonzero = [i for i, e in enumerate(cr_hist) if e]
        cb_spread = cb_nonzero[-1] - cb_nonzero[0]
        cr_spread = cr_nonzero[-1] - cr_nonzero[0]

        # bias adjustment, don't go lower than 7
        SPREAD_THRESHOLD = 7
        if self.opt.forcecolor:
            if any([
                cb_nonzero[0] > 128,
                cr_nonzero[0] > 128,
                cb_nonzero[-1] < 128,
                cr_nonzero[-1] < 128,
            ]):
                return True, True
        elif cb_spread < SPREAD_THRESHOLD and cr_spread < SPREAD_THRESHOLD:
            return True, False

        DIFF_THRESHOLD = diff_threshold
        if any([
            cb_nonzero[0] <= 128 - DIFF_THRESHOLD, 
            cr_nonzero[0] <= 128 - DIFF_THRESHOLD, 
            cb_nonzero[-1] >= 128 + DIFF_THRESHOLD, 
            cr_nonzero[-1] >= 128 + DIFF_THRESHOLD,
        ]):
            return True, True
        
        return False, None

    def calculate_color(self):
        img = self.image.convert("YCbCr")
        _, cb, cr = img.split()
        cb_hist_original = cb.histogram()
        cr_hist_original = cr.histogram()

        # you can increase 22 but don't increase 10. 4 maybe can go higher
        for cutoff, diff_threshold in [((0, 0), 22), ((.2, .2), 10), ((3, 3), 4)]:
            done, decision = self.color_precision(cb_hist_original, cr_hist_original, cutoff, diff_threshold)
            if done:
                return decision
        return False
        
    def saveToDir(self):
        try:
            flags = []
            if self.rotated:
                flags.append('Rotated')
            if self.fill != 'white':
                flags.append('BlackBackground')
            if self.opt.kindle_scribe_azw3 and self.image.size[1] > 1920:
                w, h = self.image.size
                targetPath = self.save_with_codec(self.image.crop((0, 0, w, 1920)), self.targetPathStart + self.targetPathOrder + '-above')
                self.save_with_codec(self.image.crop((0, 1920, w, h)), self.targetPathStart + self.targetPathOrder + '-below')
            elif self.opt.kindle_scribe_azw3:
                targetPath = self.save_with_codec(self.image, self.targetPathStart + self.targetPathOrder + '-whole')
            else:
                targetPath = self.save_with_codec(self.image, self.targetPathStart + self.targetPathOrder)
            if os.path.isfile(self.orgPath):
                os.remove(self.orgPath)
            return [Path(targetPath).name, flags]
        except IOError as err:
            raise RuntimeError('Cannot save image. ' + str(err))

    def save_with_codec(self, image, targetPath):
        if self.opt.forcepng:
            image.info.pop('transparency', None)
            if self.opt.iskindle and ('MOBI' in self.opt.format or 'EPUB' in self.opt.format):
                targetPath += '.gif'
                image.save(targetPath, 'GIF', optimize=1, interlace=False)
            else:
                targetPath += '.png'
                image.save(targetPath, 'PNG', optimize=1)
        else:
            targetPath += '.jpg'
            if self.opt.mozjpeg:
                with io.BytesIO() as output:
                    image.save(output, format="JPEG", optimize=1, quality=self.opt.jpegquality)
                    input_jpeg_bytes = output.getvalue()
                    output_jpeg_bytes = mozjpeg_lossless_optimization.optimize(input_jpeg_bytes)
                    with open(targetPath, "wb") as output_jpeg_file:
                        output_jpeg_file.write(output_jpeg_bytes)
            else:
                image.save(targetPath, 'JPEG', optimize=1, quality=self.opt.jpegquality)
        return targetPath

    def gammaCorrectImage(self):
        gamma = self.opt.gamma
        if gamma < 0.1:
            gamma = self.gamma
            if self.gamma != 1.0 and self.color:
                gamma = 1.0
        if gamma == 1.0:
            pass
        else:
            self.image = Image.eval(self.image, lambda a: int(255 * (a / 255.) ** gamma))

    def autocontrastImage(self):
        if self.opt.webtoon:
            return
        if self.opt.noautocontrast:
            return
        if self.color and not self.opt.colorautocontrast:
            return

        # if image is extremely low contrast, that was probably intentional
        extrema = self.image.convert('L').getextrema()
        if extrema[1] - extrema[0] < (255 - 32 * 3):
            return

        if self.opt.autolevel:
            self.autolevelImage()

        self.image = ImageOps.autocontrast(self.image, preserve_tone=True)

    def autolevelImage(self):
        img = self.image
        if self.color:
            img = self.image.convert("YCbCr")
            y, cb, cr = img.split()
            img = y
        else:
            img = img.convert('L')
        h = img.histogram()
        most_common_dark_pixel_count = max(h[:64])
        black_point = h.index(most_common_dark_pixel_count)
        bp = black_point
        img = img.point(lambda p: p if p > bp else bp)
        if self.color:
            self.image = Image.merge(mode='YCbCr', bands=[img, cb, cr]).convert('RGB')
        else:
            self.image = img

    def convertToGrayscale(self):
        self.image = self.image.convert('L')

    def quantizeImage(self):
        # remove all color pixels from image, since colorCheck() has some tolerance
        # quantize with a small number of color pixels in a mostly b/w image can have unexpected results
        self.image = self.image.convert("RGB")

        palImg = Image.new('P', (1, 1))
        palImg.putpalette(self.palette)
        self.image = self.image.quantize(palette=palImg)

    def optimizeForDisplay(self, eraserainbow, is_color):
        # Erase rainbow artifacts for grayscale and color images by removing spectral frequencies that cause Moire interference with color filter array
        if eraserainbow and all(dim > 1 for dim in self.image.size):
            self.image = erase_rainbow_artifacts(self.image, is_color)

    def resizeImage(self):
        if self.opt.norotate and self.targetPathOrder in ('-kcc-a', '-kcc-d') and not self.opt.kindle_scribe_azw3:
            # TODO: Kindle Scribe case
            if self.opt.kindle_azw3 and any(dim > 1920 for dim in self.image.size):
                self.image = ImageOps.contain(self.image, (1920, 1920), Image.Resampling.LANCZOS)
            elif self.image.size[0] > self.size[0] * 2 or self.image.size[1] > self.size[1]:
                self.image = ImageOps.contain(self.image, (self.size[0] * 2, self.size[1]), Image.Resampling.LANCZOS)
            return
        
        ratio_device = float(self.size[1]) / float(self.size[0])
        ratio_image = float(self.image.size[1]) / float(self.image.size[0])
        method = self.resize_method()
        if self.opt.stretch:
            self.image = self.image.resize(self.size, method)
        elif method == Image.Resampling.BICUBIC and not self.opt.upscale:
            pass
        else: # if image bigger than device resolution or smaller with upscaling
            if abs(ratio_image - ratio_device) < AUTO_CROP_THRESHOLD:
                self.image = ImageOps.fit(self.image, self.size, method=method)
            elif (self.opt.format in ('CBZ', 'PDF') or self.opt.kfx) and not self.opt.white_borders:
                self.image = ImageOps.pad(self.image, self.size, method=method, color=self.fill)
            else:
                self.image = ImageOps.contain(self.image, self.size, method=method)

    def resize_method(self):
        if self.image.size[0] < self.size[0] and self.image.size[1] < self.size[1]:
            return Image.Resampling.BICUBIC
        else:
            return Image.Resampling.LANCZOS

    def maybeCrop(self, box, minimum):
        w, h = self.image.size
        left, upper, right, lower = box
        if self.opt.preservemargin:
            ratio = 1 - self.opt.preservemargin / 100
            box = left * ratio, upper * ratio, right + (w - right) * (1 - ratio), lower + (h - lower) * (1 - ratio)
        box_area = (box[2] - box[0]) * (box[3] - box[1])
        image_area = self.image.size[0] * self.image.size[1]
        if (box_area / image_area) >= minimum:
            self.image = self.image.crop(box)

    def cropPageNumber(self, power, minimum):
        bbox = get_bbox_crop_margin_page_number(self.image, power, self.fill)
        
        if bbox:
            w, h = self.image.size
            left, upper, right, lower = bbox
            # don't crop more than 10% of image
            bbox = (min(0.1*w, left), min(0.1*h, upper), max(0.9*w, right), max(0.9*h, lower))
            self.maybeCrop(bbox, minimum)

    def cropMargin(self, power, minimum):
        bbox = get_bbox_crop_margin(self.image, power, self.fill)
        
        if bbox:
            w, h = self.image.size
            left, upper, right, lower = bbox
            # don't crop more than 10% of image
            bbox = (min(0.1*w, left), min(0.1*h, upper), max(0.9*w, right), max(0.9*h, lower))
            self.maybeCrop(bbox, minimum)

    def cropInterPanelEmptySections(self, direction):
        self.image = crop_empty_inter_panel(self.image, direction, background_color=self.fill)

class Cover:
    def __init__(self, source, opt):
        self.options = opt
        self.source = source
        self.image = Image.open(source)
        # backwards compatibility for Pillow >9.1.0
        if not hasattr(Image, 'Resampling'):
            Image.Resampling = Image
        self.process()

    def process(self):
        self.image = self.image.convert('RGB')
        self.image = ImageOps.autocontrast(self.image, preserve_tone=True)
        if not self.options.forcecolor:
            self.image = self.image.convert('L')
        self.crop_main_cover()

        size = list(self.options.profileData[1])
        if self.options.kindle_scribe_azw3:
            size[0] = min(size[0], 1920)
            size[1] = min(size[1], 1920)
        self.image.thumbnail(tuple(size), Image.Resampling.LANCZOS)

    def crop_main_cover(self):
        w, h = self.image.size
        if w / h > 2:
            if self.options.righttoleft:
                self.image = self.image.crop((w/6, 0, w/2 - w * 0.02, h))
            else:
                self.image = self.image.crop((w/2 + w * 0.02, 0, 5/6 * w, h))
        elif w / h > 1.34:
            if self.options.righttoleft:
                self.image = self.image.crop((0, 0, w/2 - w * 0.03, h))
            else:
                self.image = self.image.crop((w/2 + w * 0.03, 0, w, h))

    def save_to_epub(self, target, tomeid, len_tomes=0):
        try:
            if tomeid == 0:
                self.image.save(target, "JPEG", optimize=1, quality=self.options.jpegquality)
            else:
                copy = self.image.copy()
                draw = ImageDraw.Draw(copy)
                w, h = copy.size
                draw.text(
                    xy=(w/2, h * .85),
                    text=f'{tomeid}/{len_tomes}',
                    anchor='ms',
                    font_size=h//7,
                    fill=255,
                    stroke_fill=0,
                    stroke_width=25
                )
                copy.save(target, "JPEG", optimize=1, quality=self.options.jpegquality)
        except IOError:
            raise RuntimeError('Failed to save cover.')

    def saveToKindle(self, kindle, asin):
        self.image = ImageOps.contain(self.image, (300, 470), Image.Resampling.LANCZOS)
        try:
            self.image.save(os.path.join(kindle.path.split('documents')[0], 'system', 'thumbnails',
                                         'thumbnail_' + asin + '_EBOK_portrait.jpg'), 'JPEG', optimize=1, quality=self.options.jpegquality)
        except IOError:
            raise RuntimeError('Failed to upload cover.')
