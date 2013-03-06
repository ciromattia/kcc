#!/usr/bin/env python
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
__version__ = '2.6'
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
                      "<link href=\"", "../" * (backref - 1), "stylesheet.css\" type=\"text/css\" rel=\"stylesheet\"/>\n",
                      "<link href=\"", "../" * (backref - 1), "page_styles.css\" type=\"text/css\" rel=\"stylesheet\"/>\n",
                      "</head>\n",
                      "<body class=\"kcc\">\n",
                      "<div class=\"kcc1\"><img src=\"", "../" * backref, "Images/", postfix, imgfile, "\" alt=\"",
                      imgfile, "\" class=\"kcc2\"/></div>\n",
                      #"<div id=\"", filename[0], "-1\">\n",
                      #"<a class=\"app-amzn-magnify\" data-app-amzn-magnify='{\"targetId\":\"", filename[0],
                      #"-1-magTargetParent\", \"ordinal\":1}'></a>\n",
                      #"</div>\n",
                      #"<div id=\"", filename[0], "-1-magTargetParent\" class=\"target-mag-parent\">\n",
                      #"<div class=\"target-mag-lb\">\n",
                      #"</div>\n",
                      #"<div id=\"", filename[0], "-1-magTarget\" class=\"target-mag\">\n",
                      #"<img src=\"../" * backref, "Images/", postfix, imgfile, "\" alt=\"", imgfile, "\"/>\n",
                      #"</div></div>\n",
                      "</body>\n",
                      "</html>"
                      ])
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
                  "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd\">\n",
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


def buildOPF(profile, dstdir, title, filelist, cover=None, righttoleft=False):
    opffile = os.path.join(dstdir, 'OEBPS', 'content.opf')
    # read the first file resolution
    profilelabel, deviceres, palette, gamma = image.ProfileData.Profiles[profile]
    imgres = str(deviceres[0]) + "x" + str(deviceres[1])
    if righttoleft:
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
                  "<meta name=\"fixed-layout\" content=\"true\"/>\n",
                  "<meta name=\"orientation-lock\" content=\"none\"/>\n",
                  "<meta name=\"original-resolution\" content=\"", imgres, "\"/>\n",
                  "<meta name=\"primary-writing-mode\" content=\"", writingmode, "\"/>\n",
                  "<meta name=\"rendition:layout\" content=\"pre-paginated\"/>\n",
                  "<meta name=\"rendition:orientation\" content=\"auto\"/>\n",
                  "</metadata>\n<manifest>\n<item id=\"ncx\" href=\"toc.ncx\" ",
                  "media-type=\"application/x-dtbncx+xml\"/>\n"
                  ])
    # set cover
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
    if (options.profile == 'K4' or options.profile == 'KHD') and splitCount > 0:
        splitCountUsed = 1
        while splitCountUsed <= splitCount:
            f.write("<item id=\"blank-page" + str(splitCountUsed) +
                    "\" href=\"Text/blank.html\" media-type=\"application/xhtml+xml\"/>\n")
            splitCountUsed += 1
    f.write("</manifest>\n<spine toc=\"ncx\">\n")
    splitCountUsed = 1
    for entry in reflist:
        if entry.endswith("-1"):
            if ((righttoleft and facing == 'left') or (not righttoleft and facing == 'right')) and \
                    (options.profile == 'K4' or options.profile == 'KHD'):
                f.write("<itemref idref=\"blank-page" + str(splitCountUsed) + "\" properties=\"layout-blank\"/>\n")
                splitCountUsed += 1
            f.write("<itemref idref=\"page_" + entry + "\" properties=\"page-spread-" + facing1 + "\"/>\n")
        elif entry.endswith("-2"):
            f.write("<itemref idref=\"page_" + entry + "\" properties=\"page-spread-" + facing2 + "\"/>\n")
            if righttoleft:
                facing = "right"
            else:
                facing = "left"
        else:
            f.write("<itemref idref=\"page_" + entry + "\" properties=\"page-spread-" + facing + "\"/>\n")
            if facing == 'right':
                facing = 'left'
            else:
                facing = 'right'
    f.write("</spine>\n<guide>\n</guide>\n</package>\n")
    f.close()
    # finish with standard ePub folders
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
    img.optimizeImage(options.gamma)
    img.cropWhiteSpace(10.0)
    if options.cutpagenumbers:
        img.cutPageNumber()
    img.resizeImage(options.upscale, options.stretch, options.black_borders, isSplit, toRight)
    if not options.notquantize:
        img.quantizeImage()


def dirImgProcess(path):
    global options
    global splitCount
    splitCount = 0
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
                    else:
                        toRight1 = True
                        toRight2 = False
                    if options.righttoleft:
                        if facing == "left":
                            splitCount += 1
                        facing = "right"
                    else:
                        if facing == "right":
                            splitCount += 1
                        facing = "left"
                    img0 = image.ComicPage(split[0], options.profile)
                    applyImgOptimization(img0, True, toRight1)
                    img0.saveToDir(dirpath, options.notquantize)
                    img1 = image.ComicPage(split[1], options.profile)
                    applyImgOptimization(img1, True, toRight2)
                    img1.saveToDir(dirpath, options.notquantize)
                else:
                    if facing == "right":
                        facing = "left"
                    else:
                        facing = "right"
                    applyImgOptimization(img)
                    img.saveToDir(dirpath, options.notquantize)


def genEpubStruct(path):
    global options
    filelist = []
    chapterlist = []
    cover = None
    os.mkdir(os.path.join(path, 'OEBPS', 'Text'))
    f = open(os.path.join(path, 'OEBPS', 'Text', 'page_styles.css'), 'w')
    f.writelines(["@page {\n",
                  "  margin-bottom: 0;\n",
                  "  margin-top: 0\n",
                  "}\n"])
    f.close()
    f = open(os.path.join(path, 'OEBPS', 'Text', 'stylesheet.css'), 'w')
    f.writelines([".kcc {\n",
                  "  display: block;\n",
                  "  margin-bottom: 0;\n",
                  "  margin-left: 0;\n",
                  "  margin-right: 0;\n",
                  "  margin-top: 0;\n",
                  "  padding-bottom: 0;\n",
                  "  padding-left: 0;\n",
                  "  padding-right: 0;\n",
                  "  padding-top: 0;\n",
                  "  text-align: left\n",
                  "}\n",
                  ".kcc1 {\n",
                  "  display: block;\n",
                  "  text-align: center\n",
                  "}\n",
                  ".kcc2 {\n",
                  "  height: auto;\n",
                  "  width: auto\n",
                  "}\n"])
    f.close()
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(path, 'OEBPS', 'Images')):
        chapter = False
        for afile in filenames:
            filename = getImageFileName(afile)
            if filename is not None:
                # put credits at the end
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
    buildOPF(options.profile, path, options.title, filelist, cover, options.righttoleft)
    if (options.profile == 'K4' or options.profile == 'KHD') and splitCount > 0:
        filelist.append(buildBlankHTML(os.path.join(path, 'OEBPS', 'Text')))


def getWorkFolder(afile):
    workdir = tempfile.mkdtemp()
    fname = os.path.splitext(afile)
    if os.path.isdir(afile):
        try:
            import shutil
            os.rmdir(workdir)   # needed for copytree() fails if dst already exists
            copytree(afile, workdir)
            path = workdir
        except OSError:
            raise
    elif fname[1].lower() == '.pdf':
        pdf = pdfjpgextract.PdfJpgExtract(afile)
        path = pdf.extract()
    else:
        cbx = cbxarchive.CBxArchive(afile)
        if cbx.isCbxFile():
            path = cbx.extract(workdir)
        else:
            raise TypeError
    move(path, path + "_temp")
    move(path + "_temp", os.path.join(path, 'OEBPS', 'Images'))
    return path


def Copyright():
    print ('comic2ebook v%(__version__)s. '
           'Written 2012 by Ciro Mattia Gonano.' % globals())


def Usage():
    print "Generates HTML, NCX and OPF for a Comic ebook from a bunch of images."
    print "Optimized for creating MOBI files to be read on Kindle Paperwhite."
    parser.print_help()


def main(argv=None):
    global parser, options, epub_path
    usage = "Usage: %prog [options] comic_file|comic_folder"
    parser = OptionParser(usage=usage, version=__version__)
    parser.add_option("-p", "--profile", action="store", dest="profile", default="KHD",
                      help="Device profile (Choose one among K1, K2, K3, K4, KDX, KDXG or KHD) [Default=KHD]")
    parser.add_option("-t", "--title", action="store", dest="title", default="defaulttitle",
                      help="Comic title [Default=filename]")
    parser.add_option("-m", "--manga-style", action="store_true", dest="righttoleft", default=False,
                      help="Manga style (Right-to-left reading and splitting) [Default=False]")
    parser.add_option("--noprocessing", action="store_false", dest="imgproc", default=True,
                      help="Do not apply image preprocessing (Page splitting and optimizations) [Default=True]")
    parser.add_option("--nodithering", action="store_true", dest="notquantize", default=False,
                      help="Disable image quantization [Default=False]")
    parser.add_option("--gamma", type="float", dest="gamma", default="0.0",
                      help="Apply gamma correction to linearize the image [Default=Auto]")
    parser.add_option("--upscale", action="store_true", dest="upscale", default=False,
                      help="Resize images smaller than device's resolution [Default=False]")
    parser.add_option("--stretch", action="store_true", dest="stretch", default=False,
                      help="Stretch images to device's resolution [Default=False]")
    parser.add_option("--blackborders", action="store_true", dest="black_borders", default=False,
                      help="Use black borders (Instead of white ones) when not stretching and ratio "
                      + "is not like the device's one [Default=False]")
    parser.add_option("--rotate", action="store_true", dest="rotate", default=False,
                      help="Rotate landscape pages instead of splitting them [Default=False]")
    parser.add_option("--nosplitrotate", action="store_true", dest="nosplitrotate", default=False,
                      help="Disable splitting and rotation [Default=False]")
    parser.add_option("--nocutpagenumbers", action="store_false", dest="cutpagenumbers", default=True,
                      help="Do not try to cut page numbering on images [Default=True]")
    parser.add_option("-o", "--output", action="store", dest="output", default=None,
                      help="Output generated EPUB to specified directory or file")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="Verbose output [Default=False]")
    options, args = parser.parse_args(argv)
    if len(args) != 1:
        parser.print_help()
        return
    path = getWorkFolder(args[0])
    if options.title == 'defaulttitle':
        options.title = os.path.splitext(os.path.basename(args[0]))[0]
    if options.imgproc:
        print "Processing images..."
        dirImgProcess(path + "/OEBPS/Images/")
    print "\nCreating ePub structure..."
    genEpubStruct(path)
    # actually zip the ePub
    if options.output is not None:
        if options.output.endswith('.epub'):
            epubpath = os.path.abspath(options.output)
        elif os.path.isdir(args[0]):
            epubpath = os.path.abspath(options.output) + "/" + os.path.basename(args[0]) + '.epub'
        else:
            epubpath = os.path.abspath(options.output) + "/" \
                + os.path.basename(os.path.splitext(args[0])[0]) + '.epub'
    elif os.path.isdir(args[0]):
        epubpath = args[0] + '.epub'
    else:
        epubpath = os.path.splitext(args[0])[0] + '.epub'
    make_archive(path + '_comic', 'zip', path)
    move(path + '_comic.zip', epubpath)
    rmtree(path)
    return epubpath


def getEpubPath():
    global epub_path
    return epub_path

if __name__ == "__main__":
    Copyright()
    main(sys.argv[1:])
    sys.exit(0)
