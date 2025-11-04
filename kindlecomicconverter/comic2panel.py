# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2019 Pawel Jastrzebski <pawelj@iosphe.re>
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

import math
import os
import sys
from argparse import ArgumentParser
from shutil import rmtree
from multiprocessing import Pool
from PIL import Image, ImageChops, ImageOps, ImageDraw, ImageFilter, ImageFile
from PIL.Image import Dither
from .shared import dot_clean, getImageFileName, walkLevel, walkSort, sanitizeTrace

ImageFile.LOAD_TRUNCATED_IMAGES = True


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
        dot_clean(directory)
        for root, _, files in walkLevel(directory, 0):
            for name in files:
                if getImageFileName(name) is not None:
                    i = Image.open(os.path.join(root, name))
                    images.append([os.path.join(root, name), i.size[0], i.size[1]])
                    sizes.append(i.size[0])
        if len(images) > 0:
            targetWidth = max(set(sizes), key=sizes.count)
            for i in images:
                targetHeight += i[2]
                imagesValid.append(i[0])
            # Silently drop directories that contain too many images
            # 131072 = GIMP_MAX_IMAGE_SIZE / 4
            if targetHeight > 131072 * 3:
                raise RuntimeError(f'Image too tall at {targetHeight} pixels. {targetWidth} pixels wide. Try using separate chapter folders or file fusion.')
            result = Image.new('RGB', (targetWidth, targetHeight))
            y = 0
            for i in imagesValid:
                img = Image.open(i).convert('RGB')
                if img.size[0] < targetWidth or img.size[0] > targetWidth:
                    widthPercent = (targetWidth / float(img.size[0]))
                    heightSize = int((float(img.size[1]) * float(widthPercent)))
                    img = ImageOps.fit(img, (targetWidth, heightSize), method=Image.BICUBIC, centering=(0.5, 0.5))
                result.paste(img, (0, y))
                y += img.size[1]
                os.remove(i)
            savePath = os.path.split(imagesValid[0])
            result.save(os.path.join(savePath[0], os.path.splitext(savePath[1])[0] + '.png'), 'PNG')
    except Exception:
        return str(sys.exc_info()[1]), sanitizeTrace(sys.exc_info()[2])


def detectSolid(img):
    return not ImageChops.invert(img).getbbox() or not img.getbbox()


def splitImageTick(output):
    if output:
        splitWorkerOutput.append(output)
        splitWorkerPool.terminate()
    if GUI:
        GUI.progressBarTick.emit('tick')
        if not GUI.conversionAlive:
            splitWorkerPool.terminate()


# noinspection PyUnboundLocalVariable
def splitImage(work):
    try:
        path = work[0]
        name = work[1]
        opt = work[2]
        filePath = os.path.join(path, name)
        Image.warnings.simplefilter('error', Image.DecompressionBombWarning)
        Image.MAX_IMAGE_PIXELS = 1000000000
        imgOrg = Image.open(filePath).convert('RGB')
        # I experimented with custom vertical edge kernel [-1, 2, -1] but got poor results
        imgEdges = Image.open(filePath).convert('L').filter(ImageFilter.FIND_EDGES)
        # threshold of 8 is too high. 5 is too low.
        imgProcess = imgEdges.point(lambda p: 255 if p > 6 else 0).convert('1', dither=Dither.NONE)

        widthImg, heightImg = imgOrg.size
        if heightImg > opt.height:
            if opt.debug:
                drawImg = Image.open(filePath).convert(mode='RGBA')
                draw = ImageDraw.Draw(drawImg)

            # Find panels
            yWork = 0
            panelDetected = False
            panels = []
            # check git history for how these constant values changed
            h_pad = int(widthImg / 20)
            v_pad = int(widthImg / 80)
            if v_pad % 2:
                v_pad += 1
            while yWork < heightImg:
                tmpImg = imgProcess.crop((h_pad, yWork, widthImg - h_pad, yWork + v_pad))
                solid = detectSolid(tmpImg)
                if not solid and not panelDetected:
                    panelDetected = True
                    panelY1 = yWork
                if heightImg - yWork <= (v_pad // 2):
                    if not solid and panelDetected:
                        panelY2 = heightImg
                        panelDetected = False
                        panels.append((panelY1, panelY2, panelY2 - panelY1))
                if solid and panelDetected:
                    panelDetected = False
                    panelY2 = yWork
                    # skip short panel at start
                    if panelY1 < v_pad * 2 and panelY2 - panelY1 < v_pad * 2:
                        continue
                    panels.append((panelY1, panelY2, panelY2 - panelY1))
                yWork += v_pad // 2

            max_width = 1072
            virtual_width = min((max_width, opt.width, widthImg))
            if opt.width > max_width:
                virtual_height = int(opt.height/max_width*virtual_width)
            else:
                virtual_height = int(opt.height/opt.width*virtual_width)
            opt.height = virtual_height

            # Split too big panels
            panelsProcessed = []
            for panel in panels:
                # 1.52 too high
                if panel[2] <= opt.height * 1.5:
                    panelsProcessed.append(panel)
                elif panel[2] <= opt.height * 2:
                    diff = panel[2] - opt.height
                    panelsProcessed.append((panel[0], panel[1] - diff, opt.height))
                    panelsProcessed.append((panel[1] - opt.height, panel[1], opt.height))
                else:
                    # split super long panels with overlap
                    parts = math.ceil(panel[2] / opt.height)
                    diff = panel[2] // parts
                    panelsProcessed.append((panel[0], panel[0] + opt.height, opt.height))
                    for x in range(1, parts - 1):
                        start = panel[0] + (x * diff)
                        panelsProcessed.append((start, start + opt.height, opt.height))
                    panelsProcessed.append((panel[1] - opt.height, panel[1], opt.height))

            if opt.debug:
                for panel in panelsProcessed:
                    draw.rectangle(((0, panel[0]), (widthImg, panel[1])), (0, 255, 0, 128), (0, 0, 255, 255))
                debugImage = Image.alpha_composite(imgOrg.convert(mode='RGBA'), drawImg)
                # debugImage.show()
                debugImage.save(os.path.join(path, os.path.splitext(name)[0] + '-debug.png'), 'PNG')

            # Create virtual pages
            pages = []
            currentPage = []
            # TODO: 1.25 way too high, 1.1 too high, 1.05 slightly too high(?), optimized for 2 page landscape reading
            # opt.height = max_height = virtual_height * 1.00
            pageLeft = opt.height
            panelNumber = 0
            for panel in panelsProcessed:
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
                    pageHeight += panelsProcessed[panel][2]
                if pageHeight > 15:
                    newPage = Image.new('RGB', (widthImg, pageHeight))
                    for panel in page:
                        panelImg = imgOrg.crop((0, panelsProcessed[panel][0], widthImg, panelsProcessed[panel][1]))
                        newPage.paste(panelImg, (0, targetHeight))
                        targetHeight += panelsProcessed[panel][2]
                    newPage.save(os.path.join(path, os.path.splitext(name)[0] + '-' + str(pageNumber).zfill(4) + '.png'), 'PNG')
                    pageNumber += 1
            os.remove(filePath)
    except Exception:
        return str(sys.exc_info()[1]), sanitizeTrace(sys.exc_info()[2])


def main(argv=None, qtgui=None):
    global args, GUI, splitWorkerPool, splitWorkerOutput, mergeWorkerPool, mergeWorkerOutput
    parser = ArgumentParser(prog="kcc-c2p", usage="kcc-c2p [options] [input]", add_help=False)

    mandatory_options = parser.add_argument_group("MANDATORY")
    main_options = parser.add_argument_group("MAIN")
    other_options = parser.add_argument_group("OTHER")
    mandatory_options.add_argument("input", action="extend", nargs="*", default=None,
                              help="Full path to comic folder(s) to be processed. Separate multiple inputs"
                                   " with spaces.")
    main_options.add_argument("-y", "--height", type=int, dest="height", default=0,
                              help="Height of the target device screen")
    main_options.add_argument("-x", "--width", type=int, dest="width", default=0,
                              help="Width of the target device screen")
    main_options.add_argument("-i", "--in-place", action="store_true", dest="inPlace", default=False,
                              help="Overwrite source directory")
    main_options.add_argument("-m", "--merge", action="store_true", dest="merge", default=False,
                              help="Combine every directory into a single image before splitting")
    other_options.add_argument("-d", "--debug", action="store_true", dest="debug", default=False,
                               help="Create debug file for every split image")
    other_options.add_argument("-h", "--help", action="help",
                               help="Show this help message and exit")
    args = parser.parse_args(argv)
    if qtgui:
        GUI = qtgui
    else:
        GUI = None
    if not argv or args.input == []:
        parser.print_help()
        return 1
    if args.height > 0:
        for sourceDir in args.input:
            targetDir = sourceDir + "-Splitted"
            if os.path.isdir(sourceDir):
                rmtree(targetDir, True)
                os.renames(sourceDir, targetDir)
                work = []
                pagenumber = 1
                splitWorkerOutput = []
                splitWorkerPool = Pool(maxtasksperchild=10)
                if args.merge:
                    print("Merging images...")
                    directoryNumer = 1
                    mergeWork = []
                    mergeWorkerOutput = []
                    mergeWorkerPool = Pool(maxtasksperchild=10)
                    mergeWork.append([targetDir])
                    for root, dirs, files in os.walk(targetDir, False):
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
                        rmtree(targetDir, True)
                        raise UserWarning("Conversion interrupted.")
                    if len(mergeWorkerOutput) > 0:
                        rmtree(targetDir, True)
                        raise RuntimeError("One of workers crashed. Cause: " + mergeWorkerOutput[0][0],
                                           mergeWorkerOutput[0][1])
                print("Splitting images...")
                dot_clean(targetDir)
                for root, _, files in os.walk(targetDir, False):
                    for name in files:
                        if getImageFileName(name) is not None:
                            pagenumber += 1
                            work.append([root, name, args])
                        else:
                            os.remove(os.path.join(root, name))
                if GUI:
                    GUI.progressBarTick.emit('Splitting images')
                    GUI.progressBarTick.emit(str(pagenumber))
                    GUI.progressBarTick.emit('tick')
                if len(work) > 0:
                    for i in work:
                        splitWorkerPool.apply_async(func=splitImage, args=(i, ), callback=splitImageTick)
                    splitWorkerPool.close()
                    splitWorkerPool.join()
                    dot_clean(targetDir)
                    if GUI and not GUI.conversionAlive:
                        rmtree(targetDir, True)
                        raise UserWarning("Conversion interrupted.")
                    if len(splitWorkerOutput) > 0:
                        rmtree(targetDir, True)
                        raise RuntimeError("One of workers crashed. Cause: " + splitWorkerOutput[0][0],
                                           splitWorkerOutput[0][1])
                    if args.inPlace:
                        os.renames(targetDir, sourceDir)
                else:
                    rmtree(targetDir, True)
                    raise UserWarning("C2P: Source directory is empty.")
            else:
                raise UserWarning("Provided input is not a directory.")
    else:
        raise UserWarning("Target height is not set.")
