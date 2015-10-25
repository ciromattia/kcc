# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2015 Pawel Jastrzebski <pawelj@iosphe.re>
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

import os.path
import psutil


class Kindle:
    def __init__(self):
        self.path = self.findDevice()
        if self.path:
            self.coverSupport = self.checkThumbnails()
        else:
            self.coverSupport = False

    def findDevice(self):
        for drive in psutil.disk_partitions(False):
            if 'removable' in drive[3] or 'vfat' in drive[2] or 'msdos' in drive[2]:
                if os.path.isdir(os.path.join(drive[1], 'system')) and \
                        os.path.isdir(os.path.join(drive[1], 'documents')):
                    return drive[1]
        return False

    def checkThumbnails(self):
        if os.path.isdir(os.path.join(self.path, 'system', 'thumbnails')):
            return True
        return False
