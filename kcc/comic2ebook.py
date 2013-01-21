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
# Changelog
#  1.00 - Initial version
#  1.10 - Added support for CBZ/CBR files
#  1.11 - Added support for ZIP/RAR extensions
#  1.20 - Comic optimizations! Split pages not target-oriented (landscape
#       with portrait target or portrait with landscape target), add palette
#       and other image optimizations from Mangle.
#       WARNING: PIL is required for all image mangling!
#  1.30 - Fixed an issue in OPF generation for device resolution
#       Reworked options system (call with -h option to get the inline help)
#  1.40 - Added some options for controlling image optimization
#       Further optimization (ImageOps, page numbering cut, autocontrast)
#  1.41 - Fixed a serious bug on resizing when img ratio was bigger than device one
#  1.50 - Support for subfolders
#
# Todo:
#   - Add gracefully exit for CBR if no rarfile.py and no unrar
#       executable are found
#   - Improve error reporting

__version__ = '1.50'
__license__   = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>'
__docformat__ = 'restructuredtext en'

import os
import sys
from optparse import OptionParser
import image, cbxarchive, pdfjpgextract

def buildHTML(path,file):
    filename = getImageFileName(file)
    if filename is not None:
        htmlfile = os.path.join(path,filename[0] + '.html')
        f = open(htmlfile, "w")
        f.writelines(["<!DOCTYPE html SYSTEM \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">\n",
                      "<html xmlns=\"http://www.w3.org/1999/xhtml\">\n",
                      "<head>\n",
                      "<title>",filename[0],"</title>\n",
                      "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>\n",
                      "</head>\n",
                      "<body>\n",
                      "<div><img src=\"",file,"\" /></div>\n",
                      "</body>\n",
                      "</html>"
                      ])
        f.close()
        return path,file

def buildNCX(dstdir, title, chapters):
    ncxfile = dstdir + '/toc.ncx'
    f = open(ncxfile, "w")
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
        "<!DOCTYPE ncx PUBLIC \"-//NISO//DTD ncx 2005-1//EN\" \"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd\">\n",
        "<ncx version=\"2005-1\" xml:lang=\"en-US\" xmlns=\"http://www.daisy.org/z3986/2005/ncx/\">\n",
        "<head>\n</head>\n",
        "<docTitle><text>",title,"</text></docTitle>\n",
        "<navMap>"
        ])
    for chapter in chapters:
        folder = chapter[0].replace(dstdir,'').lstrip('/')
        title = os.path.basename(folder)
        filename = getImageFileName(os.path.join(folder,chapter[1]))
        f.write("<navPoint id=\"" + folder + "\"><navLabel><text>" + title
                + "</text></navLabel><content src=\"" + filename[0] + ".html\"/></navPoint>\n")
    f.write("</navMap>\n</ncx>")
    f.close()
    return

def buildOPF(profile, dstdir, title, filelist, cover=None):
    opffile = dstdir + '/content.opf'
    # read the first file resolution
    profilelabel, deviceres, palette = image.ProfileData.Profiles[profile]
    imgres = str(deviceres[0]) + "x" + str(deviceres[1])
    f = open(opffile, "w")
    f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
        "<package version=\"2.0\" unique-identifier=\"PrimaryID\" xmlns=\"http://www.idpf.org/2007/opf\">\n",
        "<metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:opf=\"http://www.idpf.org/2007/opf\">\n",
        "<dc:title>",title,"</dc:title>\n",
        "<dc:language>en-US</dc:language>\n",
        "<meta name=\"cover\" content=\"cover\"/>\n",
        "<meta name=\"book-type\" content=\"comic\"/>\n",
        "<meta name=\"zero-gutter\" content=\"true\"/>\n",
        "<meta name=\"zero-margin\" content=\"true\"/>\n",
        "<meta name=\"fixed-layout\" content=\"true\"/>\n",
        "<meta name=\"orientation-lock\" content=\"portrait\"/>\n",
        "<meta name=\"original-resolution\" content=\"" + imgres + "\"/>\n",
        "</metadata>\n<manifest>\n<item id=\"ncx\" href=\"toc.ncx\" media-type=\"application/x-dtbncx+xml\"/>\n"
        ])
    # set cover
    if cover is not None:
        folder = cover[0].replace(dstdir,'').lstrip('/')
        filename = getImageFileName(cover[1])
        if '.png' == filename[1]:
            mt = 'image/png'
        else:
            mt = 'image/jpeg'
        f.write("<item id=\"cover\" href=\"" + os.path.join(folder,cover[1]) + "\" media-type=\"" + mt + "\"/>\n")
    for path in filelist:
        folder = path[0].replace(dstdir,'').lstrip('/')
        filename = getImageFileName(path[1])
        uniqueid = os.path.join(folder,filename[0]).replace('/','_')
        f.write("<item id=\"page_" + uniqueid + "\" href=\"" + os.path.join(folder,filename[0])
                + ".html\" media-type=\"application/xhtml+xml\"/>\n")
        if '.png' == filename[1]:
            mt = 'image/png'
        else:
            mt = 'image/jpeg'
        f.write("<item id=\"img_" + uniqueid + "\" href=\"" + os.path.join(folder,path[1]) + "\" media-type=\"" + mt + "\"/>\n")
    f.write("</manifest>\n<spine toc=\"ncx\">\n")
    for path in filelist:
        folder = path[0].replace(dstdir,'').lstrip('/')
        filename = getImageFileName(path[1])
        uniqueid = os.path.join(folder,filename[0]).replace('/','_')
        f.write("<itemref idref=\"page_" + uniqueid + "\" />\n")
    f.write("</spine>\n<guide>\n</guide>\n</package>\n")
    f.close()
    return

def getImageFileName(file):
    filename = os.path.splitext(file)
    if filename[0].startswith('.') or (filename[1].lower() != '.png' and filename[1].lower() != '.jpg' and filename[1].lower() != '.jpeg'):
        return None
    return filename

def isInFilelist(file,list):
    filename = os.path.splitext(file)
    seen = False
    for item in list:
        if filename[0] == item[0]:
            seen = True
    return seen

def applyImgOptimization(img):
    img.optimizeImage()
    img.cropWhiteSpace(10.0)
    if options.cutpagenumbers:
        img.cutPageNumber()
    img.resizeImage(options.upscale,options.stretch)
    img.quantizeImage()


def dirImgProcess(path):
    global options

    for (dirpath, dirnames, filenames) in os.walk(path):
        for file in filenames:
            if getImageFileName(file) is not None:
                if options.verbose:
                    print "Optimizing " + file + " for " + options.profile
                else:
                    print ".",
                img = image.ComicPage(os.path.join(dirpath,file), options.profile)
                split = img.splitPage(dirpath, options.righttoleft)
                if split is not None:
                    if options.verbose:
                        print "Splitted " + file
                    img0 = image.ComicPage(split[0],options.profile)
                    img1 = image.ComicPage(split[1],options.profile)
                    applyImgOptimization(img0)
                    img0.saveToDir(dirpath)
                    applyImgOptimization(img1)
                    img1.saveToDir(dirpath)
                else:
                    applyImgOptimization(img)
                    img.saveToDir(dirpath)

def genEpubStruct(path):
    global options
    filelist = []
    chapterlist = []
    cover = None
    for (dirpath, dirnames, filenames) in os.walk(path):
        chapter = False
        for file in filenames:
            if getImageFileName(file) is not None:
                # put credits at the end
                if "credits" in file.lower():
                    os.rename(os.path.join(dirpath,file), os.path.join(dirpath,'ZZZ999_'+file))
                    file = 'ZZZ999_'+file
                filelist.append(buildHTML(dirpath,file))
                if not chapter:
                    chapterlist.append((dirpath,filelist[-1][1]))
                    chapter = True
                if cover is None:
                    cover = filelist[-1]
    if options.title == 'defaulttitle':
        options.title = os.path.basename(path)
    buildNCX(path,options.title,chapterlist)
    # ensure we're sorting files alphabetically
    filelist = sorted(filelist, key=lambda name: (name[0].lower(), name[1].lower()))
    buildOPF(options.profile,path,options.title,filelist,cover)

def getWorkFolder(file):
    fname = os.path.splitext(file)
    if fname[1].lower() == '.pdf':
        pdf = pdfjpgextract.PdfJpgExtract(file)
        pdf.extract()
        return pdf.getPath()
    else:
        cbx = cbxarchive.CBxArchive(file)
        if cbx.isCbxFile():
            cbx.extract()
            return cbx.getPath()
        else:
            try:
                import shutil
                if not os.path.isdir(file + "_orig"):
                    shutil.copytree(file, file + "_orig")
                return file
            except OSError:
                raise

def Copyright():
    print ('comic2ebook v%(__version__)s. '
        'Written 2012 by Ciro Mattia Gonano.' % globals())

def Usage():
    print "Generates HTML, NCX and OPF for a Comic ebook from a bunch of images"
    print "Optimized for creating Mobipockets to be read into Kindle Paperwhite"
    parser.print_help()

def main(argv=None):
    global parser, options
    usage = "Usage: %prog [options] comic_file|comic_folder"
    parser = OptionParser(usage=usage, version=__version__)
    parser.add_option("-p", "--profile", action="store", dest="profile", default="KHD",
                      help="Device profile (choose one among K1, K2, K3, K4, KDX, KDXG or KHD) [default=KHD]")
    parser.add_option("-t", "--title", action="store", dest="title", default="defaulttitle",
                      help="Comic title [default=filename]")
    parser.add_option("-m", "--manga-style", action="store_true", dest="righttoleft", default=False,
                      help="Split pages 'manga style' (right-to-left reading) [default=False]")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="Verbose output [default=False]")
    parser.add_option("-i", "--image-processing", action="store_false", dest="imgproc", default=True,
                    help="Apply image preprocessing (page splitting and optimizations) [default=True]")
    parser.add_option("--upscale-images", action="store_true", dest="upscale", default=False,
                    help="Resize images smaller than device's resolution [default=False]")
    parser.add_option("--stretch-images", action="store_true", dest="stretch", default=False,
                    help="Stretch images to device's resolution [default=False]")
    parser.add_option("--cut-page-numbers", action="store_false", dest="cutpagenumbers", default=True,
                    help="Try to cut page numbering on images [default=True]")
    options, args = parser.parse_args(argv)
    if len(args) != 1:
        parser.print_help()
        return
    path = args[0]
    path = getWorkFolder(path)
    if options.imgproc:
        print "Processing images..."
        dirImgProcess(path)
    print "Creating ePub structure..."
    genEpubStruct(path)


if __name__ == "__main__":
    Copyright()
    main(sys.argv[1:])
    sys.exit(0)
