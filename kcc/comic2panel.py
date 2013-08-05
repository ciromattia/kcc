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
__version__ = '3.1'
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import sys
import os
from shutil import rmtree, copytree
from optparse import OptionParser
from multiprocessing import Pool, freeze_support
from PIL import Image, ImageStat


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


def sanitizePanelSize(panel, options):
    newPanels = []
    if panel[2] > 1.5 * options.height:
        if (panel[2] / 2) > 1.5 * options.height:
            diff = (panel[2] / 4)
            newPanels.append([panel[0], panel[1] - diff*3, diff])
            newPanels.append([panel[1] - diff*3, panel[1] - diff*2, diff])
            newPanels.append([panel[1] - diff*2, panel[1] - diff, diff])
            newPanels.append([panel[1] - diff, panel[1], diff])
        else:
            newPanels.append([panel[0], panel[1] - (panel[2] / 2), (panel[2] / 2)])
            newPanels.append([panel[1] - (panel[2] / 2), panel[1], (panel[2] / 2)])
    else:
        newPanels = [panel]
    return newPanels


def splitImage_init(options):
    splitImage.options = options


# noinspection PyUnresolvedReferences
def splitImage(work):
    path = work[0]
    name = work[1]
    options = splitImage.options
    # Harcoded options
    threshold = 10.0
    delta = 10

    fileExpanded = os.path.splitext(name)
    image = Image.open(os.path.join(path, name))
    image = image.convert('RGB')
    widthImg, heightImg = image.size
    if heightImg > options.height:
        if options.debug:
            from PIL import ImageDraw
            debugImage = Image.open(os.path.join(path, name))
            draw = ImageDraw.Draw(debugImage)

        # Find panels
        y1 = 0
        y2 = 10
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
            y2Temp = y1
            if options.debug:
                draw.line([(0, y1Temp), (widthImg, y1Temp)], fill=(0, 255, 0))
                draw.line([(0, y2Temp), (widthImg, y2Temp)], fill=(255, 0, 0))
            panelHeight = y2Temp - y1Temp
            if y2Temp < heightImg:
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
            newPage = Image.new('RGB', (widthImg, pageHeight))
            for panel in page:
                panelImg = image.crop([0, panels[panel][0], widthImg, panels[panel][1]])
                newPage.paste(panelImg, (0, targetHeight))
                targetHeight += panels[panel][2]
            newPage.save(os.path.join(path, fileExpanded[0] + '-' + str(pageNumber) + '.png'), 'PNG')
            pageNumber += 1
        print ".",
        os.remove(os.path.join(path, name))


def Copyright():
    print ('comic2panel v%(__version__)s. '
           'Written 2013 by Ciro Mattia Gonano and Pawel Jastrzebski.' % globals())


# noinspection PyBroadException
def main(argv=None):
    global options
    usage = "Usage: %prog [options] comic_folder"
    parser = OptionParser(usage=usage, version=__version__)
    parser.add_option("-y", "--height", type="int", dest="height", default=0,
                      help="Target device screen height [Default=0]")
    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False,
                      help="Create debug file for every splitted image [Default=False]")
    options, args = parser.parse_args(argv)
    if len(args) != 1:
        parser.print_help()
        return
    if options.height > 0:
        options.sourceDir = args[0]
        options.targetDir = args[0] + "-Splitted"
        print "Spliting images..."
        if os.path.isdir(options.sourceDir):
            rmtree(options.targetDir, True)
            copytree(options.sourceDir, options.targetDir)
            work = []
            pool = Pool(None, splitImage_init, [options])
            for root, dirs, files in os.walk(options.targetDir, False):
                for name in files:
                    if getImageFileName(name) is not None:
                        work.append([root, name])
                    else:
                        os.remove(os.path.join(root, name))
            if len(work) > 0:
                workers = pool.map_async(func=splitImage, iterable=work)
                pool.close()
                pool.join()
                try:
                    workers.get()
                except:
                    rmtree(options.targetDir)
                    print "ERROR: One of workers crashed. Cause: " + str(sys.exc_info()[1])
                    sys.exit(1)
            else:
                rmtree(options.targetDir)
                print "ERROR: Source directory is empty!!"
                sys.exit(1)
        else:
            print "ERROR: Provided path is not a directory!"
            sys.exit(1)
    else:
        print "ERROR: Target height was not provided!"
        sys.exit(1)

if __name__ == "__main__":
    freeze_support()
    Copyright()
    main(sys.argv[1:])
    sys.exit(0)