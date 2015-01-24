# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013-2015 Pawel Jastrzebski <pawelj@iosphe.re>
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
from copy import copy
from glob import glob
from json import loads
from urllib.request import Request, urlopen
from re import split, sub, compile
from stat import S_IWRITE, S_IREAD, S_IEXEC
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from tempfile import mkdtemp
from shutil import move, copytree, rmtree
from optparse import OptionParser, OptionGroup
from multiprocessing import Pool
from xml.dom.minidom import parse
from uuid import uuid4
from slugify import slugify as slugifyExt
from PIL import Image
from subprocess import STDOUT, PIPE
from psutil import Popen, virtual_memory
from scandir import walk
try:
    from PyQt5 import QtCore
except ImportError:
    QtCore = None
from .shared import md5Checksum, getImageFileName, walkLevel, saferReplace
from . import comic2panel
from . import image
from . import cbxarchive
from . import pdfjpgextract
from . import dualmetafix
from . import __version__


def main(argv=None):
    global options
    parser = makeParser()
    optionstemplate, args = parser.parse_args(argv)
    if len(args) == 0:
        parser.print_help()
        return
    sources = set([source for arg in args for source in glob(arg)])
    outputPath = []
    if len(sources) == 0:
        print('No matching files found.')
        return
    for source in sources:
        options = copy(optionstemplate)
        checkOptions()
        if len(sources) > 1:
            print('\nWorking on ' + source)
        outputPath = makeBook(source)
    return outputPath


def buildHTML(path, imgfile, imgfilepath):
    imgfilepath = md5Checksum(imgfilepath)
    filename = getImageFileName(imgfile)
    if options.imgproc:
        if "Rotated" in options.imgIndex[imgfilepath]:
            rotatedPage = True
        else:
            rotatedPage = False
        if "NoPanelView" in options.imgIndex[imgfilepath]:
            noPV = True
        else:
            noPV = False
        if "NoHorizontalPanelView" in options.imgIndex[imgfilepath]:
            noHorizontalPV = True
        else:
            noHorizontalPV = False
        if "NoVerticalPanelView" in options.imgIndex[imgfilepath]:
            noVerticalPV = True
        else:
            noVerticalPV = False
    else:
        rotatedPage = False
        noPV = False
        noHorizontalPV = False
        noVerticalPV = False
    htmlpath = ''
    postfix = ''
    backref = 1
    head = path
    while True:
        head, tail = os.path.split(head)
        if tail == 'Images':
            htmlpath = os.path.join(head, 'Text', postfix)
            break
        postfix = tail + "/" + postfix
        backref += 1
    if not os.path.exists(htmlpath):
        os.makedirs(htmlpath)
    htmlfile = os.path.join(htmlpath, filename[0] + '.html')
    f = open(htmlfile, "w", encoding='UTF-8')
    f.writelines(["<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\" ",
                  "\"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">\n",
                  "<html xmlns=\"http://www.w3.org/1999/xhtml\">\n",
                  "<head>\n",
                  "<title>", filename[0], "</title>\n",
                  "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>\n",
                  "<link href=\"", "../" * (backref - 1),
                  "style.css\" type=\"text/css\" rel=\"stylesheet\"/>\n",
                  "</head>\n",
                  "<body>\n",
                  "<div class=\"fs\">\n",
                  "<div><img src=\"", "../" * backref, "Images/", postfix, imgfile, "\" alt=\"",
                  imgfile, "\" class=\"singlePage\"/></div>\n"
                  ])
    if options.panelview and not noPV:
        if not noHorizontalPV and not noVerticalPV:
            if rotatedPage:
                if options.righttoleft:
                    order = [1, 3, 2, 4]
                else:
                    order = [2, 4, 1, 3]
            else:
                if options.righttoleft:
                    order = [2, 1, 4, 3]
                else:
                    order = [1, 2, 3, 4]
            boxes = ["BoxTL", "BoxTR", "BoxBL", "BoxBR"]
        elif noHorizontalPV and not noVerticalPV:
            if rotatedPage:
                if options.righttoleft:
                    order = [1, 2]
                else:
                    order = [2, 1]
            else:
                order = [1, 2]
            boxes = ["BoxT", "BoxB"]
        elif not noHorizontalPV and noVerticalPV:
            if rotatedPage:
                order = [1, 2]
            else:
                if options.righttoleft:
                    order = [2, 1]
                else:
                    order = [1, 2]
            boxes = ["BoxL", "BoxR"]
        else:
            order = [1]
            boxes = ["BoxC"]
        for i in range(0, len(boxes)):
            f.writelines(["<div id=\"" + boxes[i] + "\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                          "'{\"targetId\":\"" + boxes[i] + "-Panel-Parent\", \"ordinal\":" + str(order[i]),
                          "}'></a></div>\n"])
        if options.quality == 2:
            imgfilepv = str.split(imgfile, ".")
            imgfilepv[0] += "-hq"
            imgfilepv = ".".join(imgfilepv)
        else:
            imgfilepv = imgfile
        xl, yu, xr, yd = detectMargins(imgfilepath)
        boxStyles = {"BoxTL": "left:" + xl + ";top:" + yu + ";",
                     "BoxTR": "right:" + xr + ";top:" + yu + ";",
                     "BoxBL": "left:" + xl + ";bottom:" + yd + ";",
                     "BoxBR": "right:" + xr + ";bottom:" + yd + ";",
                     "BoxT": "left:-25%;top:" + yu + ";",
                     "BoxB": "left:-25%;bottom:" + yd + ";",
                     "BoxL": "left:" + xl + ";top:-25%;",
                     "BoxR": "right:" + xr + ";top:-25%;",
                     "BoxC": "left:-25%;top:-25%;"
                     }
        for box in boxes:
            f.writelines(["<div id=\"" + box + "-Panel-Parent\" class=\"target-mag-parent\"><div id=\"",
                          "Generic-Panel\" class=\"target-mag\"><img style=\"" + boxStyles[box] + "\" src=\"",
                          "../" * backref, "Images/", postfix, imgfilepv, "\" alt=\"" + imgfilepv,
                          "\"/></div></div>\n",
                          ])
    f.writelines(["</div>\n</body>\n</html>"])
    f.close()
    return path, imgfile


def buildNCX(dstdir, title, chapters, chapterNames):
    options.uuid = str(uuid4())
    ncxfile = os.path.join(dstdir, 'OEBPS', 'toc.ncx')
    f = open(ncxfile, "w", encoding='UTF-8')
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
                  "<!DOCTYPE ncx PUBLIC \"-//NISO//DTD ncx 2005-1//EN\" ",
                  "\"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd\">\n",
                  "<ncx version=\"2005-1\" xml:lang=\"en-US\" xmlns=\"http://www.daisy.org/z3986/2005/ncx/\">\n",
                  "<head>\n",
                  "<meta name=\"dtb:uid\" content=\"", options.uuid, "\"/>\n",
                  "<meta name=\"dtb:depth\" content=\"1\"/>\n",
                  "<meta name=\"dtb:totalPageCount\" content=\"0\"/>\n",
                  "<meta name=\"dtb:maxPageNumber\" content=\"0\"/>\n",
                  "<meta name=\"generated\" content=\"true\"/>\n",
                  "</head>\n",
                  "<docTitle><text>", title, "</text></docTitle>\n",
                  "<navMap>"
                  ])
    for chapter in chapters:
        folder = chapter[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\')
        if os.path.basename(folder) != "Text":
            title = chapterNames[os.path.basename(folder)]
        filename = getImageFileName(os.path.join(folder, chapter[1]))
        f.write("<navPoint id=\"" + folder.replace('/', '_').replace('\\', '_') + "\"><navLabel><text>"
                + title + "</text></navLabel><content src=\"" + filename[0].replace("\\", "/")
                + ".html\"/></navPoint>\n")
    f.write("</navMap>\n</ncx>")
    f.close()


def buildOPF(dstdir, title, filelist, cover=None):
    opffile = os.path.join(dstdir, 'OEBPS', 'content.opf')
    profilelabel, deviceres, palette, gamma, panelviewsize = options.profileData
    if options.righttoleft:
        writingmode = "horizontal-rl"
    else:
        writingmode = "horizontal-lr"
    f = open(opffile, "w", encoding='UTF-8')
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
                  "<package version=\"2.0\" unique-identifier=\"BookID\" ",
                  "xmlns=\"http://www.idpf.org/2007/opf\">\n",
                  "<metadata xmlns:opf=\"http://www.idpf.org/2007/opf\" ",
                  "xmlns:dc=\"http://purl.org/dc/elements/1.1/\">\n",
                  "<dc:title>", title, "</dc:title>\n",
                  "<dc:language>en-US</dc:language>\n",
                  "<dc:identifier id=\"BookID\" opf:scheme=\"UUID\">", options.uuid, "</dc:identifier>\n"])
    for author in options.authors:
        f.writelines(["<dc:creator>", author, "</dc:creator>\n"])
    f.writelines(["<meta name=\"generator\" content=\"KindleComicConverter-" + __version__ + "\"/>\n",
                  "<meta name=\"RegionMagnification\" content=\"true\"/>\n",
                  "<meta name=\"region-mag\" content=\"true\"/>\n",
                  "<meta name=\"cover\" content=\"cover\"/>\n",
                  "<meta name=\"book-type\" content=\"comic\"/>\n",
                  "<meta name=\"rendition:layout\" content=\"pre-paginated\"/>\n",
                  "<meta name=\"zero-gutter\" content=\"true\"/>\n",
                  "<meta name=\"zero-margin\" content=\"true\"/>\n",
                  "<meta name=\"fixed-layout\" content=\"true\"/>\n"
                  "<meta name=\"rendition:orientation\" content=\"portrait\"/>\n",
                  "<meta name=\"orientation-lock\" content=\"portrait\"/>\n",
                  "<meta name=\"original-resolution\" content=\"",
                  str(deviceres[0]) + "x" + str(deviceres[1]), "\"/>\n",
                  "<meta name=\"primary-writing-mode\" content=\"", writingmode, "\"/>\n",
                  "<meta name=\"ke-border-color\" content=\"#ffffff\"/>\n",
                  "<meta name=\"ke-border-width\" content=\"0\"/>\n",
                  "</metadata>\n<manifest>\n<item id=\"ncx\" href=\"toc.ncx\" ",
                  "media-type=\"application/x-dtbncx+xml\"/>\n"])
    if cover is not None:
        filename = getImageFileName(cover.replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\'))
        if '.png' == filename[1]:
            mt = 'image/png'
        else:
            mt = 'image/jpeg'
        f.write("<item id=\"cover\" href=\"Images/cover" + filename[1] + "\" media-type=\"" + mt + "\"/>\n")
    reflist = []
    for path in filelist:
        folder = path[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\').replace("\\", "/")
        filename = getImageFileName(path[1])
        uniqueid = os.path.join(folder, filename[0]).replace('/', '_').replace('\\', '_')
        reflist.append(uniqueid)
        f.write("<item id=\"page_" + str(uniqueid) + "\" href=\""
                + folder.replace('Images', 'Text') + "/" + filename[0]
                + ".html\" media-type=\"application/xhtml+xml\"/>\n")
        if '.png' == filename[1]:
            mt = 'image/png'
        else:
            mt = 'image/jpeg'
        f.write("<item id=\"img_" + str(uniqueid) + "\" href=\"" + folder + "/" + path[1] + "\" media-type=\""
                + mt + "\"/>\n")
    f.write("<item id=\"css\" href=\"Text/style.css\" media-type=\"text/css\"/>\n")
    f.write("</manifest>\n<spine toc=\"ncx\">\n")
    for entry in reflist:
        f.write("<itemref idref=\"page_" + entry + "\"/>\n")
    f.write("</spine>\n<guide>\n</guide>\n</package>\n")
    f.close()
    os.mkdir(os.path.join(dstdir, 'META-INF'))
    f = open(os.path.join(dstdir, 'META-INF', 'container.xml'), 'w', encoding='UTF-8')
    f.writelines(["<?xml version=\"1.0\"?>\n",
                  "<container version=\"1.0\" xmlns=\"urn:oasis:names:tc:opendocument:xmlns:container\">\n",
                  "<rootfiles>\n",
                  "<rootfile full-path=\"OEBPS/content.opf\" media-type=\"application/oebps-package+xml\"/>\n",
                  "</rootfiles>\n",
                  "</container>"])
    f.close()


def buildEPUB(path, chapterNames, tomeNumber):
    filelist = []
    chapterlist = []
    cover = None
    _, deviceres, _, _, panelviewsize = options.profileData
    os.mkdir(os.path.join(path, 'OEBPS', 'Text'))
    f = open(os.path.join(path, 'OEBPS', 'Text', 'style.css'), 'w', encoding='UTF-8')
    # DON'T COMPRESS CSS. KINDLE WILL FAIL TO PARSE IT.
    # Generic Panel View support + Margins fix for Non-Kindle devices.
    f.writelines(["@page {\n",
                  "margin-bottom: 0;\n",
                  "margin-top: 0\n",
                  "}\n",
                  "body {\n",
                  "display: block;\n",
                  "margin-bottom: 0;\n",
                  "margin-left: 0;\n",
                  "margin-right: 0;\n",
                  "margin-top: 0;\n",
                  "padding-bottom: 0;\n",
                  "padding-left: 0;\n",
                  "padding-right: 0;\n",
                  "padding-top: 0;\n",
                  "text-align: left\n",
                  "}\n",
                  "div.fs {\n",
                  "height: ", str(deviceres[1]), "px;\n",
                  "width: ", str(deviceres[0]), "px;\n",
                  "position: relative;\n",
                  "display: block;\n",
                  "text-align: center\n",
                  "}\n",
                  "div.fs a {\n",
                  "display: block;\n",
                  "width : 100%;\n",
                  "height: 100%;\n",
                  "}\n",
                  "div.fs div {\n",
                  "position: absolute;\n",
                  "}\n",
                  "img.singlePage {\n",
                  "position: absolute;\n",
                  "height: ", str(deviceres[1]), "px;\n",
                  "width: ", str(deviceres[0]), "px;\n",
                  "}\n",
                  "div.target-mag-parent {\n",
                  "width:100%;\n",
                  "height:100%;\n",
                  "display:none;\n",
                  "}\n",
                  "div.target-mag {\n",
                  "position: absolute;\n",
                  "display: block;\n",
                  "overflow: hidden;\n",
                  "}\n",
                  "div.target-mag img {\n",
                  "position: absolute;\n",
                  "height: ", str(panelviewsize[1]), "px;\n",
                  "width: ", str(panelviewsize[0]), "px;\n",
                  "}\n",
                  "#Generic-Panel {\n",
                  "top: 0;\n",
                  "height: 100%;\n",
                  "width: 100%;\n",
                  "}\n",
                  "#BoxC {\n",
                  "top: 0;\n",
                  "height: 100%;\n",
                  "width: 100%;\n",
                  "}\n",
                  "#BoxT {\n",
                  "top: 0;\n",
                  "height: 50%;\n",
                  "width: 100%;\n",
                  "}\n",
                  "#BoxB {\n",
                  "bottom: 0;\n",
                  "height: 50%;\n",
                  "width: 100%;\n",
                  "}\n",
                  "#BoxL {\n",
                  "left: 0;\n",
                  "height: 100%;\n",
                  "width: 50%;\n",
                  "}\n",
                  "#BoxR {\n",
                  "right: 0;\n",
                  "height: 100%;\n",
                  "width: 50%;\n",
                  "}\n",
                  "#BoxTL {\n",
                  "top: 0;\n",
                  "left: 0;\n",
                  "height: 50%;\n",
                  "width: 50%;\n",
                  "}\n",
                  "#BoxTR {\n",
                  "top: 0;\n",
                  "right: 0;\n",
                  "height: 50%;\n",
                  "width: 50%;\n",
                  "}\n",
                  "#BoxBL {\n",
                  "bottom: 0;\n",
                  "left: 0;\n",
                  "height: 50%;\n",
                  "width: 50%;\n",
                  "}\n",
                  "#BoxBR {\n",
                  "bottom: 0;\n",
                  "right: 0;\n",
                  "height: 50%;\n",
                  "width: 50%;\n",
                  "}",
                  ])
    f.close()
    for (dirpath, dirnames, filenames) in walk(os.path.join(path, 'OEBPS', 'Images')):
        chapter = False
        for afile in filenames:
            filename = getImageFileName(afile)
            if '-kcc-hq' not in filename[0]:
                filelist.append(buildHTML(dirpath, afile, os.path.join(dirpath, afile)))
                if not chapter:
                    chapterlist.append((dirpath.replace('Images', 'Text'), filelist[-1][1]))
                    chapter = True
                if cover is None:
                    cover = os.path.join(os.path.join(path, 'OEBPS', 'Images'),
                                         'cover' + getImageFileName(filelist[-1][1])[1])
                    image.Cover(os.path.join(filelist[-1][0], filelist[-1][1]), cover, options, tomeNumber)
    buildNCX(path, options.title, chapterlist, chapterNames)
    # Ensure we're sorting files alphabetically
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in split('([0-9]+)', key)]
    filelist.sort(key=lambda name: (alphanum_key(name[0].lower()), alphanum_key(name[1].lower())))
    buildOPF(path, options.title, filelist, cover)


def imgOptimization(img, opt, hqImage=None):
    if not img.fill:
        img.getImageFill()
    if not opt.webtoon:
        img.cropWhiteSpace()
    if opt.cutpagenumbers and not opt.webtoon:
        img.cutPageNumber()
    img.optimizeImage()
    if hqImage:
        img.resizeImage(0)
        img.calculateBorder(hqImage, True)
    else:
        img.resizeImage()
        if opt.panelview:
            if opt.quality == 0:
                img.calculateBorder(img)
            elif opt.quality == 1:
                img.calculateBorder(img, True)
    if opt.forcepng and not opt.forcecolor:
        img.quantizeImage()


def imgDirectoryProcessing(path):
    global workerPool, workerOutput
    workerPool = Pool()
    workerOutput = []
    options.imgIndex = {}
    options.imgPurgeIndex = []
    work = []
    pagenumber = 0
    for (dirpath, dirnames, filenames) in walk(path):
        for afile in filenames:
            pagenumber += 1
            work.append([afile, dirpath, options])
    if GUI:
        GUI.progressBarTick.emit(str(pagenumber))
    if len(work) > 0:
        for i in work:
            workerPool.apply_async(func=imgFileProcessing, args=(i, ), callback=imgFileProcessingTick)
        workerPool.close()
        workerPool.join()
        if GUI and not GUI.conversionAlive:
            rmtree(os.path.join(path, '..', '..'), True)
            raise UserWarning("Conversion interrupted.")
        if len(workerOutput) > 0:
            rmtree(os.path.join(path, '..', '..'), True)
            raise RuntimeError("One of workers crashed. Cause: " + workerOutput[0])
        for file in options.imgPurgeIndex:
            if os.path.isfile(file):
                os.remove(file)
    else:
        rmtree(os.path.join(path, '..', '..'), True)
        raise UserWarning("Source directory is empty.")


def imgFileProcessingTick(output):
    if isinstance(output, str):
        workerOutput.append(output)
        workerPool.terminate()
    else:
        for page in output:
            if page is not None:
                if isinstance(page, str):
                    options.imgPurgeIndex.append(page)
                else:
                    options.imgIndex[page[0]] = page[1]
    if GUI:
        GUI.progressBarTick.emit('tick')
        if not GUI.conversionAlive:
            workerPool.terminate()


def imgFileProcessing(work):
    try:
        afile = work[0]
        dirpath = work[1]
        opt = work[2]
        output = []
        img = image.ComicPage(os.path.join(dirpath, afile), opt)
        if opt.quality == 2:
            wipe = False
        else:
            wipe = True
        if opt.nosplitrotate:
            splitter = None
        else:
            splitter = img.splitPage(dirpath)
        if splitter is not None:
            img0 = image.ComicPage(splitter[0], opt)
            imgOptimization(img0, opt)
            output.append(img0.saveToDir(dirpath))
            img1 = image.ComicPage(splitter[1], opt)
            imgOptimization(img1, opt)
            output.append(img1.saveToDir(dirpath))
            if wipe:
                output.append(img0.origFileName)
                output.append(img1.origFileName)
            if opt.quality == 2:
                img0b = image.ComicPage(splitter[0], opt, img0.fill)
                imgOptimization(img0b, opt, img0)
                output.append(img0b.saveToDir(dirpath))
                img1b = image.ComicPage(splitter[1], opt, img1.fill)
                imgOptimization(img1b, opt, img1)
                output.append(img1b.saveToDir(dirpath))
                output.append(img0.origFileName)
                output.append(img1.origFileName)
            output.append(img.origFileName)
        else:
            imgOptimization(img, opt)
            output.append(img.saveToDir(dirpath))
            if wipe:
                output.append(img.origFileName)
            if opt.quality == 2:
                img2 = image.ComicPage(os.path.join(dirpath, afile), opt, img.fill)
                if img.rotated:
                    img2.image = img2.image.rotate(90, Image.BICUBIC, True)
                    img2.rotated = True
                imgOptimization(img2, opt, img)
                output.append(img2.saveToDir(dirpath))
                output.append(img.origFileName)
        return output
    except Exception:
        return str(sys.exc_info()[1])


def getWorkFolder(afile):
    if len(afile) > 240:
        raise UserWarning("Path is too long.")
    if os.path.isdir(afile):
        workdir = mkdtemp('', 'KCC-TMP-')
        try:
            os.rmdir(workdir)   # needed for copytree() fails if dst already exists
            fullPath = os.path.join(workdir, 'OEBPS', 'Images')
            if len(fullPath) > 240:
                raise UserWarning("Path is too long.")
            copytree(afile, fullPath)
            sanitizePermissions(fullPath)
            return workdir
        except OSError:
            rmtree(workdir, True)
            raise
    elif afile.lower().endswith('.pdf'):
        pdf = pdfjpgextract.PdfJpgExtract(afile)
        path, njpg = pdf.extract()
        if njpg == 0:
            rmtree(path, True)
            raise UserWarning("Failed to extract images.")
    else:
        workdir = mkdtemp('', 'KCC-TMP-')
        cbx = cbxarchive.CBxArchive(afile)
        if cbx.isCbxFile():
            try:
                path = cbx.extract(workdir)
            except OSError:
                rmtree(workdir, True)
                raise UserWarning("Failed to extract file.")
        else:
            rmtree(workdir, True)
            raise TypeError
    if len(os.path.join(path, 'OEBPS', 'Images')) > 240:
        raise UserWarning("Path is too long.")
    move(path, path + "_temp")
    move(path + "_temp", os.path.join(path, 'OEBPS', 'Images'))
    return path


def getOutputFilename(srcpath, wantedname, ext, tomeNumber):
    if srcpath[-1] == os.path.sep:
        srcpath = srcpath[:-1]
    if not ext.startswith('.'):
        ext = '.' + ext
    if wantedname is not None:
        if wantedname.endswith(ext):
            filename = os.path.abspath(wantedname)
        elif os.path.isdir(srcpath):
            filename = os.path.join(os.path.abspath(options.output), os.path.basename(srcpath) + ext)
        else:
            filename = os.path.join(os.path.abspath(options.output),
                                    os.path.basename(os.path.splitext(srcpath)[0]) + ext)
    elif os.path.isdir(srcpath):
        filename = srcpath + tomeNumber + ext
    else:
        filename = os.path.splitext(srcpath)[0] + tomeNumber + ext
    if os.path.isfile(filename):
        counter = 0
        basename = os.path.splitext(filename)[0]
        while os.path.isfile(basename + '_kcc' + str(counter) + ext):
            counter += 1
        filename = basename + '_kcc' + str(counter) + ext
    return filename


def getComicInfo(path, originalPath):
    xmlPath = os.path.join(path, 'ComicInfo.xml')
    options.authors = ['KCC']
    options.remoteCovers = {}
    titleSuffix = ''
    if options.title == 'defaulttitle':
        defaultTitle = True
        if os.path.isdir(originalPath):
            options.title = os.path.basename(originalPath)
        else:
            options.title = os.path.splitext(os.path.basename(originalPath))[0]
    else:
        defaultTitle = False
    if os.path.exists(xmlPath):
        try:
            xml = parse(xmlPath)
        except Exception:
            os.remove(xmlPath)
            return
        options.authors = []
        if defaultTitle:
            if len(xml.getElementsByTagName('Series')) != 0:
                options.title = xml.getElementsByTagName('Series')[0].firstChild.nodeValue
            if len(xml.getElementsByTagName('Volume')) != 0:
                titleSuffix += ' V' + xml.getElementsByTagName('Volume')[0].firstChild.nodeValue
            if len(xml.getElementsByTagName('Number')) != 0:
                titleSuffix += ' #' + xml.getElementsByTagName('Number')[0].firstChild.nodeValue
            options.title += titleSuffix
        if len(xml.getElementsByTagName('Writer')) != 0:
            authorsTemp = str.split(xml.getElementsByTagName('Writer')[0].firstChild.nodeValue, ', ')
            for author in authorsTemp:
                options.authors.append(author)
        if len(xml.getElementsByTagName('Penciller')) != 0:
            authorsTemp = str.split(xml.getElementsByTagName('Penciller')[0].firstChild.nodeValue, ', ')
            for author in authorsTemp:
                options.authors.append(author)
        if len(xml.getElementsByTagName('Inker')) != 0:
            authorsTemp = str.split(xml.getElementsByTagName('Inker')[0].firstChild.nodeValue, ', ')
            for author in authorsTemp:
                options.authors.append(author)
        if len(xml.getElementsByTagName('Colorist')) != 0:
            authorsTemp = str.split(xml.getElementsByTagName('Colorist')[0].firstChild.nodeValue, ', ')
            for author in authorsTemp:
                options.authors.append(author)
        if len(options.authors) > 0:
            options.authors = list(set(options.authors))
            options.authors.sort()
        else:
            options.authors = ['KCC']
        if len(xml.getElementsByTagName('ScanInformation')) != 0:
            coverId = xml.getElementsByTagName('ScanInformation')[0].firstChild.nodeValue
            coverId = compile('(MCD\\()(\\d+)(\\))').search(coverId)
            if coverId:
                options.remoteCovers = getCoversFromMCB(coverId.group(2))
        os.remove(xmlPath)


def getCoversFromMCB(mangaID):
    covers = {}
    try:
        jsonRaw = urlopen(Request('http://mcd.iosphe.re/api/v1/series/' + mangaID + '/',
                                  headers={'User-Agent': 'KindleComicConverter/' + __version__}))
        jsonData = loads(jsonRaw.readall().decode('utf-8'))
        for volume in jsonData['Covers']['a']:
            if volume['Side'] == 'front':
                covers[int(volume['Volume'])] = volume['Raw']
    except Exception:
        return {}
    return covers


def getDirectorySize(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def sanitizeTree(filetree):
    chapterNames = {}
    for root, dirs, files in walk(filetree, False):
        for name in files:
            splitname = os.path.splitext(name)
            slugified = slugify(splitname[0])
            while os.path.exists(os.path.join(root, slugified + splitname[1])) and splitname[0].upper()\
                    != slugified.upper():
                slugified += "A"
            newKey = os.path.join(root, slugified + splitname[1])
            key = os.path.join(root, name)
            if key != newKey:
                saferReplace(key, newKey)
        for name in dirs:
            tmpName = name
            slugified = slugify(name)
            while os.path.exists(os.path.join(root, slugified)) and name.upper() != slugified.upper():
                slugified += "A"
            chapterNames[slugified] = tmpName
            newKey = os.path.join(root, slugified)
            key = os.path.join(root, name)
            if key != newKey:
                saferReplace(key, newKey)
    return chapterNames


def sanitizeTreeKobo(filetree):
    pageNumber = 0
    for root, dirs, files in walk(filetree):
        files.sort()
        dirs.sort()
        for name in files:
            splitname = os.path.splitext(name)
            slugified = str(pageNumber).zfill(5)
            pageNumber += 1
            while os.path.exists(os.path.join(root, slugified + splitname[1])) and splitname[0].upper()\
                    != slugified.upper():
                slugified += "A"
            newKey = os.path.join(root, slugified + splitname[1])
            key = os.path.join(root, name)
            if key != newKey:
                saferReplace(key, newKey)


def sanitizePermissions(filetree):
    for root, dirs, files in walk(filetree, False):
        for name in files:
            os.chmod(os.path.join(root, name), S_IWRITE | S_IREAD)
        for name in dirs:
            os.chmod(os.path.join(root, name), S_IWRITE | S_IREAD | S_IEXEC)


# noinspection PyUnboundLocalVariable
def splitDirectory(path):
    # Detect directory stucture
    for root, dirs, files in walkLevel(os.path.join(path, 'OEBPS', 'Images'), 0):
        subdirectoryNumber = len(dirs)
        filesNumber = len(files)
    if subdirectoryNumber == 0:
        # No subdirectories
        mode = 0
    else:
        if filesNumber > 0:
            print('\nWARNING: Automatic output splitting failed.')
            if GUI:
                GUI.addMessage.emit('Automatic output splitting failed. <a href='
                                    '"https://github.com/ciromattia/kcc/wiki'
                                    '/Automatic-output-splitting">'
                                    'More details.</a>', 'warning', False)
                GUI.addMessage.emit('', '', False)
            return [path]
        detectedSubSubdirectories = False
        detectedFilesInSubdirectories = False
        for root, dirs, files in walkLevel(os.path.join(path, 'OEBPS', 'Images'), 1):
            if root != os.path.join(path, 'OEBPS', 'Images'):
                if len(dirs) != 0:
                    detectedSubSubdirectories = True
                elif len(dirs) == 0 and detectedSubSubdirectories:
                    print('\nWARNING: Automatic output splitting failed.')
                    if GUI:
                        GUI.addMessage.emit('Automatic output splitting failed. <a href='
                                            '"https://github.com/ciromattia/kcc/wiki'
                                            '/Automatic-output-splitting">'
                                            'More details.</a>', 'warning', False)
                        GUI.addMessage.emit('', '', False)
                    return [path]
                if len(files) != 0:
                    detectedFilesInSubdirectories = True
        if detectedSubSubdirectories:
            # Two levels of subdirectories
            mode = 2
        else:
            # One level of subdirectories
            mode = 1
        if detectedFilesInSubdirectories and detectedSubSubdirectories:
            print('\nWARNING: Automatic output splitting failed.')
            if GUI:
                GUI.addMessage.emit('Automatic output splitting failed. <a href='
                                    '"https://github.com/ciromattia/kcc/wiki'
                                    '/Automatic-output-splitting">'
                                    'More details.</a>', 'warning', False)
                GUI.addMessage.emit('', '', False)
            return [path]
    # Split directories
    splitter = splitProcess(os.path.join(path, 'OEBPS', 'Images'), mode)
    path = [path]
    for tome in splitter:
        path.append(tome)
    return path


def splitProcess(path, mode):
    output = []
    currentSize = 0
    currentTarget = path
    if options.webtoon:
        targetSize = 104857600
    else:
        targetSize = 419430400
    if mode == 0:
        for root, dirs, files in walkLevel(path, 0):
            for name in files:
                size = os.path.getsize(os.path.join(root, name))
                if currentSize + size > targetSize:
                    currentTarget, pathRoot = createNewTome()
                    output.append(pathRoot)
                    currentSize = size
                else:
                    currentSize += size
                if path != currentTarget:
                    move(os.path.join(root, name), os.path.join(currentTarget, name))
    elif mode == 1:
        for root, dirs, files in walkLevel(path, 0):
            for name in dirs:
                size = getDirectorySize(os.path.join(root, name))
                if currentSize + size > targetSize:
                    currentTarget, pathRoot = createNewTome()
                    output.append(pathRoot)
                    currentSize = size
                else:
                    currentSize += size
                if path != currentTarget:
                    move(os.path.join(root, name), os.path.join(currentTarget, name))
    elif mode == 2:
        firstTome = True
        for root, dirs, files in walkLevel(path, 0):
            for name in dirs:
                size = getDirectorySize(os.path.join(root, name))
                currentSize = 0
                if size > targetSize:
                    if not firstTome:
                        currentTarget, pathRoot = createNewTome()
                        output.append(pathRoot)
                    else:
                        firstTome = False
                    for rootInside, dirsInside, filesInside in walkLevel(os.path.join(root, name), 0):
                        for nameInside in dirsInside:
                            size = getDirectorySize(os.path.join(rootInside, nameInside))
                            if currentSize + size > targetSize:
                                currentTarget, pathRoot = createNewTome()
                                output.append(pathRoot)
                                currentSize = size
                            else:
                                currentSize += size
                            if path != currentTarget:
                                move(os.path.join(rootInside, nameInside), os.path.join(currentTarget, nameInside))
                else:
                    if not firstTome:
                        currentTarget, pathRoot = createNewTome()
                        output.append(pathRoot)
                        move(os.path.join(root, name), os.path.join(currentTarget, name))
                    else:
                        firstTome = False
    return output


def detectCorruption(tmpPath, orgPath):
    for root, dirs, files in walk(tmpPath, False):
        for name in files:
            if getImageFileName(name) is not None:
                path = os.path.join(root, name)
                pathOrg = orgPath + path.split('OEBPS' + os.path.sep + 'Images')[1]
                if os.path.getsize(path) == 0:
                    rmtree(os.path.join(tmpPath, '..', '..'), True)
                    raise RuntimeError('Image file %s is corrupted.' % pathOrg)
                try:
                    img = Image.open(path)
                    img.verify()
                    img = Image.open(path)
                    img.load()
                except Exception:
                    rmtree(os.path.join(tmpPath, '..', '..'), True)
                    raise RuntimeError('Image file %s is corrupted.' % pathOrg)
            else:
                os.remove(os.path.join(root, name))


def detectMargins(path):
    if options.imgproc:
        for flag in options.imgIndex[path]:
            if "Margins-" in flag:
                flag = flag.split('-')
                xl = flag[1]
                yu = flag[2]
                xr = flag[3]
                yd = flag[4]
                if xl != "0":
                    xl = "-" + str(float(xl)/100) + "%"
                else:
                    xl = "0%"
                if xr != "0":
                    xr = "-" + str(float(xr)/100) + "%"
                else:
                    xr = "0%"
                if yu != "0":
                    yu = "-" + str(float(yu)/100) + "%"
                else:
                    yu = "0%"
                if yd != "0":
                    yd = "-" + str(float(yd)/100) + "%"
                else:
                    yd = "0%"
                return xl, yu, xr, yd
    return '0%', '0%', '0%', '0%'


def createNewTome():
    tomePathRoot = mkdtemp('', 'KCC-TMP-')
    tomePath = os.path.join(tomePathRoot, 'OEBPS', 'Images')
    os.makedirs(tomePath)
    return tomePath, tomePathRoot


def slugify(value):
    value = slugifyExt(value)
    value = sub(r'0*([0-9]{4,})', r'\1', sub(r'([0-9]+)', r'0000\1', value))
    return value


def makeZIP(zipFilename, baseDir, isEPUB=False):
    zipFilename = os.path.abspath(zipFilename) + '.zip'
    zipOutput = ZipFile(zipFilename, 'w', ZIP_DEFLATED)
    if isEPUB:
        zipOutput.writestr('mimetype', 'application/epub+zip', ZIP_STORED)
    for dirpath, dirnames, filenames in walk(baseDir):
        for name in filenames:
            path = os.path.normpath(os.path.join(dirpath, name))
            aPath = os.path.normpath(os.path.join(dirpath.replace(baseDir, ''), name))
            if os.path.isfile(path):
                zipOutput.write(path, aPath)
    zipOutput.close()
    return zipFilename


def makeParser():
    """Create and return an option parser set up with KCC options."""
    psr = OptionParser(usage="Usage: kcc-c2e [options] comic_file|comic_folder", add_help_option=False)

    mainOptions = OptionGroup(psr, "MAIN")
    processingOptions = OptionGroup(psr, "PROCESSING")
    outputOptions = OptionGroup(psr, "OUTPUT SETTINGS")
    customProfileOptions = OptionGroup(psr, "CUSTOM PROFILE")
    otherOptions = OptionGroup(psr, "OTHER")

    mainOptions.add_option("-p", "--profile", action="store", dest="profile", default="KV",
                           help="Device profile (Available options: K1, K2, K345, KDX, KPW, KV, KFHD, KFHDX, KFHDX8,"
                                " KFA, KoMT, KoG, KoA, KoAHD, KoAH2O) [Default=KV]")
    mainOptions.add_option("-q", "--quality", type="int", dest="quality", default="0",
                           help="Quality of Panel View. 0 - Normal 1 - High 2 - Ultra [Default=0]")
    mainOptions.add_option("-m", "--manga-style", action="store_true", dest="righttoleft", default=False,
                           help="Manga style (Right-to-left reading and splitting)")
    mainOptions.add_option("-w", "--webtoon", action="store_true", dest="webtoon", default=False,
                           help="Webtoon processing mode"),

    outputOptions.add_option("-o", "--output", action="store", dest="output", default=None,
                             help="Output generated file to specified directory or file")
    outputOptions.add_option("-t", "--title", action="store", dest="title", default="defaulttitle",
                             help="Comic title [Default=filename or directory name]")
    outputOptions.add_option("-f", "--format", action="store", dest="format", default="Auto",
                             help="Output format (Available options: Auto, MOBI, EPUB, CBZ) [Default=Auto]")
    outputOptions.add_option("--batchsplit", action="store_true", dest="batchsplit", default=False,
                             help="Split output into multiple files"),

    processingOptions.add_option("--blackborders", action="store_true", dest="black_borders", default=False,
                                 help="Disable autodetection and force black borders")
    processingOptions.add_option("--whiteborders", action="store_true", dest="white_borders", default=False,
                                 help="Disable autodetection and force white borders")
    processingOptions.add_option("--forcecolor", action="store_true", dest="forcecolor", default=False,
                                 help="Don't convert images to grayscale")
    processingOptions.add_option("--forcepng", action="store_true", dest="forcepng", default=False,
                                 help="Create PNG files instead JPEG")
    processingOptions.add_option("--gamma", type="float", dest="gamma", default="0.0",
                                 help="Apply gamma correction to linearize the image [Default=Auto]")
    processingOptions.add_option("--nocutpagenumbers", action="store_false", dest="cutpagenumbers", default=True,
                                 help="Don't try to cut page numbering on images")
    processingOptions.add_option("--noprocessing", action="store_false", dest="imgproc", default=True,
                                 help="Don't apply image preprocessing")
    processingOptions.add_option("--nosplitrotate", action="store_true", dest="nosplitrotate", default=False,
                                 help="Disable splitting and rotation")
    processingOptions.add_option("--rotate", action="store_true", dest="rotate", default=False,
                                 help="Rotate landscape pages instead of splitting them")
    processingOptions.add_option("--stretch", action="store_true", dest="stretch", default=False,
                                 help="Stretch images to device's resolution")
    processingOptions.add_option("--upscale", action="store_true", dest="upscale", default=False,
                                 help="Resize images smaller than device's resolution")

    customProfileOptions.add_option("--customwidth", type="int", dest="customwidth", default=0,
                                    help="Replace screen width provided by device profile")
    customProfileOptions.add_option("--customheight", type="int", dest="customheight", default=0,
                                    help="Replace screen height provided by device profile")

    otherOptions.add_option("-h", "--help", action="help",
                            help="Show this help message and exit")

    psr.add_option_group(mainOptions)
    psr.add_option_group(outputOptions)
    psr.add_option_group(processingOptions)
    psr.add_option_group(customProfileOptions)
    psr.add_option_group(otherOptions)
    return psr


def checkOptions():
    global options
    options.panelview = True
    options.bordersColor = None
    if options.format == 'Auto':
        if options.profile in ['K1', 'K2', 'K345', 'KPW', 'KV', 'KFHD', 'KFHDX', 'KFHDX8', 'KFA']:
            options.format = 'MOBI'
        elif options.profile in ['Other']:
            options.format = 'EPUB'
        elif options.profile in ['KDX', 'KoMT', 'KoG', 'KoA', 'KoAHD', 'KoAH2O']:
            options.format = 'CBZ'
    if options.white_borders:
        options.bordersColor = 'white'
    if options.black_borders:
        options.bordersColor = 'black'
    # Splitting MOBI is not optional
    if options.format == 'MOBI':
        options.batchsplit = True
    # Disabling grayscale conversion for Kindle Fire family.
    if 'KFH' in options.profile or options.forcecolor:
        options.forcecolor = True
    else:
        options.forcecolor = False
    # Older Kindle don't need higher resolution files due lack of Panel View.
    if options.profile == 'K1' or options.profile == 'K2' or options.profile == 'KDX':
        options.quality = 0
        options.panelview = False
    # Webtoon mode mandatory options
    if options.webtoon:
        options.nosplitrotate = True
        options.quality = 0
        options.panelview = False
    # Disable all Kindle features for other e-readers
    if options.profile == 'OTHER':
        options.panelview = False
        options.quality = 0
    if 'Ko' in options.profile:
        options.panelview = False
        # Kobo models can't use ultra quality mode
        if options.quality == 2:
            options.quality = 1
    # Kindle for Android profile require target resolution.
    if options.profile == 'KFA' and (options.customwidth == 0 or options.customheight == 0):
        print("ERROR: Kindle for Android profile require --customwidth and --customheight options!")
        sys.exit(1)
    # CBZ files on Kindle DX/DXG support higher resolution
    if options.profile == 'KDX' and options.format == 'CBZ':
        options.customheight = 1200
    # Ultra mode don't work with CBZ format
    if options.quality == 2 and options.format == 'CBZ':
        options.quality = 1
    # Override profile data
    if options.customwidth != 0 or options.customheight != 0:
        X = image.ProfileData.Profiles[options.profile][1][0]
        Y = image.ProfileData.Profiles[options.profile][1][1]
        if options.customwidth != 0:
            X = options.customwidth
        if options.customheight != 0:
            Y = options.customheight
        newProfile = ("Custom", (int(X), int(Y)), image.ProfileData.Palette16,
                      image.ProfileData.Profiles[options.profile][3], (int(int(X)*1.5), int(int(Y)*1.5)))
        image.ProfileData.Profiles["Custom"] = newProfile
        options.profile = "Custom"
    options.profileData = image.ProfileData.Profiles[options.profile]


def checkTools(source):
    source = source.upper()
    if source.endswith('.CBR') or source.endswith('.RAR'):
        rarExitCode = Popen('unrar', stdout=PIPE, stderr=STDOUT, shell=True)
        rarExitCode = rarExitCode.wait()
        if rarExitCode != 0 and rarExitCode != 7:
            print('\nUnRAR is missing!')
            exit(1)
    elif source.endswith('.CB7') or source.endswith('.7Z'):
        sevenzaExitCode = Popen('7za', stdout=PIPE, stderr=STDOUT, shell=True)
        sevenzaExitCode = sevenzaExitCode.wait()
        if sevenzaExitCode != 0 and sevenzaExitCode != 7:
            print('\n7za is missing!')
            exit(1)
    if options.format == 'MOBI':
        kindleGenExitCode = Popen('kindlegen -locale en', stdout=PIPE, stderr=STDOUT, shell=True)
        if kindleGenExitCode.wait() != 0:
            print('\nKindleGen is missing!')
            exit(1)


def makeBook(source, qtGUI=None):
    """Generates MOBI/EPUB/CBZ comic ebook from a bunch of images."""
    global GUI
    GUI = qtGUI
    if GUI:
        GUI.progressBarTick.emit('1')
    else:
        checkTools(source)
    path = getWorkFolder(source)
    print("\nChecking images...")
    getComicInfo(os.path.join(path, "OEBPS", "Images"), source)
    detectCorruption(os.path.join(path, "OEBPS", "Images"), source)
    if options.webtoon:
        if options.customheight > 0:
            comic2panel.main(['-y ' + str(options.customheight), '-i', '-m', path], qtGUI)
        else:
            comic2panel.main(['-y ' + str(image.ProfileData.Profiles[options.profile][1][1]), '-i', '-m', path], qtGUI)
    if options.imgproc:
        print("\nProcessing images...")
        if GUI:
            GUI.progressBarTick.emit('Processing images')
        imgDirectoryProcessing(os.path.join(path, "OEBPS", "Images"))
    if GUI:
        GUI.progressBarTick.emit('1')
    chapterNames = sanitizeTree(os.path.join(path, 'OEBPS', 'Images'))
    if 'Ko' in options.profile and options.format == 'CBZ':
        sanitizeTreeKobo(os.path.join(path, 'OEBPS', 'Images'))
    if options.batchsplit:
        tomes = splitDirectory(path)
    else:
        tomes = [path]
    filepath = []
    tomeNumber = 0
    if GUI:
        if options.format == 'CBZ':
            GUI.progressBarTick.emit('Compressing CBZ files')
        else:
            GUI.progressBarTick.emit('Compressing EPUB files')
        GUI.progressBarTick.emit(str(len(tomes) + 1))
        GUI.progressBarTick.emit('tick')
    options.baseTitle = options.title
    for tome in tomes:
        if len(tomes) > 9:
            tomeNumber += 1
            options.title = options.baseTitle + ' [' + str(tomeNumber).zfill(2) + '/' + str(len(tomes)).zfill(2) + ']'
        elif len(tomes) > 1:
            tomeNumber += 1
            options.title = options.baseTitle + ' [' + str(tomeNumber) + '/' + str(len(tomes)) + ']'
        if options.format == 'CBZ':
            print("\nCreating CBZ file...")
            if len(tomes) > 1:
                filepath.append(getOutputFilename(source, options.output, '.cbz', ' ' + str(tomeNumber)))
            else:
                filepath.append(getOutputFilename(source, options.output, '.cbz', ''))
            makeZIP(tome + '_comic', os.path.join(tome, "OEBPS", "Images"))
        else:
            print("\nCreating EPUB file...")
            buildEPUB(tome, chapterNames, tomeNumber)
            if len(tomes) > 1:
                filepath.append(getOutputFilename(source, options.output, '.epub', ' ' + str(tomeNumber)))
            else:
                filepath.append(getOutputFilename(source, options.output, '.epub', ''))
            makeZIP(tome + '_comic', tome, True)
        move(tome + '_comic.zip', filepath[-1])
        rmtree(tome, True)
        if GUI:
            GUI.progressBarTick.emit('tick')
    if not GUI and options.format == 'MOBI':
        print("\nCreating MOBI file...")
        work = []
        for i in filepath:
            work.append([i])
        output = makeMOBI(work, GUI)
        for errors in output:
            if errors[0] != 0:
                print('KINDLEGEN ERROR!')
                print(errors)
                return filepath
        for i in filepath:
            output = makeMOBIFix(i)
            if not output[0]:
                print('DUALMETAFIX ERROR!')
                return filepath
            else:
                os.remove(i.replace('.epub', '.mobi') + '_toclean')
    return filepath


def makeMOBIFix(item):
    os.remove(item)
    mobiPath = item.replace('.epub', '.mobi')
    move(mobiPath, mobiPath + '_toclean')
    try:
        dualmetafix.DualMobiMetaFix(mobiPath + '_toclean', mobiPath, bytes(str(uuid4()), 'UTF-8'))
        return [True]
    except Exception as err:
        return [False, format(err)]


def makeMOBIWorkerTick(output):
    makeMOBIWorkerOutput.append(output)
    if output[0] != 0:
        makeMOBIWorkerPool.terminate()
    if GUI:
        GUI.progressBarTick.emit('tick')
        if not GUI.conversionAlive:
            makeMOBIWorkerPool.terminate()


def makeMOBIWorker(item):
    item = item[0]
    kindlegenErrorCode = 0
    kindlegenError = ''
    try:
        if os.path.getsize(item) < 629145600:
            output = Popen('kindlegen -dont_append_source -locale en "' + item + '"',
                           stdout=PIPE, stderr=STDOUT, shell=True)
            for line in output.stdout:
                line = line.decode('utf-8')
                # ERROR: Generic error
                if "Error(" in line:
                    kindlegenErrorCode = 1
                    kindlegenError = line
                # ERROR: EPUB too big
                if ":E23026:" in line:
                    kindlegenErrorCode = 23026
                if kindlegenErrorCode > 0:
                    break
        else:
            # ERROR: EPUB too big
            kindlegenErrorCode = 23026
        return [kindlegenErrorCode, kindlegenError, item]
    except Exception as err:
        # ERROR: KCC unknown generic error
        kindlegenErrorCode = 1
        kindlegenError = format(err)
        return [kindlegenErrorCode, kindlegenError, item]


def makeMOBI(work, qtGUI=None):
    global GUI, makeMOBIWorkerPool, makeMOBIWorkerOutput
    GUI = qtGUI
    makeMOBIWorkerOutput = []
    availableMemory = virtual_memory().total/1000000000
    if availableMemory <= 2:
        threadNumber = 1
    elif 2 < availableMemory <= 4:
        threadNumber = 2
    else:
        threadNumber = 4
    makeMOBIWorkerPool = Pool(threadNumber)
    for i in work:
        makeMOBIWorkerPool.apply_async(func=makeMOBIWorker, args=(i, ), callback=makeMOBIWorkerTick)
    makeMOBIWorkerPool.close()
    makeMOBIWorkerPool.join()
    return makeMOBIWorkerOutput
