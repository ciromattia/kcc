#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
#
# This is a python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
#
# This script strips the penultimate record from a Mobipocket file.
# This is useful because the current KindleGen add a compressed copy
# of the source files used in this record, making the ebook produced
# about twice as big as it needs to be.
#
#
# This is free and unencumbered software released into the public domain.
# 
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
# 
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
# 
# For more information, please refer to <http://unlicense.org/>
#
# Written by Paul Durrant, 2010-2011, paul@durrant.co.uk, pdurrant on mobileread.com
# With enhancements by Kevin Hendricks, KevinH on mobileread.com
#
# Changelog
#  1.00 - Initial version
#  1.10 - Added an option to output the stripped data
#  1.20 - Added check for source files section (thanks Piquan)
#  1.30 - Added prelim Support for K8 style mobis
#  1.31 - removed the SRCS section but kept a 0 size entry for it
#  1.32 - removes the SRCS section and its entry, now updates metadata 121 if needed
#  1.33 - now uses and modifies mobiheader SRCS and CNT
#  1.34 - added credit for Kevin Hendricks
#  1.35 - fixed bug when more than one compilation (SRCS/CMET) records

__version__ = '1.35'

import sys
import struct
import binascii

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)


class StripException(Exception):
    pass


class SectionStripper:
    def loadSection(self, section):
        if (section + 1 == self.num_sections):
            endoff = len(self.data_file)
        else:
            endoff = self.sections[section + 1][0]
        off = self.sections[section][0]
        return self.data_file[off:endoff]

    def patch(self, off, new):
        self.data_file = self.data_file[:off] + new + self.data_file[off+len(new):]

    def strip(self, off, len):
        self.data_file = self.data_file[:off] + self.data_file[off+len:]

    def patchSection(self, section, new, in_off = 0):
        if (section + 1 == self.num_sections):
            endoff = len(self.data_file)
        else:
            endoff = self.sections[section + 1][0]
        off = self.sections[section][0]
        assert off + in_off + len(new) <= endoff
        self.patch(off + in_off, new)

    def updateEXTH121(self, srcs_secnum, srcs_cnt, mobiheader):
        mobi_length, = struct.unpack('>L',mobiheader[0x14:0x18])
        exth_flag, = struct.unpack('>L', mobiheader[0x80:0x84])
        exth = 'NONE'
        try:
            if exth_flag & 0x40:
                exth = mobiheader[16 + mobi_length:]
                if (len(exth) >= 4) and (exth[:4] == 'EXTH'):
                    nitems, = struct.unpack('>I', exth[8:12])
                    pos = 12
                    for i in xrange(nitems):
                        type, size = struct.unpack('>II', exth[pos: pos + 8])
                        # print type, size
                        if type == 121:
                            boundaryptr, =struct.unpack('>L',exth[pos+8: pos + size])
                            if srcs_secnum <= boundaryptr:
                                boundaryptr -= srcs_cnt
                                prefix = mobiheader[0:16 + mobi_length + pos + 8]
                                suffix = mobiheader[16 + mobi_length + pos + 8 + 4:]
                                nval = struct.pack('>L',boundaryptr)
                                mobiheader = prefix + nval + suffix
                        pos += size
        except:
            pass
        return mobiheader

    def __init__(self, datain):
        if datain[0x3C:0x3C+8] != 'BOOKMOBI':
            raise StripException("invalid file format")
        self.num_sections, = struct.unpack('>H', datain[76:78])
        
        # get mobiheader and check SRCS section number and count
        offset0, = struct.unpack_from('>L', datain, 78)
        offset1, = struct.unpack_from('>L', datain, 86)
        mobiheader = datain[offset0:offset1]
        srcs_secnum, srcs_cnt = struct.unpack_from('>2L', mobiheader, 0xe0)
        if srcs_secnum == 0xffffffff or srcs_cnt == 0:
            raise StripException("File doesn't contain the sources section.")

        print "Found SRCS section number %d, and count %d" % (srcs_secnum, srcs_cnt)
        # find its offset and length
        next = srcs_secnum + srcs_cnt
        srcs_offset, flgval = struct.unpack_from('>2L', datain, 78+(srcs_secnum*8))
        next_offset, flgval = struct.unpack_from('>2L', datain, 78+(next*8))
        srcs_length = next_offset - srcs_offset
        if datain[srcs_offset:srcs_offset+4] != 'SRCS':
            raise StripException("SRCS section num does not point to SRCS.")
        print "   beginning at offset %0x and ending at offset %0x" % (srcs_offset, srcs_length)

        # it appears bytes 68-71 always contain (2*num_sections) + 1
        # this is not documented anyplace at all but it appears to be some sort of next 
        # available unique_id used to identify specific sections in the palm db
        self.data_file = datain[:68] + struct.pack('>L',((self.num_sections-srcs_cnt)*2+1))
        self.data_file += datain[72:76]

        # write out the number of sections reduced by srtcs_cnt
        self.data_file = self.data_file + struct.pack('>H',self.num_sections-srcs_cnt)

        # we are going to remove srcs_cnt SRCS sections so the offset of every entry in the table
        # up to the srcs secnum must begin 8 bytes earlier per section removed (each table entry is 8 )
        delta = -8 * srcs_cnt
        for i in xrange(srcs_secnum):
            offset, flgval = struct.unpack_from('>2L', datain, 78+(i*8))
            offset += delta
            self.data_file += struct.pack('>L',offset) + struct.pack('>L',flgval)
            
        # for every record after the srcs_cnt SRCS records we must start it
        # earlier by 8*srcs_cnt + the length of the srcs sections themselves)
        delta = delta - srcs_length
        for i in xrange(srcs_secnum+srcs_cnt,self.num_sections):
            offset, flgval = struct.unpack_from('>2L', datain, 78+(i*8))
            offset += delta
            flgval = 2 * (i - srcs_cnt)
            self.data_file += struct.pack('>L',offset) + struct.pack('>L',flgval)

        # now pad it out to begin right at the first offset
        # typically this is 2 bytes of nulls
        first_offset, flgval = struct.unpack_from('>2L', self.data_file, 78)
        self.data_file += '\0' * (first_offset - len(self.data_file))

        # now finally add on every thing up to the original src_offset
        self.data_file += datain[offset0: srcs_offset]
    
        # and everything afterwards
        self.data_file += datain[srcs_offset+srcs_length:]
        
        #store away the SRCS section in case the user wants it output
        self.stripped_data_header = datain[srcs_offset:srcs_offset+16]
        self.stripped_data = datain[srcs_offset+16:srcs_offset+srcs_length]

        # update the number of sections count
        self.num_section = self.num_sections - srcs_cnt
        
        # update the srcs_secnum and srcs_cnt in the mobiheader
        offset0, flgval0 = struct.unpack_from('>2L', self.data_file, 78)
        offset1, flgval1 = struct.unpack_from('>2L', self.data_file, 86)
        mobiheader = self.data_file[offset0:offset1]
        mobiheader = mobiheader[:0xe0]+ struct.pack('>L', 0xffffffff) + struct.pack('>L', 0) + mobiheader[0xe8:]

        # if K8 mobi, handle metadata 121 in old mobiheader
        mobiheader = self.updateEXTH121(srcs_secnum, srcs_cnt, mobiheader)
        self.data_file = self.data_file[0:offset0] + mobiheader + self.data_file[offset1:]
        print "done"

    def getResult(self):
        return self.data_file

    def getStrippedData(self):
        return self.stripped_data

    def getHeader(self):
        return self.stripped_data_header

if __name__ == "__main__":
    sys.stdout=Unbuffered(sys.stdout)
    print ('KindleStrip v%(__version__)s. '
       'Written 2010-2012 by Paul Durrant and Kevin Hendricks.' % globals())
    if len(sys.argv)<3 or len(sys.argv)>4:
        print "Strips the Sources record from Mobipocket ebooks"
        print "For ebooks generated using KindleGen 1.1 and later that add the source"
        print "Usage:"
        print "    %s <infile> <outfile> <strippeddatafile>" % sys.argv[0]
        print "<strippeddatafile> is optional."
        sys.exit(1)
    else:
        infile = sys.argv[1]
        outfile = sys.argv[2]
        data_file = file(infile, 'rb').read()
        try:
            strippedFile = SectionStripper(data_file)
            file(outfile, 'wb').write(strippedFile.getResult())
            print "Header Bytes: " + binascii.b2a_hex(strippedFile.getHeader())
            if len(sys.argv)==4:
                file(sys.argv[3], 'wb').write(strippedFile.getStrippedData())
        except StripException, e:
            print "Error: %s" % e
            sys.exit(1)
    sys.exit(0)
