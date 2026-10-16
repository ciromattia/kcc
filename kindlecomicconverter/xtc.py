# -*- coding: utf-8 -*-
#
# Copyright (c) 2026 Kindle Comic Converter contributors
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted, provided that the
# above copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""Compact XTC v1 output for XTEINK X4 readers."""

from pathlib import Path
import struct

from PIL import Image


XTC_HEADER = struct.Struct('<IHHIIQQQQ')
XTC_PAGE_INDEX = struct.Struct('<QIHH')
XTG_HEADER = struct.Struct('<IHHBBIQ')


def encode_xtg(image):
    """Encode an uncompressed 1-bit XTG page."""
    if not 1 <= image.width <= 0xFFFF or not 1 <= image.height <= 0xFFFF:
        raise ValueError('XTG dimensions must be between 1 and 65535')
    monochrome = image.convert('L').convert('1', dither=Image.Dither.FLOYDSTEINBERG)
    # Pillow mode 1 matches XTG's row-major, MSB-first pixel layout.
    data = monochrome.tobytes()
    return XTG_HEADER.pack(0x00475458, image.width, image.height, 0, 0,
                           len(data), int.from_bytes(data[:8], 'little')) + data


def write_xtc(image_paths, output_path):
    """Write pages in input order using the compact, metadata-free layout."""
    paths = list(image_paths)
    if not 1 <= len(paths) <= 0xFFFF:
        raise ValueError('XTC output requires between 1 and 65535 pages')
    output_path = Path(output_path)
    index_offset = XTC_HEADER.size
    data_offset = index_offset + len(paths) * XTC_PAGE_INDEX.size
    page_index = []
    with output_path.open('wb') as output:
        output.write(XTC_HEADER.pack(0x00435458, 0x0100, len(paths),
                                     0, 0, 0, index_offset, data_offset, 0))
        output.write(b'\0' * (len(paths) * XTC_PAGE_INDEX.size))
        for path in paths:
            with Image.open(path) as page:
                data = encode_xtg(page)
                width, height = page.size
            page_index.append(XTC_PAGE_INDEX.pack(output.tell(), len(data), width, height))
            output.write(data)
        output.seek(index_offset)
        output.write(b''.join(page_index))
    return output_path
