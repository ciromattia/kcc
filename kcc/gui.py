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
import ttk
import comic2ebook
import kindlestrip
from image import ProfileData
from subprocess import call
import os
import shutil
import stat
import traceback


class MainWindow:

    def clear_files(self):
        self.filelist = []
        self.refresh_list()

    def change_gamma(self):
        if self.aEntry['state'] == DISABLED:
            self.aEntry['state'] = NORMAL
        else:
            self.aEntry['state'] = DISABLED

    def open_files(self):
        filetypes = [('All files', '.*'), ('Comic files', ('*.cbr', '*.cbz', '*.zip', '*.rar', '*.pdf'))]
        f = tkFileDialog.askopenfilenames(title="Choose files", filetypes=filetypes)
        if not isinstance(f, tuple):
            f = self.master.tk.splitlist(f)
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
        try:
            if len(self.filelist) > 0:
                self.submit['state'] = NORMAL
            else:
                self.submit['state'] = DISABLED
        except AttributeError:
            pass

    def initialize(self):
        self.filelocation = Listbox(self.master)
        self.filelocation.grid(row=0, columnspan=4, sticky=W + E + N + S)
        self.refresh_list()

        self.clear_file = Button(self.master, text="Clear files", command=self.clear_files)
        self.clear_file.grid(row=4, column=0, sticky=W + E + N + S)
        self.open_file = Button(self.master, text="Add files", command=self.open_files)
        self.open_file.grid(row=4, column=1, sticky=W + E + N + S)
        self.open_folder = Button(self.master, text="Add folder", command=self.open_folder)
        self.open_folder.grid(row=4, column=2, sticky=W + E + N + S)

        self.profile = StringVar()
        profiles = sorted(ProfileData.ProfileLabels.iterkeys())
        self.profile.set(profiles[-1])
        w = apply(OptionMenu, (self.master, self.profile) + tuple(profiles))
        w.grid(row=4, column=3, sticky=W + E + N + S)

        self.options = {
            'Aepub_only': IntVar(None, 0),
            'Bmangastyle': IntVar(None, 0),
            'Cnopanelviewhq': IntVar(None, 0),
            'Dimage_preprocess': IntVar(None, 0),
            'Eforcepng': IntVar(None, 0),
            'Fimage_gamma': DoubleVar(None, 0.0),
            'Gimage_upscale': IntVar(None, 0),
            'Himage_stretch': IntVar(None, 0),
            'Iblack_borders': IntVar(None, 0),
            'Jrotate': IntVar(None, 0),
            'Knosplitrotate': IntVar(None, 0),
            'Lcut_page_numbers': IntVar(None, 0)
        }
        self.optionlabels = {
            'Aepub_only': "Generate EPUB only",
            'Bmangastyle': "Manga mode",
            'Cnopanelviewhq': "Disable high quality Panel View",
            'Dimage_preprocess': "Disable image optimizations",
            'Eforcepng': "Create PNG files instead JPEG",
            'Fimage_gamma': "Custom gamma correction",
            'Gimage_upscale': "Allow image upscaling",
            'Himage_stretch': "Stretch images",
            'Iblack_borders': "Use black borders",
            'Jrotate': "Rotate images instead splitting them",
            'Knosplitrotate': "Disable splitting and rotation",
            'Lcut_page_numbers': "Disable page numbers cutting"
        }
        self.optionsButtons = {}
        for key in sorted(self.options):
            if isinstance(self.options[key], IntVar) or isinstance(self.options[key], BooleanVar):
                self.optionsButtons[key] = Checkbutton(self.master, text=self.optionlabels[key],
                                                       variable=self.options[key])
                self.optionsButtons[key].grid(columnspan=4, sticky=W + N + S)
            elif isinstance(self.options[key], DoubleVar):
                self.optionsButtons[key] = Checkbutton(self.master, text=self.optionlabels[key],
                                                       command=self.change_gamma)
                self.optionsButtons[key].grid(columnspan=4, sticky=W + N + S)
                self.aEntry = Entry(self.master, textvariable=self.options[key])
                self.aEntry['state'] = DISABLED
                self.aEntry.grid(column=3, row=(self.master.grid_size()[1] - 1), sticky=W + N + S)

        self.submit = Button(self.master, text="CONVERT", command=self.start_conversion, fg="red", state=DISABLED)
        self.submit.grid(columnspan=4, sticky=W + E + N + S)
        aLabel = Label(self.master, text="File progress:", anchor=W, justify=LEFT)
        aLabel.grid(column=0, sticky=E)
        self.progress_file = ttk.Progressbar(orient=HORIZONTAL, length=200, mode='determinate', maximum=4)
        self.progress_file.grid(column=1, columnspan=3, row=(self.master.grid_size()[1] - 1), sticky=W + E + N + S)
        aLabel = Label(self.master, text="Overall progress:", anchor=W, justify=LEFT)
        aLabel.grid(column=0, sticky=E)
        self.progress_overall = ttk.Progressbar(orient=HORIZONTAL, length=200, mode='determinate')
        self.progress_overall.grid(column=1, columnspan=3, row=(self.master.grid_size()[1] - 1), sticky=W + E + N + S)

        retcode = call("kindlegen", shell=True)
        if retcode == 1:
            self.optionsButtons['Aepub_only'].select()
            self.optionsButtons['Aepub_only']['state'] = DISABLED

    def start_conversion(self):
        self.submit['state'] = DISABLED
        self.master.update()
        self.convert()
        self.submit['state'] = NORMAL
        self.master.update()

    def convert(self):
        if len(self.filelist) < 1:
            tkMessageBox.showwarning('No files selected!', "Please choose files to convert.")
            return
        profilekey = ProfileData.ProfileLabels[self.profile.get()]
        argv = ["-p", profilekey]
        if self.options['Bmangastyle'].get() == 1:
            argv.append("-m")
        if self.options['Cnopanelviewhq'].get() == 1:
            argv.append("--nopanelviewhq")
        if self.options['Dimage_preprocess'].get() == 1:
            argv.append("--noprocessing")
        if self.options['Eforcepng'].get() == 1:
            argv.append("--forcepng")
        if self.options['Fimage_gamma'].get() != 0.0:
            argv.append("--gamma")
            argv.append(self.options['Fimage_gamma'].get())
        if self.options['Gimage_upscale'].get() == 1:
            argv.append("--upscale")
        if self.options['Himage_stretch'].get() == 1:
            argv.append("--stretch")
        if self.options['Iblack_borders'].get() == 1:
            argv.append("--blackborders")
        if self.options['Jrotate'].get() == 1:
            argv.append("--rotate")
        if self.options['Knosplitrotate'].get() == 1:
            argv.append("--nosplitrotate")
        if self.options['Lcut_page_numbers'].get() == 1:
            argv.append("--nocutpagenumbers")
        errors = False
        left_files = len(self.filelist)
        filenum = 0
        self.progress_overall['value'] = 0
        self.progress_overall['maximum'] = left_files
        for entry in self.filelist:
            self.progress_overall['value'] = filenum
            self.progress_file['value'] = 1
            self.master.update()
            filenum += 1
            subargv = list(argv)
            try:
                subargv.append(entry)
                epub_path = comic2ebook.main(subargv)
                self.progress_file['value'] = 2
                self.master.update()
            except Exception as err:
                type_, value_, traceback_ = sys.exc_info()
                tkMessageBox.showerror('KCC Error', "Error on file %s:\n%s\nTraceback:\n%s" %
                                                    (subargv[-1], str(err), traceback.format_tb(traceback_)))
                errors = True
                continue
            if self.options['Aepub_only'].get() == 0:
                try:
                    if os.path.getsize(epub_path) > 314572800:
                        # do not call kindlegen if source is bigger than 300MB
                        tkMessageBox.showwarning('KindleGen Warning',
                                                 "ePub file %s is bigger than 300MB, not suitable for kindlegen" %
                                                 epub_path)
                        continue
                    retcode = call("kindlegen \"" + epub_path + "\"", shell=True)
                    if retcode < 0:
                        print >>sys.stderr, "Child was terminated by signal", -retcode
                    else:
                        print >>sys.stderr, "Child returned", retcode
                    self.progress_file['value'] = 3
                    self.master.update()
                except OSError as e:
                    tkMessageBox.showerror('KindleGen Error', "Error on file %s:\n%s" % (epub_path, e))
                    errors = True
                    continue
                mobifile = epub_path.replace('.epub', '.mobi')
                try:
                    shutil.move(mobifile, mobifile + '_tostrip')
                    kindlestrip.main((mobifile + '_tostrip', mobifile))
                    os.remove(mobifile + '_tostrip')
                    self.progress_file['value'] = 4
                    self.master.update()
                except Exception, err:
                    tkMessageBox.showerror('KindleStrip Error', "Error on file %s:\n%s" % (mobifile, str(err)))
                    errors = True
                    continue
            else:
                    self.progress_file['value'] = 4
                    self.master.update()
        if errors:
            tkMessageBox.showwarning("Done", "Conversion completed with errors.")
        else:
            tkMessageBox.showinfo("Done", "Conversion successful!")
        # reset progressbars
        self.progress_overall['value'] = 0
        self.progress_file['value'] = 0
        self.master.update()

    def remove_readonly(self, fn, path):
        if fn is os.rmdir:
            os.chmod(path, stat.S_IWRITE)
            os.rmdir(path)
        elif fn is os.remove:
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)

    def __init__(self, master):
        self.filelist = []
        self.master = master
        self.initialize()
