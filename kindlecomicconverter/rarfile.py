# rarfile.py
#
# Copyright (c) 2005-2014  Marko Kreen <markokr@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

r"""RAR archive reader.

This is Python module for Rar archive reading.  The interface
is made as :mod:`zipfile`-like as possible.

Basic logic:
 - Parse archive structure with Python.
 - Extract non-compressed files with Python
 - Extract compressed files with unrar.
 - Optionally write compressed data to temp file to speed up unrar,
   otherwise it needs to scan whole archive on each execution.

Example::

    import rarfile

    rf = rarfile.RarFile('myarchive.rar')
    for f in rf.infolist():
        print f.filename, f.file_size
        if f.filename == 'README':
            print(rf.read(f))

Archive files can also be accessed via file-like object returned
by :meth:`RarFile.open`::

    import rarfile

    with rarfile.RarFile('archive.rar') as rf:
        with rf.open('README') as f:
            for ln in f:
                print(ln.strip())

There are few module-level parameters to tune behaviour,
here they are with defaults, and reason to change it::

    import rarfile

    # Set to full path of unrar.exe if it is not in PATH
    rarfile.UNRAR_TOOL = "unrar"

    # Set to 0 if you don't look at comments and want to
    # avoid wasting time for parsing them
    rarfile.NEED_COMMENTS = 1

    # Set up to 1 if you don't want to deal with decoding comments
    # from unknown encoding.  rarfile will try couple of common
    # encodings in sequence.
    rarfile.UNICODE_COMMENTS = 0

    # Set to 1 if you prefer timestamps to be datetime objects
    # instead tuples
    rarfile.USE_DATETIME = 0

    # Set to '/' to be more compatible with zipfile
    rarfile.PATH_SEP = '\\'

For more details, refer to source.

"""

__version__ = '2.7-kcc'

# export only interesting items
__all__ = ['is_rarfile', 'RarInfo', 'RarFile', 'RarExtFile']

##
## Imports and compat - support both Python 2.x and 3.x
##

import sys, os, struct, errno
from struct import pack, unpack
from binascii import crc32
from tempfile import mkstemp
from subprocess import Popen, PIPE, STDOUT
from datetime import datetime

# only needed for encryped headers
try:
    from Crypto.Cipher import AES
    try:
        from hashlib import sha1
    except ImportError:
        from sha import new as sha1
    _have_crypto = 1
except ImportError:
    _have_crypto = 0

# compat with 2.x
if sys.hexversion < 0x3000000:
    # prefer 3.x behaviour
    range = xrange
    # py2.6 has broken bytes()
    def bytes(s, enc):
        return str(s)
else:
    unicode = str

# see if compat bytearray() is needed
try:
    bytearray
except NameError:
    import array
    class bytearray:
        def __init__(self, val = ''):
            self.arr = array.array('B', val)
            self.append = self.arr.append
            self.__getitem__ = self.arr.__getitem__
            self.__len__ = self.arr.__len__
        def decode(self, *args):
            return self.arr.tostring().decode(*args)

# Optimized .readinto() requires memoryview
try:
    memoryview
    have_memoryview = 1
except NameError:
    have_memoryview = 0

# Struct() for older python
try:
    from struct import Struct
except ImportError:
    class Struct:
        def __init__(self, fmt):
            self.format = fmt
            self.size = struct.calcsize(fmt)
        def unpack(self, buf):
            return unpack(self.format, buf)
        def unpack_from(self, buf, ofs = 0):
            return unpack(self.format, buf[ofs : ofs + self.size])
        def pack(self, *args):
            return pack(self.format, *args)

# file object superclass
try:
    from io import RawIOBase
except ImportError:
    class RawIOBase(object):
        def close(self):
            pass


##
## Module configuration.  Can be tuned after importing.
##

#: default fallback charset
DEFAULT_CHARSET = "windows-1252"

#: list of encodings to try, with fallback to DEFAULT_CHARSET if none succeed
TRY_ENCODINGS = ('utf8', 'utf-16le')

#: 'unrar', 'rar' or full path to either one
UNRAR_TOOL = "unrar"

#: Command line args to use for opening file for reading.
OPEN_ARGS = ('p', '-inul')

#: Command line args to use for extracting file to disk.
EXTRACT_ARGS = ('x', '-y', '-idq')

#: args for testrar()
TEST_ARGS = ('t', '-idq')

#
# Allow use of tool that is not compatible with unrar.
#
# By default use 'bsdtar' which is 'tar' program that
# sits on top of libarchive.
#
# Problems with libarchive RAR backend:
# - Does not support solid archives.
# - Does not support password-protected archives.
#

ALT_TOOL = 'bsdtar'
ALT_OPEN_ARGS = ('-x', '--to-stdout', '-f')
ALT_EXTRACT_ARGS = ('-x', '-f')
ALT_TEST_ARGS = ('-t', '-f')
ALT_CHECK_ARGS = ('--help',)

#: whether to speed up decompression by using tmp archive
USE_EXTRACT_HACK = 0

#: limit the filesize for tmp archive usage
HACK_SIZE_LIMIT = 20*1024*1024

#: whether to parse file/archive comments.
NEED_COMMENTS = 1

#: whether to convert comments to unicode strings
UNICODE_COMMENTS = 0

#: Convert RAR time tuple into datetime() object
USE_DATETIME = 0

#: Separator for path name components.  RAR internally uses '\\'.
#: Use '/' to be similar with zipfile.
PATH_SEP = '\\'

##
## rar constants
##

# block types
RAR_BLOCK_MARK          = 0x72 # r
RAR_BLOCK_MAIN          = 0x73 # s
RAR_BLOCK_FILE          = 0x74 # t
RAR_BLOCK_OLD_COMMENT   = 0x75 # u
RAR_BLOCK_OLD_EXTRA     = 0x76 # v
RAR_BLOCK_OLD_SUB       = 0x77 # w
RAR_BLOCK_OLD_RECOVERY  = 0x78 # x
RAR_BLOCK_OLD_AUTH      = 0x79 # y
RAR_BLOCK_SUB           = 0x7a # z
RAR_BLOCK_ENDARC        = 0x7b # {

# flags for RAR_BLOCK_MAIN
RAR_MAIN_VOLUME         = 0x0001
RAR_MAIN_COMMENT        = 0x0002
RAR_MAIN_LOCK           = 0x0004
RAR_MAIN_SOLID          = 0x0008
RAR_MAIN_NEWNUMBERING   = 0x0010
RAR_MAIN_AUTH           = 0x0020
RAR_MAIN_RECOVERY       = 0x0040
RAR_MAIN_PASSWORD       = 0x0080
RAR_MAIN_FIRSTVOLUME    = 0x0100
RAR_MAIN_ENCRYPTVER     = 0x0200

# flags for RAR_BLOCK_FILE
RAR_FILE_SPLIT_BEFORE   = 0x0001
RAR_FILE_SPLIT_AFTER    = 0x0002
RAR_FILE_PASSWORD       = 0x0004
RAR_FILE_COMMENT        = 0x0008
RAR_FILE_SOLID          = 0x0010
RAR_FILE_DICTMASK       = 0x00e0
RAR_FILE_DICT64         = 0x0000
RAR_FILE_DICT128        = 0x0020
RAR_FILE_DICT256        = 0x0040
RAR_FILE_DICT512        = 0x0060
RAR_FILE_DICT1024       = 0x0080
RAR_FILE_DICT2048       = 0x00a0
RAR_FILE_DICT4096       = 0x00c0
RAR_FILE_DIRECTORY      = 0x00e0
RAR_FILE_LARGE          = 0x0100
RAR_FILE_UNICODE        = 0x0200
RAR_FILE_SALT           = 0x0400
RAR_FILE_VERSION        = 0x0800
RAR_FILE_EXTTIME        = 0x1000
RAR_FILE_EXTFLAGS       = 0x2000

# flags for RAR_BLOCK_ENDARC
RAR_ENDARC_NEXT_VOLUME  = 0x0001
RAR_ENDARC_DATACRC      = 0x0002
RAR_ENDARC_REVSPACE     = 0x0004
RAR_ENDARC_VOLNR        = 0x0008

# flags common to all blocks
RAR_SKIP_IF_UNKNOWN     = 0x4000
RAR_LONG_BLOCK          = 0x8000

# Host OS types
RAR_OS_MSDOS = 0
RAR_OS_OS2   = 1
RAR_OS_WIN32 = 2
RAR_OS_UNIX  = 3
RAR_OS_MACOS = 4
RAR_OS_BEOS  = 5

# Compression methods - '0'..'5'
RAR_M0 = 0x30
RAR_M1 = 0x31
RAR_M2 = 0x32
RAR_M3 = 0x33
RAR_M4 = 0x34
RAR_M5 = 0x35

##
## internal constants
##

RAR_ID = bytes("Rar!\x1a\x07\x00", 'ascii')
RAR5_ID = bytes("Rar!\x1a\x07\x01", 'ascii')
ZERO = bytes("\0", 'ascii')
EMPTY = bytes("", 'ascii')

S_BLK_HDR = Struct('<HBHH')
S_FILE_HDR = Struct('<LLBLLBBHL')
S_LONG = Struct('<L')
S_SHORT = Struct('<H')
S_BYTE = Struct('<B')
S_COMMENT_HDR = Struct('<HBBH')

##
## Public interface
##

class Error(Exception):
    """Base class for rarfile errors."""
class BadRarFile(Error):
    """Incorrect data in archive."""
class NotRarFile(Error):
    """The file is not RAR archive."""
class BadRarName(Error):
    """Cannot guess multipart name components."""
class NoRarEntry(Error):
    """File not found in RAR"""
class PasswordRequired(Error):
    """File requires password"""
class NeedFirstVolume(Error):
    """Need to start from first volume."""
class NoCrypto(Error):
    """Cannot parse encrypted headers - no crypto available."""
class RarExecError(Error):
    """Problem reported by unrar/rar."""
class RarWarning(RarExecError):
    """Non-fatal error"""
class RarFatalError(RarExecError):
    """Fatal error"""
class RarCRCError(RarExecError):
    """CRC error during unpacking"""
class RarLockedArchiveError(RarExecError):
    """Must not modify locked archive"""
class RarWriteError(RarExecError):
    """Write error"""
class RarOpenError(RarExecError):
    """Open error"""
class RarUserError(RarExecError):
    """User error"""
class RarMemoryError(RarExecError):
    """Memory error"""
class RarCreateError(RarExecError):
    """Create error"""
class RarNoFilesError(RarExecError):
    """No files that match pattern were found"""
class RarUserBreak(RarExecError):
    """User stop"""
class RarUnknownError(RarExecError):
    """Unknown exit code"""
class RarSignalExit(RarExecError):
    """Unrar exited with signal"""
class RarCannotExec(RarExecError):
    """Executable not found."""


def is_rarfile(xfile):
    '''Check quickly whether file is rar archive.'''
    with open(xfile, 'rb') as fh:
        buf = fh.read(len(RAR_ID))
    if buf == RAR_ID or buf == RAR5_ID:
        return True
    else:
        return False


class RarInfo(object):
    r'''An entry in rar archive.

    :mod:`zipfile`-compatible fields:
    
        filename
            File name with relative path.
            Default path separator is '\\', to change set rarfile.PATH_SEP.
            Always unicode string.
        date_time
            Modification time, tuple of (year, month, day, hour, minute, second).
            Or datetime() object if USE_DATETIME is set.
        file_size
            Uncompressed size.
        compress_size
            Compressed size.
        CRC
            CRC-32 of uncompressed file, unsigned int.
        comment
            File comment.  Byte string or None.  Use UNICODE_COMMENTS
            to get automatic decoding to unicode.
        volume
            Volume nr, starting from 0.

    RAR-specific fields:

        compress_type
            Compression method: 0x30 - 0x35.
        extract_version
            Minimal Rar version needed for decompressing.
        host_os
            Host OS type, one of RAR_OS_* constants.
        mode
            File attributes. May be either dos-style or unix-style, depending on host_os.
        volume_file
            Volume file name, where file starts.
        mtime
            Optional time field: Modification time, with float seconds.
            Same as .date_time but with more precision.
        ctime
            Optional time field: creation time, with float seconds.
        atime
            Optional time field: last access time, with float seconds.
        arctime
            Optional time field: archival time, with float seconds.

    Internal fields:

        type
            One of RAR_BLOCK_* types.  Only entries with type==RAR_BLOCK_FILE are shown in .infolist().
        flags
            For files, RAR_FILE_* bits.
    '''

    __slots__ = (
        # zipfile-compatible fields
        'filename',
        'file_size',
        'compress_size',
        'date_time',
        'comment',
        'CRC',
        'volume',
        'orig_filename', # bytes in unknown encoding

        # rar-specific fields
        'extract_version',
        'compress_type',
        'host_os',
        'mode',
        'type',
        'flags',

        # optional extended time fields
        # tuple where the sec is float, or datetime().
        'mtime', # same as .date_time
        'ctime',
        'atime',
        'arctime',

        # RAR internals
        'name_size',
        'header_size',
        'header_crc',
        'file_offset',
        'add_size',
        'header_data',
        'header_base',
        'header_offset',
        'salt',
        'volume_file',
    )

    def isdir(self):
        '''Returns True if the entry is a directory.'''
        if self.type == RAR_BLOCK_FILE:
            return (self.flags & RAR_FILE_DIRECTORY) == RAR_FILE_DIRECTORY
        return False

    def needs_password(self):
        return self.flags & RAR_FILE_PASSWORD


class RarFile(object):
    '''Parse RAR structure, provide access to files in archive.
    '''

    #: Archive comment.  Byte string or None.  Use :data:`UNICODE_COMMENTS`
    #: to get automatic decoding to unicode.
    comment = None

    def __init__(self, rarfile, mode="r", charset=None, info_callback=None,
                 crc_check = True, errors = "stop"):
        """Open and parse a RAR archive.
        
        Parameters:

            rarfile
                archive file name
            mode
                only 'r' is supported.
            charset
                fallback charset to use, if filenames are not already Unicode-enabled.
            info_callback
                debug callback, gets to see all archive entries.
            crc_check
                set to False to disable CRC checks
            errors
                Either "stop" to quietly stop parsing on errors,
                or "strict" to raise errors.  Default is "stop".
        """
        self.rarfile = rarfile
        self.comment = None
        self._charset = charset or DEFAULT_CHARSET
        self._info_callback = info_callback

        self._info_list = []
        self._info_map = {}
        self._needs_password = False
        self._password = None
        self._crc_check = crc_check
        self._vol_list = []

        if errors == "stop":
            self._strict = False
        elif errors == "strict":
            self._strict = True
        else:
            raise ValueError("Invalid value for 'errors' parameter.")

        self._main = None

        if mode != "r":
            raise NotImplementedError("RarFile supports only mode=r")

        self._parse()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def setpassword(self, password):
        '''Sets the password to use when extracting.'''
        self._password = password
        if not self._main:
            self._parse()

    def needs_password(self):
        '''Returns True if any archive entries require password for extraction.'''
        return self._needs_password

    def namelist(self):
        '''Return list of filenames in archive.'''
        return [f.filename for f in self._info_list]

    def infolist(self):
        '''Return RarInfo objects for all files/directories in archive.'''
        return self._info_list

    def volumelist(self):
        '''Returns filenames of archive volumes.

        In case of single-volume archive, the list contains
        just the name of main archive file.
        '''
        return self._vol_list

    def getinfo(self, fname):
        '''Return RarInfo for file.'''

        if isinstance(fname, RarInfo):
            return fname

        # accept both ways here
        if PATH_SEP == '/':
            fname2 = fname.replace("\\", "/")
        else:
            fname2 = fname.replace("/", "\\")

        try:
            return self._info_map[fname]
        except KeyError:
            try:
                return self._info_map[fname2]
            except KeyError:
                raise NoRarEntry("No such file: "+fname)

    def open(self, fname, mode = 'r', psw = None):
        '''Returns file-like object (:class:`RarExtFile`),
        from where the data can be read.
        
        The object implements :class:`io.RawIOBase` interface, so it can
        be further wrapped with :class:`io.BufferedReader`
        and :class:`io.TextIOWrapper`.

        On older Python where io module is not available, it implements
        only .read(), .seek(), .tell() and .close() methods.

        The object is seekable, although the seeking is fast only on
        uncompressed files, on compressed files the seeking is implemented
        by reading ahead and/or restarting the decompression.

        Parameters:

            fname
                file name or RarInfo instance.
            mode
                must be 'r'
            psw
                password to use for extracting.
        '''

        if mode != 'r':
            raise NotImplementedError("RarFile.open() supports only mode=r")

        # entry lookup
        inf = self.getinfo(fname)
        if inf.isdir():
            raise TypeError("Directory does not have any data: " + inf.filename)

        if inf.flags & RAR_FILE_SPLIT_BEFORE:
            raise NeedFirstVolume("Partial file, please start from first volume: " + inf.filename)

        # check password
        if inf.needs_password():
            psw = psw or self._password
            if psw is None:
                raise PasswordRequired("File %s requires password" % inf.filename)
        else:
            psw = None

        # is temp write usable?
        use_hack = 1
        if not self._main:
            use_hack = 0
        elif self._main.flags & (RAR_MAIN_SOLID | RAR_MAIN_PASSWORD):
            use_hack = 0
        elif inf.flags & (RAR_FILE_SPLIT_BEFORE | RAR_FILE_SPLIT_AFTER):
            use_hack = 0
        elif is_filelike(self.rarfile):
            pass
        elif inf.file_size > HACK_SIZE_LIMIT:
            use_hack = 0
        elif not USE_EXTRACT_HACK:
            use_hack = 0

        # now extract
        if inf.compress_type == RAR_M0 and (inf.flags & RAR_FILE_PASSWORD) == 0:
            return self._open_clear(inf)
        elif use_hack:
            return self._open_hack(inf, psw)
        else:
            return self._open_unrar(self.rarfile, inf, psw)

    def read(self, fname, psw = None):
        """Return uncompressed data for archive entry.
        
        For longer files using :meth:`RarFile.open` may be better idea.

        Parameters:

            fname
                filename or RarInfo instance
            psw
                password to use for extracting.
        """

        f = self.open(fname, 'r', psw)
        try:
            return f.read()
        finally:
            f.close()

    def close(self):
        """Release open resources."""
        pass

    def printdir(self):
        """Print archive file list to stdout."""
        for f in self._info_list:
            print(f.filename)

    def extract(self, member, path=None, pwd=None):
        """Extract single file into current directory.
        
        Parameters:

            member
                filename or :class:`RarInfo` instance
            path
                optional destination path
            pwd
                optional password to use
        """
        if isinstance(member, RarInfo):
            fname = member.filename
        else:
            fname = member
        self._extract([fname], path, pwd)

    def extractall(self, path=None, members=None, pwd=None):
        """Extract all files into current directory.
        
        Parameters:

            path
                optional destination path
            members
                optional filename or :class:`RarInfo` instance list to extract
            pwd
                optional password to use
        """
        fnlist = []
        if members is not None:
            for m in members:
                if isinstance(m, RarInfo):
                    fnlist.append(m.filename)
                else:
                    fnlist.append(m)
        self._extract(fnlist, path, pwd)

    def testrar(self):
        """Let 'unrar' test the archive.
        """
        cmd = [UNRAR_TOOL] + list(TEST_ARGS)
        add_password_arg(cmd, self._password)
        cmd.append(self.rarfile)
        p = custom_popen(cmd)
        output = p.communicate()[0]
        check_returncode(p, output)

    def strerror(self):
        """Return error string if parsing failed,
        or None if no problems.
        """
        return self._parse_error

    ##
    ## private methods
    ##

    def _set_error(self, msg, *args):
        if args:
            msg = msg % args
        self._parse_error = msg
        if self._strict:
            raise BadRarFile(msg)

    # store entry
    def _process_entry(self, item):
        if item.type == RAR_BLOCK_FILE:
            # use only first part
            if (item.flags & RAR_FILE_SPLIT_BEFORE) == 0:
                self._info_map[item.filename] = item
                self._info_list.append(item)
                # remember if any items require password
                if item.needs_password():
                    self._needs_password = True
            elif len(self._info_list) > 0:
                # final crc is in last block
                old = self._info_list[-1]
                old.CRC = item.CRC
                old.compress_size += item.compress_size

        # parse new-style comment
        if item.type == RAR_BLOCK_SUB and item.filename == 'CMT':
            if not NEED_COMMENTS:
                pass
            elif item.flags & (RAR_FILE_SPLIT_BEFORE | RAR_FILE_SPLIT_AFTER):
                pass
            elif item.flags & RAR_FILE_SOLID:
                # file comment
                cmt = self._read_comment_v3(item, self._password)
                if len(self._info_list) > 0:
                    old = self._info_list[-1]
                    old.comment = cmt
            else:
                # archive comment
                cmt = self._read_comment_v3(item, self._password)
                self.comment = cmt

        if self._info_callback:
            self._info_callback(item)

    # read rar
    def _parse(self):
        self._fd = None
        try:
            self._parse_real()
        finally:
            if self._fd:
                self._fd.close()
                self._fd = None

    def _parse_real(self):
        fd = XFile(self.rarfile)
        self._fd = fd
        id = fd.read(len(RAR_ID))
        if id != RAR_ID and id != RAR5_ID:
            raise NotRarFile("Not a Rar archive: "+self.rarfile)

        volume = 0  # first vol (.rar) is 0
        more_vols = 0
        endarc = 0
        volfile = self.rarfile
        self._vol_list = [self.rarfile]
        while 1:
            if endarc:
                h = None    # don't read past ENDARC
            else:
                h = self._parse_header(fd)
            if not h:
                if more_vols:
                    volume += 1
                    fd.close()
                    try:
                        volfile = self._next_volname(volfile)
                        fd = XFile(volfile)
                    except IOError:
                        self._set_error("Cannot open next volume: %s", volfile)
                        break
                    self._fd = fd
                    more_vols = 0
                    endarc = 0
                    self._vol_list.append(volfile)
                    continue
                break
            h.volume = volume
            h.volume_file = volfile

            if h.type == RAR_BLOCK_MAIN and not self._main:
                self._main = h
                if h.flags & RAR_MAIN_NEWNUMBERING:
                    # RAR 2.x does not set FIRSTVOLUME,
                    # so check it only if NEWNUMBERING is used
                    if (h.flags & RAR_MAIN_FIRSTVOLUME) == 0:
                        raise NeedFirstVolume("Need to start from first volume")
                if h.flags & RAR_MAIN_PASSWORD:
                    self._needs_password = True
                    if not self._password:
                        self._main = None
                        break
            elif h.type == RAR_BLOCK_ENDARC:
                more_vols = h.flags & RAR_ENDARC_NEXT_VOLUME
                endarc = 1
            elif h.type == RAR_BLOCK_FILE:
                # RAR 2.x does not write RAR_BLOCK_ENDARC
                if h.flags & RAR_FILE_SPLIT_AFTER:
                    more_vols = 1
                # RAR 2.x does not set RAR_MAIN_FIRSTVOLUME
                if volume == 0 and h.flags & RAR_FILE_SPLIT_BEFORE:
                    raise NeedFirstVolume("Need to start from first volume")

            # store it
            self._process_entry(h)

            # go to next header
            if h.add_size > 0:
                fd.seek(h.file_offset + h.add_size, 0)

    # AES encrypted headers
    _last_aes_key = (None, None, None) # (salt, key, iv)
    def _decrypt_header(self, fd):
        if not _have_crypto:
            raise NoCrypto('Cannot parse encrypted headers - no crypto')
        salt = fd.read(8)
        if self._last_aes_key[0] == salt:
            key, iv = self._last_aes_key[1:]
        else:
            key, iv = rar3_s2k(self._password, salt)
            self._last_aes_key = (salt, key, iv)
        return HeaderDecrypt(fd, key, iv)

    # read single header
    def _parse_header(self, fd):
        try:
            # handle encrypted headers
            if self._main and self._main.flags & RAR_MAIN_PASSWORD:
                if not self._password:
                    return
                fd = self._decrypt_header(fd)

            # now read actual header
            return self._parse_block_header(fd)
        except struct.error:
            self._set_error('Broken header in RAR file')
            return None

    # common header
    def _parse_block_header(self, fd):
        h = RarInfo()
        h.header_offset = fd.tell()
        h.comment = None

        # read and parse base header
        buf = fd.read(S_BLK_HDR.size)
        if not buf:
            return None
        t = S_BLK_HDR.unpack_from(buf)
        h.header_crc, h.type, h.flags, h.header_size = t
        h.header_base = S_BLK_HDR.size
        pos = S_BLK_HDR.size

        # read full header
        if h.header_size > S_BLK_HDR.size:
            h.header_data = buf + fd.read(h.header_size - S_BLK_HDR.size)
        else:
            h.header_data = buf
        h.file_offset = fd.tell()

        # unexpected EOF?
        if len(h.header_data) != h.header_size:
            self._set_error('Unexpected EOF when reading header')
            return None

        # block has data assiciated with it?
        if h.flags & RAR_LONG_BLOCK:
            h.add_size = S_LONG.unpack_from(h.header_data, pos)[0]
        else:
            h.add_size = 0

        # parse interesting ones, decide header boundaries for crc
        if h.type == RAR_BLOCK_MARK:
            return h
        elif h.type == RAR_BLOCK_MAIN:
            h.header_base += 6
            if h.flags & RAR_MAIN_ENCRYPTVER:
                h.header_base += 1
            if h.flags & RAR_MAIN_COMMENT:
                self._parse_subblocks(h, h.header_base)
                self.comment = h.comment
        elif h.type == RAR_BLOCK_FILE:
            self._parse_file_header(h, pos)
        elif h.type == RAR_BLOCK_SUB:
            self._parse_file_header(h, pos)
            h.header_base = h.header_size
        elif h.type == RAR_BLOCK_OLD_AUTH:
            h.header_base += 8
        elif h.type == RAR_BLOCK_OLD_EXTRA:
            h.header_base += 7
        else:
            h.header_base = h.header_size

        # check crc
        if h.type == RAR_BLOCK_OLD_SUB:
            crcdat = h.header_data[2:] + fd.read(h.add_size)
        else:
            crcdat = h.header_data[2:h.header_base]

        calc_crc = crc32(crcdat) & 0xFFFF

        # return good header
        if h.header_crc == calc_crc:
            return h

        # header parsing failed.
        self._set_error('Header CRC error (%02x): exp=%x got=%x (xlen = %d)',
                h.type, h.header_crc, calc_crc, len(crcdat))

        # instead panicing, send eof
        return None

    # read file-specific header
    def _parse_file_header(self, h, pos):
        fld = S_FILE_HDR.unpack_from(h.header_data, pos)
        h.compress_size = fld[0]
        h.file_size = fld[1]
        h.host_os = fld[2]
        h.CRC = fld[3]
        h.date_time = parse_dos_time(fld[4])
        h.extract_version = fld[5]
        h.compress_type = fld[6]
        h.name_size = fld[7]
        h.mode = fld[8]
        pos += S_FILE_HDR.size

        if h.flags & RAR_FILE_LARGE:
            h1 = S_LONG.unpack_from(h.header_data, pos)[0]
            h2 = S_LONG.unpack_from(h.header_data, pos + 4)[0]
            h.compress_size |= h1 << 32
            h.file_size |= h2 << 32
            pos += 8
            h.add_size = h.compress_size

        name = h.header_data[pos : pos + h.name_size ]
        pos += h.name_size
        if h.flags & RAR_FILE_UNICODE:
            nul = name.find(ZERO)
            h.orig_filename = name[:nul]
            u = UnicodeFilename(h.orig_filename, name[nul + 1 : ])
            h.filename = u.decode()

            # if parsing failed fall back to simple name
            if u.failed:
                h.filename = self._decode(h.orig_filename)
        else:
            h.orig_filename = name
            h.filename = self._decode(name)

        # change separator, if requested
        if PATH_SEP != '\\':
            h.filename = h.filename.replace('\\', PATH_SEP)

        if h.flags & RAR_FILE_SALT:
            h.salt = h.header_data[pos : pos + 8]
            pos += 8
        else:
            h.salt = None

        # optional extended time stamps
        if h.flags & RAR_FILE_EXTTIME:
            pos = self._parse_ext_time(h, pos)
        else:
            h.mtime = h.atime = h.ctime = h.arctime = None

        # base header end
        h.header_base = pos

        if h.flags & RAR_FILE_COMMENT:
            self._parse_subblocks(h, pos)

        # convert timestamps
        if USE_DATETIME:
            h.date_time = to_datetime(h.date_time)
            h.mtime = to_datetime(h.mtime)
            h.atime = to_datetime(h.atime)
            h.ctime = to_datetime(h.ctime)
            h.arctime = to_datetime(h.arctime)

        # .mtime is .date_time with more precision
        if h.mtime:
            if USE_DATETIME:
                h.date_time = h.mtime
            else:
                # keep seconds int
                h.date_time = h.mtime[:5] + (int(h.mtime[5]),)

        return pos

    # find old-style comment subblock
    def _parse_subblocks(self, h, pos):
        hdata = h.header_data
        while pos < len(hdata):
            # ordinary block header
            t = S_BLK_HDR.unpack_from(hdata, pos)
            scrc, stype, sflags, slen = t
            pos_next = pos + slen
            pos += S_BLK_HDR.size

            # corrupt header
            if pos_next < pos:
                break

            # followed by block-specific header
            if stype == RAR_BLOCK_OLD_COMMENT and pos + S_COMMENT_HDR.size <= pos_next:
                declen, ver, meth, crc = S_COMMENT_HDR.unpack_from(hdata, pos)
                pos += S_COMMENT_HDR.size
                data = hdata[pos : pos_next]
                cmt = rar_decompress(ver, meth, data, declen, sflags,
                                     crc, self._password)
                if not self._crc_check:
                    h.comment = self._decode_comment(cmt)
                elif crc32(cmt) & 0xFFFF == crc:
                    h.comment = self._decode_comment(cmt)

            pos = pos_next

    def _parse_ext_time(self, h, pos):
        data = h.header_data

        # flags and rest of data can be missing
        flags = 0
        if pos + 2 <= len(data):
            flags = S_SHORT.unpack_from(data, pos)[0]
            pos += 2

        h.mtime, pos = self._parse_xtime(flags >> 3*4, data, pos, h.date_time)
        h.ctime, pos = self._parse_xtime(flags >> 2*4, data, pos)
        h.atime, pos = self._parse_xtime(flags >> 1*4, data, pos)
        h.arctime, pos = self._parse_xtime(flags >> 0*4, data, pos)
        return pos

    def _parse_xtime(self, flag, data, pos, dostime = None):
        unit = 10000000.0 # 100 ns units
        if flag & 8:
            if not dostime:
                t = S_LONG.unpack_from(data, pos)[0]
                dostime = parse_dos_time(t)
                pos += 4
            rem = 0
            cnt = flag & 3
            for i in range(cnt):
                b = S_BYTE.unpack_from(data, pos)[0]
                rem = (b << 16) | (rem >> 8)
                pos += 1
            sec = dostime[5] + rem / unit
            if flag & 4:
                sec += 1
            dostime = dostime[:5] + (sec,)
        return dostime, pos

    # given current vol name, construct next one
    def _next_volname(self, volfile):
        if is_filelike(volfile):
            raise IOError("Working on single FD")
        if self._main.flags & RAR_MAIN_NEWNUMBERING:
            return self._next_newvol(volfile)
        return self._next_oldvol(volfile)

    # new-style next volume
    def _next_newvol(self, volfile):
        i = len(volfile) - 1
        while i >= 0:
            if volfile[i] >= '0' and volfile[i] <= '9':
                return self._inc_volname(volfile, i)
            i -= 1
        raise BadRarName("Cannot construct volume name: "+volfile)

    # old-style next volume
    def _next_oldvol(self, volfile):
        # rar -> r00
        if volfile[-4:].lower() == '.rar':
            return volfile[:-2] + '00'
        return self._inc_volname(volfile, len(volfile) - 1)

    # increase digits with carry, otherwise just increment char
    def _inc_volname(self, volfile, i):
        fn = list(volfile)
        while i >= 0:
            if fn[i] != '9':
                fn[i] = chr(ord(fn[i]) + 1)
                break
            fn[i] = '0'
            i -= 1
        return ''.join(fn)

    def _open_clear(self, inf):
        return DirectReader(self, inf)

    # put file compressed data into temporary .rar archive, and run
    # unrar on that, thus avoiding unrar going over whole archive
    def _open_hack(self, inf, psw = None):
        BSIZE = 32*1024

        size = inf.compress_size + inf.header_size
        rf = XFile(inf.volume_file, 0)
        rf.seek(inf.header_offset)

        tmpfd, tmpname = mkstemp(suffix='.rar')
        tmpf = os.fdopen(tmpfd, "wb")

        try:
            # create main header: crc, type, flags, size, res1, res2
            mh = S_BLK_HDR.pack(0x90CF, 0x73, 0, 13) + ZERO * (2+4)
            tmpf.write(RAR_ID + mh)
            while size > 0:
                if size > BSIZE:
                    buf = rf.read(BSIZE)
                else:
                    buf = rf.read(size)
                if not buf:
                    raise BadRarFile('read failed: ' + inf.filename)
                tmpf.write(buf)
                size -= len(buf)
            tmpf.close()
            rf.close()
        except:
            rf.close()
            tmpf.close()
            os.unlink(tmpname)
            raise

        return self._open_unrar(tmpname, inf, psw, tmpname)

    def _read_comment_v3(self, inf, psw=None):

        # read data
        rf = XFile(inf.volume_file)
        rf.seek(inf.file_offset)
        data = rf.read(inf.compress_size)
        rf.close()

        # decompress
        cmt = rar_decompress(inf.extract_version, inf.compress_type, data,
                             inf.file_size, inf.flags, inf.CRC, psw, inf.salt)

        # check crc
        if self._crc_check:
            crc = crc32(cmt)
            if crc < 0:
                crc += (long(1) << 32)
            if crc != inf.CRC:
                return None

        return self._decode_comment(cmt)

    # extract using unrar
    def _open_unrar(self, rarfile, inf, psw = None, tmpfile = None):
        if is_filelike(rarfile):
            raise ValueError("Cannot use unrar directly on memory buffer")
        cmd = [UNRAR_TOOL] + list(OPEN_ARGS)
        add_password_arg(cmd, psw)
        cmd.append(rarfile)

        # not giving filename avoids encoding related problems
        if not tmpfile:
            fn = inf.filename
            if PATH_SEP != os.sep:
                fn = fn.replace(PATH_SEP, os.sep)
            cmd.append(fn)

        # read from unrar pipe
        return PipeReader(self, inf, cmd, tmpfile)

    def _decode(self, val):
        for c in TRY_ENCODINGS:
            try:
                return val.decode(c)
            except UnicodeError:
                pass
        return val.decode(self._charset, 'replace')

    def _decode_comment(self, val):
        if UNICODE_COMMENTS:
            return self._decode(val)
        return val

    # call unrar to extract a file
    def _extract(self, fnlist, path=None, psw=None):
        cmd = [UNRAR_TOOL] + list(EXTRACT_ARGS)

        # pasoword
        psw = psw or self._password
        add_password_arg(cmd, psw)

        # rar file
        cmd.append(self.rarfile)

        # file list
        for fn in fnlist:
            if os.sep != PATH_SEP:
                fn = fn.replace(PATH_SEP, os.sep)
            cmd.append(fn)

        # destination path
        if path is not None:
            cmd.append(path + os.sep)

        # call
        p = custom_popen(cmd)
        output = p.communicate()[0]
        check_returncode(p, output)

##
## Utility classes
##

class UnicodeFilename:
    """Handle unicode filename decompression"""

    def __init__(self, name, encdata):
        self.std_name = bytearray(name)
        self.encdata = bytearray(encdata)
        self.pos = self.encpos = 0
        self.buf = bytearray()
        self.failed = 0

    def enc_byte(self):
        try:
            c = self.encdata[self.encpos]
            self.encpos += 1
            return c
        except IndexError:
            self.failed = 1
            return 0

    def std_byte(self):
        try:
            return self.std_name[self.pos]
        except IndexError:
            self.failed = 1
            return ord('?')

    def put(self, lo, hi):
        self.buf.append(lo)
        self.buf.append(hi)
        self.pos += 1

    def decode(self):
        hi = self.enc_byte()
        flagbits = 0
        while self.encpos < len(self.encdata):
            if flagbits == 0:
                flags = self.enc_byte()
                flagbits = 8
            flagbits -= 2
            t = (flags >> flagbits) & 3
            if t == 0:
                self.put(self.enc_byte(), 0)
            elif t == 1:
                self.put(self.enc_byte(), hi)
            elif t == 2:
                self.put(self.enc_byte(), self.enc_byte())
            else:
                n = self.enc_byte()
                if n & 0x80:
                    c = self.enc_byte()
                    for i in range((n & 0x7f) + 2):
                        lo = (self.std_byte() + c) & 0xFF
                        self.put(lo, hi)
                else:
                    for i in range(n + 2):
                        self.put(self.std_byte(), 0)
        return self.buf.decode("utf-16le", "replace")


class RarExtFile(RawIOBase):
    """Base class for file-like object that :meth:`RarFile.open` returns.

    Provides public methods and common crc checking.

    Behaviour:
     - no short reads - .read() and .readinfo() read as much as requested.
     - no internal buffer, use io.BufferedReader for that.

    If :mod:`io` module is available (Python 2.6+, 3.x), then this calls
    will inherit from :class:`io.RawIOBase` class.  This makes line-based
    access available: :meth:`RarExtFile.readline` and ``for ln in f``.
    """

    #: Filename of the archive entry
    name = None

    def __init__(self, rf, inf):
        RawIOBase.__init__(self)

        # standard io.* properties
        self.name = inf.filename
        self.mode = 'rb'

        self.rf = rf
        self.inf = inf
        self.crc_check = rf._crc_check
        self.fd = None
        self.CRC = 0
        self.remain = 0
        self.returncode = 0

        self._open()

    def _open(self):
        if self.fd:
            self.fd.close()
        self.fd = None
        self.CRC = 0
        self.remain = self.inf.file_size

    def read(self, cnt = None):
        """Read all or specified amount of data from archive entry."""

        # sanitize cnt
        if cnt is None or cnt < 0:
            cnt = self.remain
        elif cnt > self.remain:
            cnt = self.remain
        if cnt == 0:
            return EMPTY

        # actual read
        data = self._read(cnt)
        if data:
            self.CRC = crc32(data, self.CRC)
            self.remain -= len(data)
        if len(data) != cnt:
            raise BadRarFile("Failed the read enough data")

        # done?
        if not data or self.remain == 0:
            #self.close()
            self._check()
        return data

    def _check(self):
        """Check final CRC."""
        if not self.crc_check:
            return
        if self.returncode:
            check_returncode(self, '')
        if self.remain != 0:
            raise BadRarFile("Failed the read enough data")
        crc = self.CRC
        if crc < 0:
            crc += (long(1) << 32)
        if crc != self.inf.CRC:
            raise BadRarFile("Corrupt file - CRC check failed: " + self.inf.filename)

    def _read(self, cnt):
        """Actual read that gets sanitized cnt."""

    def close(self):
        """Close open resources."""

        RawIOBase.close(self)

        if self.fd:
            self.fd.close()
            self.fd = None

    def __del__(self):
        """Hook delete to make sure tempfile is removed."""
        self.close()

    def readinto(self, buf):
        """Zero-copy read directly into buffer.

        Returns bytes read.
        """

        data = self.read(len(buf))
        n = len(data)
        try:
            buf[:n] = data
        except TypeError:
            import array
            if not isinstance(buf, array.array):
                raise
            buf[:n] = array.array(buf.typecode, data)
        return n

    def tell(self):
        """Return current reading position in uncompressed data."""
        return self.inf.file_size - self.remain

    def seek(self, ofs, whence = 0):
        """Seek in data.
        
        On uncompressed files, the seeking works by actual
        seeks so it's fast.  On compresses files its slow
        - forward seeking happends by reading ahead,
        backwards by re-opening and decompressing from the start.
        """

        # disable crc check when seeking
        self.crc_check = 0

        fsize = self.inf.file_size
        cur_ofs = self.tell()

        if whence == 0:     # seek from beginning of file
            new_ofs = ofs
        elif whence == 1:   # seek from current position
            new_ofs = cur_ofs + ofs
        elif whence == 2:   # seek from end of file
            new_ofs = fsize + ofs
        else:
            raise ValueError('Invalid value for whence')

        # sanity check
        if new_ofs < 0:
            new_ofs = 0
        elif new_ofs > fsize:
            new_ofs = fsize

        # do the actual seek
        if new_ofs >= cur_ofs:
            self._skip(new_ofs - cur_ofs)
        else:
            # process old data ?
            #self._skip(fsize - cur_ofs)
            # reopen and seek
            self._open()
            self._skip(new_ofs)
        return self.tell()

    def _skip(self, cnt):
        """Read and discard data"""
        while cnt > 0:
            if cnt > 8192:
                buf = self.read(8192)
            else:
                buf = self.read(cnt)
            if not buf:
                break
            cnt -= len(buf)

    def readable(self):
        """Returns True"""
        return True

    def writable(self):
        """Returns False.
        
        Writing is not supported."""
        return False

    def seekable(self):
        """Returns True.
        
        Seeking is supported, although it's slow on compressed files.
        """
        return True

    def readall(self):
        """Read all remaining data"""
        # avoid RawIOBase default impl
        return self.read()


class PipeReader(RarExtFile):
    """Read data from pipe, handle tempfile cleanup."""

    def __init__(self, rf, inf, cmd, tempfile=None):
        self.cmd = cmd
        self.proc = None
        self.tempfile = tempfile
        RarExtFile.__init__(self, rf, inf)

    def _close_proc(self):
        if not self.proc:
            return
        if self.proc.stdout:
            self.proc.stdout.close()
        if self.proc.stdin:
            self.proc.stdin.close()
        if self.proc.stderr:
            self.proc.stderr.close()
        self.proc.wait()
        self.returncode = self.proc.returncode
        self.proc = None

    def _open(self):
        RarExtFile._open(self)

        # stop old process
        self._close_proc()

        # launch new process
        self.returncode = 0
        self.proc = custom_popen(self.cmd)
        self.fd = self.proc.stdout

        # avoid situation where unrar waits on stdin
        if self.proc.stdin:
            self.proc.stdin.close()

    def _read(self, cnt):
        """Read from pipe."""

        # normal read is usually enough
        data = self.fd.read(cnt)
        if len(data) == cnt or not data:
            return data

        # short read, try looping
        buf = [data]
        cnt -= len(data)
        while cnt > 0:
            data = self.fd.read(cnt)
            if not data:
                break
            cnt -= len(data)
            buf.append(data)
        return EMPTY.join(buf)

    def close(self):
        """Close open resources."""

        self._close_proc()
        RarExtFile.close(self)

        if self.tempfile:
            try:
                os.unlink(self.tempfile)
            except OSError:
                pass
            self.tempfile = None

    if have_memoryview:
        def readinto(self, buf):
            """Zero-copy read directly into buffer."""
            cnt = len(buf)
            if cnt > self.remain:
                cnt = self.remain
            vbuf = memoryview(buf)
            res = got = 0
            while got < cnt:
                res = self.fd.readinto(vbuf[got : cnt])
                if not res:
                    break
                if self.crc_check:
                    self.CRC = crc32(vbuf[got : got + res], self.CRC)
                self.remain -= res
                got += res
            return got


class DirectReader(RarExtFile):
    """Read uncompressed data directly from archive."""

    def _open(self):
        RarExtFile._open(self)

        self.volfile = self.inf.volume_file
        self.fd = XFile(self.volfile, 0)
        self.fd.seek(self.inf.header_offset, 0)
        self.cur = self.rf._parse_header(self.fd)
        self.cur_avail = self.cur.add_size

    def _skip(self, cnt):
        """RAR Seek, skipping through rar files to get to correct position
        """

        while cnt > 0:
            # next vol needed?
            if self.cur_avail == 0:
                if not self._open_next():
                    break

            # fd is in read pos, do the read
            if cnt > self.cur_avail:
                cnt -= self.cur_avail
                self.remain -= self.cur_avail
                self.cur_avail = 0
            else:
                self.fd.seek(cnt, 1)
                self.cur_avail -= cnt
                self.remain -= cnt
                cnt = 0

    def _read(self, cnt):
        """Read from potentially multi-volume archive."""

        buf = []
        while cnt > 0:
            # next vol needed?
            if self.cur_avail == 0:
                if not self._open_next():
                    break

            # fd is in read pos, do the read
            if cnt > self.cur_avail:
                data = self.fd.read(self.cur_avail)
            else:
                data = self.fd.read(cnt)
            if not data:
                break

            # got some data
            cnt -= len(data)
            self.cur_avail -= len(data)
            buf.append(data)

        if len(buf) == 1:
            return buf[0]
        return EMPTY.join(buf)

    def _open_next(self):
        """Proceed to next volume."""

        # is the file split over archives?
        if (self.cur.flags & RAR_FILE_SPLIT_AFTER) == 0:
            return False

        if self.fd:
            self.fd.close()
            self.fd = None

        # open next part
        self.volfile = self.rf._next_volname(self.volfile)
        fd = open(self.volfile, "rb", 0)
        self.fd = fd

        # loop until first file header
        while 1:
            cur = self.rf._parse_header(fd)
            if not cur:
                raise BadRarFile("Unexpected EOF")
            if cur.type in (RAR_BLOCK_MARK, RAR_BLOCK_MAIN):
                if cur.add_size:
                    fd.seek(cur.add_size, 1)
                continue
            if cur.orig_filename != self.inf.orig_filename:
                raise BadRarFile("Did not found file entry")
            self.cur = cur
            self.cur_avail = cur.add_size
            return True

    if have_memoryview:
        def readinto(self, buf):
            """Zero-copy read directly into buffer."""
            got = 0
            vbuf = memoryview(buf)
            while got < len(buf):
                # next vol needed?
                if self.cur_avail == 0:
                    if not self._open_next():
                        break

                # lenght for next read
                cnt = len(buf) - got
                if cnt > self.cur_avail:
                    cnt = self.cur_avail

                # read into temp view
                res = self.fd.readinto(vbuf[got : got + cnt])
                if not res:
                    break
                if self.crc_check:
                    self.CRC = crc32(vbuf[got : got + res], self.CRC)
                self.cur_avail -= res
                self.remain -= res
                got += res
            return got


class HeaderDecrypt:
    """File-like object that decrypts from another file"""
    def __init__(self, f, key, iv):
        self.f = f
        self.ciph = AES.new(key, AES.MODE_CBC, iv)
        self.buf = EMPTY

    def tell(self):
        return self.f.tell()

    def read(self, cnt=None):
        if cnt > 8*1024:
            raise BadRarFile('Bad count to header decrypt - wrong password?')

        # consume old data
        if cnt <= len(self.buf):
            res = self.buf[:cnt]
            self.buf = self.buf[cnt:]
            return res
        res = self.buf
        self.buf = EMPTY
        cnt -= len(res)

        # decrypt new data
        BLK = self.ciph.block_size
        while cnt > 0:
            enc = self.f.read(BLK)
            if len(enc) < BLK:
                break
            dec = self.ciph.decrypt(enc)
            if cnt >= len(dec):
                res += dec
                cnt -= len(dec)
            else:
                res += dec[:cnt]
                self.buf = dec[cnt:]
                cnt = 0

        return res

# handle (filename|filelike) object
class XFile(object):
    __slots__ = ('_fd', '_need_close')
    def __init__(self, xfile, bufsize = 1024):
        if is_filelike(xfile):
            self._need_close = False
            self._fd = xfile
            self._fd.seek(0)
        else:
            self._need_close = True
            self._fd = open(xfile, 'rb', bufsize)
    def read(self, n=None):
        return self._fd.read(n)
    def tell(self):
        return self._fd.tell()
    def seek(self, ofs, whence=0):
        return self._fd.seek(ofs, whence)
    def readinto(self, dst):
        return self._fd.readinto(dst)
    def close(self):
        if self._need_close:
            self._fd.close()
    def __enter__(self):
        return self
    def __exit__(self, typ, val, tb):
        self.close()

##
## Utility functions
##

def is_filelike(obj):
    if isinstance(obj, str) or isinstance(obj, unicode):
        return False
    res = True
    for a in ('read', 'tell', 'seek'):
        res = res and hasattr(obj, a)
    if not res:
        raise ValueError("Invalid object passed as file")
    return True

def rar3_s2k(psw, salt):
    """String-to-key hash for RAR3."""

    seed = psw.encode('utf-16le') + salt
    iv = EMPTY
    h = sha1()
    for i in range(16):
        for j in range(0x4000):
            cnt = S_LONG.pack(i*0x4000 + j)
            h.update(seed + cnt[:3])
            if j == 0:
                iv += h.digest()[19:20]
    key_be = h.digest()[:16]
    key_le = pack("<LLLL", *unpack(">LLLL", key_be))
    return key_le, iv

def rar_decompress(vers, meth, data, declen=0, flags=0, crc=0, psw=None, salt=None):
    """Decompress blob of compressed data.

    Used for data with non-standard header - eg. comments.
    """

    # already uncompressed?
    if meth == RAR_M0 and (flags & RAR_FILE_PASSWORD) == 0:
        return data

    # take only necessary flags
    flags = flags & (RAR_FILE_PASSWORD | RAR_FILE_SALT | RAR_FILE_DICTMASK)
    flags |= RAR_LONG_BLOCK

    # file header
    fname = bytes('data', 'ascii')
    date = 0
    mode = 0x20
    fhdr = S_FILE_HDR.pack(len(data), declen, RAR_OS_MSDOS, crc,
                           date, vers, meth, len(fname), mode)
    fhdr += fname
    if flags & RAR_FILE_SALT:
        if not salt:
            return EMPTY
        fhdr += salt

    # full header
    hlen = S_BLK_HDR.size + len(fhdr)
    hdr = S_BLK_HDR.pack(0, RAR_BLOCK_FILE, flags, hlen) + fhdr
    hcrc = crc32(hdr[2:]) & 0xFFFF
    hdr = S_BLK_HDR.pack(hcrc, RAR_BLOCK_FILE, flags, hlen) + fhdr

    # archive main header
    mh = S_BLK_HDR.pack(0x90CF, RAR_BLOCK_MAIN, 0, 13) + ZERO * (2+4)

    # decompress via temp rar
    tmpfd, tmpname = mkstemp(suffix='.rar')
    tmpf = os.fdopen(tmpfd, "wb")
    try:
        tmpf.write(RAR_ID + mh + hdr + data)
        tmpf.close()

        cmd = [UNRAR_TOOL] + list(OPEN_ARGS)
        add_password_arg(cmd, psw, (flags & RAR_FILE_PASSWORD))
        cmd.append(tmpname)

        p = custom_popen(cmd)
        return p.communicate()[0]
    finally:
        tmpf.close()
        os.unlink(tmpname)

def to_datetime(t):
    """Convert 6-part time tuple into datetime object."""

    if t is None:
        return None

    # extract values
    year, mon, day, h, m, xs = t
    s = int(xs)
    us = int(1000000 * (xs - s))

    # assume the values are valid
    try:
        return datetime(year, mon, day, h, m, s, us)
    except ValueError:
        pass

    # sanitize invalid values
    MDAY = (0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if mon < 1:  mon = 1
    if mon > 12: mon = 12
    if day < 1:  day = 1
    if day > MDAY[mon]: day = MDAY[mon]
    if h > 23:   h = 23
    if m > 59:   m = 59
    if s > 59:   s = 59
    if mon == 2 and day == 29:
        try:
            return datetime(year, mon, day, h, m, s, us)
        except ValueError:
            day = 28
    return datetime(year, mon, day, h, m, s, us)

def parse_dos_time(stamp):
    """Parse standard 32-bit DOS timestamp."""

    sec = stamp & 0x1F; stamp = stamp >> 5
    min = stamp & 0x3F; stamp = stamp >> 6
    hr  = stamp & 0x1F; stamp = stamp >> 5
    day = stamp & 0x1F; stamp = stamp >> 5
    mon = stamp & 0x0F; stamp = stamp >> 4
    yr = (stamp & 0x7F) + 1980
    return (yr, mon, day, hr, min, sec * 2)

def custom_popen(cmd):
    """Disconnect cmd from parent fds, read only from stdout."""

    # needed for py2exe
    creationflags = 0
    if sys.platform == 'win32':
        creationflags = 0x08000000 # CREATE_NO_WINDOW

    # run command
    try:
        p = Popen(cmd, bufsize = 0,
                  stdout = PIPE, stdin = PIPE, stderr = STDOUT,
                  creationflags = creationflags)
    except OSError:
        ex = sys.exc_info()[1]
        if ex.errno == errno.ENOENT:
            raise RarCannotExec("Unrar not installed? (rarfile.UNRAR_TOOL=%r)" % UNRAR_TOOL)
        raise
    return p

def custom_check(cmd, ignore_retcode=False):
    """Run command, collect output, raise error if needed."""
    p = custom_popen(cmd)
    out, err = p.communicate()
    if p.returncode and not ignore_retcode:
        raise RarExecError("Check-run failed")
    return out

def add_password_arg(cmd, psw, required=False):
    """Append password switch to commandline."""
    if UNRAR_TOOL == ALT_TOOL:
        return
    if psw is not None:
        cmd.append('-p' + psw)
    else:
        cmd.append('-p-')

def check_returncode(p, out):
    """Raise exception according to unrar exit code"""

    code = p.returncode
    if code == 0:
        return
    if code == 9:
        return

    # map return code to exception class
    errmap = [None,
        RarWarning, RarFatalError, RarCRCError, RarLockedArchiveError,
        RarWriteError, RarOpenError, RarUserError, RarMemoryError,
        RarCreateError, RarNoFilesError] # codes from rar.txt
    if UNRAR_TOOL == ALT_TOOL:
        errmap = [None]
    if code > 0 and code < len(errmap):
        exc = errmap[code]
    elif code == 255:
        exc = RarUserBreak
    elif code < 0:
        exc = RarSignalExit
    else:
        exc = RarUnknownError

    # format message
    if out:
        msg = "%s [%d]: %s" % (exc.__doc__, p.returncode, out)
    else:
        msg = "%s [%d]" % (exc.__doc__, p.returncode)

    raise exc(msg)

#
# Check if unrar works
#

try:
    # does UNRAR_TOOL work?
    custom_check([UNRAR_TOOL], True)
except RarCannotExec:
    try:
        # does ALT_TOOL work?
        custom_check([ALT_TOOL] + list(ALT_CHECK_ARGS), True)
        # replace config
        UNRAR_TOOL = ALT_TOOL
        OPEN_ARGS = ALT_OPEN_ARGS
        EXTRACT_ARGS = ALT_EXTRACT_ARGS
        TEST_ARGS = ALT_TEST_ARGS
    except RarCannotExec:
        # no usable tool, only uncompressed archives work
        pass

