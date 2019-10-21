# -*- coding: utf-8 -*-
#
# Based on initial version of DualMetaFix. Copyright (C) 2013 Kevin Hendricks
# Changes for KCC Copyright (C) 2014-2019 Pawel Jastrzebski <pawelj@iosphe.re>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import struct
import mmap
import shutil


class DualMetaFixException(Exception):
    pass


# palm database offset constants
number_of_pdb_records = 76
first_pdb_record = 78

# important rec0 offsets
mobi_header_base = 16
mobi_header_length = 20
mobi_version = 36
title_offset = 84


def getint(data, ofs, sz='L'):
    i, = struct.unpack_from('>' + sz, data, ofs)
    return i


def writeint(data, ofs, n, slen='L'):
    if slen == 'L':
        return data[:ofs] + struct.pack('>L', n) + data[ofs + 4:]
    else:
        return data[:ofs] + struct.pack('>H', n) + data[ofs + 2:]


def getsecaddr(datain, secno):
    nsec = getint(datain, number_of_pdb_records, 'H')
    if (secno < 0) | (secno >= nsec):
        emsg = 'requested section number %d out of range (nsec=%d)' % (secno, nsec)
        raise DualMetaFixException(emsg)
    secstart = getint(datain, first_pdb_record + secno * 8)
    if secno == nsec - 1:
        secend = len(datain)
    else:
        secend = getint(datain, first_pdb_record + (secno + 1) * 8)
    return secstart, secend


def readsection(datain, secno):
    secstart, secend = getsecaddr(datain, secno)
    return datain[secstart:secend]


# overwrite section - must be exact same length as original
def replacesection(datain, secno, secdata):
    secstart, secend = getsecaddr(datain, secno)
    seclen = secend - secstart
    if len(secdata) != seclen:
        raise DualMetaFixException('section length change in replacesection')
    datain[secstart:secstart + seclen] = secdata


def get_exth_params(rec0):
    ebase = mobi_header_base + getint(rec0, mobi_header_length)
    if rec0[ebase:ebase + 4] != b'EXTH':
        raise DualMetaFixException('EXTH tag not found where expected')
    elen = getint(rec0, ebase + 4)
    enum = getint(rec0, ebase + 8)
    rlen = len(rec0)
    return ebase, elen, enum, rlen


def add_exth(rec0, exth_num, exth_bytes):
    ebase, elen, enum, rlen = get_exth_params(rec0)
    newrecsize = 8 + len(exth_bytes)
    newrec0 = rec0[0:ebase + 4] + struct.pack('>L', elen + newrecsize) + struct.pack('>L', enum + 1) + \
        struct.pack('>L', exth_num) + struct.pack('>L', newrecsize) + exth_bytes + rec0[ebase + 12:]
    newrec0 = writeint(newrec0, title_offset, getint(newrec0, title_offset) + newrecsize)
    # keep constant record length by removing newrecsize null bytes from end
    sectail = newrec0[-newrecsize:]
    if sectail != b'\0' * newrecsize:
        raise DualMetaFixException('add_exth: trimmed non-null bytes at end of section')
    newrec0 = newrec0[0:rlen]
    return newrec0


def read_exth(rec0, exth_num):
    exth_values = []
    ebase, elen, enum, rlen = get_exth_params(rec0)
    ebase += 12
    while enum > 0:
        exth_id = getint(rec0, ebase)
        if exth_id == exth_num:
            # We might have multiple exths, so build a list.
            exth_values.append(rec0[ebase + 8:ebase + getint(rec0, ebase + 4)])
        enum -= 1
        ebase = ebase + getint(rec0, ebase + 4)
    return exth_values


def del_exth(rec0, exth_num):
    ebase, elen, enum, rlen = get_exth_params(rec0)
    ebase_idx = ebase + 12
    enum_idx = 0
    while enum_idx < enum:
        exth_id = getint(rec0, ebase_idx)
        exth_size = getint(rec0, ebase_idx + 4)
        if exth_id == exth_num:
            newrec0 = rec0
            newrec0 = writeint(newrec0, title_offset, getint(newrec0, title_offset) - exth_size)
            newrec0 = newrec0[:ebase_idx] + newrec0[ebase_idx + exth_size:]
            newrec0 = newrec0[0:ebase + 4] + struct.pack('>L', elen - exth_size) + \
                struct.pack('>L', enum - 1) + newrec0[ebase + 12:]
            newrec0 += b'\0' * exth_size
            if rlen != len(newrec0):
                raise DualMetaFixException('del_exth: incorrect section size change')
            return newrec0
        enum_idx += 1
        ebase_idx = ebase_idx + exth_size
    return rec0


class DualMobiMetaFix:
    def __init__(self, infile, outfile, asin):
        shutil.copyfile(infile, outfile)
        f = open(outfile, "r+b")
        self.datain = mmap.mmap(f.fileno(), 0)
        self.datain_rec0 = readsection(self.datain, 0)

        # in the first mobi header
        # add 501 to "EBOK", add 113 as asin
        rec0 = self.datain_rec0
        rec0 = del_exth(rec0, 501)
        rec0 = del_exth(rec0, 113)
        rec0 = add_exth(rec0, 501, b'EBOK')
        rec0 = add_exth(rec0, 113, asin)
        replacesection(self.datain, 0, rec0)

        ver = getint(self.datain_rec0, mobi_version)
        self.combo = (ver != 8)
        if not self.combo:
            return

        exth121 = read_exth(self.datain_rec0, 121)
        if len(exth121) == 0:
            self.combo = False
            return
        else:
            # only pay attention to first exth121
            # (there should only be one)
            datain_kf8, = struct.unpack_from('>L', exth121[0], 0)
            if datain_kf8 == 0xffffffff:
                self.combo = False
                return
        self.datain_kfrec0 = readsection(self.datain, datain_kf8)

        # in the second header
        # add 501 to "EBOK", add 113 as asin
        rec0 = self.datain_kfrec0
        rec0 = del_exth(rec0, 501)
        rec0 = del_exth(rec0, 113)
        rec0 = add_exth(rec0, 501, b'EBOK')
        rec0 = add_exth(rec0, 113, asin)
        replacesection(self.datain, datain_kf8, rec0)

        self.datain.flush()
        self.datain.close()
