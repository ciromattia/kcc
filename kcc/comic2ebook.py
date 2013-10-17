#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2013 Ciro Mattia Gonano <ciromattia@gmail.com>
# Copyright (c) 2013 Pawel Jastrzebski <pawelj@vulturis.eu>
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
__version__ = '3.4'
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import os
import sys
import tempfile
import re
import stat
import string
from shutil import move, copyfile, copytree, rmtree, make_archive
from optparse import OptionParser, OptionGroup
from multiprocessing import Pool, Queue, freeze_support
try:
    from PyQt4 import QtCore
except ImportError:
    QtCore = None
import comic2panel
import image
import cbxarchive
import pdfjpgextract


def buildHTML(path, imgfile):
    filename = getImageFileName(imgfile)
    if filename is not None:
        if "_kccrot" in str(filename):
            rotatedPage = True
        else:
            rotatedPage = False
        if "_kccnh" in str(filename):
            noHorizontalPV = True
        else:
            noHorizontalPV = False
        if "_kccnv" in str(filename):
            noVerticalPV = True
        else:
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
                        order = [2, 1]
                    else:
                        order = [1, 2]
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
                imgfilepv = string.split(imgfile, ".")
                imgfilepv[0] = imgfilepv[0].split("_kccx")[0].replace("_kccnh", "").replace("_kccnv", "")
                imgfilepv[0] += "_kcchq"
                imgfilepv = string.join(imgfilepv, ".")
            else:
                imgfilepv = imgfile
            if "_kccx" in filename[0]:
                xy = string.split(filename[0], "_kccx")[1]
                x = string.split(xy, "_kccy")[0].lstrip("0")
                y = string.split(xy, "_kccy")[1].lstrip("0")
                if x != "":
                    x = "-" + str(float(x)/100) + "%"
                else:
                    x = "0%"
                if y != "":
                    y = "-" + str(float(y)/100) + "%"
                else:
                    y = "0%"
            else:
                x = "0%"
                y = "0%"
            boxStyles = {"BoxTL": "left:" + x + ";top:" + y + ";",
                         "BoxTR": "right:" + x + ";top:" + y + ";",
                         "BoxBL": "left:" + x + ";bottom:" + y + ";",
                         "BoxBR": "right:" + x + ";bottom:" + y + ";",
                         "BoxT": "left:-25%;top:" + y + ";",
                         "BoxB": "left:-25%;bottom:" + y + ";",
                         "BoxL": "left:" + x + ";top:-25%;",
                         "BoxR": "right:" + x + ";top:-25%;",
                         "BoxC": "right:-25%;top:-25%;"
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
                  "<meta name=\"dtb:depth\" content=\"1\"/>\n",
                  "<meta name=\"dtb:totalPageCount\" content=\"0\"/>\n",
                  "<meta name=\"dtb:maxPageNumber\" content=\"0\"/>\n",
                  "<meta name=\"generated\" content=\"true\"/>\n",
                  "</head>\n",
                  "<docTitle><text>", title.encode('utf-8'), "</text></docTitle>\n",
                  "<navMap>"
                  ])
    for chapter in chapters:
        folder = chapter[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\')
        if os.path.basename(folder) != "Text":
            title = os.path.basename(folder)
        filename = getImageFileName(os.path.join(folder, chapter[1]))
        f.write("<navPoint id=\"" + folder.replace('/', '_').replace('\\', '_') + "\"><navLabel><text>"
                + title.encode('utf-8') + "</text></navLabel><content src=\"" + filename[0].replace("\\", "/")
                + ".html\"/></navPoint>\n")
    f.write("</navMap>\n</ncx>")
    f.close()
    return


def buildOPF(dstdir, title, filelist, cover=None):
    opffile = os.path.join(dstdir, 'OEBPS', 'content.opf')
    profilelabel, deviceres, palette, gamma, panelviewsize = options.profileData
    imgres = str(deviceres[0]) + "x" + str(deviceres[1])
    if options.righttoleft:
        writingmode = "horizontal-rl"
    else:
        writingmode = "horizontal-lr"
    f = open(opffile, "w")
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
                  "<package version=\"2.0\" unique-identifier=\"BookID\" ",
                  "xmlns=\"http://www.idpf.org/2007/opf\">\n",
                  "<metadata xmlns:opf=\"http://www.idpf.org/2007/opf\" ",
                  "xmlns:dc=\"http://purl.org/dc/elements/1.1/\">\n",
                  "<dc:title>", title.encode('utf-8'), "</dc:title>\n",
                  "<dc:language>en-US</dc:language>\n",
                  "<dc:identifier id=\"BookID\" opf:scheme=\"UUID\">", options.uuid, "</dc:identifier>\n",
                  "<dc:Creator>KCC</dc:Creator>\n",
                  "<meta name=\"generator\" content=\"KindleComicConverter-" + __version__ + "\"/>\n",
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
                  "<meta name=\"original-resolution\" content=\"", imgres, "\"/>\n",
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
        f.write("<item id=\"page_" + uniqueid + "\" href=\""
                + folder.replace('Images', 'Text') + "/" + filename[0]
                + ".html\" media-type=\"application/xhtml+xml\"/>\n")
        if '.png' == filename[1]:
            mt = 'image/png'
        else:
            mt = 'image/jpeg'
        f.write("<item id=\"img_" + uniqueid + "\" href=\"" + folder + "/" + path[1] + "\" media-type=\""
                + mt + "\"/>\n")
    f.write("<item id=\"css\" href=\"Text/style.css\" media-type=\"text/css\"/>\n")
    f.write("</manifest>\n<spine toc=\"ncx\">\n")
    for entry in reflist:
        f.write("<itemref idref=\"page_" + entry + "\"/>\n")
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


def applyImgOptimization(img, opt, overrideQuality=5):
    img.getImageFill(opt.webtoon)
    if not opt.webtoon:
        img.cropWhiteSpace(10.0)
    if opt.cutpagenumbers and not opt.webtoon:
        img.cutPageNumber()
    img.optimizeImage(opt.gamma)
    if overrideQuality != 5:
        img.resizeImage(opt.upscale, opt.stretch, opt.bordersColor, overrideQuality)
    else:
        img.resizeImage(opt.upscale, opt.stretch, opt.bordersColor, opt.quality)
    if opt.forcepng and not opt.forcecolor:
        img.quantizeImage()


def dirImgProcess(path):
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
                    queue.get(True, 5)
                except:
                    pass
                if not GUI.conversionAlive:
                    pool.terminate()
                    rmtree(os.path.join(path, '..', '..'), True)
                    raise UserWarning("Conversion interrupted.")
                GUI.emit(QtCore.SIGNAL("progressBarTick"))
        pool.join()
        queue.close()
        try:
            splitpages = splitpages.get()
        except:
            rmtree(os.path.join(path, '..', '..'), True)
            raise RuntimeError("One of workers crashed. Cause: " + str(sys.exc_info()[1]))
        splitpages = filter(None, splitpages)
        splitpages.sort()
        for page in splitpages:
            if (page + pagenumbermodifier) % 2 == 0:
                pagenumbermodifier += 1
            pagenumbermodifier += 1
    else:
        rmtree(os.path.join(path, '..', '..'), True)
        raise UserWarning("Source directory is empty.")


def fileImgProcess_init(queue, opt):
    fileImgProcess.queue = queue
    fileImgProcess.options = opt


# noinspection PyUnresolvedReferences
def fileImgProcess(work):
    afile = work[0]
    dirpath = work[1]
    pagenumber = work[2]
    opt = fileImgProcess.options
    output = None
    if opt.verbose:
        print "Optimizing " + afile + " for " + opt.profile
    else:
        print ".",
    fileImgProcess.queue.put(".")
    img = image.ComicPage(os.path.join(dirpath, afile), opt.profileData)
    if opt.quality == 2:
        wipe = False
    else:
        wipe = True
    if opt.nosplitrotate:
        split = None
    else:
        split = img.splitPage(dirpath, opt.righttoleft, opt.rotate)
    if split is not None:
        if opt.verbose:
            print "Splitted " + afile
        output = pagenumber
        img0 = image.ComicPage(split[0], opt.profileData)
        applyImgOptimization(img0, opt)
        img0.saveToDir(dirpath, opt.forcepng, opt.forcecolor, wipe)
        img1 = image.ComicPage(split[1], opt.profileData)
        applyImgOptimization(img1, opt)
        img1.saveToDir(dirpath, opt.forcepng, opt.forcecolor, wipe)
        if opt.quality == 2:
            img3 = image.ComicPage(split[0], opt.profileData)
            applyImgOptimization(img3, opt, 0)
            img3.saveToDir(dirpath, opt.forcepng, opt.forcecolor, True)
            img4 = image.ComicPage(split[1], opt.profileData)
            applyImgOptimization(img4, opt, 0)
            img4.saveToDir(dirpath, opt.forcepng, opt.forcecolor, True)
    else:
        applyImgOptimization(img, opt)
        img.saveToDir(dirpath, opt.forcepng, opt.forcecolor, wipe)
        if opt.quality == 2:
            img2 = image.ComicPage(os.path.join(dirpath, afile), opt.profileData)
            if img.rotated:
                img2.image = img2.image.rotate(90)
                img2.rotated = True
            applyImgOptimization(img2, opt, 0)
            img2.saveToDir(dirpath, opt.forcepng, opt.forcecolor, True)
    return output


def genEpubStruct(path):
    filelist = []
    chapterlist = []
    cover = None
    _, deviceres, _, _, panelviewsize = options.profileData
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
    # Ensure we're sorting files alphabetically
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    filelist.sort(key=lambda name: (alphanum_key(name[0].lower()), alphanum_key(name[1].lower())))
    buildOPF(path, options.title, filelist, cover)


def getWorkFolder(afile):
    if len(afile) > 240:
        raise UserWarning("Path is too long.")
    if os.path.isdir(afile):
        workdir = tempfile.mkdtemp('', 'KCC-TMP-')
        #workdir = tempfile.mkdtemp('', 'KCC-TMP-', os.path.join(os.path.splitext(afile)[0], '..'))
        try:
            os.rmdir(workdir)   # needed for copytree() fails if dst already exists
            fullPath = os.path.join(workdir, 'OEBPS', 'Images')
            if len(fullPath) > 240:
                raise UserWarning("Path is too long.")
            copytree(afile, fullPath)
            sanitizeTreeBeforeConversion(fullPath)
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
        workdir = tempfile.mkdtemp('', 'KCC-TMP-')
        #workdir = tempfile.mkdtemp('', 'KCC-TMP-', os.path.dirname(afile))
        cbx = cbxarchive.CBxArchive(afile)
        if cbx.isCbxFile():
            try:
                path = cbx.extract(workdir)
            except OSError:
                rmtree(workdir, True)
                print 'UnRAR/7za not found or file failed to extract!'
                sys.exit(21)
        else:
            rmtree(workdir, True)
            raise TypeError
    if len(os.path.join(path, 'OEBPS', 'Images')) > 240:
        raise UserWarning("Path is too long.")
    move(path, path + "_temp")
    move(path + "_temp", os.path.join(path, 'OEBPS', 'Images'))
    return path


def slugify(value):
    # Normalizes string, converts to lowercase, removes non-alpha characters and converts spaces to hyphens.
    import unicodedata
    if isinstance(value, str):
        #noinspection PyArgumentList
        value = unicodedata.normalize('NFKD', unicode(value, 'latin1')).encode('ascii', 'ignore')
    elif isinstance(value, unicode):
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
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
                while os.path.exists(os.path.join(root, slugified + splitname[1])) and splitname[0].upper()\
                        != slugified.upper():
                    slugified += "A"
                os.rename(os.path.join(root, name), os.path.join(root, slugified + splitname[1]))
        for name in dirs:
            if name.startswith('.'):
                os.remove(os.path.join(root, name))
            else:
                slugified = slugify(name)
                while os.path.exists(os.path.join(root, slugified)) and name.upper() != slugified.upper():
                    slugified += "A"
                os.rename(os.path.join(root, name), os.path.join(root, slugified))


def sanitizeTreeBeforeConversion(filetree):
    for root, dirs, files in os.walk(filetree, False):
        for name in files:
            os.chmod(os.path.join(root, name), stat.S_IWRITE | stat.S_IREAD)
            # Detect corrupted files - Phase 1
            if os.path.getsize(os.path.join(root, name)) == 0:
                os.remove(os.path.join(root, name))
        for name in dirs:
            os.chmod(os.path.join(root, name), stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)


def getDirectorySize(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


# noinspection PyUnusedLocal
def createNewTome(parentPath):
    tomePathRoot = tempfile.mkdtemp('', 'KCC-TMP-')
    #tomePathRoot = tempfile.mkdtemp('', 'KCC-TMP-', parentPath)
    tomePath = os.path.join(tomePathRoot, 'OEBPS', 'Images')
    os.makedirs(tomePath)
    return tomePath, tomePathRoot


def walkLevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]


def splitDirectory(path, mode, parentPath):
    output = []
    currentSize = 0
    currentTarget = path
    if mode == 0:
        for root, dirs, files in walkLevel(path, 0):
            for name in files:
                size = os.path.getsize(os.path.join(root, name))
                if currentSize + size > 262144000:
                    currentTarget, pathRoot = createNewTome(parentPath)
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
                if currentSize + size > 262144000:
                    currentTarget, pathRoot = createNewTome(parentPath)
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
                if size > 262144000:
                    if not firstTome:
                        currentTarget, pathRoot = createNewTome(parentPath)
                        output.append(pathRoot)
                    else:
                        firstTome = False
                    for rootInside, dirsInside, filesInside in walkLevel(os.path.join(root, name), 0):
                        for nameInside in dirsInside:
                            size = getDirectorySize(os.path.join(rootInside, nameInside))
                            if currentSize + size > 262144000:
                                currentTarget, pathRoot = createNewTome(parentPath)
                                output.append(pathRoot)
                                currentSize = size
                            else:
                                currentSize += size
                            if path != currentTarget:
                                move(os.path.join(rootInside, nameInside), os.path.join(currentTarget, nameInside))
                else:
                    if not firstTome:
                        currentTarget, pathRoot = createNewTome(parentPath)
                        output.append(pathRoot)
                        move(os.path.join(root, name), os.path.join(currentTarget, name))
                    else:
                        firstTome = False
    return output


# noinspection PyUnboundLocalVariable
def preSplitDirectory(path):
    if getDirectorySize(os.path.join(path, 'OEBPS', 'Images')) > 262144000:
        # Detect directory stucture
        for root, dirs, files in walkLevel(os.path.join(path, 'OEBPS', 'Images'), 0):
            subdirectoryNumber = len(dirs)
            filesNumber = len(files)
        if subdirectoryNumber == 0:
            # No subdirectories
            mode = 0
        else:
            if filesNumber > 0:
                print '\nWARNING: Automatic output splitting failed.'
                if GUI:
                    GUI.emit(QtCore.SIGNAL("addMessage"), 'Automatic output splitting failed. <a href='
                                                          '"https://github.com/ciromattia/kcc/wiki'
                                                          '/Automatic-output-splitting">'
                                                          'More details.</a>', 'warning')
                    GUI.emit(QtCore.SIGNAL("addMessage"), '')
                return [path]
            detectedSubSubdirectories = False
            detectedFilesInSubdirectories = False
            for root, dirs, files in walkLevel(os.path.join(path, 'OEBPS', 'Images'), 1):
                if root != os.path.join(path, 'OEBPS', 'Images'):
                    if len(dirs) != 0:
                        detectedSubSubdirectories = True
                    elif len(dirs) == 0 and detectedSubSubdirectories:
                        print '\nWARNING: Automatic output splitting failed.'
                        if GUI:
                            GUI.emit(QtCore.SIGNAL("addMessage"), 'Automatic output splitting failed. <a href='
                                                                  '"https://github.com/ciromattia/kcc/wiki'
                                                                  '/Automatic-output-splitting">'
                                                                  'More details.</a>', 'warning')
                            GUI.emit(QtCore.SIGNAL("addMessage"), '')
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
                print '\nWARNING: Automatic output splitting failed.'
                if GUI:
                    GUI.emit(QtCore.SIGNAL("addMessage"), 'Automatic output splitting failed. <a href='
                                                          '"https://github.com/ciromattia/kcc/wiki'
                                                          '/Automatic-output-splitting">'
                                                          'More details.</a>', 'warning')
                    GUI.emit(QtCore.SIGNAL("addMessage"), '')
                return [path]
        # Split directories
        split = splitDirectory(os.path.join(path, 'OEBPS', 'Images'), mode, os.path.join(path, '..'))
        path = [path]
        for tome in split:
            path.append(tome)
        return path
    else:
        # No splitting is necessary
        return [path]


def Copyright():
    print ('comic2ebook v%(__version__)s. '
           'Written 2013 by Ciro Mattia Gonano and Pawel Jastrzebski.' % globals())


def Usage():
    print "Generates EPUB/CBZ comic ebook from a bunch of images."
    parser.print_help()


def main(argv=None, qtGUI=None):
    global parser, options, GUI
    parser = OptionParser(usage="Usage: %prog [options] comic_file|comic_folder", add_help_option=False)
    mainOptions = OptionGroup(parser, "MAIN")
    processingOptions = OptionGroup(parser, "PROCESSING")
    outputOptions = OptionGroup(parser, "OUTPUT SETTINGS")
    customProfileOptions = OptionGroup(parser, "CUSTOM PROFILE")
    otherOptions = OptionGroup(parser, "OTHER")
    mainOptions.add_option("-p", "--profile", action="store", dest="profile", default="KHD",
                           help="Device profile (Choose one among K1, K2, K345, KDX, KHD, KF, KFHD, KFHD8, KFHDX,"
                                " KFHDX8, KFA) [Default=KHD]")
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
    outputOptions.add_option("--cbz-output", action="store_true", dest="cbzoutput", default=False,
                             help="Outputs a CBZ archive and does not generate EPUB")
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
    otherOptions.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                            help="Verbose output")
    otherOptions.add_option("-h", "--help", action="help",
                            help="Show this help message and exit")
    parser.add_option_group(mainOptions)
    parser.add_option_group(outputOptions)
    parser.add_option_group(processingOptions)
    parser.add_option_group(customProfileOptions)
    parser.add_option_group(otherOptions)
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
    if options.webtoon:
        if GUI:
            GUI.emit(QtCore.SIGNAL("progressBarTick"), 'status', 'Splitting images')
        if options.customheight > 0:
            comic2panel.main(['-y ' + str(options.customheight), '-i', path], qtGUI)
        else:
            comic2panel.main(['-y ' + str(image.ProfileData.Profiles[options.profile][1][1]), '-i', path], qtGUI)
    if options.imgproc:
        print "\nProcessing images..."
        if GUI:
            GUI.emit(QtCore.SIGNAL("progressBarTick"), 'status', 'Processing images')
        dirImgProcess(path + "/OEBPS/Images/")
    if GUI:
        GUI.emit(QtCore.SIGNAL("progressBarTick"), 1)
    sanitizeTree(os.path.join(path, 'OEBPS', 'Images'))
    if options.batchsplit:
        tomes = preSplitDirectory(path)
    else:
        tomes = [path]
    filepath = []
    tomeNumber = 0
    for tome in tomes:
        if os.path.isdir(args[0]):
            barePath = os.path.basename(args[0])
        else:
            barePath = os.path.splitext(os.path.basename(args[0]))[0]
        if len(tomes) > 1:
            tomeNumber += 1
            options.title = barePath + ' ' + str(tomeNumber)
        elif options.title == 'defaulttitle':
            options.title = barePath
        if options.cbzoutput:
            # if CBZ output wanted, compress all images and return filepath
            print "\nCreating CBZ file..."
            if len(tomes) > 1:
                filepath.append(getOutputFilename(args[0], options.output, '.cbz', ' ' + str(tomeNumber)))
            else:
                filepath.append(getOutputFilename(args[0], options.output, '.cbz', ''))
            make_archive(tome + '_comic', 'zip', tome + '/OEBPS/Images')
        else:
            print "\nCreating EPUB structure..."
            genEpubStruct(tome)
            # actually zip the ePub
            if len(tomes) > 1:
                filepath.append(getOutputFilename(args[0], options.output, '.epub', ' ' + str(tomeNumber)))
            else:
                filepath.append(getOutputFilename(args[0], options.output, '.epub', ''))
            make_archive(tome + '_comic', 'zip', tome)
        move(tome + '_comic.zip', filepath[-1])
        rmtree(tome, True)
    return filepath


def getOutputFilename(srcpath, wantedname, ext, tomeNumber):
    if not ext.startswith('.'):
        ext = '.' + ext
    if wantedname is not None:
        if wantedname.endswith(ext):
            filename = os.path.abspath(wantedname)
        elif os.path.isdir(srcpath):
            filename = os.path.abspath(options.output) + "/" + os.path.basename(srcpath) + ext
        else:
            filename = os.path.abspath(options.output) + "/" + os.path.basename(os.path.splitext(srcpath)[0]) + ext
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


def checkOptions():
    global options
    options.panelview = True
    options.bordersColor = None
    if options.white_borders:
        options.bordersColor = "white"
    if options.black_borders:
        options.bordersColor = "black"
    # Disabling grayscale conversion for Kindle Fire family.
    if options.profile == 'KF' or options.profile == 'KFHD' or options.profile == 'KFHD8' or options.profile == 'KFHDX'\
       or options.profile == 'KFHDX8' or options.forcecolor:
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
    # Kindle for Android profile require target resolution.
    if options.profile == 'KFA' and (options.customwidth == 0 or options.customheight == 0):
        print "ERROR: Kindle for Android profile require --customwidth and --customheight options!"
        sys.exit(1)
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


if __name__ == "__main__":
    freeze_support()
    Copyright()
    main(sys.argv[1:])
    sys.exit(0)
