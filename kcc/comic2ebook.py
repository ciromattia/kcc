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
__version__ = '2.9'
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>'
__docformat__ = 'restructuredtext en'

import os
import sys
import tempfile
import re
from shutil import move
from shutil import copyfile
from shutil import copytree
from shutil import rmtree
from shutil import make_archive
from optparse import OptionParser
import image
import cbxarchive
import pdfjpgextract


def buildHTML(path, imgfile):
    filename = getImageFileName(imgfile)
    if filename is not None:
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
            if options.panelviewhorizontal:
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

            f.writelines(["<div id=\"BoxTL-Panel-Parent\" class=\"target-mag-parent\"><div id=\"BoxTL-Panel\" class=\"",
                          "target-mag\"><img src=\"", "../" * backref, "Images/", postfix, imgfile, "\" alt=\"",
                          imgfile, "\"/></div></div>\n",
                          "<div id=\"BoxTR-Panel-Parent\" class=\"target-mag-parent\"><div id=\"BoxTR-Panel\" class=\"",
                          "target-mag\"><img src=\"", "../" * backref, "Images/", postfix, imgfile, "\" alt=\"",
                          imgfile, "\"/></div></div>\n",
                          "<div id=\"BoxBL-Panel-Parent\" class=\"target-mag-parent\"><div id=\"BoxBL-Panel\" class=\"",
                          "target-mag\"><img src=\"", "../" * backref, "Images/", postfix, imgfile, "\" alt=\"",
                          imgfile, "\"/></div></div>\n",
                          "<div id=\"BoxBR-Panel-Parent\" class=\"target-mag-parent\"><div id=\"BoxBR-Panel\" class=\"",
                          "target-mag\"><img src=\"", "../" * backref, "Images/", postfix, imgfile, "\" alt=\"",
                          imgfile, "\"/></div></div>\n"
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
    ncxfile = os.path.join(dstdir, 'OEBPS', 'toc.ncx')
    f = open(ncxfile, "w")
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
                  "<!DOCTYPE ncx PUBLIC \"-//NISO//DTD ncx 2005-1//EN\" ",
                  "\"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd\">\n",
                  "<ncx version=\"2005-1\" xml:lang=\"en-US\" xmlns=\"http://www.daisy.org/z3986/2005/ncx/\">\n",
                  "<head>\n",
                  "<meta name=\"dtb:uid\" content=\"015ffaec-9340-42f8-b163-a0c5ab7d0611\"/>\n",
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
                + "</text></navLabel><content src=\"" + filename[0] + ".html\"/></navPoint>\n")
    f.write("</navMap>\n</ncx>")
    f.close()
    return


def buildOPF(profile, dstdir, title, filelist, cover=None):
    opffile = os.path.join(dstdir, 'OEBPS', 'content.opf')
    # read the first file resolution
    profilelabel, deviceres, palette, gamma, panelviewsize = image.ProfileData.Profiles[profile]
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
    from uuid import uuid4
    uuid = str(uuid4())
    uuid = uuid.encode('utf-8')
    f = open(opffile, "w")
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
                  "<package version=\"2.0\" unique-identifier=\"BookID\" xmlns=\"http://www.idpf.org/2007/opf\">\n",
                  "<metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\" ",
                  "xmlns:opf=\"http://www.idpf.org/2007/opf\">\n",
                  "<dc:title>", title, "</dc:title>\n",
                  "<dc:language>en-US</dc:language>\n",
                  "<dc:identifier id=\"BookID\" opf:scheme=\"UUID\">", uuid, "</dc:identifier>\n",
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
        f.write("<item id=\"cover\" href=\"" + filename[0] + filename[1] + "\" media-type=\"" + mt + "\"/>\n")
    reflist = []
    for path in filelist:
        folder = path[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\')
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
        if entry.endswith("-1"):
            # noinspection PyRedundantParentheses
            if ((options.righttoleft and facing == 'left') or (not options.righttoleft and facing == 'right')) and\
                    options.landscapemode:
                f.write("<itemref idref=\"blank-page" + str(splitCountUsed) + "\" properties=\"layout-blank\"/>\n")
                splitCountUsed += 1
            if options.landscapemode:
                f.write("<itemref idref=\"page_" + entry + "\" properties=\"page-spread-" + facing1 + "\"/>\n")
            else:
                f.write("<itemref idref=\"page_" + entry + "\"/>\n")
        elif entry.endswith("-2"):
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


def isInFilelist(filename, filelist):
    filename = os.path.splitext(filename)
    seen = False
    for item in filelist:
        if filename[0] == item[0]:
            seen = True
    return seen


def applyImgOptimization(img, isSplit=False, toRight=False):
    img.cropWhiteSpace(10.0)
    if options.cutpagenumbers:
        img.cutPageNumber()
    img.resizeImage(options.upscale, options.stretch, options.black_borders, isSplit, toRight, options.landscapemode,
                    options.nopanelviewhq)
    img.optimizeImage(options.gamma)
    if options.forcepng:
        img.quantizeImage()


def dirImgProcess(path):
    global options, splitCount
    if options.righttoleft:
        facing = "right"
    else:
        facing = "left"

    for (dirpath, dirnames, filenames) in os.walk(path):
        for afile in filenames:
            if getImageFileName(afile) is not None:
                if options.verbose:
                    print "Optimizing " + afile + " for " + options.profile
                else:
                    print ".",
                img = image.ComicPage(os.path.join(dirpath, afile), options.profile)
                if options.nosplitrotate:
                    split = None
                else:
                    split = img.splitPage(dirpath, options.righttoleft, options.rotate)
                if split is not None:
                    if options.verbose:
                        print "Splitted " + afile
                    if options.righttoleft:
                        toRight1 = False
                        toRight2 = True
                        if facing == "left":
                            splitCount += 1
                        facing = "right"
                    else:
                        toRight1 = True
                        toRight2 = False
                        if facing == "right":
                            splitCount += 1
                        facing = "left"
                    img0 = image.ComicPage(split[0], options.profile)
                    applyImgOptimization(img0, True, toRight1)
                    img0.saveToDir(dirpath, options.forcepng)
                    img1 = image.ComicPage(split[1], options.profile)
                    applyImgOptimization(img1, True, toRight2)
                    img1.saveToDir(dirpath, options.forcepng)
                else:
                    if facing == "right":
                        facing = "left"
                    else:
                        facing = "right"
                    applyImgOptimization(img)
                    img.saveToDir(dirpath, options.forcepng)


def genEpubStruct(path):
    global options
    filelist = []
    chapterlist = []
    cover = None
    _, deviceres, _, _, panelviewsize = image.ProfileData.Profiles[options.profile]
    sanitizeTree(os.path.join(path, 'OEBPS', 'Images'))
    os.mkdir(os.path.join(path, 'OEBPS', 'Text'))
    f = open(os.path.join(path, 'OEBPS', 'Text', 'style.css'), 'w')
    #DON'T COMPRESS CSS. KINDLE WILL FAIL TO PARSE IT.
    #Generic Panel View support + Margins fix for Non-Kindle devices.
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
            if filename is not None:
                if "credit" in afile.lower():
                    os.rename(os.path.join(dirpath, afile), os.path.join(dirpath, 'ZZZ999_' + afile))
                    afile = 'ZZZ999_' + afile
                if "+" in afile.lower() or "#" in afile.lower():
                    newfilename = afile.replace('+', '_').replace('#', '_')
                    os.rename(os.path.join(dirpath, afile), os.path.join(dirpath, newfilename))
                    afile = newfilename
                filelist.append(buildHTML(dirpath, afile))
                if not chapter:
                    chapterlist.append((dirpath.replace('Images', 'Text'), filelist[-1][1]))
                    chapter = True
                if cover is None:
                    cover = os.path.join(filelist[-1][0], 'cover' + getImageFileName(filelist[-1][1])[1])
                    copyfile(os.path.join(filelist[-1][0], filelist[-1][1]), cover)
    buildNCX(path, options.title, chapterlist)
    # ensure we're sorting files alphabetically
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    filelist.sort(key=lambda name: (alphanum_key(name[0].lower()), alphanum_key(name[1].lower())))
    buildOPF(options.profile, path, options.title, filelist, cover)
    if options.landscapemode and splitCount > 0:
        filelist.append(buildBlankHTML(os.path.join(path, 'OEBPS', 'Text')))


def getWorkFolder(afile):
    workdir = tempfile.mkdtemp()
    if os.path.isdir(afile):
        try:
            import shutil
            os.rmdir(workdir)   # needed for copytree() fails if dst already exists
            copytree(afile, workdir)
            path = workdir
        except OSError:
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
                print 'Unrar not found, please download from ' + \
                      'http://www.rarlab.com/download.htm and put into your PATH.'
                sys.exit(21)
        else:
            raise TypeError
    move(path, path + "_temp")
    move(path + "_temp", os.path.join(path, 'OEBPS', 'Images'))
    return path


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', unicode(value, 'latin1')).encode('ascii', 'ignore')
    value = re.sub('[^\w\s\.-]', '', value).strip().lower()
    value = re.sub('[-\.\s]+', '-', value)
    value = re.sub(r'([0-9]+)', r'00000\1', value)
    value = re.sub(r'0*([0-9]{6,})', r'\1', value)
    return value


def sanitizeTree(filetree):
    for root, dirs, files in os.walk(filetree):
        for name in files:
            if name.startswith('.') or name.lower() == 'thumbs.db':
                os.remove(os.path.join(root, name))
            else:
                splitname = os.path.splitext(name)
                os.rename(os.path.join(root, name),
                          os.path.join(root, slugify(splitname[0]) + splitname[1]))
        for name in dirs:
            if name.startswith('.'):
                os.remove(os.path.join(root, name))
            else:
                os.rename(os.path.join(root, name), os.path.join(root, slugify(name)))


def Copyright():
    print ('comic2ebook v%(__version__)s. '
           'Written 2012 by Ciro Mattia Gonano.' % globals())


def Usage():
    print "Generates HTML, NCX and OPF for a Comic ebook from a bunch of images."
    parser.print_help()


def main(argv=None):
    global parser, options, epub_path, splitCount
    usage = "Usage: %prog [options] comic_file|comic_folder"
    parser = OptionParser(usage=usage, version=__version__)
    parser.add_option("-p", "--profile", action="store", dest="profile", default="KHD",
                      help="Device profile (Choose one among K1, K2, K3, K4NT, K4T, KDX, KDXG or KHD) [Default=KHD]")
    parser.add_option("-t", "--title", action="store", dest="title", default="defaulttitle",
                      help="Comic title [Default=filename]")
    parser.add_option("-m", "--manga-style", action="store_true", dest="righttoleft", default=False,
                      help="Manga style (Right-to-left reading and splitting) [Default=False]")
    parser.add_option("-c", "--cbz-output", action="store_true", dest="cbzoutput", default=False,
                      help="Outputs a CBZ archive and does not generate EPUB")
    parser.add_option("--nopanelviewhq", action="store_true", dest="nopanelviewhq", default=False,
                      help="Disable high quality Panel View [Default=False]")
    parser.add_option("--panelviewhorizontal", action="store_true", dest="panelviewhorizontal", default=False,
                      help="Enable horizontal Panel View [Default=False]")
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
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="Verbose output [Default=False]")
    options, args = parser.parse_args(argv)
    checkOptions()
    if len(args) != 1:
        parser.print_help()
        return
    path = getWorkFolder(args[0])
    if options.title == 'defaulttitle':
        options.title = os.path.splitext(os.path.basename(args[0]))[0]
    splitCount = 0
    if options.imgproc:
        print "Processing images..."
        dirImgProcess(path + "/OEBPS/Images/")
    if options.cbzoutput:
        # if CBZ output wanted, compress all images and return filepath
        print "\nCreating CBZ file..."
        filepath = getOutputFilename(args[0], options.output, '.cbz')
        make_archive(path + '_comic', 'zip', path + '/OEBPS/Images')
    else:
        print "\nCreating ePub structure..."
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
    if options.profile == 'K4T' or options.profile == 'KHD':
        options.landscapemode = True
    else:
        options.landscapemode = False
    if options.profile == 'K3' or options.profile == 'K4NT':
        #Real Panel View
        options.panelview = True
    else:
        #Virtual Panel View
        options.panelview = False
    if options.profile == 'K1' or options.profile == 'K2' or options.profile == 'KDX' or options.profile == 'KDXG':
        options.nopanelviewhq = True
    if options.panelviewhorizontal:
        options.panelview = True
        options.landscapemode = False


def getEpubPath():
    global epub_path
    return epub_path

if __name__ == "__main__":
    Copyright()
    main(sys.argv[1:])
    sys.exit(0)
