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
import pathlib
import re
import sys
from argparse import ArgumentParser
from time import perf_counter, strftime, gmtime
from copy import copy
from glob import glob, escape
from re import sub
from stat import S_IWRITE, S_IREAD, S_IEXEC
from typing import List
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from tempfile import mkdtemp, gettempdir, TemporaryFile
from shutil import move, copytree, rmtree, copyfile
from multiprocessing import Pool, cpu_count
from uuid import uuid4
from natsort import os_sort_keygen, os_sorted
from slugify import slugify as slugify_ext
from PIL import Image, ImageFile
from pathlib import Path
from subprocess import STDOUT, PIPE, CalledProcessError
from psutil import virtual_memory, disk_usage
from html import escape as hescape
import pymupdf
import numpy as np

from .shared import getImageFileName, walkSort, walkLevel, sanitizeTrace, subprocess_run, dot_clean
from .comicarchive import SEVENZIP, available_archive_tools
from . import comic2panel
from . import image
from . import comicarchive
from . import dualmetafix
from . import metadata
from . import kindle
from . import __version__

ImageFile.LOAD_TRUNCATED_IMAGES = True
OS_SORT_KEY = os_sort_keygen()

def main(argv=None):
    global options
    parser = makeParser()
    args = parser.parse_args(argv)
    options = copy(args)
    if not argv or options.input == []:
        parser.print_help()
        return 0
    if sys.platform.startswith('win'):
        sources = set([source for option in options.input for source in glob(escape(option))])
    else:
        sources = set(options.input)
    if len(sources) == 0:
        print('No matching files found.')
        return 1
    for source in sources:
        source = source.rstrip('\\').rstrip('/')
        options = copy(args)
        options = checkOptions(options)
        print('Working on ' + source + '...')
        makeBook(source)
    return 0


def buildHTML(path, imgfile, imgfilepath, imgfile2=None):
    key = pathlib.Path(imgfilepath).name
    filename = getImageFileName(imgfile)
    deviceres = options.profileData[1]
    if not options.noprocessing and "Rotated" in options.imgMetadata[key]:
        rotatedPage = True
    else:
        rotatedPage = False
    if not options.noprocessing and "BlackBackground" in options.imgMetadata[key]:
        additionalStyle = 'background-color:#000000;'
    else:
        additionalStyle = ''
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
    imgsize = Image.open(os.path.join(head, "Images", postfix, imgfile)).size
    imgsizeframe = list(imgsize)
    imgsize2 = (0, 0)
    if imgfile2:
        imgsize2 = Image.open(os.path.join(head, "Images", postfix, imgfile2)).size
    imgsizeframe[1] += imgsize2[1]
    if options.hq:
        imgsizeframe = (int(imgsizeframe[0] // 1.5), int(imgsizeframe[1] // 1.5))
    f = open(htmlfile, "w", encoding='UTF-8')
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
                  "<!DOCTYPE html>\n",
                  "<html xmlns=\"http://www.w3.org/1999/xhtml\" xmlns:epub=\"http://www.idpf.org/2007/ops\">\n",
                  "<head>\n",
                  "<title>", hescape(filename[0]), "</title>\n",
                  "<link href=\"", "../" * (backref - 1), "style.css\" type=\"text/css\" rel=\"stylesheet\"/>\n",
                  "<meta name=\"viewport\" "
                  "content=\"width=" + str(imgsizeframe[0]) + ", height=" + str(imgsizeframe[1]) + "\"/>\n"
                  "</head>\n",
                  "<body style=\"" + additionalStyle + "\">\n",
                  "<div style=\"text-align:center;top:" + getTopMargin(deviceres, imgsizeframe) + "%;\">\n",
    ])
    if options.iskindle:
        # this display none div fixes formatting issues with virtual panel mode, for some reason
        f.write('<div style="display:none;">.</div>\n')
    f.write(f'<img width="{imgsize[0]}" height="{imgsize[1]}" src="{"../" * backref}Images/{postfix}{imgfile}"/>\n')
    if imgfile2:
        f.write(f'<img width="{imgsize2[0]}" height="{imgsize2[1]}" src="{"../" * backref}Images/{postfix}{imgfile2}"/>\n')
    f.write("</div>\n")
    if options.iskindle and options.panelview:
        if options.autoscale:
            size = (getPanelViewResolution(imgsize, deviceres))
        else:
            if options.hq:
                size = imgsize
            else:
                size = (int(imgsize[0] * 1.5), int(imgsize[1] * 1.5))
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


def buildNCX(dstdir, title, chapters, chapternames):
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
                  "<docTitle><text>", hescape(title), "</text></docTitle>\n",
                  "<navMap>\n"])
    for chapter in chapters:
        folder = chapter[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\')
        filename = getImageFileName(os.path.join(folder, chapter[1]))
        navID = folder.replace('/', '_').replace('\\', '_')
        if options.comicinfo_chapters:
            title = chapternames[chapter[1]]
            navID = filename[0].replace('/', '_').replace('\\', '_')
        elif os.path.basename(folder) != "Text":
            title = chapternames[os.path.basename(folder)]
        f.write("<navPoint id=\"" + navID + "\"><navLabel><text>" +
                hescape(title) + "</text></navLabel><content src=\"" + filename[0].replace("\\", "/") +
                ".xhtml\"/></navPoint>\n")
    f.write("</navMap>\n</ncx>")
    f.close()


def buildNAV(dstdir, title, chapters, chapternames):
    navfile = os.path.join(dstdir, 'OEBPS', 'nav.xhtml')
    f = open(navfile, "w", encoding='UTF-8')
    f.writelines(["<?xml version=\"1.0\" encoding=\"utf-8\"?>\n",
                  "<!DOCTYPE html>\n",
                  "<html xmlns=\"http://www.w3.org/1999/xhtml\" xmlns:epub=\"http://www.idpf.org/2007/ops\">\n",
                  "<head>\n",
                  "<title>" + hescape(title) + "</title>\n",
                  "<meta charset=\"utf-8\"/>\n",
                  "</head>\n",
                  "<body>\n",
                  "<nav xmlns:epub=\"http://www.idpf.org/2007/ops\" epub:type=\"toc\" id=\"toc\">\n",
                  "<ol>\n"])
    for chapter in chapters:
        folder = chapter[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\')
        filename = getImageFileName(os.path.join(folder, chapter[1]))
        if options.comicinfo_chapters:
            title = chapternames[chapter[1]]
        elif os.path.basename(folder) != "Text":
            title = chapternames[os.path.basename(folder)]
        f.write("<li><a href=\"" + filename[0].replace("\\", "/") + ".xhtml\">" + hescape(title) + "</a></li>\n")
    f.writelines(["</ol>\n",
                  "</nav>\n",
                  "<nav epub:type=\"page-list\">\n",
                  "<ol>\n"])
    for chapter in chapters:
        folder = chapter[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\')
        filename = getImageFileName(os.path.join(folder, chapter[1]))
        if options.comicinfo_chapters:
            title = chapternames[chapter[1]]
        elif os.path.basename(folder) != "Text":
            title = chapternames[os.path.basename(folder)]
        f.write("<li><a href=\"" + filename[0].replace("\\", "/") + ".xhtml\">" + hescape(title) + "</a></li>\n")
    f.write("</ol>\n</nav>\n</body>\n</html>")
    f.close()


def buildOPF(dstdir, title, filelist, originalpath, cover=None):
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
                  "<dc:title>", hescape(title), "</dc:title>\n",
                  "<dc:language>en-US</dc:language>\n",
                  "<dc:identifier id=\"BookID\">urn:uuid:", options.uuid, "</dc:identifier>\n",
                  "<dc:contributor id=\"contributor\">KindleComicConverter-" + __version__ + "</dc:contributor>\n"])
    if len(options.summary) > 0:
        f.writelines(["<dc:description>", hescape(options.summary), "</dc:description>\n"])
    for author in options.authors:
        f.writelines(["<dc:creator>", hescape(author), "</dc:creator>\n"])
    f.writelines(["<meta property=\"dcterms:modified\">" + strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()) + "</meta>\n",
                  "<meta name=\"cover\" content=\"cover\"/>\n"])
    if options.iskindle and options.profile != 'Custom':
        f.writelines(["<meta name=\"fixed-layout\" content=\"true\"/>\n",
                      "<meta name=\"original-resolution\" content=\"",
                      str(deviceres[0]) + "x" + str(deviceres[1]) + "\"/>\n",
                      "<meta name=\"book-type\" content=\"comic\"/>\n",
                      "<meta name=\"primary-writing-mode\" content=\"" + writingmode + "\"/>\n",
                      "<meta name=\"zero-gutter\" content=\"true\"/>\n",
                      "<meta name=\"zero-margin\" content=\"true\"/>\n",
                      "<meta name=\"ke-border-color\" content=\"#FFFFFF\"/>\n",
                      "<meta name=\"ke-border-width\" content=\"0\"/>\n",
                      "<meta name=\"orientation-lock\" content=\"none\"/>\n"])
        if options.kfx:
            f.writelines(["<meta name=\"region-mag\" content=\"false\"/>\n"])
        else:
            f.writelines(["<meta name=\"region-mag\" content=\"true\"/>\n"])
    f.writelines([
        "<meta property=\"rendition:spread\">landscape</meta>\n",
        "<meta property=\"rendition:layout\">pre-paginated</meta>\n"
    ])
    f.writelines(["</metadata>\n<manifest>\n<item id=\"ncx\" href=\"toc.ncx\" ",
                  "media-type=\"application/x-dtbncx+xml\"/>\n",
                  "<item id=\"nav\" href=\"nav.xhtml\" ",
                  "properties=\"nav\" media-type=\"application/xhtml+xml\"/>\n"])
    if cover is not None:
        mt = 'image/jpeg'
        f.write("<item id=\"cover\" href=\"Images/cover.jpg" + "\" media-type=\"" + mt +
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
        elif '.gif' == filename[1]:
            mt = 'image/gif'
        else:
            mt = 'image/jpeg'
        f.write("<item id=\"img_" + str(uniqueid) + "\" href=\"" + folder + "/" + path[1] + "\" media-type=\"" +
                mt + "\"/>\n")
        if 'above' in path[1]:
            bottom = path[1].replace('above', 'below')
            uniqueid = uniqueid.replace('above', 'below')
            f.write("<item id=\"img_" + str(uniqueid) + "\" href=\"" + folder + "/" + bottom + "\" media-type=\"" + mt + "\"/>\n")
    f.write("<item id=\"css\" href=\"Text/style.css\" media-type=\"text/css\"/>\n")


    def pageSpreadProperty(pageside):
        if options.iskindle:
            return "linear=\"yes\" properties=\"page-spread-%s\"" % pageside
        elif options.isKobo:
            return "properties=\"rendition:page-spread-%s\"" % pageside
        else:
            return ""

    if options.righttoleft:
        f.write("</manifest>\n<spine page-progression-direction=\"rtl\" toc=\"ncx\">\n")
        pageside = "right"
    else:
        f.write("</manifest>\n<spine page-progression-direction=\"ltr\" toc=\"ncx\">\n")
        pageside = "left"
    if originalpath.lower().endswith('.pdf'):
        if pageside == "right":
            pageside = "left"
        else:
            pageside = "right"       
    if options.spreadshift:
        if pageside == "right":
            pageside = "left"
        else:
            pageside = "right"
    
    # initial spread order forwards
    page_spread_property_list = []
    for entry in reflist:
        if options.righttoleft:
            if "-kcc-a" in entry or "-kcc-d" in entry:
                page_spread_property_list.append("center")
                pageside = "right"
            elif "-kcc-b" in entry:
                page_spread_property_list.append("right")
                pageside = "right"
            elif "-kcc-c" in entry:
                page_spread_property_list.append("left")
                pageside = "right"
            else:
                page_spread_property_list.append(pageside)
                if pageside == "right":
                    pageside = "left"
                else:
                    pageside = "right"
        else:
            if "-kcc-a" in entry or "-kcc-d" in entry:
                page_spread_property_list.append("center")
                pageside = "left"
            elif "-kcc-b" in entry:
                page_spread_property_list.append("left")
                pageside = "left"
            elif "-kcc-c" in entry:
                page_spread_property_list.append("right")
                pageside = "left"
            else:
                page_spread_property_list.append(pageside)
                if pageside == "right":
                    pageside = "left"
                else:
                    pageside = "right"
    
    # fix spread orders backward
    spread_seen = False
    for i in range(len(reflist) -1, -1, -1):
        entry = reflist[i]
        if "-kcc-x" not in entry:
            spread_seen = True
            if options.righttoleft:
                pageside = "left"
            else:
                pageside = "right"   
        elif spread_seen:
            page_spread_property_list[i] = pageside
            if pageside == "right":
                pageside = "left"
            else:
                pageside = "right"

    for entry, prop in zip(reflist, page_spread_property_list):
        f.write(f'<itemref idref="page_{entry}" {pageSpreadProperty(prop)}/>\n')

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

def buildEPUB(path, chapternames, tomenumber, ischunked, cover: image.Cover, originalpath, len_tomes=0):
    filelist = []
    chapterlist = []
    os.mkdir(os.path.join(path, 'OEBPS', 'Text'))
    f = open(os.path.join(path, 'OEBPS', 'Text', 'style.css'), 'w', encoding='UTF-8')
    f.writelines(["@page {\n",
                  "margin: 0;\n",
                  "}\n",
                  "body {\n",
                  "display: block;\n",
                  "margin: 0;\n",
                  "padding: 0;\n",
                  "}\n",
                  ])
    if options.kindle_scribe_azw3:
        f.writelines([
                    "img {\n",
                    "display: block;\n",
                    "}\n",
                    ])
    if options.iskindle and options.panelview:
        f.writelines(["#PV {\n",
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
    build_html_start = perf_counter()
    cover.save_to_epub(os.path.join(path, 'OEBPS', 'Images', 'cover.jpg'), tomenumber, len_tomes)
    dot_clean(path)
    options.covers.append((cover, options.uuid))
    for dirpath, dirnames, filenames in os.walk(os.path.join(path, 'OEBPS', 'Images')):
        chapter = False
        dirnames, filenames = walkSort(dirnames, filenames)
        for afile in filenames:
            if afile == 'cover.jpg':
                continue
            if 'below' in afile:
                continue
            if not chapter:
                chapterlist.append((dirpath.replace('Images', 'Text'), afile))
                chapter = True
            if 'above' in afile:
                bottom = afile.replace('above', 'below')
                filelist.append(buildHTML(dirpath, afile, os.path.join(dirpath, afile), bottom))
            else:
                filelist.append(buildHTML(dirpath, afile, os.path.join(dirpath, afile)))
    build_html_end = perf_counter()
    print(f"buildHTML: {build_html_end - build_html_start} seconds")
    # Overwrite chapternames if ComicInfo.xml has bookmarks
    if ischunked:
       options.comicinfo_chapters = []

    if options.comicinfo_chapters:
        chapterlist = []

        global_diff = 0
        diff_delta = 0

        # if split
        if options.splitter == 0:
            diff_delta = 1
        # if rotate and split
        elif options.splitter == 2:
            diff_delta = 2

        for aChapter in options.comicinfo_chapters:
            pageid = aChapter[0]
            cur_diff = global_diff
            global_diff = 0

            for x in range(0, pageid + cur_diff + 1):
                if '-kcc-b' in filelist[x][1]:
                    pageid += diff_delta
                    global_diff += diff_delta

            filename = filelist[pageid][1]
            chapterlist.append((filelist[pageid][0].replace('Images', 'Text'), filename))
            chapternames[filename] = aChapter[1]
    buildNCX(path, options.title, chapterlist, chapternames)
    buildNAV(path, options.title, chapterlist, chapternames)
    buildOPF(path, options.title, filelist, originalpath, cover)


def buildPDF(path, title, cover=None, output_file=None):
    """
    Build a PDF file from processed comic images.
    Images are combined into a single PDF optimized for e-readers.
    """
    start = perf_counter()
    # open empty PDF
    with pymupdf.open() as doc:
        doc.set_metadata({'title': title, 'author': options.authors[0]})
        # Stream images to PDF
        for root, dirs, files in os.walk(os.path.join(path, "OEBPS", "Images")):
            files.sort(key=OS_SORT_KEY)
            dirs.sort(key=OS_SORT_KEY)
            for file in files:
                w, h = Image.open(os.path.join(root, file)).size
                page = doc.new_page(width=w, height=h)
                page.insert_image(page.rect, filename=os.path.join(root, file))

        # determine output filename if not provided
        if output_file is None:
            output_file = getOutputFilename(path, None, '.pdf', '')
        
        # Save with optimizations for smaller file size
        doc.save(output_file, deflate=True, garbage=4, clean=True)
    end = perf_counter()
    print(f"MuPDF output: {end-start} sec")
    return output_file


def imgDirectoryProcessing(path):
    global workerPool, workerOutput
    workerPool = Pool(maxtasksperchild=100)
    workerOutput = []
    options.imgMetadata = {}
    work = []
    pagenumber = 0
    for dirpath, _, filenames in os.walk(path):
        for afile in filenames:
            pagenumber += 1
            work.append([afile, dirpath, options])
    if GUI:
        GUI.progressBarTick.emit(str(pagenumber))
    if len(work) > 0:
        img_processing_start = perf_counter()
        for i in work:
            workerPool.apply_async(func=imgFileProcessing, args=(i,), callback=imgFileProcessingTick)
        workerPool.close()
        workerPool.join()
        img_processing_end = perf_counter()
        print(f"imgFileProcessing: {img_processing_end - img_processing_start} seconds")

        # macOS 15 likes to add ._ files after multiprocessing
        dot_clean(path)

        if GUI and not GUI.conversionAlive:
            rmtree(os.path.join(path, '..', '..'), True)
            raise UserWarning("Conversion interrupted.")
        if len(workerOutput) > 0:
            rmtree(os.path.join(path, '..', '..'), True)
            raise RuntimeError("One of workers crashed. Cause: " + workerOutput[0][0], workerOutput[0][1])
    else:
        rmtree(os.path.join(path, '..', '..'), True)
        raise UserWarning("C2E: Source directory is empty.")


def imgFileProcessingTick(output):
    if isinstance(output, tuple):
        workerOutput.append(output)
        workerPool.terminate()
    else:
        for page in output:
            if page is not None:
                options.imgMetadata[page[0]] = page[1]
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
            img = image.ComicPage(opt, *i)
            is_color = (opt.forcecolor and img.color)
            if opt.cropping == 2 and not opt.webtoon:
                img.cropPageNumber(opt.croppingp, opt.croppingm)
            if opt.cropping == 1 and not opt.webtoon:
                img.cropMargin(opt.croppingp, opt.croppingm)
            if opt.interpanelcrop > 0:
                img.cropInterPanelEmptySections("horizontal" if opt.interpanelcrop == 1 else "both")

            img.gammaCorrectImage()

            img.autocontrastImage()
            img.resizeImage()
            img.optimizeForDisplay(opt.eraserainbow, is_color)

            if is_color:
                pass
            elif opt.forcepng:
                img.convertToGrayscale()
                if opt.format != 'PDF':
                    img.quantizeImage()
            else:
                img.convertToGrayscale()
            output.append(img.saveToDir())
        return output
    except Exception:
        return str(sys.exc_info()[1]), sanitizeTrace(sys.exc_info()[2])


def render_page(vector):
    """Render a page range of a document.

    Notes:
        The PyMuPDF document cannot be part of the argument, because that
        cannot be pickled. So we are being passed in just its filename.
        This is no performance issue, because we are a separate process and
        need to open the document anyway.
        Any page-specific function can be processed here - rendering is just
        an example - text extraction might be another.
        The work must however be self-contained: no inter-process communication
        or synchronization is possible with this design.
        Care must also be taken with which parameters are contained in the
        argument, because it will be passed in via pickling by the Pool class.
        So any large objects will increase the overall duration.
    Args:
        vector: a list containing required parameters.
    """
    # recreate the arguments
    idx = vector[0]  # this is the segment number we have to process
    cpu = vector[1]  # number of CPUs
    filename = vector[2]  # document filename
    output_dir = vector[3]
    target_height = vector[4]
    with pymupdf.open(filename) as doc:  # open the document
        num_pages = doc.page_count  # get number of pages

        # pages per segment: make sure that cpu * seg_size >= num_pages!
        seg_size = int(num_pages / cpu + 1)
        seg_from = idx * seg_size  # our first page number
        seg_to = min(seg_from + seg_size, num_pages)  # last page number

        for i in range(seg_from, seg_to):  # work through our page segment
            page = doc[i]
            zoom = target_height / page.rect.height
            mat = pymupdf.Matrix(zoom, zoom)
            # TODO: decide colorspace earlier so later color check is cheaper.
            pix = page.get_pixmap(matrix=mat, colorspace='RGB', alpha=False)
            pix.save(os.path.join(output_dir, "p-%i.png" % i))
        print("Processed page numbers %i through %i" % (seg_from, seg_to - 1))



def extract_page(vector):
    """For pages with single image (and no text). Otherwise it's recommended to use render_page()

    Notes:
        The PyMuPDF document cannot be part of the argument, because that
        cannot be pickled. So we are being passed in just its filename.
        This is no performance issue, because we are a separate process and
        need to open the document anyway.
        Any page-specific function can be processed here - rendering is just
        an example - text extraction might be another.
        The work must however be self-contained: no inter-process communication
        or synchronization is possible with this design.
        Care must also be taken with which parameters are contained in the
        argument, because it will be passed in via pickling by the Pool class.
        So any large objects will increase the overall duration.
    Args:
        vector: a list containing required parameters.
    """
    # recreate the arguments
    idx = vector[0]  # this is the segment number we have to process
    cpu = vector[1]  # number of CPUs
    filename = vector[2]  # document filename
    output_dir = vector[3]


    with pymupdf.open(filename) as doc: # open the document
        num_pages = doc.page_count  # get number of pages

        # pages per segment: make sure that cpu * seg_size >= num_pages!
        seg_size = int(num_pages / cpu + 1)
        seg_from = idx * seg_size  # our first page number
        seg_to = min(seg_from + seg_size, num_pages)  # last page number

        for i in range(seg_from, seg_to):  # work through our page segment
            output_path = os.path.join(output_dir, "p-%i.png" % i)
            page = doc.load_page(i)
            image_list = page.get_images()
            if len(image_list) > 1:
                raise UserWarning("mupdf_pdf_extract_page_image() function can be used only with single image pages.")
            if not image_list:
                width, height = int(page.rect.width), int(page.rect.height)
                blank_page = Image.new("RGB", (width, height), "white")
                blank_page.save(output_path)
            else:
                xref = image_list[0][0]
                d = doc.extract_image(xref)
                if d['cs-name'] == 'DeviceCMYK':
                    pix = pymupdf.Pixmap(doc, xref)
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                    pix.save(output_path)
                else:
                    with open(Path(output_path).with_suffix('.' + d['ext']), "wb") as imgout:
                        imgout.write(d["image"])
        print("Processed page numbers %i through %i" % (seg_from, seg_to - 1))



def mupdf_pdf_process_pages_parallel(filename, output_dir, target_height):
    render = False
    with pymupdf.open(filename) as doc:
        for page in doc:
            page_text = page.get_text().strip()
            if page_text != "":
                render = True
                break
            if len(page.get_images()) > 1:
                render = True
                break
            if len(page.get_images()) == 1:
                image = page.get_images()[0]
                if not image[5] or image[8] == 'CCITTFaxDecode':
                    render = True
                    break

    cpu = cpu_count()

    # make vectors of arguments for the processes
    vectors = [(i, cpu, filename, output_dir, target_height) for i in range(cpu)]
    print("Starting %i processes for '%s'." % (cpu, filename))


    start = perf_counter()
    with Pool() as pool:
        results = pool.map(
            render_page if render else extract_page, vectors
        )
    end = perf_counter()
    print(f"MuPDF: {end - start} sec")



def getWorkFolder(afile):
    if os.path.isdir(afile):
        if disk_usage(gettempdir())[2] < getDirectorySize(afile) * 2.5:
            raise UserWarning("Not enough disk space to perform conversion.")
        workdir = mkdtemp('', 'KCC-', os.path.dirname(afile))
        try:
            os.rmdir(workdir)
            fullPath = os.path.join(workdir, 'OEBPS', 'Images')
            copytree(afile, fullPath)
            sanitizePermissions(fullPath)
            return workdir
        except Exception:
            rmtree(workdir, True)
            raise UserWarning("Failed to prepare a workspace.")
    elif os.path.isfile(afile):
        if disk_usage(gettempdir())[2] < os.path.getsize(afile) * 2.5:
            raise UserWarning("Not enough disk space to perform conversion.")
        if afile.lower().endswith('.pdf'):
            workdir = mkdtemp('', 'KCC-', os.path.dirname(afile))
            path = workdir
            sanitizePermissions(path)
            target_height = options.profileData[1][1]
            if options.cropping == 1:
                target_height = target_height + target_height*0.20 #Account for possible margin at the top and bottom
            elif options.cropping == 2:
                target_height = target_height + target_height*0.25 #Account for possible margin at the top and bottom with page number
            try:
                mupdf_pdf_process_pages_parallel(afile, workdir, target_height)
            except Exception as e:
                rmtree(path, True)
                raise UserWarning(f"Failed to extract images from PDF file. {e}")
        else:
            workdir = mkdtemp('', 'KCC-', os.path.dirname(afile))
            try:
                cbx = comicarchive.ComicArchive(afile)
                path = cbx.extract(workdir)
                sanitizePermissions(path)

                tdir = os.listdir(workdir)
                if len(tdir) == 2 and 'ComicInfo.xml' in tdir:
                    tdir.remove('ComicInfo.xml')
                    if os.path.isdir(os.path.join(workdir, tdir[0])):
                        os.replace(
                            os.path.join(workdir, 'ComicInfo.xml'),
                            os.path.join(workdir, tdir[0], 'ComicInfo.xml')
                        )
                if len(tdir) == 1 and os.path.isdir(os.path.join(workdir, tdir[0])):
                    path = os.path.join(workdir, tdir[0])
 
            except OSError as e:
                rmtree(workdir, True)
                raise UserWarning(e)
    else:
        raise UserWarning("Failed to open source file/directory.")
    newpath = mkdtemp('', 'KCC-', os.path.dirname(afile))
    os.renames(path, os.path.join(newpath, 'OEBPS', 'Images'))
    return newpath


def getOutputFilename(srcpath, wantedname, ext, tomenumber):
    if srcpath[-1] == os.path.sep:
        srcpath = srcpath[:-1]
    if 'Ko' in options.profile and options.format == 'EPUB':
        if options.noKepub:
            # Just use normal epub extension if no_kepub option is true
            ext = '.epub'
        else:
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
        filename = srcpath + tomenumber + ext
    else:
        if 'Ko' in options.profile and options.format == 'EPUB':
            src = pathlib.Path(srcpath)
            name = re.sub(r'\W+', '_', src.stem) + tomenumber + ext
            filename = src.with_name(name)
        else:
            filename = os.path.splitext(srcpath)[0] + tomenumber + ext
    if os.path.isfile(filename):
        counter = 0
        basename = os.path.splitext(filename)[0]
        while os.path.isfile(basename + '_kcc' + str(counter) + ext):
            counter += 1
        filename = basename + '_kcc' + str(counter) + ext
    return filename


def getMetadata(path, originalpath):
    xmlPath = os.path.join(path, 'ComicInfo.xml')
    options.comicinfo_chapters = []
    options.summary = ''
    titleSuffix = ''
    if options.title == 'defaulttitle':
        defaultTitle = True
        if os.path.isdir(originalpath):
            options.title = os.path.basename(originalpath)
        else:
            options.title = os.path.splitext(os.path.basename(originalpath))[0]
    else:
        defaultTitle = False
    if options.author == 'defaultauthor':
        defaultAuthor = True
        options.authors = ['KCC']
    else:
        defaultAuthor = False
        options.authors = [options.author]

    if os.path.exists(xmlPath):
        try:
            xml = metadata.MetadataParser(xmlPath)
        except Exception:
            os.remove(xmlPath)
            return
        if options.metadatatitle == 2:
            options.title = xml.data['Title']
        elif defaultTitle:
            if xml.data['Series']:
                options.title = xml.data['Series']
            if xml.data['Volume']:
                titleSuffix += ' Vol. ' + xml.data['Volume'].zfill(2)
            if xml.data['Number']:
                titleSuffix += ' #' + xml.data['Number'].zfill(3)
            if options.metadatatitle == 1 and xml.data['Title']:
                titleSuffix += ': ' + xml.data['Title']
            options.title += titleSuffix
        if defaultAuthor:    
            options.authors = []
            for field in ['Writers', 'Pencillers', 'Inkers', 'Colorists']:
                for person in xml.data[field]:
                    options.authors.append(person)
            if len(options.authors) > 0:
                options.authors = list(set(options.authors))
                options.authors.sort()
            else:
                options.authors = ['KCC']
        if xml.data['Bookmarks']:
            options.comicinfo_chapters = xml.data['Bookmarks']
        if xml.data['Summary']:
            options.summary = xml.data['Summary']
        os.remove(xmlPath)

    if originalpath.lower().endswith('.pdf'):
        with pymupdf.open(originalpath) as doc:
            if options.metadatatitle and doc.metadata['title']:
                options.title = doc.metadata['title']
            if defaultAuthor and doc.metadata['author']:
                options.authors = [doc.metadata['author']]


def getDirectorySize(start_path='.'):
    total_size = 0
    for dirpath, _, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def getTopMargin(deviceres, size):
    y = int((deviceres[1] - size[1]) / 2) / deviceres[1] * 100
    return str(round(y, 1))


def getPanelViewResolution(imagesize, deviceres):
    scale = float(deviceres[0]) / float(imagesize[0])
    return int(deviceres[0]), int(scale * imagesize[1])


def getPanelViewSize(deviceres, size):
    x = int(deviceres[0] / 2 - size[0] / 2) / deviceres[0] * 100
    y = int(deviceres[1] / 2 - size[1] / 2) / deviceres[1] * 100
    return str(int(x)), str(int(y))


def removeNonImages(filetree):
    # clean dot from original file
    dot_clean(filetree)

    for root, dirs, files in os.walk(filetree):
        for name in files:
            _, ext = getImageFileName(name)
            if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.jp2', '.avif'):
                if os.path.exists(os.path.join(root, name)):
                    os.remove(os.path.join(root, name))
    # remove empty nested folders
    for root, dirs, files in os.walk(filetree, False):
        if not files and not dirs:
            os.rmdir(root)
    
    if not os.listdir(Path(filetree).parent):
        raise UserWarning('No images detected, nested archives are not supported.')


def sanitizeTree(filetree):
    chapterNames = {}
    page = 1
    cover_path = None
    for root, dirs, files in os.walk(filetree):
        files.sort(key=OS_SORT_KEY)
        for name in files:
            _, ext = getImageFileName(name)

            # 9999 page limit
            unique_name = f'kcc-{page:04}'
            page += 1

            newKey = os.path.join(root, unique_name + ext)
            key = os.path.join(root, name)
            if key != newKey:
                os.replace(key, newKey)
            if not cover_path:
                cover_path = newKey
        is_natural_sorted = False
        if os_sorted(dirs) == sorted(dirs):
            is_natural_sorted = True
        dirs.sort(key=OS_SORT_KEY)
        for i, name in enumerate(dirs):
            tmpName = name
            slugified = slugify(name, is_natural_sorted)
            while os.path.exists(os.path.join(root, slugified)) and name.upper() != slugified.upper():
                slugified += "A"
            chapterNames[slugified] = tmpName
            newKey = os.path.join(root, slugified)
            key = os.path.join(root, name)
            if key != newKey:
                os.replace(key, newKey)
                dirs[i] = newKey
    return chapterNames, cover_path


def flattenTree(filetree):
    for root, dirs, files in os.walk(filetree, topdown=False):
        for name in files:
            os.rename(os.path.join(root, name), os.path.join(filetree, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))


def sanitizePermissions(filetree):
    for root, dirs, files in os.walk(filetree, False):
        for name in files:
            os.chmod(os.path.join(root, name), S_IWRITE | S_IREAD)
        for name in dirs:
            os.chmod(os.path.join(root, name), S_IWRITE | S_IREAD | S_IEXEC)
    dot_clean(filetree)


def chunk_directory(path):
    level = -1
    for root, _, files in os.walk(os.path.join(path, 'OEBPS', 'Images')):
        for f in files:
            # Windows MAX_LEN = 260 plus some buffer
            if os.name == 'nt' and len(os.path.join(root, f)) > 180:
                flattenTree(os.path.join(path, 'OEBPS', 'Images'))
                level = 1
                break               
            if getImageFileName(f):
                newLevel = os.path.join(root, f).replace(os.path.join(path, 'OEBPS', 'Images'), '').count(os.sep)
                if level != -1 and level != newLevel:
                    flattenTree(os.path.join(path, 'OEBPS', 'Images'))
                    level = 1
                    break
                else:
                    level = newLevel
    if level > 0:
        parent = pathlib.Path(path).parent
        chunker = chunk_process(os.path.join(path, 'OEBPS', 'Images'), level, parent)
        path = [path]
        for tome in chunker:
            path.append(tome)
        return path
    else:
        raise UserWarning('Unsupported directory structure.')


def chunk_process(path, mode, parent):
    output = []
    currentSize = 0
    currentTarget = path
    if options.targetsize:
        targetSize = options.targetsize * 1048576
    elif options.webtoon:
        targetSize = 104857600
    else:
        targetSize = 419430400
    if options.batchsplit == 2 and mode == 2:
        mode = 3
    if options.batchsplit == 1 and mode == 2:
        with os.scandir(path) as it:
            for entry in it:
                if not entry.name.startswith('.') and entry.is_dir():
                    if getDirectorySize(os.path.join(path, entry)) > targetSize:
                        flattenTree(path)
                        mode = 1
                        break
    if mode < 3:
        for root, dirs, files in walkLevel(path, 0):
            for name in files if mode == 1 else dirs:
                size = 0
                if mode == 1: 
                    if 'below' not in name:
                        size = os.path.getsize(os.path.join(root, name))
                        if 'above' in name:
                            size += os.path.getsize(os.path.join(root, name.replace('above', 'below')))
                else:
                    size = getDirectorySize(os.path.join(root, name))
                if currentSize + size > targetSize:
                    currentTarget, pathRoot = createNewTome(parent)
                    output.append(pathRoot)
                    currentSize = size
                else:
                    currentSize += size
                if path != currentTarget:
                    move(os.path.join(root, name), os.path.join(currentTarget, name))
    else:
        firstTome = True
        for root, dirs, _ in walkLevel(path, 0):
            for name in dirs:
                if not firstTome:
                    currentTarget, pathRoot = createNewTome(parent)
                    output.append(pathRoot)
                    move(os.path.join(root, name), os.path.join(currentTarget, name))
                else:
                    firstTome = False
    return output

def detectSuboptimalProcessing(tmppath, orgpath):
    imageNumber = 0
    imageSmaller = 0
    alreadyProcessed = False
    for root, _, files in os.walk(tmppath, False):
        for name in files:
            if getImageFileName(name) is not None:
                if not alreadyProcessed and  '-kcc' in getImageFileName(name)[0]:
                    alreadyProcessed = True
                path = os.path.join(root, name)
                pathOrg = orgpath + path.split('OEBPS' + os.path.sep + 'Images')[1]
                if os.path.getsize(path) == 0:
                    rmtree(os.path.join(tmppath, '..', '..'), True)
                    raise RuntimeError('Image file %s is corrupted.' % pathOrg)
                try:
                    img = Image.open(path)
                    imageNumber += 1
                    # count images smaller than device resolution
                    if options.profileData[1][0] > img.size[0] and options.profileData[1][1] > img.size[1]:
                        imageSmaller += 1
                except Exception as err:
                    rmtree(os.path.join(tmppath, '..', '..'), True)
                    if 'decoder' in str(err) and 'not available' in str(err):
                        raise RuntimeError('Pillow was compiled without JPG and/or PNG decoder.')
                    else:
                        raise RuntimeError('Image file %s is corrupted. Error: %s' % (pathOrg, str(err)))
            else:
                try:
                    if os.path.exists(os.path.join(root, name)):
                        os.remove(os.path.join(root, name))
                except OSError as e:
                    raise RuntimeError(f"{name}: {e}")
    if alreadyProcessed:
        print("WARNING: Source files are probably created by KCC. The second conversion will decrease quality.")
        if GUI:
            GUI.addMessage.emit('Source files are probably created by KCC. The second conversion will decrease quality.'
                                , 'warning', False)
            GUI.addMessage.emit('', '', False)
    if imageSmaller > imageNumber * 0.25 and not options.upscale and not options.stretch and options.profile != 'KS':
        print("WARNING: More than 25% of images are smaller than target device resolution. "
              "Consider enabling stretching or upscaling to improve readability.")
        if GUI:
            GUI.addMessage.emit('More than 25% of images are smaller than target device resolution.', 'warning', False)
            GUI.addMessage.emit('Consider enabling stretching or upscaling to improve readability.', 'warning', False)
            GUI.addMessage.emit('', '', False)


def createNewTome(parent):
    tomePathRoot = mkdtemp('', 'KCC-', parent)
    tomePath = os.path.join(tomePathRoot, 'OEBPS', 'Images')
    os.makedirs(tomePath)
    return tomePath, tomePathRoot


def slugify(value, is_natural_sorted):
    if options.format == 'CBZ' and is_natural_sorted:
        return value
    if options.format != 'CBZ':
        # convert all unicode to ascii via slugify
        value = slugify_ext(value, regex_pattern=r'[^-a-z0-9_\.]+').strip('.')
    if not is_natural_sorted:
        # pad zeros to numbers
        value = sub(r'0*([0-9]{4,})', r'\1', sub(r'([0-9]+)', r'0000\1', value, count=2))
    return value

def makeZIP(zipfilename, basedir, isepub=False):
    start = perf_counter()
    zipfilename = os.path.abspath(zipfilename) + '.zip'
    if SEVENZIP in available_archive_tools():
        if isepub:
            mimetypeFile = open(os.path.join(basedir, 'mimetype'), 'w')
            mimetypeFile.write('application/epub+zip')
            mimetypeFile.close()
        subprocess_run([SEVENZIP, 'a', '-tzip', zipfilename, "*"], capture_output=True, check=True, cwd=basedir)
    else:
        zipOutput = ZipFile(zipfilename, 'w', ZIP_DEFLATED)
        if isepub:
            zipOutput.writestr('mimetype', 'application/epub+zip', ZIP_STORED)
        for dirpath, _, filenames in os.walk(basedir):
            for name in filenames:
                path = os.path.normpath(os.path.join(dirpath, name))
                aPath = os.path.normpath(os.path.join(dirpath.replace(basedir, ''), name))
                if os.path.isfile(path):
                    zipOutput.write(path, aPath)
        zipOutput.close()
    end = perf_counter()
    print(f"makeZIP time: {end - start} seconds")
    return zipfilename

def makeParser():
    psr = ArgumentParser(prog="kcc-c2e", usage="kcc-c2e [options] [input]", add_help=False)

    mandatory_options = psr.add_argument_group("MANDATORY")
    main_options = psr.add_argument_group("MAIN")
    processing_options = psr.add_argument_group("PROCESSING")
    output_options = psr.add_argument_group("OUTPUT SETTINGS")
    custom_profile_options = psr.add_argument_group("CUSTOM PROFILE")
    other_options = psr.add_argument_group("OTHER")

    mandatory_options.add_argument("input", action="extend", nargs="*", default=None,
                                   help="Full path to comic folder or file(s) to be processed.")

    main_options.add_argument("-p", "--profile", action="store", dest="profile", default="KV",
                              help=f"Device profile (Available options: {', '.join(image.ProfileData.Profiles.keys())})"
                                   " [Default=KV]")
    main_options.add_argument("-m", "--manga-style", action="store_true", dest="righttoleft", default=False,
                              help="Manga style (right-to-left reading and splitting)")
    main_options.add_argument("-q", "--hq", action="store_true", dest="hq", default=False,
                              help="Try to increase the quality of magnification")
    main_options.add_argument("-2", "--two-panel", action="store_true", dest="autoscale", default=False,
                              help="Display two not four panels in Panel View mode")
    main_options.add_argument("-w", "--webtoon", action="store_true", dest="webtoon", default=False,
                              help="Webtoon processing mode"),
    main_options.add_argument("--ts", "--targetsize", type=int, dest="targetsize", default=None,
                              help="the maximal size of output file in MB."
                                   " [Default=100MB for webtoon and 400MB for others]")

    output_options.add_argument("-o", "--output", action="store", dest="output", default=None,
                                help="Output generated file to specified directory or file")
    output_options.add_argument("-t", "--title", action="store", dest="title", default="defaulttitle",
                                help="Comic title [Default=filename or directory name]")
    output_options.add_argument("--metadatatitle", type=int, dest="metadatatitle", default=0,
                                help="Write title using ComicInfo.xml or other embedded metadata. 1: Combine Title with default schema "
                                     "2: Use Title only")
    output_options.add_argument("-a", "--author", action="store", dest="author", default="defaultauthor",
                                help="Author name [Default=KCC]")
    output_options.add_argument("-f", "--format", action="store", dest="format", default="Auto",
                                help="Output format (Available options: Auto, MOBI, EPUB, CBZ, KFX, MOBI+EPUB, PDF) "
                                     "[Default=Auto]")
    output_options.add_argument("--nokepub", action="store_true", dest="noKepub", default=False,
                                help="If format is EPUB, output file with '.epub' extension rather than '.kepub.epub'")
    output_options.add_argument("-b", "--batchsplit", type=int, dest="batchsplit", default="0",
                                help="Split output into multiple files. 0: Don't split 1: Automatic mode "
                                     "2: Consider every subdirectory as separate volume [Default=0]")
    output_options.add_argument("--spreadshift", action="store_true", dest="spreadshift", default=False,
                                help="Shift first page to opposite side in landscape for spread alignment")
    output_options.add_argument("--norotate", action="store_true", dest="norotate", default=False,
                                help="Do not rotate double page spreads in spread splitter option.")
    output_options.add_argument("--rotatefirst", action="store_true", dest="rotatefirst", default=False,
                                help="Put rotated 2 page spread first in spread splitter option.")

    processing_options.add_argument("-n", "--noprocessing", action="store_true", dest="noprocessing", default=False,
                                    help="Do not modify image and ignore any profile or processing option")
    processing_options.add_argument("-u", "--upscale", action="store_true", dest="upscale", default=False,
                                    help="Resize images smaller than device's resolution")
    processing_options.add_argument("-s", "--stretch", action="store_true", dest="stretch", default=False,
                                    help="Stretch images to device's resolution")
    processing_options.add_argument("-r", "--splitter", type=int, dest="splitter", default="0",
                                    help="Double page parsing mode. 0: Split 1: Rotate 2: Both [Default=0]")
    processing_options.add_argument("-g", "--gamma", type=float, dest="gamma", default="0.0",
                                    help="Apply gamma correction to linearize the image [Default=Auto]")
    output_options.add_argument("--autolevel", action="store_true", dest="autolevel", default=False,
                                help="Set most common dark pixel value to be black point for leveling.")
    processing_options.add_argument("-c", "--cropping", type=int, dest="cropping", default="2",
                                    help="Set cropping mode. 0: Disabled 1: Margins 2: Margins + page numbers [Default=2]")
    processing_options.add_argument("--cp", "--croppingpower", type=float, dest="croppingp", default="1.0",
                                    help="Set cropping power [Default=1.0]")
    processing_options.add_argument("--preservemargin", type=int, dest="preservemargin", default="0",
                                    help="After calculating crop, back up specified percentage amount. [Default=0]")
    processing_options.add_argument("--cm", "--croppingminimum", type=float, dest="croppingm", default="0.0",
                                    help="Set cropping minimum area ratio [Default=0.0]")
    processing_options.add_argument("--ipc", "--interpanelcrop", type=int, dest="interpanelcrop", default="0",
                                    help="Crop empty sections. 0: Disabled 1: Horizontally 2: Both [Default=0]")
    processing_options.add_argument("--blackborders", action="store_true", dest="black_borders", default=False,
                                    help="Disable autodetection and force black borders")
    processing_options.add_argument("--whiteborders", action="store_true", dest="white_borders", default=False,
                                    help="Disable autodetection and force white borders")
    processing_options.add_argument("--forcecolor", action="store_true", dest="forcecolor", default=False,
                                    help="Don't convert images to grayscale")
    output_options.add_argument("--eraserainbow", action="store_true", dest="eraserainbow", default=False,
                                help="Erase rainbow effect on color eink screen by attenuating interfering frequencies")
    processing_options.add_argument("--forcepng", action="store_true", dest="forcepng", default=False,
                                    help="Create PNG files instead JPEG")
    processing_options.add_argument("--mozjpeg", action="store_true", dest="mozjpeg", default=False,
                                    help="Create JPEG files using mozJpeg")
    processing_options.add_argument("--maximizestrips", action="store_true", dest="maximizestrips", default=False,
                                    help="Turn 1x4 strips to 2x2 strips")
    processing_options.add_argument("-d", "--delete", action="store_true", dest="delete", default=False,
                                    help="Delete source file(s) or a directory. It's not recoverable.")

    custom_profile_options.add_argument("--customwidth", type=int, dest="customwidth", default=0,
                                        help="Replace screen width provided by device profile")
    custom_profile_options.add_argument("--customheight", type=int, dest="customheight", default=0,
                                        help="Replace screen height provided by device profile")

    other_options.add_argument("-h", "--help", action="help",
                               help="Show this help message and exit")

    return psr


def checkOptions(options):
    options.panelview = True
    options.iskindle = False
    options.isKobo = False
    options.bordersColor = None
    options.keep_epub = False
    if options.format == 'EPUB-200MB':
        options.targetsize = 195
        options.format = 'EPUB'
        if options.batchsplit != 2:
            options.batchsplit = 1
    if options.format == 'MOBI+EPUB-200MB':
        options.keep_epub = True
        options.targetsize = 195
        options.format = 'MOBI'
        if options.batchsplit != 2:
            options.batchsplit = 1
    if options.format == 'MOBI+EPUB':
        options.keep_epub = True
        options.format = 'MOBI'
    options.kfx = False
    if options.format == 'Auto':
        if options.profile in ['KDX']:
            options.format = 'CBZ'
        elif options.profile in image.ProfileData.ProfilesKindle.keys():
            options.format = 'MOBI'
        elif options.profile in image.ProfileData.ProfilesRemarkable.keys():
            options.format = 'PDF'
        else:
            options.format = 'EPUB'
    if options.profile in image.ProfileData.ProfilesKindle.keys():
        options.iskindle = True
    else:
        options.isKobo = True
    if options.white_borders:
        options.bordersColor = 'white'
    if options.black_borders:
        options.bordersColor = 'black'
    # Splitting MOBI is not optional
    if (options.format == 'MOBI' or options.format == 'KFX') and options.batchsplit != 2:
        options.batchsplit = 1
    # Older Kindle models don't support Panel View.
    if options.profile == 'K1' or options.profile == 'K2' or options.profile == 'K34' or options.profile == 'KDX':
        options.panelview = False
        options.hq = False
    if not options.hq and not options.autoscale:
        options.panelview = False
    # Webtoon mode mandatory options
    if options.webtoon:
        options.panelview = False
        options.righttoleft = False
        options.upscale = True
        options.hq = False
    # Disable all Kindle features for other e-readers
    if options.profile == 'OTHER':
        options.panelview = False
        options.hq = False
    if 'Ko' in options.profile:
        options.panelview = False
        options.hq = False
    # CBZ files on Kindle DX/DXG support higher resolution
    if options.profile == 'KDX' and options.format == 'CBZ':
        options.customheight = 1200
    # KFX output create EPUB that might be can be by jhowell KFX Output Calibre plugin
    if options.format == 'KFX':
        options.format = 'EPUB'
        options.kfx = True
        options.panelview = False
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
    return options


def checkTools(source):
    source = source.upper()
    if source.endswith('.CB7') or source.endswith('.7Z') or source.endswith('.RAR') or source.endswith('.CBR') or \
            source.endswith('.ZIP') or source.endswith('.CBZ'):
        if SEVENZIP not in available_archive_tools():
            print('ERROR: 7z is missing!')
            sys.exit(1)
    if options.format == 'MOBI':
        try:
            subprocess_run(['kindlegen', '-locale', 'en'], stdout=PIPE, stderr=STDOUT, check=True)
        except (FileNotFoundError, CalledProcessError):
            print('ERROR: KindleGen is missing!')
            sys.exit(1)


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
    except Exception:
        raise UserWarning("Target directory is not writable.")


def makeFusion(sources: List[str]):
    if len(sources) < 2:
        raise UserWarning('Fusion requires at least 2 sources. Did you forget to uncheck fusion?')
    start = perf_counter()
    first_path = Path(sources[0])
    if first_path.is_file():
        fusion_path = first_path.parent.joinpath(first_path.stem + ' [fused]')
    else:
        fusion_path = first_path.parent.joinpath(first_path.name + ' [fused]')
    print("Running Fusion")

    for source in sources:
        print(f"Processing {source}...")
        checkPre(source)
        print("Checking images...")
        path = getWorkFolder(source)
        pathfinder = os.path.join(path, "OEBPS", "Images")
        sanitizeTree(pathfinder)
        # TODO: remove flattenTree when subchapters are supported
        flattenTree(pathfinder)
        source_path = Path(source)
        if source_path.is_file():
            os.renames(pathfinder, fusion_path.joinpath(source_path.stem))
        else:
            os.renames(pathfinder, fusion_path.joinpath(source_path.name))
        

    end = perf_counter()
    print(f"makefusion: {end - start} seconds")
    print("Combined File: "+ str(fusion_path))
    
    return str(fusion_path)


def makeBook(source, qtgui=None):
    start = perf_counter()
    global GUI
    GUI = qtgui
    if GUI:
        GUI.progressBarTick.emit('1')
    else:
        checkTools(source)
    options.kindle_scribe_azw3 = options.profile == 'KS' and ('MOBI' in options.format or 'EPUB' in options.format)
    checkPre(source)
    print("Preparing source images...")
    path = getWorkFolder(source)
    print("Checking images...")
    getMetadata(os.path.join(path, "OEBPS", "Images"), source)
    removeNonImages(os.path.join(path, "OEBPS", "Images"))
    detectSuboptimalProcessing(os.path.join(path, "OEBPS", "Images"), source)
    chapterNames, cover_path = sanitizeTree(os.path.join(path, 'OEBPS', 'Images'))
    cover = image.Cover(cover_path, options)

    if options.webtoon:
        y = image.ProfileData.Profiles[options.profile][1][1]
        comic2panel.main(['-y ' + str(y), '-i', '-m', path], qtgui)
    if options.noprocessing:
        print("Do not process image, ignore any profile or processing option")
    else:
        print("Processing images...")
        if GUI:
            GUI.progressBarTick.emit('Processing images')
        imgDirectoryProcessing(os.path.join(path, "OEBPS", "Images"))
    if GUI:
        GUI.progressBarTick.emit('1')
    if options.batchsplit > 0 or options.targetsize:
        tomes = chunk_directory(path)
    else:
        tomes = [path]
    filepath = []
    tomeNumber = 0
    if GUI:
        if options.format == 'CBZ':
            GUI.progressBarTick.emit('Compressing CBZ files')
        elif options.format == 'PDF':
            GUI.progressBarTick.emit('Creating PDF files')
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
        elif options.format == 'PDF':
            print("Creating PDF file with PyMuPDF...")
            # determine output filename based on source and tome count
            suffix = (' ' + str(tomeNumber)) if len(tomes) > 1 else ''
            output_file = getOutputFilename(source, options.output, '.pdf', suffix)
            # use optimized buildPDF logic with streaming and compression
            output_pdf = buildPDF(tome, options.title, None, output_file)
            filepath.append(output_pdf)
        else:
            print("Creating EPUB file...")
            if len(tomes) > 1:
                buildEPUB(tome, chapterNames, tomeNumber, True, cover, source, len(tomes))
                filepath.append(getOutputFilename(source, options.output, '.epub', ' ' + str(tomeNumber)))
            else:
                buildEPUB(tome, chapterNames, tomeNumber, False, cover, source)
                filepath.append(getOutputFilename(source, options.output, '.epub', ''))
            makeZIP(tome + '_comic', tome, True)
        # Copy files to final destination (PDF files are already saved directly)
        if options.format != 'PDF':
            copyfile(tome + '_comic.zip', filepath[-1])
            try:
                os.remove(tome + '_comic.zip')
            except FileNotFoundError:
                # newly temporary created file is not found. It might have been already deleted
                pass
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
        k = kindle.Kindle(options.profile)
        if k.path and k.coverSupport:
            print("Kindle detected. Uploading covers...")
        for i in filepath:
            output = makeMOBIFix(i, options.covers[filepath.index(i)][1])
            if not output[0]:
                print('Error: Failed to tweak KindleGen output!')
                return filepath
            else:
                os.remove(i.replace('.epub', '.mobi') + '_toclean')
            if k.path and k.coverSupport:
                options.covers[filepath.index(i)][0].saveToKindle(k, options.covers[filepath.index(i)][1])
    if options.delete:
        if os.path.isfile(source):
            os.remove(source)
        elif os.path.isdir(source):
            rmtree(source, True)

    end = perf_counter()
    print(f"makeBook: {end - start} seconds")
    # Clean up temporary workspace
    try:
        rmtree(path, True)
    except Exception:
        pass
    return filepath


def makeMOBIFix(item, uuid):
    is_pdoc = options.profile in image.ProfileData.ProfilesKindlePDOC.keys()
    if not options.keep_epub:
        os.remove(item)
    mobiPath = item.replace('.epub', '.mobi')
    move(mobiPath, mobiPath + '_toclean')
    try:
        dualmetafix.DualMobiMetaFix(mobiPath + '_toclean', mobiPath, bytes(uuid, 'UTF-8'), is_pdoc)
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
            output = subprocess_run(['kindlegen', '-dont_append_source', '-locale', 'en', item],
                           stdout=PIPE, stderr=STDOUT, encoding='UTF-8', errors='ignore', check=True)
        else:
            # ERROR: EPUB too big
            kindlegenErrorCode = 23026
        return [kindlegenErrorCode, kindlegenError, item]
    except CalledProcessError as err:
        for line in err.stdout.splitlines():
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
                return [0, '', item]
            if ":I1037: Mobi file built with WARNINGS!" in line:
                return [0, '', item]
        # ERROR: KCC unknown generic error
        if kindlegenErrorCode == 0:
            kindlegenErrorCode = err.returncode
            kindlegenError = err.stdout
        return [kindlegenErrorCode, kindlegenError, item]


def makeMOBI(work, qtgui=None):
    global GUI, makeMOBIWorkerPool, makeMOBIWorkerOutput
    GUI = qtgui
    makeMOBIWorkerOutput = []
    availableMemory = virtual_memory().total / 1000000000
    if availableMemory <= 2:
        threadNumber = 1
    elif 2 < availableMemory <= 4:
        threadNumber = 2
    elif 4 < availableMemory:
        threadNumber = 4
    else:
        threadNumber = None
    makeMOBIWorkerPool = Pool(threadNumber, maxtasksperchild=10)
    for i in work:
        makeMOBIWorkerPool.apply_async(func=makeMOBIWorker, args=(i, ), callback=makeMOBIWorkerTick)
    makeMOBIWorkerPool.close()
    makeMOBIWorkerPool.join()
    return makeMOBIWorkerOutput

