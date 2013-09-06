#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Ciro Mattia Gonano <ciromattia@gmail.com>
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
__version__ = '3.2.1'
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import os
import sys
from shutil import rmtree, copytree, move
from optparse import OptionParser, OptionGroup
from multiprocessing import Pool, Queue, freeze_support
try:
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    from PIL import Image, ImageStat
except ImportError:
    print "ERROR: Pillow is not installed!"
    exit(1)
try:
    from PyQt4 import QtCore
except ImportError:
    QtCore = None


def getImageFileName(imgfile):
    filename = os.path.splitext(imgfile)
    if filename[0].startswith('.') or\
            (filename[1].lower() != '.png' and
             filename[1].lower() != '.jpg' and
             filename[1].lower() != '.gif' and
             filename[1].lower() != '.tif' and
             filename[1].lower() != '.tiff' and
             filename[1].lower() != '.bmp' and
             filename[1].lower() != '.jpeg'):
        return None
    return filename


def getImageHistogram(image):
    histogram = image.histogram()
    RBGW = []
    for i in range(256):
        RBGW.append(histogram[i] + histogram[256 + i] + histogram[512 + i])
    white = 0
    black = 0
    for i in range(245, 256):
        white += RBGW[i]
    for i in range(11):
        black += RBGW[i]
    if white > black:
        return False
    else:
        return True


def getImageFill(image):
    imageSize = image.size
    imageT = image.crop((0, 0, imageSize[0], 1))
    imageB = image.crop((0, imageSize[1]-1, imageSize[0], imageSize[1]))
    fill = 0
    fill += getImageHistogram(imageT)
    fill += getImageHistogram(imageB)
    if fill == 2:
        return 'KCCFB'
    elif fill == 0:
        return 'KCCFW'
    else:
        imageL = image.crop((0, 0, 1, imageSize[1]))
        imageR = image.crop((imageSize[0]-1, 0, imageSize[0], imageSize[1]))
        fill += getImageHistogram(imageL)
        fill += getImageHistogram(imageR)
        if fill >= 2:
            return 'KCCFB'
        else:
            return 'KCCFW'


def sanitizePanelSize(panel, options):
    newPanels = []
    if panel[2] > 8 * options.height:
        diff = (panel[2] / 8)
        newPanels.append([panel[0], panel[1] - diff*7, diff])
        newPanels.append([panel[1] - diff*7, panel[1] - diff*6, diff])
        newPanels.append([panel[1] - diff*6, panel[1] - diff*5, diff])
        newPanels.append([panel[1] - diff*5, panel[1] - diff*4, diff])
        newPanels.append([panel[1] - diff*4, panel[1] - diff*3, diff])
        newPanels.append([panel[1] - diff*3, panel[1] - diff*2, diff])
        newPanels.append([panel[1] - diff*2, panel[1] - diff, diff])
        newPanels.append([panel[1] - diff, panel[1], diff])
    elif panel[2] > 4 * options.height:
        diff = (panel[2] / 4)
        newPanels.append([panel[0], panel[1] - diff*3, diff])
        newPanels.append([panel[1] - diff*3, panel[1] - diff*2, diff])
        newPanels.append([panel[1] - diff*2, panel[1] - diff, diff])
        newPanels.append([panel[1] - diff, panel[1], diff])
    elif panel[2] > 2 * options.height:
        newPanels.append([panel[0], panel[1] - (panel[2] / 2), (panel[2] / 2)])
        newPanels.append([panel[1] - (panel[2] / 2), panel[1], (panel[2] / 2)])
    else:
        newPanels = [panel]
    return newPanels


def splitImage_init(queue, options):
    splitImage.queue = queue
    splitImage.options = options


# noinspection PyUnresolvedReferences
def splitImage(work):
    path = work[0]
    name = work[1]
    options = splitImage.options
    # Harcoded options
    threshold = 1.0
    delta = 15
    print ".",
    splitImage.queue.put(".")
    fileExpanded = os.path.splitext(name)
    filePath = os.path.join(path, name)
    # Detect corrupted files
    try:
        image = Image.open(filePath)
    except IOError:
        raise RuntimeError('Cannot read image file %s' % filePath)
    try:
        image = Image.open(filePath)
        image.verify()
    except:
        raise RuntimeError('Image file %s is corrupted' % filePath)
    try:
        image = Image.open(filePath)
        image.load()
    except:
        raise RuntimeError('Image file %s is corrupted' % filePath)
    image = Image.open(filePath)
    image = image.convert('RGB')
    widthImg, heightImg = image.size
    if heightImg > options.height:
        if options.debug:
            from PIL import ImageDraw
            debugImage = Image.open(filePath)
            draw = ImageDraw.Draw(debugImage)

        # Find panels
        y1 = 0
        y2 = 15
        panels = []
        while y2 < heightImg:
            while ImageStat.Stat(image.crop([0, y1, widthImg, y2])).var[0] < threshold and y2 < heightImg:
                y2 += delta
            y2 -= delta
            y1Temp = y2
            y1 = y2 + delta
            y2 = y1 + delta
            while ImageStat.Stat(image.crop([0, y1, widthImg, y2])).var[0] >= threshold and y2 < heightImg:
                y1 += delta
                y2 += delta
            if y1 + delta >= heightImg:
                y1 = heightImg - 1
            y2Temp = y1
            if options.debug:
                draw.line([(0, y1Temp), (widthImg, y1Temp)], fill=(0, 255, 0))
                draw.line([(0, y2Temp), (widthImg, y2Temp)], fill=(255, 0, 0))
            panelHeight = y2Temp - y1Temp
            if panelHeight > delta:
                # Panels that can't be cut nicely will be forcefully splitted
                panelsCleaned = sanitizePanelSize([y1Temp, y2Temp, panelHeight], options)
                for panel in panelsCleaned:
                    panels.append(panel)
        if options.debug:
            # noinspection PyUnboundLocalVariable
            debugImage.save(os.path.join(path, fileExpanded[0] + '-debug.png'), 'PNG')

        # Create virtual pages
        pages = []
        currentPage = []
        pageLeft = options.height
        panelNumber = 0
        for panel in panels:
            if pageLeft - panel[2] > 0:
                pageLeft -= panel[2]
                currentPage.append(panelNumber)
                panelNumber += 1
            else:
                if len(currentPage) > 0:
                    pages.append(currentPage)
                pageLeft = options.height - panel[2]
                currentPage = [panelNumber]
                panelNumber += 1
        if len(currentPage) > 0:
            pages.append(currentPage)

        # Create pages
        pageNumber = 1
        for page in pages:
            pageHeight = 0
            targetHeight = 0
            for panel in page:
                pageHeight += panels[panel][2]
            if pageHeight > delta:
                newPage = Image.new('RGB', (widthImg, pageHeight))
                for panel in page:
                    panelImg = image.crop([0, panels[panel][0], widthImg, panels[panel][1]])
                    newPage.paste(panelImg, (0, targetHeight))
                    targetHeight += panels[panel][2]
                newPage.save(os.path.join(path, fileExpanded[0] + '-' +
                                          str(pageNumber) + '-' + getImageFill(newPage) + '.png'), 'PNG')
                pageNumber += 1
        os.remove(filePath)


def Copyright():
    print ('comic2panel v%(__version__)s. '
           'Written 2013 by Ciro Mattia Gonano and Pawel Jastrzebski.' % globals())


# noinspection PyBroadException
def main(argv=None, qtGUI=None):
    global options
    parser = OptionParser(usage="Usage: %prog [options] comic_folder", add_help_option=False)
    mainOptions = OptionGroup(parser, "MANDATORY")
    otherOptions = OptionGroup(parser, "OTHER")
    mainOptions.add_option("-y", "--height", type="int", dest="height", default=0,
                           help="Height of the target device screen")
    mainOptions.add_option("-i", "--in-place", action="store_true", dest="inPlace", default=False,
                           help="Overwrite source directory")
    otherOptions.add_option("-d", "--debug", action="store_true", dest="debug", default=False,
                            help="Create debug file for every splitted image")
    otherOptions.add_option("-h", "--help", action="help",
                            help="Show this help message and exit")
    parser.add_option_group(mainOptions)
    parser.add_option_group(otherOptions)
    options, args = parser.parse_args(argv)
    if qtGUI:
        GUI = qtGUI
    else:
        GUI = None
    if len(args) != 1:
        parser.print_help()
        return
    if options.height > 0:
        options.sourceDir = args[0]
        options.targetDir = args[0] + "-Splitted"
        print "\nSplitting images..."
        if os.path.isdir(options.sourceDir):
            rmtree(options.targetDir, True)
            copytree(options.sourceDir, options.targetDir)
            work = []
            pagenumber = 0
            queue = Queue()
            pool = Pool(None, splitImage_init, [queue, options])
            for root, dirs, files in os.walk(options.targetDir, False):
                for name in files:
                    if getImageFileName(name) is not None:
                        pagenumber += 1
                        work.append([root, name])
                    else:
                        os.remove(os.path.join(root, name))
            if GUI:
                GUI.emit(QtCore.SIGNAL("progressBarTick"), pagenumber)
            if len(work) > 0:
                workers = pool.map_async(func=splitImage, iterable=work)
                pool.close()
                if GUI:
                    while not workers.ready():
                        # noinspection PyBroadException
                        try:
                            queue.get(True, 5)
                        except:
                            pass
                        GUI.emit(QtCore.SIGNAL("progressBarTick"))
                pool.join()
                queue.close()
                try:
                    workers.get()
                except:
                    rmtree(options.targetDir, True)
                    raise RuntimeError("One of workers crashed. Cause: " + str(sys.exc_info()[1]))
                if GUI:
                    GUI.emit(QtCore.SIGNAL("progressBarTick"), 1)
                if options.inPlace:
                    rmtree(options.sourceDir, True)
                    move(options.targetDir, options.sourceDir)
            else:
                rmtree(options.targetDir)
                raise UserWarning("Source directory is empty.")
        else:
            raise UserWarning("Provided path is not a directory.")
    else:
        raise UserWarning("Target height is not set.")


if __name__ == "__main__":
    freeze_support()
    Copyright()
    main(sys.argv[1:])
    sys.exit(0)