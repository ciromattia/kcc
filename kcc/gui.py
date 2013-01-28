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
import tkFileDialog, tkMessageBox, ttk
import comic2ebook, kindlestrip
from image import ProfileData
from subprocess import call, Popen, PIPE, STDOUT
import os, shutil, stat

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
        self.filelocation.grid(row=0,columnspan=4,sticky=W+E+N+S)
        self.refresh_list()

        self.clear_file = Button(self.master, text="Clear files", command=self.clear_files)
        self.clear_file.grid(row=4,column=0,rowspan=3)
        self.open_file = Button(self.master, text="Add files...", command=self.open_files)
        self.open_file.grid(row=4,column=1,rowspan=3)
        self.open_folder = Button(self.master, text="Add folder...", command=self.open_folder)
        self.open_folder.grid(row=4,column=2,rowspan=3)

        self.profile = StringVar()
        options = sorted(ProfileData.ProfileLabels.iterkeys())
        self.profile.set(options[-1])
        w = apply(OptionMenu, (self.master, self.profile) + tuple(options))
        w.grid(row=1,column=3)

        self.image_preprocess = IntVar()
        self.image_preprocess = 1
        self.cut_page_numbers = IntVar()
        self.cut_page_numbers = 1
        self.mangastyle = IntVar()
        self.mangastyle = 0
        self.image_upscale = IntVar()
        self.image_upscale = 0
        self.image_stretch = IntVar()
        self.image_stretch = 0
        self.c = Checkbutton(self.master, text="Apply image optimizations",
            variable=self.image_preprocess)
        self.c.select()
        self.c.grid(row=2,column=3,sticky=W)
        self.c = Checkbutton(self.master, text="Cut page numbers",
            variable=self.cut_page_numbers)
        self.c.grid(row=3,column=3,sticky=W)
        self.c = Checkbutton(self.master, text="Split manga-style (right-to-left reading)",
            variable=self.mangastyle)
        self.c.grid(row=4,column=3,sticky=W)
        self.c = Checkbutton(self.master, text="Allow image upscaling",
            variable=self.image_upscale)
        self.c.grid(row=5,column=3,sticky=W)
        self.c = Checkbutton(self.master, text="Stretch images",
            variable=self.image_stretch)
        self.c.grid(row=6,column=3,sticky=W)

        self.progressbar = ttk.Progressbar(orient=HORIZONTAL, length=200, mode='determinate')

        self.submit = Button(self.master, text="Execute!", command=self.start_conversion, fg="red")
        self.submit.grid(row=7,column=3)
        self.progressbar.grid(row=8,column=0,columnspan=4,sticky=W+E+N+S)

#        self.debug = Listbox(self.master)
#        self.debug.grid(row=9,columnspan=4,sticky=W+E+N+S)
#        self.debug.insert(END, os.environ['PATH'])

    def start_conversion(self):
        self.progressbar.start()
        self.convert()
        self.progressbar.stop()

    def convert(self):
        profilekey = ProfileData.ProfileLabels[self.profile.get()]
        argv = ["-p",profilekey]
        if self.image_preprocess == 0:
            argv.append("--no-image-processing")
        if self.cut_page_numbers == 0:
            argv.append("--no-cut-page-numbers")
        if self.mangastyle == 1:
            argv.append("-m")
        if self.image_upscale == 1:
            argv.append("--upscale-images")
        if self.image_stretch == 1:
            argv.append("--stretch-images")
        errors = False
        for entry in self.filelist:
            self.master.update()
            try:
                subargv = list(argv)
                subargv.append(entry)
                comic2ebook.main(subargv)
                path = comic2ebook.getEpubPath()
            except Exception, err:
                tkMessageBox.showerror('Error comic2ebook', "Error on file %s:\n%s" % (subargv[-1], str(err)))
                errors = True
                continue
            try:
                retcode = call("kindlegen " + path + "/content.opf", shell=True)
                if retcode < 0:
                    print >>sys.stderr, "Child was terminated by signal", -retcode
                else:
                    print >>sys.stderr, "Child returned", retcode
            except OSError as e:
                tkMessageBox.showerror('Error kindlegen', "Error on file %s:\n%s" % (path + "/content.opf", e))
                errors = True
                continue
            try:
                kindlestrip.main((path + "/content.mobi", path + '.mobi'))
                # try to clean up temp files... may be destructive!!!
                shutil.rmtree(path, onerror=self.remove_readonly)
            except Exception, err:
                tkMessageBox.showerror('Error', "Error on file %s:\n%s" % (path + "/content.mobi", str(err)))
                errors = True
                continue
        if errors:
            tkMessageBox.showinfo(
                "Done",
                "Conversion finished (some errors have been reported)"
            )
        else:
            tkMessageBox.showinfo(
                "Done",
                "Conversion successfully done!"
            )

    def remove_readonly(self, fn, path, excinfo):
        if fn is os.rmdir:
            os.chmod(path, stat.S_IWRITE)
            os.rmdir(path)
        elif fn is os.remove:
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)

    def __init__(self, master, title):
        self.filelist = []
        self.master = master
        self.master.title(title)
        self.initialize()


