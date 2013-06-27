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
__version__ = '3.0'
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import os
import sys
import tempfile
import re
import stat
import string
from shutil import move
from shutil import copyfile
from shutil import copytree
from shutil import rmtree
from shutil import make_archive
from optparse import OptionParser
from multiprocessing import Pool, Queue, freeze_support
try:
    from PyQt4 import QtCore
except ImportError:
    QtCore = None
import image
import cbxarchive
import pdfjpgextract


def buildHTML(path, imgfile):
    filename = getImageFileName(imgfile)
    if filename is not None:
        # All files marked with this sufix need horizontal Panel View.
        if "_kccrotated" in str(filename):
            rotate = True
        else:
            rotate = False
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
        f = open(htmlfile, "w")
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
        if options.panelview:
            if rotate:
                if options.righttoleft:
                    f.writelines(["<div id=\"BoxTL\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxTL-Panel-Parent\", \"ordinal\":1}'></a></div>\n",
                                  "<div id=\"BoxTR\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxTR-Panel-Parent\", \"ordinal\":3}'></a></div>\n",
                                  "<div id=\"BoxBL\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxBL-Panel-Parent\", \"ordinal\":2}'></a></div>\n",
                                  "<div id=\"BoxBR\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify="
                                  "'{\"targetId\":\"BoxBR-Panel-Parent\", \"ordinal\":4}'></a></div>\n"
                                  ])
                else:
                    f.writelines(["<div id=\"BoxTL\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxTL-Panel-Parent\", \"ordinal\":2}'></a></div>\n",
                                  "<div id=\"BoxTR\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxTR-Panel-Parent\", \"ordinal\":4}'></a></div>\n",
                                  "<div id=\"BoxBL\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxBL-Panel-Parent\", \"ordinal\":1}'></a></div>\n",
                                  "<div id=\"BoxBR\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify="
                                  "'{\"targetId\":\"BoxBR-Panel-Parent\", \"ordinal\":3}'></a></div>\n"
                                  ])
            else:
                if options.righttoleft:
                    f.writelines(["<div id=\"BoxTL\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxTL-Panel-Parent\", \"ordinal\":2}'></a></div>\n",
                                  "<div id=\"BoxTR\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxTR-Panel-Parent\", \"ordinal\":1}'></a></div>\n",
                                  "<div id=\"BoxBL\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxBL-Panel-Parent\", \"ordinal\":4}'></a></div>\n",
                                  "<div id=\"BoxBR\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify="
                                  "'{\"targetId\":\"BoxBR-Panel-Parent\", \"ordinal\":3}'></a></div>\n"
                                  ])
                else:
                    f.writelines(["<div id=\"BoxTL\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxTL-Panel-Parent\", \"ordinal\":1}'></a></div>\n",
                                  "<div id=\"BoxTR\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxTR-Panel-Parent\", \"ordinal\":2}'></a></div>\n",
                                  "<div id=\"BoxBL\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify=",
                                  "'{\"targetId\":\"BoxBL-Panel-Parent\", \"ordinal\":3}'></a></div>\n",
                                  "<div id=\"BoxBR\"><a class=\"app-amzn-magnify\" data-app-amzn-magnify="
                                  "'{\"targetId\":\"BoxBR-Panel-Parent\", \"ordinal\":4}'></a></div>\n"
                                  ])
            if options.quality == 2:
                imgfilepv = string.split(imgfile, ".")
                imgfilepv[0] += "_kcchq"
                imgfilepv = string.join(imgfilepv, ".")
            else:
                imgfilepv = imgfile
            f.writelines(["<div id=\"BoxTL-Panel-Parent\" class=\"target-mag-parent\"><div id=\"BoxTL-Panel\" class=\"",
                          "target-mag\"><img src=\"", "../" * backref, "Images/", postfix, imgfilepv, "\" alt=\"",
                          imgfilepv, "\"/></div></div>\n",
                          "<div id=\"BoxTR-Panel-Parent\" class=\"target-mag-parent\"><div id=\"BoxTR-Panel\" class=\"",
                          "target-mag\"><img src=\"", "../" * backref, "Images/", postfix, imgfilepv, "\" alt=\"",
                          imgfilepv, "\"/></div></div>\n",
                          "<div id=\"BoxBL-Panel-Parent\" class=\"target-mag-parent\"><div id=\"BoxBL-Panel\" class=\"",
                          "target-mag\"><img src=\"", "../" * backref, "Images/", postfix, imgfilepv, "\" alt=\"",
                          imgfilepv, "\"/></div></div>\n",
                          "<div id=\"BoxBR-Panel-Parent\" class=\"target-mag-parent\"><div id=\"BoxBR-Panel\" class=\"",
                          "target-mag\"><img src=\"", "../" * backref, "Images/", postfix, imgfilepv, "\" alt=\"",
                          imgfilepv, "\"/></div></div>\n"
                          ])
        f.writelines(["</div>\n</body>\n</html>"])
        f.close()
        return path, imgfile


def buildBlankHTML(path):
    f = open(os.path.join(path, 'blank.html'), "w")
    f.writelines(["<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\" ",
                  "\"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">\n",
                  "<html xmlns=\"http://www.w3.org/1999/xhtml\">\n",
                  "<head>\n",
                  "<title></title>\n",
                  "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>\n",
                  "</head>\n",
                  "<body>\n",
                  "</body>\n",
                  "</html>"])
    f.close()
    return path


def buildNCX(dstdir, title, chapters):
    from uuid import uuid4
    options.uuid = str(uuid4())
    options.uuid = options.uuid.encode('utf-8')
    ncxfile = os.path.join(dstdir, 'OEBPS', 'toc.ncx')
    f = open(ncxfile, "w")
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
                  "<!DOCTYPE ncx PUBLIC \"-//NISO//DTD ncx 2005-1//EN\" ",
                  "\"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd\">\n",
                  "<ncx version=\"2005-1\" xml:lang=\"en-US\" xmlns=\"http://www.daisy.org/z3986/2005/ncx/\">\n",
                  "<head>\n",
                  "<meta name=\"dtb:uid\" content=\"", options.uuid, "\"/>\n",
                  "<meta name=\"dtb:depth\" content=\"2\"/>\n",
                  "<meta name=\"dtb:totalPageCount\" content=\"0\"/>\n",
                  "<meta name=\"dtb:maxPageNumber\" content=\"0\"/>\n",
                  "</head>\n",
                  "<docTitle><text>", title, "</text></docTitle>\n",
                  "<navMap>"
                  ])
    for chapter in chapters:
        folder = chapter[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\')
        title = os.path.basename(folder)
        filename = getImageFileName(os.path.join(folder, chapter[1]))
        f.write("<navPoint id=\"" + folder.replace('/', '_').replace('\\', '_') + "\"><navLabel><text>" + title
                + "</text></navLabel><content src=\"" + filename[0].replace("\\", "/") + ".html\"/></navPoint>\n")
    f.write("</navMap>\n</ncx>")
    f.close()
    return


def buildOPF(dstdir, title, filelist, cover=None):
    opffile = os.path.join(dstdir, 'OEBPS', 'content.opf')
    profilelabel, deviceres, palette, gamma, panelviewsize = options.profileData
    imgres = str(deviceres[0]) + "x" + str(deviceres[1])
    if options.righttoleft:
        writingmode = "horizontal-rl"
        facing = "right"
        facing1 = "right"
        facing2 = "left"
    else:
        writingmode = "horizontal-lr"
        facing = "left"
        facing1 = "left"
        facing2 = "right"
    f = open(opffile, "w")
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
                  "<package version=\"2.0\" unique-identifier=\"BookID\" xmlns=\"http://www.idpf.org/2007/opf\">\n",
                  "<metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\" ",
                  "xmlns:opf=\"http://www.idpf.org/2007/opf\">\n",
                  "<dc:title>", title, "</dc:title>\n",
                  "<dc:language>en-US</dc:language>\n",
                  "<dc:identifier id=\"BookID\" opf:scheme=\"UUID\">", options.uuid, "</dc:identifier>\n",
                  "<meta name=\"RegionMagnification\" content=\"true\"/>\n",
                  "<meta name=\"cover\" content=\"cover\"/>\n",
                  "<meta name=\"book-type\" content=\"comic\"/>\n",
                  "<meta name=\"zero-gutter\" content=\"true\"/>\n",
                  "<meta name=\"zero-margin\" content=\"true\"/>\n",
                  "<meta name=\"fixed-layout\" content=\"true\"/>\n"
                  ])
    if options.landscapemode:
        f.writelines(["<meta name=\"rendition:orientation\" content=\"auto\"/>\n",
                      "<meta name=\"orientation-lock\" content=\"none\"/>\n"])
    else:
        f.writelines(["<meta name=\"rendition:orientation\" content=\"portrait\"/>\n",
                      "<meta name=\"orientation-lock\" content=\"portrait\"/>\n"])
    f.writelines(["<meta name=\"original-resolution\" content=\"", imgres, "\"/>\n",
                  "<meta name=\"primary-writing-mode\" content=\"", writingmode, "\"/>\n",
                  "<meta name=\"rendition:layout\" content=\"pre-paginated\"/>\n",
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
        f.write("<item id=\"page_" + uniqueid + "\" href=\""
                + folder.replace('Images', 'Text') + "/" + filename[0]
                + ".html\" media-type=\"application/xhtml+xml\"/>\n")
        if '.png' == filename[1]:
            mt = 'image/png'
        else:
            mt = 'image/jpeg'
        f.write("<item id=\"img_" + uniqueid + "\" href=\"" + folder + "/" + path[1] + "\" media-type=\""
                + mt + "\"/>\n")
    if options.landscapemode and splitCount > 0:
        splitCountUsed = 1
        while splitCountUsed <= splitCount:
            f.write("<item id=\"blank-page" + str(splitCountUsed) +
                    "\" href=\"Text/blank.html\" media-type=\"application/xhtml+xml\"/>\n")
            splitCountUsed += 1
    f.write("<item id=\"css\" href=\"Text/style.css\" media-type=\"text/css\"/>\n")
    f.write("</manifest>\n<spine toc=\"ncx\">\n")
    splitCountUsed = 1
    for entry in reflist:
        if "_kcca" in str(entry):
            # noinspection PyRedundantParentheses
            if ((options.righttoleft and facing == 'left') or (not options.righttoleft and facing == 'right')) and\
                    options.landscapemode:
                f.write("<itemref idref=\"blank-page" + str(splitCountUsed) + "\" properties=\"layout-blank\"/>\n")
                splitCountUsed += 1
            if options.landscapemode:
                f.write("<itemref idref=\"page_" + entry + "\" properties=\"page-spread-" + facing1 + "\"/>\n")
            else:
                f.write("<itemref idref=\"page_" + entry + "\"/>\n")
        elif "_kccb" in str(entry):
            if options.landscapemode:
                f.write("<itemref idref=\"page_" + entry + "\" properties=\"page-spread-" + facing2 + "\"/>\n")
            else:
                f.write("<itemref idref=\"page_" + entry + "\"/>\n")
            if options.righttoleft:
                facing = "right"
            else:
                facing = "left"
        else:
            if options.landscapemode:
                f.write("<itemref idref=\"page_" + entry + "\" properties=\"page-spread-" + facing + "\"/>\n")
            else:
                f.write("<itemref idref=\"page_" + entry + "\"/>\n")
            if facing == 'right':
                facing = 'left'
            else:
                facing = 'right'
    f.write("</spine>\n<guide>\n</guide>\n</package>\n")
    f.close()
    os.mkdir(os.path.join(dstdir, 'META-INF'))
    f = open(os.path.join(dstdir, 'mimetype'), 'w')
    f.write('application/epub+zip')
    f.close()
    f = open(os.path.join(dstdir, 'META-INF', 'container.xml'), 'w')
    f.writelines(["<?xml version=\"1.0\"?>\n",
                  "<container version=\"1.0\" xmlns=\"urn:oasis:names:tc:opendocument:xmlns:container\">\n",
                  "<rootfiles>\n",
                  "<rootfile full-path=\"OEBPS/content.opf\" media-type=\"application/oebps-package+xml\"/>\n",
                  "</rootfiles>\n",
                  "</container>"])
    f.close()
    return


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


def applyImgOptimization(img, isSplit, toRight, options, overrideQuality=5):
    img.cropWhiteSpace(10.0)
    if options.cutpagenumbers:
        img.cutPageNumber()
    if overrideQuality != 5:
        img.resizeImage(options.upscale, options.stretch, options.black_borders, isSplit, toRight,
                        options.landscapemode, overrideQuality)
    else:
        img.resizeImage(options.upscale, options.stretch, options.black_borders, isSplit, toRight,
                        options.landscapemode, options.quality)
    img.optimizeImage(options.gamma)
    if options.forcepng and not options.forcecolor:
        img.quantizeImage()


def dirImgProcess(path, origPath):
    global options, splitCount
    work = []
    pagenumber = 0
    pagenumbermodifier = 0
    queue = Queue()
    pool = Pool(None, fileImgProcess_init, [queue, options])
    for (dirpath, dirnames, filenames) in os.walk(path):
        for afile in filenames:
            if getImageFileName(afile) is not None:
                pagenumber += 1
                work.append([afile, dirpath, pagenumber])
    if GUI:
        GUI.emit(QtCore.SIGNAL("progressBarTick"), pagenumber)
    if len(work) > 0:
        splitpages = pool.map_async(func=fileImgProcess, iterable=work)
        pool.close()
        if GUI:
            while not splitpages.ready():
                # noinspection PyBroadException
                try:
                    queue.get(True, 1)
                except:
                    pass
                GUI.emit(QtCore.SIGNAL("progressBarTick"))
        pool.join()
        queue.close()
        try:
            splitpages = splitpages.get()
        except:
            rmtree(path)
            raise RuntimeError("One of workers crashed. Cause: " + str(sys.exc_info()[1]))
        splitpages = filter(None, splitpages)
        splitpages.sort()
        for page in splitpages:
            if (page + pagenumbermodifier) % 2 == 0:
                splitCount += 1
                pagenumbermodifier += 1
            pagenumbermodifier += 1
    else:
        rmtree(path)
        raise UserWarning("Empty directory: " + origPath)


def fileImgProcess_init(queue, options):
    fileImgProcess.queue = queue
    fileImgProcess.options = options


# noinspection PyUnresolvedReferences
def fileImgProcess(work):
    afile = work[0]
    dirpath = work[1]
    pagenumber = work[2]
    options = fileImgProcess.options
    output = None
    if options.verbose:
        print "Optimizing " + afile + " for " + options.profile
    else:
        print ".",
    fileImgProcess.queue.put(".")
    img = image.ComicPage(os.path.join(dirpath, afile), options.profileData)
    if options.quality == 2:
        wipe = False
    else:
        wipe = True
    if options.nosplitrotate:
        split = None
    else:
        split = img.splitPage(dirpath, options.righttoleft, options.rotate)
    if split is not None and split is not "R":
        if options.verbose:
            print "Splitted " + afile
        if options.righttoleft:
            toRight1 = False
            toRight2 = True
        else:
            toRight1 = True
            toRight2 = False
        output = pagenumber
        img0 = image.ComicPage(split[0], options.profileData)
        applyImgOptimization(img0, True, toRight1, options)
        img0.saveToDir(dirpath, options.forcepng, options.forcecolor, wipe)
        img1 = image.ComicPage(split[1], options.profileData)
        applyImgOptimization(img1, True, toRight2, options)
        img1.saveToDir(dirpath, options.forcepng, options.forcecolor, wipe)
        if options.quality == 2:
            img3 = image.ComicPage(split[0], options.profileData)
            applyImgOptimization(img3, True, toRight1, options, 0)
            img3.saveToDir(dirpath, options.forcepng, options.forcecolor, True)
            img4 = image.ComicPage(split[1], options.profileData)
            applyImgOptimization(img4, True, toRight2, options, 0)
            img4.saveToDir(dirpath, options.forcepng, options.forcecolor, True)
    else:
        applyImgOptimization(img, False, False, options)
        img.saveToDir(dirpath, options.forcepng, options.forcecolor, wipe, split)
        if options.quality == 2:
            img2 = image.ComicPage(os.path.join(dirpath, afile), options.profileData)
            if split == "R":
                img2.image = img2.image.rotate(90)
            applyImgOptimization(img2, False, False, options, 0)
            img2.saveToDir(dirpath, options.forcepng, options.forcecolor, True, split)
    return output


def genEpubStruct(path):
    global options
    filelist = []
    chapterlist = []
    cover = None
    _, deviceres, _, _, panelviewsize = options.profileData
    sanitizeTree(os.path.join(path, 'OEBPS', 'Images'))
    os.mkdir(os.path.join(path, 'OEBPS', 'Text'))
    f = open(os.path.join(path, 'OEBPS', 'Text', 'style.css'), 'w')
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
                  "}\n",
                  "#BoxTL-Panel {\n",
                  "top: 0;\n",
                  "left: 0;\n",
                  "height: 100%;\n",
                  "width: 100%;\n",
                  "}\n",
                  "#BoxTL-Panel img {\n",
                  "top: 0%;\n",
                  "left: 0%;\n",
                  "}\n",
                  "#BoxTR-Panel {\n",
                  "top: 0;\n",
                  "right: 0;\n",
                  "height: 100%;\n",
                  "width: 100%;\n",
                  "}\n",
                  "#BoxTR-Panel img {\n",
                  "top: 0%;\n",
                  "right: 0%;\n",
                  "}\n",
                  "#BoxBL-Panel {\n",
                  "bottom: 0;\n",
                  "left: 0;\n",
                  "height: 100%;\n",
                  "width: 100%;\n",
                  "}\n",
                  "#BoxBL-Panel img {\n",
                  "bottom: 0%;\n",
                  "left: 0%;\n",
                  "}\n",
                  "#BoxBR-Panel {\n",
                  "bottom: 0;\n",
                  "right: 0;\n",
                  "height: 100%;\n",
                  "width: 100%;\n",
                  "}\n",
                  "#BoxBR-Panel img {\n",
                  "bottom: 0%;\n",
                  "right: 0%;\n",
                  "}"
                  ])
    f.close()
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(path, 'OEBPS', 'Images')):
        chapter = False
        for afile in filenames:
            filename = getImageFileName(afile)
            if filename is not None and not "_kcchq" in filename[0]:
                filelist.append(buildHTML(dirpath, afile))
                if not chapter:
                    chapterlist.append((dirpath.replace('Images', 'Text'), filelist[-1][1]))
                    chapter = True
                if cover is None:
                    cover = os.path.join(os.path.join(path, 'OEBPS', 'Images'),
                                         'cover' + getImageFileName(filelist[-1][1])[1])
                    copyfile(os.path.join(filelist[-1][0], filelist[-1][1]), cover)
    buildNCX(path, options.title, chapterlist)
    # ensure we're sorting files alphabetically
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    filelist.sort(key=lambda name: (alphanum_key(name[0].lower()), alphanum_key(name[1].lower())))
    buildOPF(path, options.title, filelist, cover)
    if options.landscapemode and splitCount > 0:
        filelist.append(buildBlankHTML(os.path.join(path, 'OEBPS', 'Text')))


def getWorkFolder(afile):
    workdir = tempfile.mkdtemp()
    if os.path.isdir(afile):
        try:
            os.rmdir(workdir)   # needed for copytree() fails if dst already exists
            fullPath = os.path.join(workdir, 'OEBPS', 'Images')
            copytree(afile, fullPath)
            sanitizeTreeBeforeConversion(fullPath)
            return workdir
        except OSError:
            rmtree(workdir)
            raise
    elif afile.lower().endswith('.pdf'):
        pdf = pdfjpgextract.PdfJpgExtract(afile)
        path = pdf.extract()
    else:
        cbx = cbxarchive.CBxArchive(afile)
        if cbx.isCbxFile():
            try:
                path = cbx.extract(workdir)
            except OSError:
                rmtree(workdir)
                print 'Unrar not found, please download from ' + \
                      'http://www.rarlab.com/download.htm and put into your PATH.'
                sys.exit(21)
        else:
            rmtree(workdir)
            raise TypeError
    move(path, path + "_temp")
    move(path + "_temp", os.path.join(path, 'OEBPS', 'Images'))
    return path


def slugify(value):
    # Normalizes string, converts to lowercase, removes non-alpha characters,
    # and converts spaces to hyphens.
    import unicodedata
    value = unicodedata.normalize('NFKD', unicode(value, 'latin1')).encode('ascii', 'ignore')
    value = re.sub('[^\w\s\.-]', '', value).strip().lower()
    value = re.sub('[-\.\s]+', '-', value)
    value = re.sub(r'([0-9]+)', r'00000\1', value)
    value = re.sub(r'0*([0-9]{6,})', r'\1', value)
    return value


def sanitizeTree(filetree):
    for root, dirs, files in os.walk(filetree, False):
        for name in files:
            if name.startswith('.') or name.lower() == 'thumbs.db':
                os.remove(os.path.join(root, name))
            else:
                splitname = os.path.splitext(name)
                slugified = slugify(splitname[0])
                while os.path.exists(os.path.join(root, slugified + splitname[1])):
                    slugified += "1"
                os.rename(os.path.join(root, name), os.path.join(root, slugified + splitname[1]))
        for name in dirs:
            if name.startswith('.'):
                os.remove(os.path.join(root, name))
            else:
                os.rename(os.path.join(root, name), os.path.join(root, slugify(name)))


def sanitizeTreeBeforeConversion(filetree):
    for root, dirs, files in os.walk(filetree, False):
        for name in files:
            os.chmod(os.path.join(root, name), stat.S_IWRITE | stat.S_IREAD)
            # Detect corrupted files - Phase 1
            if os.path.getsize(os.path.join(root, name)) == 0:
                os.remove(os.path.join(root, name))
        for name in dirs:
            os.chmod(os.path.join(root, name), stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)


def Copyright():
    print ('comic2ebook v%(__version__)s. '
           'Written 2013 by Ciro Mattia Gonano and Pawel Jastrzebski.' % globals())


def Usage():
    print "Generates EPUB/CBZ comic ebook from a bunch of images."
    parser.print_help()


def main(argv=None, qtGUI=None):
    global parser, options, epub_path, splitCount, GUI
    usage = "Usage: %prog [options] comic_file|comic_folder"
    parser = OptionParser(usage=usage, version=__version__)
    parser.add_option("-p", "--profile", action="store", dest="profile", default="KHD",
                      help="Device profile (Choose one among K1, K2, K3, K4NT, K4T, KDX, KDXG, KHD, KF, KFHD, KFHD8) "
                      "[Default=KHD]")
    parser.add_option("-t", "--title", action="store", dest="title", default="defaulttitle",
                      help="Comic title [Default=filename]")
    parser.add_option("-m", "--manga-style", action="store_true", dest="righttoleft", default=False,
                      help="Manga style (Right-to-left reading and splitting) [Default=False]")
    parser.add_option("--quality", type="int", dest="quality", default="0",
                      help="Output quality. 0 - Normal 1 - High 2 - Ultra [Default=0]")
    parser.add_option("-c", "--cbz-output", action="store_true", dest="cbzoutput", default=False,
                      help="Outputs a CBZ archive and does not generate EPUB")
    parser.add_option("--noprocessing", action="store_false", dest="imgproc", default=True,
                      help="Do not apply image preprocessing (Page splitting and optimizations) [Default=True]")
    parser.add_option("--forcepng", action="store_true", dest="forcepng", default=False,
                      help="Create PNG files instead JPEG (For non-Kindle devices) [Default=False]")
    parser.add_option("--gamma", type="float", dest="gamma", default="0.0",
                      help="Apply gamma correction to linearize the image [Default=Auto]")
    parser.add_option("--upscale", action="store_true", dest="upscale", default=False,
                      help="Resize images smaller than device's resolution [Default=False]")
    parser.add_option("--stretch", action="store_true", dest="stretch", default=False,
                      help="Stretch images to device's resolution [Default=False]")
    parser.add_option("--blackborders", action="store_true", dest="black_borders", default=False,
                      help="Use black borders instead of white ones when not stretching and ratio "
                      + "is not like the device's one [Default=False]")
    parser.add_option("--rotate", action="store_true", dest="rotate", default=False,
                      help="Rotate landscape pages instead of splitting them [Default=False]")
    parser.add_option("--nosplitrotate", action="store_true", dest="nosplitrotate", default=False,
                      help="Disable splitting and rotation [Default=False]")
    parser.add_option("--nocutpagenumbers", action="store_false", dest="cutpagenumbers", default=True,
                      help="Do not try to cut page numbering on images [Default=True]")
    parser.add_option("-o", "--output", action="store", dest="output", default=None,
                      help="Output generated file (EPUB or CBZ) to specified directory or file")
    parser.add_option("--forcecolor", action="store_true", dest="forcecolor", default=False,
                      help="Do not convert images to grayscale [Default=False]")
    parser.add_option("--customwidth", type="int", dest="customwidth", default=0,
                      help="Replace screen width provided by device profile [Default=0]")
    parser.add_option("--customheight", type="int", dest="customheight", default=0,
                      help="Replace screen height provided by device profile [Default=0]")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="Verbose output [Default=False]")
    options, args = parser.parse_args(argv)
    checkOptions()
    if qtGUI:
        GUI = qtGUI
        GUI.emit(QtCore.SIGNAL("progressBarTick"), 1)
    else:
        GUI = None
    if len(args) != 1:
        parser.print_help()
        return
    path = getWorkFolder(args[0])
    if options.title == 'defaulttitle':
        options.title = os.path.splitext(os.path.basename(args[0]))[0]
    splitCount = 0
    if options.imgproc:
        print "Processing images..."
        if GUI:
            GUI.emit(QtCore.SIGNAL("progressBarTick"), 'status', 'Processing images')
        dirImgProcess(path + "/OEBPS/Images/", args[0])
    if GUI:
        GUI.emit(QtCore.SIGNAL("progressBarTick"), 1)
    if options.cbzoutput:
        # if CBZ output wanted, compress all images and return filepath
        print "\nCreating CBZ file..."
        filepath = getOutputFilename(args[0], options.output, '.cbz')
        make_archive(path + '_comic', 'zip', path + '/OEBPS/Images')
    else:
        print "\nCreating EPUB structure..."
        genEpubStruct(path)
        # actually zip the ePub
        filepath = getOutputFilename(args[0], options.output, '.epub')
        make_archive(path + '_comic', 'zip', path)
    move(path + '_comic.zip', filepath)
    rmtree(path)
    return filepath


def getOutputFilename(srcpath, wantedname, ext):
    if not ext.startswith('.'):
        ext = '.' + ext
    if wantedname is not None:
        if wantedname.endswith(ext):
            filename = os.path.abspath(wantedname)
        elif os.path.isdir(srcpath):
            filename = os.path.abspath(options.output) + "/" + os.path.basename(srcpath) + ext
        else:
            filename = os.path.abspath(options.output) + "/" \
                       + os.path.basename(os.path.splitext(srcpath)[0]) + ext
    elif os.path.isdir(srcpath):
        filename = srcpath + ext
    else:
        filename = os.path.splitext(srcpath)[0] + ext
    if os.path.isfile(filename):
        filename = os.path.splitext(filename)[0] + '_kcc' + ext
    return filename


def checkOptions():
    global options
    # Landscape mode is only supported by Kindle Touch and Paperwhite.
    if options.profile == 'K4T' or options.profile == 'KHD':
        options.landscapemode = True
    else:
        options.landscapemode = False
    # Older Kindle don't support Virtual Panel View. We providing them configuration that will fake that feature.
    # Ultra quality mode require Real Panel View. Landscape mode don't work correcly without Virtual Panel View.
    if options.profile == 'K3' or options.profile == 'K4NT' or options.quality == 2:
        # Real Panel View
        options.panelview = True
        options.landscapemode = False
    else:
        # Virtual Panel View
        options.panelview = False
    # Disabling grayscale conversion for Kindle Fire family.
    if options.profile == 'KF' or options.profile == 'KFHD' or options.profile == 'KFHD8' or options.forcecolor:
        options.forcecolor = True
    else:
        options.forcecolor = False
    # Mixing vertical and horizontal pages require real Panel View.
    # Landscape mode don't work correcly without Virtual Panel View.
    if options.rotate:
        options.panelview = True
        options.landscapemode = False
    # Older Kindle don't need higher resolution files due lack of Panel View.
    # Kindle Fire family have very high resolution. Bigger images are not needed.
    if options.profile == 'K1' or options.profile == 'K2' or options.profile == 'KDX' or options.profile == 'KDXG'\
            or options.profile == 'KF' or options.profile == 'KFHD' or options.profile == 'KFHD8':
        options.quality = 0
        if options.profile == 'K1' or options.profile == 'K2' or options.profile == 'KDX' or options.profile == 'KDXG':
            options.panelview = False
    # Disable all Kindle features
    if options.profile == 'OTHER':
        options.landscapemode = False
        options.panelview = False
        options.quality = 0
    # Override profile data
    if options.customwidth != 0 or options.customheight != 0:
        X = image.ProfileData.Profiles[options.profile][1][0]
        Y = image.ProfileData.Profiles[options.profile][1][1]
        if options.customwidth != 0:
            X = options.customwidth
        if options.customheight != 0:
            Y = options.customheight
        newProfile = ("Custom", (X, Y), image.ProfileData.Palette16, image.ProfileData.Profiles[options.profile][3],
                      (int(X*1.5), int(Y*1.5)))
        image.ProfileData.Profiles["Custom"] = newProfile
        options.profile = "Custom"
    options.profileData = image.ProfileData.Profiles[options.profile]


def getEpubPath():
    global epub_path
    return epub_path


if __name__ == "__main__":
    freeze_support()
    Copyright()
    main(sys.argv[1:])
    sys.exit(0)
