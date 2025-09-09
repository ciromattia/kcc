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

import os
import sys
from argparse import ArgumentParser
from shutil import rmtree, copytree, move
from multiprocessing import Pool
from PIL import Image, ImageChops, ImageOps, ImageDraw
from .shared import dot_clean, getImageFileName, walkLevel, walkSort, sanitizeTrace


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
            if targetHeight > 131072:
                return None
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
        imgOrg = Image.open(filePath)
        w, h = imgOrg.size

        device_width = opt.width
        device_height = opt.height
        overlap_ratio = 13/16

        target_width = min(w, int(device_width * 6/10))
        if target_width != w:
            imgOrg = ImageOps.contain(imgOrg, (target_width, h))
        _, target_height = imgOrg.size
        virtual_device_width = int(target_width * 10/6)
        virtual_device_height = int(device_height / device_width * virtual_device_width)

        for i in range(0, target_height, int(virtual_device_height * overlap_ratio)):
            newPage = imgOrg.crop((0, i, target_width, i + virtual_device_height))
            newPage.save(os.path.join(path, os.path.splitext(name)[0] + '-' + str(i).zfill(8) + '.png'), 'PNG')

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
                copytree(sourceDir, targetDir)
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
                    if GUI and not GUI.conversionAlive:
                        rmtree(targetDir, True)
                        raise UserWarning("Conversion interrupted.")
                    if len(splitWorkerOutput) > 0:
                        rmtree(targetDir, True)
                        raise RuntimeError("One of workers crashed. Cause: " + splitWorkerOutput[0][0],
                                           splitWorkerOutput[0][1])
                    if args.inPlace:
                        rmtree(sourceDir, True)
                        move(targetDir, sourceDir)
                else:
                    rmtree(targetDir, True)
                    raise UserWarning("Source directory is empty.")
            else:
                raise UserWarning("Provided input is not a directory.")
    else:
        raise UserWarning("Target height is not set.")
