# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2016 Pawel Jastrzebski <pawelj@iosphe.re>
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

import os
import sys
from shutil import rmtree, copytree, move
from optparse import OptionParser, OptionGroup
from multiprocessing import Pool
from PIL import Image, ImageStat, ImageOps
from .shared import getImageFileName, walkLevel, walkSort, saferRemove, sanitizeTrace
try:
    from PyQt5 import QtCore
except ImportError:
    QtCore = None
try:
    from scandir import walk
except ImportError:
    walk = os.walk


def mergeDirectoryTick(output):
    if output:
        mergeWorkerOutput.append(output)
        mergeWorkerPool.terminate()
    if GUI:
        GUI.progressBarTick.emit('tick')
        if not GUI.conversionAlive:
            mergeWorkerPool.terminate()


def mergeDirectory(work):
    try:
        directory = work[0]
        images = []
        imagesValid = []
        sizes = []
        targetHeight = 0
        for root, dirs, files in walkLevel(directory, 0):
            for name in files:
                if getImageFileName(name) is not None:
                    i = Image.open(os.path.join(root, name))
                    images.append([os.path.join(root, name), i.size[0], i.size[1]])
                    sizes.append(i.size[0])
        if len(images) > 0:
            targetWidth = max(set(sizes), key=sizes.count)
            for i in images:
                if i[1] <= targetWidth:
                    targetHeight += i[2]
                    imagesValid.append(i[0])
            # Silently drop directories that contain too many images
            # 131072 = GIMP_MAX_IMAGE_SIZE / 4
            if targetHeight > 131072:
                return None
            result = Image.new('RGB', (targetWidth, targetHeight))
            y = 0
            for i in imagesValid:
                img = Image.open(i)
                img = img.convert('RGB')
                if img.size[0] < targetWidth:
                    img = ImageOps.fit(img, (targetWidth, img.size[1]), method=Image.BICUBIC, centering=(0.5, 0.5))
                result.paste(img, (0, y))
                y += img.size[1]
                saferRemove(i)
            savePath = os.path.split(imagesValid[0])
            result.save(os.path.join(savePath[0], os.path.splitext(savePath[1])[0] + '.png'), 'PNG')
    except Exception:
        return str(sys.exc_info()[1]), sanitizeTrace(sys.exc_info()[2])


def sanitizePanelSize(panel, opt):
    newPanels = []
    if panel[2] > 6 * opt.height:
        diff = int(panel[2] / 8)
        newPanels.append([panel[0], panel[1] - diff * 7, diff])
        newPanels.append([panel[1] - diff * 7, panel[1] - diff * 6, diff])
        newPanels.append([panel[1] - diff * 6, panel[1] - diff * 5, diff])
        newPanels.append([panel[1] - diff * 5, panel[1] - diff * 4, diff])
        newPanels.append([panel[1] - diff * 4, panel[1] - diff * 3, diff])
        newPanels.append([panel[1] - diff * 3, panel[1] - diff * 2, diff])
        newPanels.append([panel[1] - diff * 2, panel[1] - diff, diff])
        newPanels.append([panel[1] - diff, panel[1], diff])
    elif panel[2] > 3 * opt.height:
        diff = int(panel[2] / 4)
        newPanels.append([panel[0], panel[1] - diff * 3, diff])
        newPanels.append([panel[1] - diff * 3, panel[1] - diff * 2, diff])
        newPanels.append([panel[1] - diff * 2, panel[1] - diff, diff])
        newPanels.append([panel[1] - diff, panel[1], diff])
    elif panel[2] > 1.5 * opt.height:
        newPanels.append([panel[0], panel[1] - int(panel[2] / 2), int(panel[2] / 2)])
        newPanels.append([panel[1] - int(panel[2] / 2), panel[1], int(panel[2] / 2)])
    else:
        newPanels = [panel]
    return newPanels


def splitImageTick(output):
    if output:
        splitWorkerOutput.append(output)
        splitWorkerPool.terminate()
    if GUI:
        GUI.progressBarTick.emit('tick')
        if not GUI.conversionAlive:
            splitWorkerPool.terminate()


def splitImage(work):
    try:
        path = work[0]
        name = work[1]
        opt = work[2]
        # Hardcoded options
        threshold = 1.0
        delta = 15
        fileExpanded = os.path.splitext(name)
        filePath = os.path.join(path, name)
        image = Image.open(filePath)
        image = image.convert('RGB')
        widthImg, heightImg = image.size
        if heightImg > opt.height:
            if opt.debug:
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
                if opt.debug:
                    draw.line([(0, y1Temp), (widthImg, y1Temp)], fill=(0, 255, 0))
                    draw.line([(0, y2Temp), (widthImg, y2Temp)], fill=(255, 0, 0))
                panelHeight = y2Temp - y1Temp
                if panelHeight > delta:
                    # Panels that can't be cut nicely will be forcefully splitted
                    panelsCleaned = sanitizePanelSize([y1Temp, y2Temp, panelHeight], opt)
                    for panel in panelsCleaned:
                        panels.append(panel)
            if opt.debug:
                # noinspection PyUnboundLocalVariable
                debugImage.save(os.path.join(path, fileExpanded[0] + '-debug.png'), 'PNG')

            # Create virtual pages
            pages = []
            currentPage = []
            pageLeft = opt.height
            panelNumber = 0
            for panel in panels:
                if pageLeft - panel[2] > 0:
                    pageLeft -= panel[2]
                    currentPage.append(panelNumber)
                    panelNumber += 1
                else:
                    if len(currentPage) > 0:
                        pages.append(currentPage)
                    pageLeft = opt.height - panel[2]
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
                    newPage.save(os.path.join(path, fileExpanded[0] + '-' + str(pageNumber) + '.png'), 'PNG')
                    pageNumber += 1
            saferRemove(filePath)
    except Exception:
        return str(sys.exc_info()[1]), sanitizeTrace(sys.exc_info()[2])


def main(argv=None, qtGUI=None):
    global options, GUI, splitWorkerPool, splitWorkerOutput, mergeWorkerPool, mergeWorkerOutput
    parser = OptionParser(usage="Usage: kcc-c2p [options] comic_folder", add_help_option=False)
    mainOptions = OptionGroup(parser, "MANDATORY")
    otherOptions = OptionGroup(parser, "OTHER")
    mainOptions.add_option("-y", "--height", type="int", dest="height", default=0,
                           help="Height of the target device screen")
    mainOptions.add_option("-i", "--in-place", action="store_true", dest="inPlace", default=False,
                           help="Overwrite source directory")
    mainOptions.add_option("-m", "--merge", action="store_true", dest="merge", default=False,
                           help="Combine every directory into a single image before splitting")
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
        return 1
    if options.height > 0:
        options.sourceDir = args[0]
        options.targetDir = args[0] + "-Splitted"
        if os.path.isdir(options.sourceDir):
            rmtree(options.targetDir, True)
            copytree(options.sourceDir, options.targetDir)
            work = []
            pagenumber = 1
            splitWorkerOutput = []
            splitWorkerPool = Pool()
            if options.merge:
                print("Merging images...")
                directoryNumer = 1
                mergeWork = []
                mergeWorkerOutput = []
                mergeWorkerPool = Pool()
                mergeWork.append([options.targetDir])
                for root, dirs, files in walk(options.targetDir, False):
                    dirs, files = walkSort(dirs, files)
                    for directory in dirs:
                        directoryNumer += 1
                        mergeWork.append([os.path.join(root, directory)])
                if GUI:
                    GUI.progressBarTick.emit('Combining images')
                    GUI.progressBarTick.emit(str(directoryNumer))
                for i in mergeWork:
                    mergeWorkerPool.apply_async(func=mergeDirectory, args=(i, ), callback=mergeDirectoryTick)
                mergeWorkerPool.close()
                mergeWorkerPool.join()
                if GUI and not GUI.conversionAlive:
                    rmtree(options.targetDir, True)
                    raise UserWarning("Conversion interrupted.")
                if len(mergeWorkerOutput) > 0:
                    rmtree(options.targetDir, True)
                    raise RuntimeError("One of workers crashed. Cause: " + mergeWorkerOutput[0][0], mergeWorkerOutput[0][1])
            print("Splitting images...")
            for root, dirs, files in walk(options.targetDir, False):
                for name in files:
                    if getImageFileName(name) is not None:
                        pagenumber += 1
                        work.append([root, name, options])
                    else:
                        saferRemove(os.path.join(root, name))
            if GUI:
                GUI.progressBarTick.emit('Splitting images')
                GUI.progressBarTick.emit(str(pagenumber))
                GUI.progressBarTick.emit('tick')
            if len(work) > 0:
                for i in work:
                    splitWorkerPool.apply_async(func=splitImage, args=(i, ), callback=splitImageTick)
                splitWorkerPool.close()
                splitWorkerPool.join()
                if GUI and not GUI.conversionAlive:
                    rmtree(options.targetDir, True)
                    raise UserWarning("Conversion interrupted.")
                if len(splitWorkerOutput) > 0:
                    rmtree(options.targetDir, True)
                    raise RuntimeError("One of workers crashed. Cause: " + splitWorkerOutput[0][0], splitWorkerOutput[0][1])
                if options.inPlace:
                    rmtree(options.sourceDir)
                    move(options.targetDir, options.sourceDir)
            else:
                rmtree(options.targetDir, True)
                raise UserWarning("Source directory is empty.")
        else:
            raise UserWarning("Provided path is not a directory.")
    else:
        raise UserWarning("Target height is not set.")
