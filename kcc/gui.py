#!/usr/bin/env python
#
# Copyright (c) 2013 Ciro Mattia Gonano <ciromattia@gmail.com>
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

__license__   = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>'
__docformat__ = 'restructuredtext en'

from Tkinter import *
import tkFileDialog
import ttk
import comic2ebook
from image import ProfileData

class MainWindow:

    def clear_files(self):
        self.filelist = []
        self.refresh_list()

    def open_files(self):
        filetypes = [('all files', '.*'), ('Comic files', ('*.cbr','*.cbz','*.zip','*.rar','*.pdf'))]
        f = tkFileDialog.askopenfilenames(title="Choose a file...",filetypes=filetypes)
        if not isinstance(f,tuple):
            try:
                import re
                f = re.findall('\{(.*?)\}', f)
            except:
                import tkMessageBox
                tkMessageBox.showerror(
                    "Open file",
                    "askopenfilename() returned other than a tuple and no regex module could be found"
                )
                sys.exit(1)
        self.filelist.extend(f)
        self.refresh_list()

    def open_folder(self):
        self.filelist = tkFileDialog.askdirectory(title="Choose a folder...")
        self.refresh_list()

    def refresh_list(self):
        self.filelocation.config(state=NORMAL)
        self.filelocation.delete(0, END)
        for file in self.filelist:
            self.filelocation.insert(END, file)
        self.filelocation.config(state=DISABLED)

    def initialize(self):
        self.filelocation = Listbox(self.master)
        self.filelocation.pack(fill=BOTH, expand=1)
        self.refresh_list()

        self.clear_file = Button(self.master, text="Clear files", command=self.clear_files)
        self.clear_file.pack(side=LEFT)
        self.open_file = Button(self.master, text="Add files...", command=self.open_files)
        self.open_file.pack(side=LEFT)
        self.open_folder = Button(self.master, text="Add folder...", command=self.open_folder)
        self.open_folder.pack(side=LEFT)

        self.profile = StringVar()
        self.profile.set("KHD")
        w = apply(OptionMenu, (self.master, self.profile) + tuple(sorted(ProfileData.Profiles.iterkeys())))
        w.pack(anchor=W,fill=BOTH)

        self.mangastyle = BooleanVar()
        self.mangastyle = False
        self.c = Checkbutton(self.master, text="Split manga-style (right-to-left reading)",
                             variable=self.mangastyle)
        self.c.pack()

        #now for a button
        self.submit = Button(self.master, text="Execute!", command=self.convert, fg="red")
        self.submit.pack()

        self.progressbar = ttk.Progressbar(orient=HORIZONTAL, length=200, mode='determinate')
        self.progressbar.pack(side=BOTTOM)

    def convert(self):
        argv = ["-p",self.profile.get()]
        if self.mangastyle:
            argv.append("-m")
        self.progressbar.start()
        for entry in self.filelist:
            subargv = list(argv)
            subargv.append(entry)
            comic2ebook.main(subargv)

        print "Done!"

    def __init__(self, master, title):
        self.filelist = []
        self.master = master
        self.master.title(title)
        self.initialize()


