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
#
# Todo:
#   - Add gracefully exit for CBR if no rarfile.py and no unrar
#       executable are found
#   - Improve error reporting
#

__version__ = '1.10'

import os
import sys

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

class CBxArchive:
    def __init__(self, origFileName):
        self.cbxexts = ['.cbz', '.cbr']
        self.origFileName = origFileName
        self.filename = os.path.splitext(origFileName)
        self.path = self.filename[0]

    def isCbxFile(self):
        result = (self.filename[1].lower() in self.cbxexts)
        if result == True:
            return result
        return False

    def getPath(self):
        return self.path

    def extractCBZ(self):
        try:
            from zipfile import ZipFile
        except ImportError:
            self.cbzFile = None
        cbzFile = ZipFile(self.origFileName)
        for f in cbzFile.namelist():
            if (f.startswith('__MACOSX') or f.endswith('.DS_Store')):
                pass # skip MacOS special files
            elif f.endswith('/'):
                try:
                    os.makedirs(self.path+f)
                except:
                    pass #the dir exists so we are going to extract the images only.
            else:
                cbzFile.extract(f, self.path)

    def extractCBR(self):
        try:
            import rarfile
        except ImportError:
            self.cbrFile = None
        cbrFile = rarfile.RarFile(self.origFileName)
        for f in cbrFile.namelist():
            if f.endswith('/'):
                try:
                    os.makedirs(self.path+f)
                except:
                    pass #the dir exists so we are going to extract the images only.
            else:
                cbrFile.extract(f, self.path)

    def extract(self):
        if ('.cbr' == self.filename[1].lower()):
            self.extractCBR()
        elif ('.cbz' == self.filename[1].lower()):
            self.extractCBZ()
        dir = os.listdir(self.path)
        if (len(dir) == 1):
            import shutil
            for f in os.listdir(self.path + "/" + dir[0]):
                shutil.move(self.path + "/" + dir[0] + "/" + f,self.path)
            os.rmdir(self.path + "/" + dir[0])

class HTMLbuilder:
    def getResult(self):
        if (self.filename[0].startswith('.') or (self.filename[1] != '.png' and self.filename[1] != '.jpg' and self.filename[1] != '.jpeg')):
            return None
        return self.filename

    def __init__(self, dstdir, file):
        self.filename = os.path.splitext(file)
        basefilename = self.filename[0]
        ext = self.filename[1]
        if (basefilename.startswith('.') or (ext != '.png' and ext != '.jpg' and ext != '.jpeg')):
            return
        htmlfile = dstdir + '/' + basefilename + '.html'
        f = open(htmlfile, "w");
        f.writelines(["<!DOCTYPE html SYSTEM \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">\n",
                    "<html xmlns=\"http://www.w3.org/1999/xhtml\">\n",
                    "<head>\n",
                    "<title>",basefilename,"</title>\n",
                    "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>\n",
                    "</head>\n",
                    "<body>\n",
                    "<div><img src=\"",file,"\" /></div>\n",
                    "</body>\n",
                    "</html>"
                    ])
        f.close()

class NCXbuilder:
    def __init__(self, dstdir, title):
        ncxfile = dstdir + '/content.ncx'
        f = open(ncxfile, "w");
        f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
            "<!DOCTYPE ncx PUBLIC \"-//NISO//DTD ncx 2005-1//EN\" \"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd\">\n",
            "<ncx version=\"2005-1\" xml:lang=\"en-US\" xmlns=\"http://www.daisy.org/z3986/2005/ncx/\">\n",
            "<head>\n</head>\n",
            "<docTitle><text>",title,"</text></docTitle>\n",
            "<navMap></navMap>\n</ncx>"
            ])
        f.close()
        return

class OPFBuilder:
    def __init__(self, dstdir, title, filelist):
        opffile = dstdir + '/content.opf'
        # read the first file resolution
        try:
            from PIL import Image
            im = Image.open(dstdir + "/" + filelist[0][0] + filelist[0][1])
            width, height = im.size
            imgres = str(width) + "x" + str(height)
        except ImportError:
	    print "Could not load PIL, falling back on default HD"
            imgres = "758x1024"
        f = open(opffile, "w");
        f.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
            "<package version=\"2.0\" unique-identifier=\"PrimaryID\" xmlns=\"http://www.idpf.org/2007/opf\">\n",
            "<metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:opf=\"http://www.idpf.org/2007/opf\">\n",
            "<dc:title>",title,"</dc:title>\n",
            "<dc:language>en-US</dc:language>\n",
            "<meta name=\"book-type\" content=\"comic\"/>\n",
            "<meta name=\"zero-gutter\" content=\"true\"/>\n",
            "<meta name=\"zero-margin\" content=\"true\"/>\n",
            "<meta name=\"fixed-layout\" content=\"true\"/>\n",
            "<meta name=\"orientation-lock\" content=\"portrait\"/>\n",
            "<meta name=\"original-resolution\" content=\"" + imgres + "\"/>\n",
            "</metadata><manifest><item id=\"ncx\" href=\"content.ncx\" media-type=\"application/x-dtbncx+xml\"/>\n"])
        for filename in filelist:
            f.write("<item id=\"page_" + filename[0] + "\" href=\"" + filename[0] + ".html\" media-type=\"application/xhtml+xml\"/>\n")
        for filename in filelist:
            if ('.png' == filename[1]):
                mt = 'image/png';
            else:
                mt = 'image/jpeg';
            f.write("<item id=\"img_" + filename[0] + "\" href=\"" + filename[0] + filename[1] + "\" media-type=\"" + mt + "\"/>\n")
        f.write("</manifest>\n<spine toc=\"ncx\">\n")
        for filename in filelist:
            f.write("<itemref idref=\"page_" + filename[0] + "\" />\n")
        f.write("</spine>\n<guide>\n</guide>\n</package>\n")
        f.close()
        return

if __name__ == "__main__":
    sys.stdout=Unbuffered(sys.stdout)
    print ('comic2ebook v%(__version__)s. '
       'Written 2012 by Ciro Mattia Gonano.' % globals())
    if len(sys.argv)<2 or len(sys.argv)>3:
        print "Generates HTML, NCX and OPF for a Comic ebook from a bunch of images"
        print "Optimized for creating Mobipockets to be read into Kindle Paperwhite"
        print "Usage:"
        print "    %s <dir> <title>" % sys.argv[0]
        print " <title> is optional"
        sys.exit(1)
    else:
        dir = sys.argv[1]
        cbx = CBxArchive(dir)
        if cbx.isCbxFile():
            cbx.extract()
            dir = cbx.getPath()
        if len(sys.argv)==3:
            title = sys.argv[2]
        else:
            title = "comic"
        filelist = []
        for file in os.listdir(dir):
            filename = HTMLbuilder(dir,file).getResult()
            if (filename != None):
                filelist.append(filename)
        NCXbuilder(dir,title)
        OPFBuilder(dir,title,filelist)
    sys.exit(0)
