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
__version__ = '4.0'
__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>, Pawel Jastrzebski <pawelj@vulturis.eu>'
__docformat__ = 'restructuredtext en'

import os
import sys
import re
import stat
import string
import zipfile
from tempfile import mkdtemp
from shutil import move, copyfile, copytree, rmtree
from optparse import OptionParser, OptionGroup
from multiprocessing import Pool
from xml.dom.minidom import parse
from uuid import uuid4
from slugify import slugify
try:
    # noinspection PyUnresolvedReferences
    from PIL import Image
    if tuple(map(int, ('2.3.0'.split(".")))) > tuple(map(int, (Image.PILLOW_VERSION.split(".")))):
        print("ERROR: Pillow 2.3.0 or newer is required!")
        if sys.platform.startswith('linux'):
            import tkinter
            import tkinter.messagebox
            importRoot = tkinter.Tk()
            importRoot.withdraw()
            tkinter.messagebox.showerror("KCC - Error", "Pillow 2.3.0 or newer is required!")
        exit(1)
except ImportError:
    print("ERROR: Pillow is not installed!")
    if sys.platform.startswith('linux'):
        import tkinter
        import tkinter.messagebox
        importRoot = tkinter.Tk()
        importRoot.withdraw()
        tkinter.messagebox.showerror("KCC - Error", "Pillow 2.3.0 or newer is required!")
    exit(1)
try:
    from PyQt5 import QtCore
except ImportError:
    QtCore = None
from . import comic2panel
from . import image
from . import cbxarchive
from . import pdfjpgextract


def buildHTML(path, imgfile):
    filename = getImageFileName(imgfile)
    if filename is not None:
        if "_kccrot" in str(filename):
            rotatedPage = True
        else:
            rotatedPage = False
        if "_kccnpv" in str(filename):
            noPV = True
        else:
            noPV = False
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
                imgfilepv = string.split(imgfile, ".")
                imgfilepv[0] = imgfilepv[0].split("_kccxl")[0].replace("_kccnh", "").replace("_kccnv", "")
                imgfilepv[0] += "_kcchq"
                imgfilepv = string.join(imgfilepv, ".")
            else:
                imgfilepv = imgfile
            if "_kccxl" in filename[0]:
                borders = filename[0].split('_kccxl')[1]
                borders = re.findall('[0-9]{1,6}', borders)
                xl = borders[0].lstrip("0")
                yu = borders[1].lstrip("0")
                xr = borders[2].lstrip("0")
                yd = borders[3].lstrip("0")
                if xl != "":
                    xl = "-" + str(float(xl)/100) + "%"
                else:
                    xl = "0%"
                if xr != "":
                    xr = "-" + str(float(xr)/100) + "%"
                else:
                    xr = "0%"
                if yu != "":
                    yu = "-" + str(float(yu)/100) + "%"
                else:
                    yu = "0%"
                if yd != "":
                    yd = "-" + str(float(yd)/100) + "%"
                else:
                    yd = "0%"
            else:
                xl = "0%"
                yu = "0%"
                xr = "0%"
                yd = "0%"
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


def buildNCX(dstdir, title, chapters):
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
                  "<docTitle><text>", title, "</text></docTitle>\n",
                  "<navMap>"
                  ])
    for chapter in chapters:
        folder = chapter[0].replace(os.path.join(dstdir, 'OEBPS'), '').lstrip('/').lstrip('\\\\')
        if os.path.basename(folder) != "Text":
            title = os.path.basename(folder)
        filename = getImageFileName(os.path.join(folder, chapter[1]))
        f.write("<navPoint id=\"" + folder.replace('/', '_').replace('\\', '_') + "\"><navLabel><text>"
                + title + "</text></navLabel><content src=\"" + filename[0].replace("\\", "/")
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
                  "<dc:title>", title, "</dc:title>\n",
                  "<dc:language>en-US</dc:language>\n",
                  "<dc:identifier id=\"BookID\" opf:scheme=\"UUID\">", options.uuid, "</dc:identifier>\n"])
    for author in options.authors:
        f.writelines(["<dc:creator>", author.encode('utf-8'), "</dc:creator>\n"])
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


def applyImgOptimization(img, opt, hqImage=None):
    if not img.fill:
        img.getImageFill(opt.webtoon)
    if not opt.webtoon:
        img.cropWhiteSpace(10.0)
    if opt.cutpagenumbers and not opt.webtoon:
        img.cutPageNumber()
    img.optimizeImage(opt.gamma)
    if hqImage:
        img.resizeImage(opt.upscale, opt.stretch, opt.bordersColor, 0)
        img.calculateBorder(hqImage, True)
    else:
        img.resizeImage(opt.upscale, opt.stretch, opt.bordersColor, opt.quality)
        if opt.panelview:
            if opt.quality == 0:
                img.calculateBorder(img)
            elif opt.quality == 1:
                img.calculateBorder(img, True)
    if opt.forcepng and not opt.forcecolor:
        img.quantizeImage()


def dirImgProcess(path):
    global workerPool, workerOutput
    workerPool = Pool()
    workerOutput = []
    work = []
    pagenumber = 0
    for (dirpath, dirnames, filenames) in os.walk(path):
        for afile in filenames:
            if getImageFileName(afile) is not None:
                pagenumber += 1
                work.append([afile, dirpath, options])
    if GUI:
        GUI.emit(QtCore.SIGNAL("progressBarTick"), pagenumber)
    if len(work) > 0:
        for i in work:
            workerPool.apply_async(func=fileImgProcess, args=(i, ), callback=fileImgProcess_tick)
        workerPool.close()
        workerPool.join()
        if GUI and not GUI.conversionAlive:
            rmtree(os.path.join(path, '..', '..'), True)
            raise UserWarning("Conversion interrupted.")
        if len(workerOutput) > 0:
            rmtree(os.path.join(path, '..', '..'), True)
            raise RuntimeError("One of workers crashed. Cause: " + workerOutput[0])
    else:
        rmtree(os.path.join(path, '..', '..'), True)
        raise UserWarning("Source directory is empty.")


def fileImgProcess_tick(output):
    if output:
        workerOutput.append(output)
        workerPool.terminate()
    if GUI:
        GUI.emit(QtCore.SIGNAL("progressBarTick"))
        if not GUI.conversionAlive:
            workerPool.terminate()


def fileImgProcess(work):
    try:
        afile = work[0]
        dirpath = work[1]
        opt = work[2]
        if opt.verbose:
            print("Optimizing " + afile + " for " + opt.profile)
        else:
            print(".", end=' ')
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
                print("Splitted " + afile)
            img0 = image.ComicPage(split[0], opt.profileData)
            applyImgOptimization(img0, opt)
            img0.saveToDir(dirpath, opt.forcepng, opt.forcecolor, wipe)
            img1 = image.ComicPage(split[1], opt.profileData)
            applyImgOptimization(img1, opt)
            img1.saveToDir(dirpath, opt.forcepng, opt.forcecolor, wipe)
            if opt.quality == 2:
                img0b = image.ComicPage(split[0], opt.profileData, img0.fill)
                applyImgOptimization(img0b, opt, img0)
                img0b.saveToDir(dirpath, opt.forcepng, opt.forcecolor, True)
                img1b = image.ComicPage(split[1], opt.profileData, img1.fill)
                applyImgOptimization(img1b, opt, img1)
                img1b.saveToDir(dirpath, opt.forcepng, opt.forcecolor, True)
        else:
            applyImgOptimization(img, opt)
            img.saveToDir(dirpath, opt.forcepng, opt.forcecolor, wipe)
            if opt.quality == 2:
                img2 = image.ComicPage(os.path.join(dirpath, afile), opt.profileData, img.fill)
                if img.rotated:
                    img2.image = img2.image.rotate(90)
                    img2.rotated = True
                applyImgOptimization(img2, opt, img)
                img2.saveToDir(dirpath, opt.forcepng, opt.forcecolor, True)
    except Exception:
        import traceback
        traceback.print_tb(sys.exc_info()[2])
        return str(sys.exc_info()[1])


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
        workdir = mkdtemp('', 'KCC-TMP-')
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
        workdir = mkdtemp('', 'KCC-TMP-')
        cbx = cbxarchive.CBxArchive(afile)
        if cbx.isCbxFile():
            try:
                path = cbx.extract(workdir)
            except OSError:
                rmtree(workdir, True)
                print('UnRAR/7za not found or file failed to extract!')
                sys.exit(21)
        else:
            rmtree(workdir, True)
            raise TypeError
    if len(os.path.join(path, 'OEBPS', 'Images')) > 240:
        raise UserWarning("Path is too long.")
    move(path, path + "_temp")
    move(path + "_temp", os.path.join(path, 'OEBPS', 'Images'))
    return path


def checkComicInfo(path, originalPath):
    xmlPath = os.path.join(path, 'ComicInfo.xml')
    options.authors = ['KCC']
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
            authorsTemp = string.split(xml.getElementsByTagName('Writer')[0].firstChild.nodeValue, ', ')
            for author in authorsTemp:
                options.authors.append(author)
        if len(xml.getElementsByTagName('Penciller')) != 0:
            authorsTemp = string.split(xml.getElementsByTagName('Penciller')[0].firstChild.nodeValue, ', ')
            for author in authorsTemp:
                options.authors.append(author)
        if len(xml.getElementsByTagName('Inker')) != 0:
            authorsTemp = string.split(xml.getElementsByTagName('Inker')[0].firstChild.nodeValue, ', ')
            for author in authorsTemp:
                options.authors.append(author)
        if len(xml.getElementsByTagName('Colorist')) != 0:
            authorsTemp = string.split(xml.getElementsByTagName('Colorist')[0].firstChild.nodeValue, ', ')
            for author in authorsTemp:
                options.authors.append(author)
        if len(options.authors) > 0:
            options.authors = list(set(options.authors))
            options.authors.sort()
        else:
            options.authors = ['KCC']
        os.remove(xmlPath)


# TODO: Check if replacement work correctly
#def slugify(value):
#    # Normalizes string, converts to lowercase, removes non-alpha characters and converts spaces to hyphens.
#    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
#    value = re.sub('[^\w\s\.-]', '', value).strip().lower()
#    value = re.sub('[-\.\s]+', '-', value)
#    value = re.sub(r'([0-9]+)', r'00000\1', value)
#    value = re.sub(r'0*([0-9]{6,})', r'\1', value)
#    return value


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
        for name in dirs:
            os.chmod(os.path.join(root, name), stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)


def getDirectorySize(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def createNewTome():
    tomePathRoot = mkdtemp('', 'KCC-TMP-')
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


def splitDirectory(path, mode):
    output = []
    currentSize = 0
    currentTarget = path
    if mode == 0:
        for root, dirs, files in walkLevel(path, 0):
            for name in files:
                size = os.path.getsize(os.path.join(root, name))
                if currentSize + size > 262144000:
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
                if currentSize + size > 262144000:
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
                if size > 262144000:
                    if not firstTome:
                        currentTarget, pathRoot = createNewTome()
                        output.append(pathRoot)
                    else:
                        firstTome = False
                    for rootInside, dirsInside, filesInside in walkLevel(os.path.join(root, name), 0):
                        for nameInside in dirsInside:
                            size = getDirectorySize(os.path.join(rootInside, nameInside))
                            if currentSize + size > 262144000:
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


#noinspection PyUnboundLocalVariable
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
                print('\nWARNING: Automatic output splitting failed.')
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
                        print('\nWARNING: Automatic output splitting failed.')
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
                print('\nWARNING: Automatic output splitting failed.')
                if GUI:
                    GUI.emit(QtCore.SIGNAL("addMessage"), 'Automatic output splitting failed. <a href='
                                                          '"https://github.com/ciromattia/kcc/wiki'
                                                          '/Automatic-output-splitting">'
                                                          'More details.</a>', 'warning')
                    GUI.emit(QtCore.SIGNAL("addMessage"), '')
                return [path]
        # Split directories
        split = splitDirectory(os.path.join(path, 'OEBPS', 'Images'), mode)
        path = [path]
        for tome in split:
            path.append(tome)
        return path
    else:
        # No splitting is necessary
        return [path]


def detectCorruption(tmpPath, orgPath):
    for root, dirs, files in os.walk(tmpPath, False):
        for name in files:
            if getImageFileName(name) is not None:
                path = os.path.join(root, name)
                pathOrg = os.path.join(orgPath, name)
                if os.path.getsize(path) == 0:
                    rmtree(os.path.join(tmpPath, '..', '..'), True)
                    raise RuntimeError('Image file %s is corrupted.' % pathOrg)
                try:
                    img = Image.open(path)
                    img.verify()
                    img = Image.open(path)
                    img.load()
                except:
                    rmtree(os.path.join(tmpPath, '..', '..'), True)
                    raise RuntimeError('Image file %s is corrupted.' % pathOrg)


def makeZIP(zipFilename, baseDir, isEPUB=False):
    zipFilename = os.path.abspath(zipFilename) + '.zip'
    zipOutput = zipfile.ZipFile(zipFilename, 'w', zipfile.ZIP_DEFLATED)
    if isEPUB:
        zipOutput.writestr('mimetype', 'application/epub+zip', zipfile.ZIP_STORED)
    for dirpath, dirnames, filenames in os.walk(baseDir):
        for name in filenames:
            path = os.path.normpath(os.path.join(dirpath, name))
            aPath = os.path.normpath(os.path.join(dirpath.replace(baseDir, ''), name))
            if os.path.isfile(path):
                zipOutput.write(path, aPath)
    zipOutput.close()
    return zipFilename


def Copyright():
    print(('comic2ebook v%(__version__)s. '
           'Written 2013 by Ciro Mattia Gonano and Pawel Jastrzebski.' % globals()))


def Usage():
    print("Generates EPUB/CBZ comic ebook from a bunch of images.")
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
                                " KFHDX8, KFA, KoMT, KoG, KoA, KoAHD) [Default=KHD]")
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
    detectCorruption(path + "/OEBPS/Images/", args[0])
    checkComicInfo(path + "/OEBPS/Images/", args[0])
    if options.webtoon:
        if options.customheight > 0:
            comic2panel.main(['-y ' + str(options.customheight), '-i', '-m', path], qtGUI)
        else:
            comic2panel.main(['-y ' + str(image.ProfileData.Profiles[options.profile][1][1]), '-i', '-m', path], qtGUI)
    if options.imgproc:
        print("\nProcessing images...")
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
    if GUI:
        if options.cbzoutput:
            GUI.emit(QtCore.SIGNAL("progressBarTick"), 'status', 'Compressing CBZ files')
        else:
            GUI.emit(QtCore.SIGNAL("progressBarTick"), 'status', 'Compressing EPUB files')
        GUI.emit(QtCore.SIGNAL("progressBarTick"), len(tomes) + 1)
        GUI.emit(QtCore.SIGNAL("progressBarTick"))
    options.baseTitle = options.title
    for tome in tomes:
        if len(tomes) > 1:
            tomeNumber += 1
            options.title = options.baseTitle + ' [' + str(tomeNumber) + '/' + str(len(tomes)) + ']'
        if options.cbzoutput:
            # if CBZ output wanted, compress all images and return filepath
            print("\nCreating CBZ file...")
            if len(tomes) > 1:
                filepath.append(getOutputFilename(args[0], options.output, '.cbz', ' ' + str(tomeNumber)))
            else:
                filepath.append(getOutputFilename(args[0], options.output, '.cbz', ''))
            makeZIP(tome + '_comic', tome + '/OEBPS/Images')
        else:
            print("\nCreating EPUB structure...")
            genEpubStruct(tome)
            # actually zip the ePub
            if len(tomes) > 1:
                filepath.append(getOutputFilename(args[0], options.output, '.epub', ' ' + str(tomeNumber)))
            else:
                filepath.append(getOutputFilename(args[0], options.output, '.epub', ''))
            makeZIP(tome + '_comic', tome, True)
        move(tome + '_comic.zip', filepath[-1])
        rmtree(tome, True)
        if GUI:
            GUI.emit(QtCore.SIGNAL("progressBarTick"))
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
    if options.profile == 'KDX' and options.cbzoutput:
        options.customheight = 1200
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