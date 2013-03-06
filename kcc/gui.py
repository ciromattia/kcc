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

__license__ = 'ISC'
__copyright__ = '2012-2013, Ciro Mattia Gonano <ciromattia@gmail.com>'
__docformat__ = 'restructuredtext en'

from Tkinter import *
import tkFileDialog
import tkMessageBox
import comic2ebook
import kindlestrip
from image import ProfileData
from subprocess import call
import os
import shutil
import stat


class MainWindow:

    def clear_files(self):
        self.filelist = []
        self.refresh_list()

    def open_files(self):
        filetypes = [('All files', '.*'), ('Comic files', ('*.cbr', '*.cbz', '*.zip', '*.rar', '*.pdf'))]
        f = tkFileDialog.askopenfilenames(title="Choose files", filetypes=filetypes)
        if not isinstance(f, tuple):
            try:
                import re
                f = re.findall('\{(.*?)\}', f)
            except:
                sys.exit(1)
        self.filelist.extend(f)
        self.refresh_list()

    def open_folder(self):
        f = tkFileDialog.askdirectory(title="Choose folder:")
        self.filelist.extend([f])
        self.refresh_list()

    def refresh_list(self):
        self.filelocation.config(state=NORMAL)
        self.filelocation.delete(0, END)
        for afile in self.filelist:
            self.filelocation.insert(END, afile)
        self.filelocation.config(state=DISABLED)

    def initialize(self):
        self.filelocation = Listbox(self.master)
        self.filelocation.grid(row=0, columnspan=4, sticky=W + E + N + S)
        self.refresh_list()

        self.clear_file = Button(self.master, text="Clear files", command=self.clear_files)
        self.clear_file.grid(row=4, column=0, rowspan=3)
        self.open_file = Button(self.master, text="Add files", command=self.open_files)
        self.open_file.grid(row=4, column=1, rowspan=3)
        self.open_folder = Button(self.master, text="Add folder", command=self.open_folder)
        self.open_folder.grid(row=4, column=2, rowspan=3)

        self.profile = StringVar()
        profiles = sorted(ProfileData.ProfileLabels.iterkeys())
        self.profile.set(profiles[-1])
        w = apply(OptionMenu, (self.master, self.profile) + tuple(profiles))
        w.grid(row=4, column=3, sticky=W + E + N + S)

        self.options = {
            'epub_only': IntVar(None, 0),
            'image_preprocess': IntVar(None, 1),
            'notquantize': IntVar(None, 0),
            'nosplitrotate': IntVar(None, 0),
            'rotate': IntVar(None, 0),
            'cut_page_numbers': IntVar(None, 1),
            'mangastyle': IntVar(None, 0),
            'image_gamma': DoubleVar(None, 0.0),
            'image_upscale': IntVar(None, 0),
            'image_stretch': IntVar(None, 0),
            'black_borders': IntVar(None, 0)
        }
        self.optionlabels = {
            'epub_only': "Generate EPUB only",
            'image_preprocess': "Apply image optimizations",
            'notquantize': "Disable image quantization",
            'nosplitrotate': "Disable splitting and rotation",
            'rotate': "Rotate landscape images instead of splitting them",
            'cut_page_numbers': "Cut page numbers",
            'mangastyle': "Manga mode",
            'image_gamma': "Custom gamma\n(if 0.0 the default gamma for the profile will be used)",
            'image_upscale': "Allow image upscaling",
            'image_stretch': "Stretch images",
            'black_borders': "Use black borders"
        }
        for key in self.options:
            if isinstance(self.options[key], IntVar) or isinstance(self.options[key], BooleanVar):
                aCheckButton = Checkbutton(self.master, text=self.optionlabels[key], variable=self.options[key])
                aCheckButton.grid(columnspan=4, sticky=W + N + S)
            elif isinstance(self.options[key], DoubleVar):
                aLabel = Label(self.master, text=self.optionlabels[key], justify=RIGHT)
                aLabel.grid(column=0, columnspan=3, sticky=W + N + S)
                aEntry = Entry(self.master, textvariable=self.options[key])
                aEntry.grid(column=3, row=(self.master.grid_size()[1] - 1), sticky=W + N + S)

        self.submit = Button(self.master, text="CONVERT", command=self.start_conversion, fg="red")
        self.submit.grid(columnspan=4, sticky=W + E + N + S)

    def start_conversion(self):
        self.convert()

    def convert(self):
        if len(self.filelist) < 1:
            tkMessageBox.showwarning('No files selected!', "Please choose files to convert.")
            return
        profilekey = ProfileData.ProfileLabels[self.profile.get()]
        argv = ["-p", profilekey]
        if self.options['image_gamma'].get() != 0.0:
            argv.append("--gamma")
            argv.append(self.options['image_gamma'].get())
        if self.options['image_preprocess'].get() == 0:
            argv.append("--no-image-processing")
        if self.options['notquantize'].get() == 1:
            argv.append("--nodithering")
        if self.options['nosplitrotate'].get() == 1:
            argv.append("--nosplitrotate")
        if self.options['rotate'].get() == 1:
            argv.append("--rotate")
        if self.options['cut_page_numbers'].get() == 0:
            argv.append("--no-cut-page-numbers")
        if self.options['mangastyle'].get() == 1:
            argv.append("-m")
        if self.options['image_upscale'].get() == 1:
            argv.append("--upscale-images")
        if self.options['image_stretch'].get() == 1:
            argv.append("--stretch-images")
        if self.options['black_borders'].get() == 1:
            argv.append("--black-borders")
        errors = False
        for entry in self.filelist:
            self.master.update()
            subargv = list(argv)
            try:
                subargv.append(entry)
                epub_path = comic2ebook.main(subargv)
            except Exception, err:
                tkMessageBox.showerror('KCC Error', "Error on file %s:\n%s" % (subargv[-1], str(err)))
                errors = True
                continue
            if self.options['epub_only'] == 1:
                continue
            try:
                retcode = call("kindlegen \"" + epub_path + "\"", shell=True)
                if retcode < 0:
                    print >>sys.stderr, "Child was terminated by signal", -retcode
                else:
                    print >>sys.stderr, "Child returned", retcode
            except OSError as e:
                tkMessageBox.showerror('KindleGen Error', "Error on file %s:\n%s" % (epub_path, e))
                errors = True
                continue
            mobifile = epub_path.replace('.epub', '.mobi')
            try:
                shutil.move(mobifile, mobifile + '_tostrip')
                kindlestrip.main((mobifile + '_tostrip', mobifile))
                os.remove(mobifile + '_tostrip')
            except Exception, err:
                tkMessageBox.showerror('Error', "Error on file %s:\n%s" % (mobifile, str(err)))
                errors = True
                continue
        if errors:
            tkMessageBox.showinfo(
                "Done",
                "Conversion failed. Errors have been reported."
            )
        else:
            tkMessageBox.showinfo(
                "Done",
                "Conversion successful!"
            )

    def remove_readonly(self, fn, path):
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
