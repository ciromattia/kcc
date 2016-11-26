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
from time import strftime, gmtime
from copy import copy
from glob import glob
from json import loads
from urllib.request import Request, urlopen
from re import sub
from stat import S_IWRITE, S_IREAD, S_IEXEC
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from tempfile import mkdtemp, gettempdir, TemporaryFile
from shutil import move, copytree, rmtree
from optparse import OptionParser, OptionGroup
from multiprocessing import Pool
from uuid import uuid4
from slugify import slugify as slugifyExt
from PIL import Image
from subprocess import STDOUT, PIPE
from psutil import Popen, virtual_memory
from html import escape
try:
    from PyQt5 import QtCore
except ImportError:
    QtCore = None
try:
    from scandir import walk
except ImportError:
    walk = os.walk
from .shared import md5Checksum, getImageFileName, walkSort, walkLevel, saferReplace, saferRemove, sanitizeTrace
from . import comic2panel
from . import image
from . import cbxarchive
from . import pdfjpgextract
from . import dualmetafix
from . import metadata
from . import kindle
from . import __version__


def main(argv=None):
    global options
    parser = makeParser()
    optionstemplate, args = parser.parse_args(argv)
    if len(args) == 0:
        parser.print_help()
        return 0
    if sys.platform.startswith('win'):
        sources = set([source for arg in args for source in glob(arg)])
    else:
        sources = set(args)
    if len(sources) == 0:
        print('No matching files found.')
        return 1
    for source in sources:
        source = source.rstrip('\\').rstrip('/')
        options = copy(optionstemplate)
        checkOptions()
        if len(sources) > 1:
            print('Working on ' + source + '...')
        makeBook(source)
    return 0


def buildHTML(path, imgfile, imgfilepath):
    imgfilepath = md5Checksum(imgfilepath)
    filename = getImageFileName(imgfile)
    deviceres = options.profileData[1]
    if "Rotated" in options.imgIndex[imgfilepath]:
        rotatedPage = True
    else:
        rotatedPage = False
    if "BlackFill" in options.imgIndex[imgfilepath]:
        additionalStyle = 'background-color:#000000;'
    else:
        additionalStyle = 'background-color:#FFFFFF;'
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
    htmlfile = os.path.join(htmlpath, filename[0] + '.xhtml')
    f = open(htmlfile, "w", encoding='UTF-8')
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
                  "<!DOCTYPE html>\n",
                  "<html xmlns=\"http://www.w3.org/1999/xhtml\" xmlns:epub=\"http://www.idpf.org/2007/ops\">\n",
                  "<head>\n",
                  "<title>", escape(filename[0]), "</title>\n",
                  "<link href=\"", "../" * (backref - 1), "style.css\" type=\"text/css\" rel=\"stylesheet\"/>\n",
                  "<meta name=\"viewport\" "
                  "content=\"width=" + str(deviceres[0]) + ", height=" + str(deviceres[1]) + "\"/>\n"
                  "</head>\n",
                  "<body style=\"background-image: ",
                  "url('", "../" * backref, "Images/", postfix, imgfile, "'); " + additionalStyle + "\">\n"])
    if options.iskindle and options.panelview:
        sizeTmp = Image.open(os.path.join(head, "Images", postfix, imgfile)).size
        if options.autoscale:
            size = (getPanelViewResolution(sizeTmp, deviceres))
        else:
            size = (int(sizeTmp[0] * 1.5), int(sizeTmp[1] * 1.5))
        if size[0] - deviceres[0] < deviceres[0] * 0.01:
            noHorizontalPV = True
        else:
            noHorizontalPV = False
        if size[1] - deviceres[1] < deviceres[1] * 0.01:
            noVerticalPV = True
        else:
            noVerticalPV = False
        x, y = getPanelViewSize(deviceres, size)
        boxStyles = {"PV-TL": "position:absolute;left:0;top:0;",
                     "PV-TR": "position:absolute;right:0;top:0;",
                     "PV-BL": "position:absolute;left:0;bottom:0;",
                     "PV-BR": "position:absolute;right:0;bottom:0;",
                     "PV-T": "position:absolute;top:0;left:" + x + "%;",
                     "PV-B": "position:absolute;bottom:0;left:" + x + "%;",
                     "PV-L": "position:absolute;left:0;top:" + y + "%;",
                     "PV-R": "position:absolute;right:0;top:" + y + "%;"}
        f.write("<div id=\"PV\">\n")
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
            boxes = ["PV-TL", "PV-TR", "PV-BL", "PV-BR"]
        elif noHorizontalPV and not noVerticalPV:
            if rotatedPage:
                if options.righttoleft:
                    order = [1, 2]
                else:
                    order = [2, 1]
            else:
                order = [1, 2]
            boxes = ["PV-T", "PV-B"]
        elif not noHorizontalPV and noVerticalPV:
            if rotatedPage:
                order = [1, 2]
            else:
                if options.righttoleft:
                    order = [2, 1]
                else:
                    order = [1, 2]
            boxes = ["PV-L", "PV-R"]
        else:
            order = []
            boxes = []
        for i in range(0, len(boxes)):
            f.writelines(["<div id=\"" + boxes[i] + "\">\n",
                          "<a style=\"display:inline-block;width:100%;height:100%;\" class=\"app-amzn-magnify\" "
                          "data-app-amzn-magnify='{\"targetId\":\"" + boxes[i] +
                          "-P\", \"ordinal\":" + str(order[i]) + "}'></a>\n",
                          "</div>\n"])
        f.write("</div>\n")
        for box in boxes:
            f.writelines(["<div class=\"PV-P\" id=\"" + box + "-P\" style=\"" + additionalStyle + "\">\n",
                          "<img style=\"" + boxStyles[box] + "\" src=\"", "../" * backref, "Images/", postfix,
                          imgfile, "\" width=\"" + str(size[0]) + "\" height=\"" + str(size[1]) + "\"/>\n",
                          "</div>\n"])
    f.writelines(["</body>\n",
                  "</html>\n"])
    f.close()
    return path, imgfile


def buildNCX(dstdir, title, chapters, chapterNames):
    ncxfile = os.path.join(dstdir, 'OEBPS', 'toc.ncx')
    f = open(ncxfile, "w", encoding='UTF-8')
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
                  "<ncx version=\"2005-1\" xml:lang=\"en-US\" xmlns=\"http://www.daisy.org/z3986/2005/ncx/\">\n",
                  "<head>\n",
                  "<meta name=\"dtb:uid\" content=\"urn:uuid:", options.uuid, "\"/>\n",
                  "<meta name=\"dtb:depth\" content=\"1\"/>\n",
                  "<meta name=\"dtb:totalPageCount\" content=\"0\"/>\n",
                  "<meta name=\"dtb:maxPageNumber\" content=\"0\"/>\n",
                  "<meta name=\"generated\" content=\"true\"/>\n",
                  "</head>\n",
                  "<docTitle><text>", escape(title), "</text></docTitle>\n",
                  "<navMap>\n"])
    for chapter in chapters:
        folder = chapter[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\')
        filename = getImageFileName(os.path.join(folder, chapter[1]))
        navID = folder.replace('/', '_').replace('\\', '_')
        if options.chapters:
            title = chapterNames[chapter[1]]
            navID = filename[0].replace('/', '_').replace('\\', '_')
        elif os.path.basename(folder) != "Text":
            title = chapterNames[os.path.basename(folder)]
        f.write("<navPoint id=\"" + navID + "\"><navLabel><text>" +
                escape(title) + "</text></navLabel><content src=\"" + filename[0].replace("\\", "/") +
                ".xhtml\"/></navPoint>\n")
    f.write("</navMap>\n</ncx>")
    f.close()


def buildNAV(dstdir, title, chapters, chapterNames):
    navfile = os.path.join(dstdir, 'OEBPS', 'nav.xhtml')
    f = open(navfile, "w", encoding='UTF-8')
    f.writelines(["<?xml version=\"1.0\" encoding=\"utf-8\"?>\n",
                  "<!DOCTYPE html>\n",
                  "<html xmlns=\"http://www.w3.org/1999/xhtml\" xmlns:epub=\"http://www.idpf.org/2007/ops\">\n",
                  "<head>\n",
                  "<title>" + escape(title) + "</title>\n",
                  "<meta charset=\"utf-8\"/>\n",
                  "</head>\n",
                  "<body>\n",
                  "<nav xmlns:epub=\"http://www.idpf.org/2007/ops\" epub:type=\"toc\" id=\"toc\">\n",
                  "<ol>\n"])
    for chapter in chapters:
        folder = chapter[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\')
        filename = getImageFileName(os.path.join(folder, chapter[1]))
        if options.chapters:
            title = chapterNames[chapter[1]]
        elif os.path.basename(folder) != "Text":
            title = chapterNames[os.path.basename(folder)]
        f.write("<li><a href=\"" + filename[0].replace("\\", "/") + ".xhtml\">" + escape(title) + "</a></li>\n")
    f.writelines(["</ol>\n",
                  "</nav>\n",
                  "<nav epub:type=\"page-list\">\n",
                  "<ol>\n"])
    for chapter in chapters:
        folder = chapter[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\')
        filename = getImageFileName(os.path.join(folder, chapter[1]))
        if options.chapters:
            title = chapterNames[chapter[1]]
        elif os.path.basename(folder) != "Text":
            title = chapterNames[os.path.basename(folder)]
        f.write("<li><a href=\"" + filename[0].replace("\\", "/") + ".xhtml\">" + escape(title) + "</a></li>\n")
    f.write("</ol>\n</nav>\n</body>\n</html>")
    f.close()


def buildOPF(dstdir, title, filelist, cover=None):
    opffile = os.path.join(dstdir, 'OEBPS', 'content.opf')
    deviceres = options.profileData[1]
    if options.righttoleft:
        writingmode = "horizontal-rl"
    else:
        writingmode = "horizontal-lr"
    f = open(opffile, "w", encoding='UTF-8')
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
                  "<package version=\"3.0\" unique-identifier=\"BookID\" ",
                  "xmlns=\"http://www.idpf.org/2007/opf\">\n",
                  "<metadata xmlns:opf=\"http://www.idpf.org/2007/opf\" ",
                  "xmlns:dc=\"http://purl.org/dc/elements/1.1/\">\n",
                  "<dc:title>", title, "</dc:title>\n",
                  "<dc:language>en-US</dc:language>\n",
                  "<dc:identifier id=\"BookID\">urn:uuid:", options.uuid, "</dc:identifier>\n",
                  "<dc:contributor id=\"contributor\">KindleComicConverter-" + __version__ + "</dc:contributor>\n"])
    if len(options.summary) > 0:
        f.writelines(["<dc:description>", options.summary, "</dc:description>\n"])
    for author in options.authors:
        f.writelines(["<dc:creator>", author, "</dc:creator>\n"])
    f.writelines(["<meta property=\"dcterms:modified\">" + strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()) + "</meta>\n",
                  "<meta name=\"cover\" content=\"cover\"/>\n",
                  "<meta property=\"rendition:orientation\">portrait</meta>\n",
                  "<meta property=\"rendition:spread\">portrait</meta>\n",
                  "<meta property=\"rendition:layout\">pre-paginated</meta>\n"])
    if options.iskindle and options.profile != 'Custom':
        f.writelines(["<meta name=\"original-resolution\" content=\"",
                      str(deviceres[0]) + "x" + str(deviceres[1]) + "\"/>\n",
                      "<meta name=\"book-type\" content=\"comic\"/>\n",
                      "<meta name=\"RegionMagnification\" content=\"true\"/>\n",
                      "<meta name=\"primary-writing-mode\" content=\"" + writingmode + "\"/>\n",
                      "<meta name=\"zero-gutter\" content=\"true\"/>\n",
                      "<meta name=\"zero-margin\" content=\"true\"/>\n",
                      "<meta name=\"ke-border-color\" content=\"#ffffff\"/>\n",
                      "<meta name=\"ke-border-width\" content=\"0\"/>\n"])
    f.writelines(["</metadata>\n<manifest>\n<item id=\"ncx\" href=\"toc.ncx\" ",
                  "media-type=\"application/x-dtbncx+xml\"/>\n",
                  "<item id=\"nav\" href=\"nav.xhtml\" ",
                  "properties=\"nav\" media-type=\"application/xhtml+xml\"/>\n"])
    if cover is not None:
        filename = getImageFileName(cover.replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\'))
        if '.png' == filename[1]:
            mt = 'image/png'
        else:
            mt = 'image/jpeg'
        f.write("<item id=\"cover\" href=\"Images/cover" + filename[1] + "\" media-type=\"" + mt +
                "\" properties=\"cover-image\"/>\n")
    reflist = []
    for path in filelist:
        folder = path[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\').replace("\\", "/")
        filename = getImageFileName(path[1])
        uniqueid = os.path.join(folder, filename[0]).replace('/', '_').replace('\\', '_')
        reflist.append(uniqueid)
        f.write("<item id=\"page_" + str(uniqueid) + "\" href=\"" +
                folder.replace('Images', 'Text') + "/" + filename[0] +
                ".xhtml\" media-type=\"application/xhtml+xml\"/>\n")
        if '.png' == filename[1]:
            mt = 'image/png'
        else:
            mt = 'image/jpeg'
        f.write("<item id=\"img_" + str(uniqueid) + "\" href=\"" + folder + "/" + path[1] + "\" media-type=\"" +
                mt + "\"/>\n")
    f.write("<item id=\"css\" href=\"Text/style.css\" media-type=\"text/css\"/>\n")
    if options.righttoleft:
        f.write("</manifest>\n<spine page-progression-direction=\"rtl\" toc=\"ncx\">\n")
    else:
        f.write("</manifest>\n<spine page-progression-direction=\"ltr\" toc=\"ncx\">\n")
    for entry in reflist:
        f.write("<itemref idref=\"page_" + entry + "\"/>\n")
    f.write("</spine>\n</package>\n")
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
    os.mkdir(os.path.join(path, 'OEBPS', 'Text'))
    f = open(os.path.join(path, 'OEBPS', 'Text', 'style.css'), 'w', encoding='UTF-8')
    f.writelines(["@page {\n",
                  "margin: 0;\n",
                  "}\n",
                  "body {\n",
                  "display: block;\n",
                  "margin: 0;\n",
                  "padding: 0;\n",
                  "background-position: center center;\n",
                  "background-repeat: no-repeat;\n",
                  "background-size: auto auto;\n",
                  "}\n",
                  "#PV {\n",
                  "position: absolute;\n",
                  "width: 100%;\n",
                  "height: 100%;\n",
                  "top: 0;\n",
                  "left: 0;\n",
                  "}\n",
                  "#PV-T {\n",
                  "top: 0;\n",
                  "width: 100%;\n",
                  "height: 50%;\n",
                  "}\n",
                  "#PV-B {\n",
                  "bottom: 0;\n",
                  "width: 100%;\n",
                  "height: 50%;\n",
                  "}\n",
                  "#PV-L {\n",
                  "left: 0;\n",
                  "width: 49.5%;\n",
                  "height: 100%;\n",
                  "float: left;\n",
                  "}\n",
                  "#PV-R {\n",
                  "right: 0;\n",
                  "width: 49.5%;\n",
                  "height: 100%;\n",
                  "float: right;\n",
                  "}\n",
                  "#PV-TL {\n",
                  "top: 0;\n",
                  "left: 0;\n",
                  "width: 49.5%;\n",
                  "height: 50%;\n",
                  "float: left;\n",
                  "}\n",
                  "#PV-TR {\n",
                  "top: 0;\n",
                  "right: 0;\n",
                  "width: 49.5%;\n",
                  "height: 50%;\n",
                  "float: right;\n",
                  "}\n",
                  "#PV-BL {\n",
                  "bottom: 0;\n",
                  "left: 0;\n",
                  "width: 49.5%;\n",
                  "height: 50%;\n",
                  "float: left;\n",
                  "}\n",
                  "#PV-BR {\n",
                  "bottom: 0;\n",
                  "right: 0;\n",
                  "width: 49.5%;\n",
                  "height: 50%;\n",
                  "float: right;\n",
                  "}\n",
                  ".PV-P {\n",
                  "width: 100%;\n",
                  "height: 100%;\n",
                  "top: 0;\n",
                  "position: absolute;\n",
                  "display: none;\n",
                  "}\n"])
    f.close()
    for (dirpath, dirnames, filenames) in walk(os.path.join(path, 'OEBPS', 'Images')):
        chapter = False
        dirnames, filenames = walkSort(dirnames, filenames)
        for afile in filenames:
            filelist.append(buildHTML(dirpath, afile, os.path.join(dirpath, afile)))
            if not chapter:
                chapterlist.append((dirpath.replace('Images', 'Text'), filelist[-1][1]))
                chapter = True
            if cover is None:
                cover = os.path.join(os.path.join(path, 'OEBPS', 'Images'),
                                     'cover' + getImageFileName(filelist[-1][1])[1])
                options.covers.append((image.Cover(os.path.join(filelist[-1][0], filelist[-1][1]), cover, options,
                                                   tomeNumber), options.uuid))
    # Overwrite chapternames if tree is flat and ComicInfo.xml has bookmarks
    if not chapterNames and options.chapters:
        chapterlist = []
        globaldiff = 0
        for aChapter in options.chapters:
            pageid = aChapter[0]
            for x in range(0, pageid + globaldiff + 1):
                if '-kcc-b' in filelist[x][1]:
                    pageid += 1
            if '-kcc-c' in filelist[pageid][1]:
                pageid -= 1
            filename = filelist[pageid][1]
            chapterlist.append((filelist[pageid][0].replace('Images', 'Text'), filename))
            chapterNames[filename] = aChapter[1]
            globaldiff = pageid - (aChapter[0] + globaldiff)
    buildNCX(path, options.title, chapterlist, chapterNames)
    buildNAV(path, options.title, chapterlist, chapterNames)
    buildOPF(path, options.title, filelist, cover)


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
            raise RuntimeError("One of workers crashed. Cause: " + workerOutput[0][0], workerOutput[0][1])
        for file in options.imgPurgeIndex:
            if os.path.isfile(file):
                saferRemove(file)
    else:
        rmtree(os.path.join(path, '..', '..'), True)
        raise UserWarning("Source directory is empty.")


def imgFileProcessingTick(output):
    if isinstance(output, tuple):
        workerOutput.append(output)
        workerPool.terminate()
    else:
        for page in output:
            if page is not None:
                options.imgIndex[page[0]] = page[1]
                options.imgPurgeIndex.append(page[2])
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
        workImg = image.ComicPageParser((dirpath, afile), opt)
        for i in workImg.payload:
            img = image.ComicPage(i[0], i[1], i[2], i[3], i[4], opt)
            if opt.cropping == 2 and not opt.webtoon:
                img.cropPageNumber(opt.croppingp)
            if opt.cropping > 0 and not opt.webtoon:
                img.cropMargin(opt.croppingp)
            img.autocontrastImage()
            img.resizeImage()
            if opt.forcepng and not opt.forcecolor:
                img.quantizeImage()
            output.append(img.saveToDir())
        return output
    except Exception:
        return str(sys.exc_info()[1]), sanitizeTrace(sys.exc_info()[2])


def getWorkFolder(afile):
    if os.path.isdir(afile):
        workdir = mkdtemp('', 'KCC-')
        try:
            os.rmdir(workdir)
            fullPath = os.path.join(workdir, 'OEBPS', 'Images')
            copytree(afile, fullPath)
            sanitizePermissions(fullPath)
            return workdir
        except:
            rmtree(workdir, True)
            raise UserWarning("Failed to prepare a workspace.")
    elif os.path.isfile(afile) and afile.lower().endswith('.pdf'):
        pdf = pdfjpgextract.PdfJpgExtract(afile)
        path, njpg = pdf.extract()
        if njpg == 0:
            rmtree(path, True)
            raise UserWarning("Failed to extract images from PDF file.")
    elif os.path.isfile(afile):
        workdir = mkdtemp('', 'KCC-')
        cbx = cbxarchive.CBxArchive(afile)
        if cbx.isCbxFile():
            try:
                path = cbx.extract(workdir)
            except:
                rmtree(workdir, True)
                raise UserWarning("Failed to extract archive.")
        else:
            rmtree(workdir, True)
            raise UserWarning("Failed to detect archive format.")
    else:
        raise UserWarning("Failed to open source file/directory.")
    sanitizePermissions(path)
    newpath = mkdtemp('', 'KCC-')
    copytree(path, os.path.join(newpath, 'OEBPS', 'Images'))
    rmtree(path, True)
    return newpath


def getOutputFilename(srcpath, wantedname, ext, tomeNumber):
    if srcpath[-1] == os.path.sep:
        srcpath = srcpath[:-1]
    if 'Ko' in options.profile and options.format == 'EPUB':
        ext = '.kepub.epub'
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
        if 'Ko' in options.profile and options.format == 'EPUB':
            path = srcpath.split(os.path.sep)
            path[-1] = ''.join(e for e in path[-1].split('.')[0] if e.isalnum()) + tomeNumber + ext
            if not path[-1].split('.')[0]:
                path[-1] = 'KCCPlaceholder' + tomeNumber + ext
            filename = os.path.sep.join(path)
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
    options.chapters = []
    options.summary = ''
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
            xml = metadata.MetadataParser(xmlPath)
        except Exception:
            saferRemove(xmlPath)
            return
        options.authors = []
        if defaultTitle:
            if xml.data['Series']:
                options.title = escape(xml.data['Series'])
            if xml.data['Volume']:
                titleSuffix += ' V' + xml.data['Volume'].zfill(2)
            if xml.data['Number']:
                titleSuffix += ' #' + xml.data['Number'].zfill(3)
            options.title += titleSuffix
        for field in ['Writers', 'Pencillers', 'Inkers', 'Colorists']:
            for person in xml.data[field]:
                options.authors.append(escape(person))
        if len(options.authors) > 0:
            options.authors = list(set(options.authors))
            options.authors.sort()
        else:
            options.authors = ['KCC']
        if xml.data['MUid']:
            options.remoteCovers = getCoversFromMCB(xml.data['MUid'])
        if xml.data['Bookmarks']:
            options.chapters = xml.data['Bookmarks']
        if xml.data['Summary']:
            options.summary = escape(xml.data['Summary'])
        saferRemove(xmlPath)


def getCoversFromMCB(mangaID):
    covers = {}
    try:
        jsonRaw = urlopen(Request('http://mcd.iosphe.re/api/v1/series/' + mangaID + '/',
                                  headers={'User-Agent': 'KindleComicConverter/' + __version__}))
        jsonData = loads(jsonRaw.read().decode('utf-8'))
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


def getPanelViewResolution(imageSize, deviceRes):
    scale = float(deviceRes[0]) / float(imageSize[0])
    return int(deviceRes[0]), int(scale * imageSize[1])


def getPanelViewSize(deviceres, size):
    x = int(deviceres[0] / 2 - size[0] / 2) / deviceres[0] * 100
    y = int(deviceres[1] / 2 - size[1] / 2) / deviceres[1] * 100
    return str(int(x)), str(int(y))


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
        dirs, files = walkSort(dirs, files)
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


def splitDirectory(path):
    level = -1
    for root, _, files in os.walk(os.path.join(path, 'OEBPS', 'Images')):
        for f in files:
            if f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png') or f.endswith('.gif'):
                newLevel = os.path.join(root, f).replace(os.path.join(path, 'OEBPS', 'Images'), '').count(os.sep)
                if level != -1 and level != newLevel:
                    level = 0
                    break
                else:
                    level = newLevel
    if level > 0:
        splitter = splitProcess(os.path.join(path, 'OEBPS', 'Images'), level)
        path = [path]
        for tome in splitter:
            path.append(tome)
        return path
    else:
        raise UserWarning('Unsupported directory structure.')


def splitProcess(path, mode):
    output = []
    currentSize = 0
    currentTarget = path
    if options.webtoon:
        targetSize = 104857600
    else:
        targetSize = 419430400
    if options.batchsplit == 2 and mode == 2:
        mode = 3
    if mode < 3:
        for root, dirs, files in walkLevel(path, 0):
            for name in files if mode == 1 else dirs:
                if mode == 1:
                    size = os.path.getsize(os.path.join(root, name))
                else:
                    size = getDirectorySize(os.path.join(root, name))
                if currentSize + size > targetSize:
                    currentTarget, pathRoot = createNewTome()
                    output.append(pathRoot)
                    currentSize = size
                else:
                    currentSize += size
                if path != currentTarget:
                    move(os.path.join(root, name), os.path.join(currentTarget, name))
    else:
        firstTome = True
        for root, dirs, files in walkLevel(path, 0):
            for name in dirs:
                if not firstTome:
                    currentTarget, pathRoot = createNewTome()
                    output.append(pathRoot)
                    move(os.path.join(root, name), os.path.join(currentTarget, name))
                else:
                    firstTome = False
    return output


def detectCorruption(tmpPath, orgPath):
    imageNumber = 0
    imageSmaller = 0
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
                    imageNumber += 1
                    if options.profileData[1][0] > img.size[0] and options.profileData[1][1] > img.size[1]:
                        imageSmaller += 1
                except Exception as err:
                    rmtree(os.path.join(tmpPath, '..', '..'), True)
                    if 'decoder' in str(err) and 'not available' in str(err):
                        raise RuntimeError('Pillow was compiled without JPG and/or PNG decoder.')
                    else:
                        raise RuntimeError('Image file %s is corrupted.' % pathOrg)
            else:
                saferRemove(os.path.join(root, name))
    if imageSmaller > imageNumber * 0.25 and not options.upscale and not options.stretch:
        print("WARNING: More than 1/4 of images are smaller than target device resolution. "
              "Consider enabling stretching or upscaling to improve readability.")
        if GUI:
            GUI.addMessage.emit('More than 1/4 of images are smaller than target device resolution.', 'warning', False)
            GUI.addMessage.emit('Consider enabling stretching or upscaling to improve readability.', 'warning', False)
            GUI.addMessage.emit('', '', False)


def createNewTome():
    tomePathRoot = mkdtemp('', 'KCC-')
    tomePath = os.path.join(tomePathRoot, 'OEBPS', 'Images')
    os.makedirs(tomePath)
    return tomePath, tomePathRoot


def slugify(value):
    value = slugifyExt(value)
    value = sub(r'0*([0-9]{4,})', r'\1', sub(r'([0-9]+)', r'0000\1', value, count=2))
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
    psr = OptionParser(usage="Usage: kcc-c2e [options] comic_file|comic_folder", add_help_option=False)

    mainOptions = OptionGroup(psr, "MAIN")
    processingOptions = OptionGroup(psr, "PROCESSING")
    outputOptions = OptionGroup(psr, "OUTPUT SETTINGS")
    customProfileOptions = OptionGroup(psr, "CUSTOM PROFILE")
    otherOptions = OptionGroup(psr, "OTHER")

    mainOptions.add_option("-p", "--profile", action="store", dest="profile", default="KV",
                           help="Device profile (Available options: K1, K2, K3, K45, KDX, KPW, KV, KoMT, KoG, KoGHD,"
                                " KoA, KoAHD, KoAH2O, KoAO) [Default=KV]")
    mainOptions.add_option("-m", "--manga-style", action="store_true", dest="righttoleft", default=False,
                           help="Manga style (right-to-left reading and splitting)")
    mainOptions.add_option("-2", "--two-panel", action="store_true", dest="autoscale", default=False,
                           help="Display two not four panels in Panel View mode")
    mainOptions.add_option("-w", "--webtoon", action="store_true", dest="webtoon", default=False,
                           help="Webtoon processing mode"),

    outputOptions.add_option("-o", "--output", action="store", dest="output", default=None,
                             help="Output generated file to specified directory or file")
    outputOptions.add_option("-t", "--title", action="store", dest="title", default="defaulttitle",
                             help="Comic title [Default=filename or directory name]")
    outputOptions.add_option("-f", "--format", action="store", dest="format", default="Auto",
                             help="Output format (Available options: Auto, MOBI, EPUB, CBZ) [Default=Auto]")
    outputOptions.add_option("-b", "--batchsplit", type="int", dest="batchsplit", default="0",
                             help="Split output into multiple files. 0: Don't split 1: Automatic mode "
                                  "2: Consider every subdirectory as separate volume [Default=0]")

    processingOptions.add_option("-u", "--upscale", action="store_true", dest="upscale", default=False,
                                 help="Resize images smaller than device's resolution")
    processingOptions.add_option("-s", "--stretch", action="store_true", dest="stretch", default=False,
                                 help="Stretch images to device's resolution")
    processingOptions.add_option("-r", "--splitter", type="int", dest="splitter", default="0",
                                 help="Double page parsing mode. 0: Split 1: Rotate 2: Both [Default=0]")
    processingOptions.add_option("-g", "--gamma", type="float", dest="gamma", default="0.0",
                                 help="Apply gamma correction to linearize the image [Default=Auto]")
    processingOptions.add_option("-c", "--cropping", type="int", dest="cropping", default="2",
                                 help="Set cropping mode. 0: Disabled 1: Margins 2: Margins + page numbers [Default=2]")
    processingOptions.add_option("--cp", "--croppingpower", type="float", dest="croppingp", default="1.0",
                                 help="Set cropping power [Default=1.0]")
    processingOptions.add_option("--blackborders", action="store_true", dest="black_borders", default=False,
                                 help="Disable autodetection and force black borders")
    processingOptions.add_option("--whiteborders", action="store_true", dest="white_borders", default=False,
                                 help="Disable autodetection and force white borders")
    processingOptions.add_option("--forcecolor", action="store_true", dest="forcecolor", default=False,
                                 help="Don't convert images to grayscale")
    processingOptions.add_option("--forcepng", action="store_true", dest="forcepng", default=False,
                                 help="Create PNG files instead JPEG")

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
    options.iskindle = False
    options.bordersColor = None
    if options.format == 'Auto':
        if options.profile in ['K1', 'K2', 'K3', 'K45', 'KPW', 'KV']:
            options.format = 'MOBI'
        elif options.profile in ['OTHER', 'KoMT', 'KoG', 'KoGHD', 'KoA', 'KoAHD', 'KoAH2O', 'KoAO']:
            options.format = 'EPUB'
        elif options.profile in ['KDX']:
            options.format = 'CBZ'
    if options.profile in ['K1', 'K2', 'K3', 'K45', 'KPW', 'KV']:
        options.iskindle = True
    if options.white_borders:
        options.bordersColor = 'white'
    if options.black_borders:
        options.bordersColor = 'black'
    # Splitting MOBI is not optional
    if options.format == 'MOBI' and options.batchsplit != 2:
        options.batchsplit = 1
    # Older Kindle don't need higher resolution files due lack of Panel View.
    if options.profile == 'K1' or options.profile == 'K2' or options.profile == 'K3' or options.profile == 'KDX':
        options.panelview = False
    # Webtoon mode mandatory options
    if options.webtoon:
        options.panelview = False
        options.righttoleft = False
        options.upscale = True
    # Disable all Kindle features for other e-readers
    if options.profile == 'OTHER':
        options.panelview = False
    if 'Ko' in options.profile:
        options.panelview = False
    # CBZ files on Kindle DX/DXG support higher resolution
    if options.profile == 'KDX' and options.format == 'CBZ':
        options.customheight = 1200
    # Override profile data
    if options.customwidth != 0 or options.customheight != 0:
        X = image.ProfileData.Profiles[options.profile][1][0]
        Y = image.ProfileData.Profiles[options.profile][1][1]
        if options.customwidth != 0:
            X = options.customwidth
        if options.customheight != 0:
            Y = options.customheight
        newProfile = ("Custom", (int(X), int(Y)), image.ProfileData.Palette16,
                      image.ProfileData.Profiles[options.profile][3])
        image.ProfileData.Profiles["Custom"] = newProfile
        options.profile = "Custom"
    options.profileData = image.ProfileData.Profiles[options.profile]


def checkTools(source):
    source = source.upper()
    if source.endswith('.CBR') or source.endswith('.RAR'):
        rarExitCode = Popen('unrar', stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
        rarExitCode = rarExitCode.wait()
        if rarExitCode != 0 and rarExitCode != 7:
            print('ERROR: UnRAR is missing!')
            exit(1)
    elif source.endswith('.CB7') or source.endswith('.7Z'):
        sevenzaExitCode = Popen('7za', stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
        sevenzaExitCode = sevenzaExitCode.wait()
        if sevenzaExitCode != 0 and sevenzaExitCode != 7:
            print('ERROR: 7za is missing!')
            exit(1)
    if options.format == 'MOBI':
        kindleGenExitCode = Popen('kindlegen -locale en', stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
        if kindleGenExitCode.wait() != 0:
            print('ERROR: KindleGen is missing!')
            exit(1)


def checkPre(source):
    # Make sure that all temporary files are gone
    for root, dirs, _ in walkLevel(gettempdir(), 0):
        for tempdir in dirs:
            if tempdir.startswith('KCC-'):
                rmtree(os.path.join(root, tempdir), True)
    # Make sure that target directory is writable
    if os.path.isdir(source):
        src = os.path.abspath(os.path.join(source, '..'))
    else:
        src = os.path.dirname(source)
    try:
        with TemporaryFile(prefix='KCC-', dir=src):
            pass
    except:
        raise UserWarning("Target directory is not writable.")


def makeBook(source, qtGUI=None):
    global GUI
    GUI = qtGUI
    if GUI:
        GUI.progressBarTick.emit('1')
    else:
        checkTools(source)
    checkPre(source)
    print("Preparing source images...")
    path = getWorkFolder(source)
    print("Checking images...")
    getComicInfo(os.path.join(path, "OEBPS", "Images"), source)
    detectCorruption(os.path.join(path, "OEBPS", "Images"), source)
    if options.webtoon:
        if image.ProfileData.Profiles[options.profile][1][1] > 1024:
            y = 1024
        else:
            y = image.ProfileData.Profiles[options.profile][1][1]
        comic2panel.main(['-y ' + str(y), '-i', '-m', path], qtGUI)
    print("Processing images...")
    if GUI:
        GUI.progressBarTick.emit('Processing images')
    imgDirectoryProcessing(os.path.join(path, "OEBPS", "Images"))
    if GUI:
        GUI.progressBarTick.emit('1')
    chapterNames = sanitizeTree(os.path.join(path, 'OEBPS', 'Images'))
    if 'Ko' in options.profile and options.format == 'CBZ':
        sanitizeTreeKobo(os.path.join(path, 'OEBPS', 'Images'))
    if options.batchsplit > 0:
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
    options.covers = []
    for tome in tomes:
        options.uuid = str(uuid4())
        if len(tomes) > 9:
            tomeNumber += 1
            options.title = options.baseTitle + ' [' + str(tomeNumber).zfill(2) + '/' + str(len(tomes)).zfill(2) + ']'
        elif len(tomes) > 1:
            tomeNumber += 1
            options.title = options.baseTitle + ' [' + str(tomeNumber) + '/' + str(len(tomes)) + ']'
        if options.format == 'CBZ':
            print("Creating CBZ file...")
            if len(tomes) > 1:
                filepath.append(getOutputFilename(source, options.output, '.cbz', ' ' + str(tomeNumber)))
            else:
                filepath.append(getOutputFilename(source, options.output, '.cbz', ''))
            makeZIP(tome + '_comic', os.path.join(tome, "OEBPS", "Images"))
        else:
            print("Creating EPUB file...")
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
        print("Creating MOBI files...")
        work = []
        for i in filepath:
            work.append([i])
        output = makeMOBI(work, GUI)
        for errors in output:
            if errors[0] != 0:
                print('Error: KindleGen failed to create MOBI!')
                print(errors)
                return filepath
        k = kindle.Kindle()
        if k.path and k.coverSupport:
            print("Kindle detected. Uploading covers...")
        for i in filepath:
            output = makeMOBIFix(i, options.covers[filepath.index(i)][1])
            if not output[0]:
                print('Error: Failed to tweak KindleGen output!')
                return filepath
            else:
                saferRemove(i.replace('.epub', '.mobi') + '_toclean')
            if k.path and k.coverSupport:
                options.covers[filepath.index(i)][0].saveToKindle(k, options.covers[filepath.index(i)][1])
    return filepath


def makeMOBIFix(item, uuid):
    saferRemove(item)
    mobiPath = item.replace('.epub', '.mobi')
    move(mobiPath, mobiPath + '_toclean')
    try:
        dualmetafix.DualMobiMetaFix(mobiPath + '_toclean', mobiPath, bytes(uuid, 'UTF-8'))
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
                           stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
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
                if ":I1036: Mobi file built successfully" in line:
                    output.terminate()
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
    availableMemory = virtual_memory().total / 1000000000
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
