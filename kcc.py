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
#
# Todo:
#   - Add gracefully exit for CBR if no rarfile.py and no unrar
#       executable are found
#   - Improve error reporting
#   - recurse into dirtree for multiple comics

__version__ = '2.0'
__license__   = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>'
__docformat__ = 'restructuredtext en'

from Tkinter import *
from kcc import gui

root = Tk()
app = gui.MainWindow(master=root,title="Kindle Comic Converter v" + __version__)
root.tkraise()
root.mainloop()
