# Based on initial version of KindleUnpack. Copyright (C) 2009 Charles M. Hannum <root@ihack.net>
# Improvements Copyright (C) 2009-2012 P. Durrant, K. Hendricks, S. Siebert, fandrieu, DiapDealer, nickredding
# Changes for KCC Copyright (C) 2013 Pawel Jastrzebski <pawelj@vulturis.eu>
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
# from uuid import uuid4

# important  pdb header offsets
unique_id_seed = 68
number_of_pdb_records = 76

# important palmdoc header offsets
book_length = 4
book_record_count = 8
first_pdb_record = 78

# important rec0 offsets
length_of_book = 4
mobi_header_base = 16
mobi_header_length = 20
mobi_type = 24
mobi_version = 36
first_non_text = 80
title_offset = 84
first_image_record = 108
first_content_index = 192
last_content_index = 194
kf8_last_content_index = 192  # for KF8 mobi headers
fcis_index = 200
flis_index = 208
srcs_index = 224
srcs_count = 228
primary_index = 244
datp_index = 256
huffoff = 112
hufftbloff = 120


def getint(datain, ofs, sz='L'):
    i, = struct.unpack_from('>'+sz, datain, ofs)
    return i


def writeint(datain, ofs, n, length='L'):
    if length == 'L':
        return datain[:ofs]+struct.pack('>L', n)+datain[ofs+4:]
    else:
        return datain[:ofs]+struct.pack('>H', n)+datain[ofs+2:]


def getsecaddr(datain, secno):
    nsec = getint(datain, number_of_pdb_records, 'H')
    assert secno >= 0 & secno < nsec, 'secno %d out of range (nsec=%d)' % (secno, nsec)
    secstart = getint(datain, first_pdb_record+secno*8)
    if secno == nsec-1:
        secend = len(datain)
    else:
        secend = getint(datain, first_pdb_record+(secno+1)*8)
    return secstart, secend


def readsection(datain, secno):
    secstart, secend = getsecaddr(datain, secno)
    return datain[secstart:secend]


def writesection(datain, secno, secdata):  # overwrite, accounting for different length
    dataout = deletesectionrange(datain, secno, secno)
    return insertsection(dataout, secno, secdata)


def nullsection(datain, secno):  # make it zero-length without deleting it
    datalst = []
    nsec = getint(datain, number_of_pdb_records, 'H')
    secstart, secend = getsecaddr(datain, secno)
    zerosecstart, zerosecend = getsecaddr(datain, 0)
    dif = secend-secstart
    datalst.append(datain[:first_pdb_record])
    for i in range(0, secno+1):
        ofs, flgval = struct.unpack_from('>2L', datain, first_pdb_record+i*8)
        datalst.append(struct.pack('>L', ofs) + struct.pack('>L', flgval))
    for i in range(secno+1, nsec):
        ofs, flgval = struct.unpack_from('>2L', datain, first_pdb_record+i*8)
        ofs -= dif
        datalst.append(struct.pack('>L', ofs) + struct.pack('>L', flgval))
    lpad = zerosecstart - (first_pdb_record + 8*nsec)
    if lpad > 0:
        datalst.append('\0' * lpad)
    datalst.append(datain[zerosecstart: secstart])
    datalst.append(datain[secend:])
    dataout = "".join(datalst)
    return dataout


def deletesectionrange(datain, firstsec, lastsec):  # delete a range of sections
    datalst = []
    firstsecstart, firstsecend = getsecaddr(datain, firstsec)
    lastsecstart, lastsecend = getsecaddr(datain, lastsec)
    zerosecstart, zerosecend = getsecaddr(datain, 0)
    dif = lastsecend - firstsecstart + 8*(lastsec-firstsec+1)
    nsec = getint(datain, number_of_pdb_records, 'H')
    datalst.append(datain[:unique_id_seed])
    datalst.append(struct.pack('>L', 2*(nsec-(lastsec-firstsec+1))+1))
    datalst.append(datain[unique_id_seed+4:number_of_pdb_records])
    datalst.append(struct.pack('>H', nsec-(lastsec-firstsec+1)))
    newstart = zerosecstart - 8*(lastsec-firstsec+1)
    for i in range(0, firstsec):
        ofs, flgval = struct.unpack_from('>2L', datain, first_pdb_record+i*8)
        ofs -= 8 * (lastsec - firstsec + 1)
        datalst.append(struct.pack('>L', ofs) + struct.pack('>L', flgval))
    for i in range(lastsec+1, nsec):
        ofs, flgval = struct.unpack_from('>2L', datain, first_pdb_record+i*8)
        ofs -= dif
        flgval = 2*(i-(lastsec-firstsec+1))
        datalst.append(struct.pack('>L', ofs) + struct.pack('>L', flgval))
    lpad = newstart - (first_pdb_record + 8*(nsec - (lastsec - firstsec + 1)))
    if lpad > 0:
        datalst.append('\0' * lpad)
    datalst.append(datain[zerosecstart:firstsecstart])
    datalst.append(datain[lastsecend:])
    dataout = "".join(datalst)
    return dataout


def insertsection(datain, secno, secdata):  # insert a new section
    datalst = []
    nsec = getint(datain, number_of_pdb_records, 'H')
    secstart, secend = getsecaddr(datain, secno)
    zerosecstart, zerosecend = getsecaddr(datain, 0)
    dif = len(secdata)
    datalst.append(datain[:unique_id_seed])
    datalst.append(struct.pack('>L', 2*(nsec+1)+1))
    datalst.append(datain[unique_id_seed+4:number_of_pdb_records])
    datalst.append(struct.pack('>H', nsec+1))
    newstart = zerosecstart + 8
    for i in range(0, secno):
        ofs, flgval = struct.unpack_from('>2L', datain, first_pdb_record+i*8)
        ofs += 8
        datalst.append(struct.pack('>L', ofs) + struct.pack('>L', flgval))
    datalst.append(struct.pack('>L', secstart + 8) + struct.pack('>L', (2*secno)))
    for i in range(secno, nsec):
        ofs, flgval = struct.unpack_from('>2L', datain, first_pdb_record+i*8)
        ofs = ofs + dif + 8
        flgval = 2*(i+1)
        datalst.append(struct.pack('>L', ofs) + struct.pack('>L', flgval))
    lpad = newstart - (first_pdb_record + 8*(nsec + 1))
    if lpad > 0:
        datalst.append('\0' * lpad)
    datalst.append(datain[zerosecstart:secstart])
    datalst.append(secdata)
    datalst.append(datain[secstart:])
    dataout = "".join(datalst)
    return dataout


def insertsectionrange(sectionsource, firstsec, lastsec, sectiontarget, targetsec):  # insert a range of sections
    dataout = sectiontarget
    for idx in range(lastsec, firstsec-1, -1):
        dataout = insertsection(dataout, targetsec, readsection(sectionsource, idx))
    return dataout


def get_exth_params(rec0):
    ebase = mobi_header_base + getint(rec0, mobi_header_length)
    elen = getint(rec0, ebase+4)
    enum = getint(rec0, ebase+8)
    return ebase, elen, enum


def add_exth(rec0, exth_num, exth_bytes):
    ebase, elen, enum = get_exth_params(rec0)
    newrecsize = 8+len(exth_bytes)
    newrec0 = rec0[0:ebase+4]+struct.pack('>L', elen+newrecsize)+struct.pack('>L', enum+1) +\
        struct.pack('>L', exth_num) + struct.pack('>L', newrecsize)+exth_bytes+rec0[ebase+12:]
    newrec0 = writeint(newrec0, title_offset, getint(newrec0, title_offset)+newrecsize)
    return newrec0


def read_exth(rec0, exth_num):
    exth_values = []
    ebase, elen, enum = get_exth_params(rec0)
    ebase += 12
    while enum > 0:
        exth_id = getint(rec0, ebase)
        if exth_id == exth_num:
            # We might have multiple exths, so build a list.
            exth_values.append(rec0[ebase+8:ebase+getint(rec0, ebase+4)])
        enum -= 1
        ebase = ebase+getint(rec0, ebase+4)
    return exth_values


def write_exth(rec0, exth_num, exth_bytes):
    ebase, elen, enum = get_exth_params(rec0)
    ebase_idx = ebase+12
    enum_idx = enum
    while enum_idx > 0:
        exth_id = getint(rec0, ebase_idx)
        if exth_id == exth_num:
            dif = len(exth_bytes)+8-getint(rec0, ebase_idx+4)
            newrec0 = rec0
            if dif != 0:
                newrec0 = writeint(newrec0, title_offset, getint(newrec0, title_offset)+dif)
            return newrec0[:ebase+4]+struct.pack('>L', elen+len(exth_bytes)+8-getint(rec0, ebase_idx+4)) +\
                struct.pack('>L', enum)+rec0[ebase+12:ebase_idx+4] +\
                struct.pack('>L', len(exth_bytes)+8)+exth_bytes +\
                rec0[ebase_idx+getint(rec0, ebase_idx+4):]
        enum_idx -= 1
        ebase_idx = ebase_idx+getint(rec0, ebase_idx+4)
    return rec0


def del_exth(rec0, exth_num):
    ebase, elen, enum = get_exth_params(rec0)
    ebase_idx = ebase+12
    enum_idx = 0
    while enum_idx < enum:
        exth_id = getint(rec0, ebase_idx)
        exth_size = getint(rec0, ebase_idx+4)
        if exth_id == exth_num:
            newrec0 = rec0
            newrec0 = writeint(newrec0, title_offset, getint(newrec0, title_offset)-exth_size)
            newrec0 = newrec0[:ebase_idx]+newrec0[ebase_idx+exth_size:]
            newrec0 = newrec0[0:ebase+4]+struct.pack('>L', elen-exth_size)+struct.pack('>L', enum-1)+newrec0[ebase+12:]
            return newrec0
        enum_idx += 1
        ebase_idx = ebase_idx+exth_size
    return rec0


class mobi_split:
    def __init__(self, infile, newKindle):
        try:
            datain = open(infile, 'rb').read()
            datain_rec0 = readsection(datain, 0)
            ver = getint(datain_rec0, mobi_version)
            # fake_asin = str(uuid4())
            self.combo = (ver != 8)
            if not self.combo:
                return
            exth121 = read_exth(datain_rec0, 121)
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
            datain_kfrec0 = readsection(datain, datain_kf8)
            firstimage = getint(datain_rec0, first_image_record)
            lastimage = getint(datain_rec0, last_content_index, 'H')

            if not newKindle:
                # create the standalone mobi7
                num_sec = getint(datain, number_of_pdb_records, 'H')
                # remove BOUNDARY up to but not including ELF record
                self.result_file = deletesectionrange(datain, datain_kf8-1, num_sec-2)
                # check if there are SRCS records and delete them
                srcs = getint(datain_rec0, srcs_index)
                num_srcs = getint(datain_rec0, srcs_count)
                if srcs != 0xffffffff and num_srcs > 0:
                    self.result_file = deletesectionrange(self.result_file, srcs, srcs+num_srcs-1)
                    datain_rec0 = writeint(datain_rec0, srcs_index, 0xffffffff)
                    datain_rec0 = writeint(datain_rec0, srcs_count, 0)
                # reset the EXTH 121 KF8 Boundary meta data to 0xffffffff
                datain_rec0 = write_exth(datain_rec0, 121, struct.pack('>L', 0xffffffff))
                # datain_rec0 = del_exth(datain_rec0,121)
                # datain_rec0 = del_exth(datain_rec0,534)
                # don't remove the EXTH 125 KF8 Count of Resources, seems to be present in mobi6 files as well
                # set the EXTH 129 KF8 Masthead / Cover Image string to the null string
                datain_rec0 = write_exth(datain_rec0, 129, '')
                # don't remove the EXTH 131 KF8 Unidentified Count, seems to be present in mobi6 files as well

                # Make sure we have an ASIN & cdeType set...
                # if len(read_exth(datain_rec0, 113)) == 0:
                #     datain_rec0 = add_exth(datain_rec0, 113, fake_asin)
                # if len(read_exth(datain_rec0, 504)) == 0:
                #     datain_rec0 = add_exth(datain_rec0, 504, fake_asin)
                if len(read_exth(datain_rec0, 501)) == 0:
                    datain_rec0 = add_exth(datain_rec0, 501, b'EBOK')

                # need to reset flags stored in 0x80-0x83
                # old mobi with exth: 0x50, mobi7 part with exth: 0x1850, mobi8 part with exth: 0x1050
                # Bit Flags
                # 0x1000 = Bit 12 indicates if embedded fonts are used or not
                # 0x0800 = means this Header points to *shared* images/resource/fonts ??
                # 0x0080 = unknown new flag, why is this now being set by Kindlegen 2.8?
                # 0x0040 = exth exists
                # 0x0010 = Not sure but this is always set so far
                fval, = struct.unpack_from('>L', datain_rec0, 0x80)
                # need to remove flag 0x0800 for KindlePreviewer 2.8 and unset Bit 12 for embedded fonts
                fval &= 0x07FF
                datain_rec0 = datain_rec0[:0x80] + struct.pack('>L', fval) + datain_rec0[0x84:]
                self.result_file = writesection(self.result_file, 0, datain_rec0)
                if lastimage == 0xffff:
                    # find the lowest of the next sections and copy up to that.
                    ofs_list = [(kf8_last_content_index, 'L'), (fcis_index, 'L'), (flis_index, 'L'), (datp_index, 'L'),
                                (hufftbloff, 'L')]
                    for ofs, sz in ofs_list:
                        n = getint(datain_kfrec0, ofs, sz)
                        if 0 < n < lastimage:
                            lastimage = n-1

                # Try to null out FONT and RES, but leave the (empty) PDB record so image refs remain valid
                for i in range(firstimage, lastimage):
                    imgsec = readsection(self.result_file, i)
                    if imgsec[0:4] in ['RESC', 'FONT']:
                        self.result_file = nullsection(self.result_file, i)
                # mobi7 finished
            else:
                # create standalone mobi8
                self.result_file = deletesectionrange(datain, 0, datain_kf8-1)
                target = getint(datain_kfrec0, first_image_record)
                self.result_file = insertsectionrange(datain, firstimage, lastimage, self.result_file, target)
                datain_kfrec0 = readsection(self.result_file, 0)

                # Only keep the correct EXTH 116 StartOffset, KG 2.5 carries over the one from the mobi7 part,
                # which then points at garbage in the mobi8 part, and confuses FW 3.4
                kf8starts = read_exth(datain_kfrec0, 116)
                # If we have multiple StartOffset, keep only the last one
                kf8start_count = len(kf8starts)
                while kf8start_count > 1:
                    kf8start_count -= 1
                    datain_kfrec0 = del_exth(datain_kfrec0, 116)

                # update the EXTH 125 KF8 Count of Images/Fonts/Resources
                datain_kfrec0 = write_exth(datain_kfrec0, 125, struct.pack('>L', lastimage-firstimage+1))

                # Same dance for the KF8, we want an ASIN & cdeType :)
                # if len(read_exth(datain_kfrec0, 113)) == 0:
                #     datain_kfrec0 = add_exth(datain_kfrec0, 113, fake_asin)
                # if len(read_exth(datain_kfrec0, 504)) == 0:
                #     datain_kfrec0 = add_exth(datain_kfrec0, 504, fake_asin)
                if len(read_exth(datain_kfrec0, 501)) == 0:
                    datain_kfrec0 = add_exth(datain_kfrec0, 501, b'EBOK')

                # need to reset flags stored in 0x80-0x83
                # old mobi with exth: 0x50, mobi7 part with exth: 0x1850, mobi8 part with exth: 0x1050
                # standalone mobi8 with exth: 0x0050
                # Bit Flags
                # 0x1000 = Bit 12 indicates if embedded fonts are used or not
                # 0x0800 = means this Header points to *shared* images/resource/fonts ??
                # 0x0080 = unknown new flag, why is this now being set by Kindlegen 2.8?
                # 0x0040 = exth exists
                # 0x0010 = Not sure but this is always set so far
                fval, = struct.unpack_from('>L', datain_kfrec0, 0x80)
                fval &= 0x1FFF
                fval |= 0x0800
                datain_kfrec0 = datain_kfrec0[:0x80] + struct.pack('>L', fval) + datain_kfrec0[0x84:]

                # properly update other index pointers that have been shifted by the insertion of images
                ofs_list = [(kf8_last_content_index, 'L'), (fcis_index, 'L'), (flis_index, 'L'), (datp_index, 'L'),
                            (hufftbloff, 'L')]
                for ofs, sz in ofs_list:
                    n = getint(datain_kfrec0, ofs, sz)
                    if n != 0xffffffff:
                        datain_kfrec0 = writeint(datain_kfrec0, ofs, n+lastimage-firstimage+1, sz)
                self.result_file = writesection(self.result_file, 0, datain_kfrec0)
                # mobi8 finished
        except Exception:
                raise

    def getResult(self):
        return self.result_file