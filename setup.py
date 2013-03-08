"""
cx_freeze build script for KCC.

Will automatically ensure that all build prerequisites are available via ez_setup

Usage (Windows/Mac OS X):
    python setup.py build
"""
from ez_setup import use_setuptools
use_setuptools()

import sys
from cx_Freeze import setup, Executable

NAME = "KindleComicConverter"
VERSION = "2.7"
MAIN = "kcc.py"

if sys.platform == "darwin":
    icon = "comic2ebook.icns"
    base = None
    buildEXEOptions = {}
elif sys.platform == "win32":
    icon = "comic2ebook.ico"
    base = "Win32GUI"
    buildEXEOptions = {"include_files": ["comic2ebook.ico"]}

setup(
    name = NAME,
    version = VERSION,
    author = "Ciro Mattia Gonano",
    author_email = "ciromattia@gmail.com",
    description = "A tool to convert comics (CBR/CBZ/PDFs/image folders) to MOBI.",
    license = "ISC License (ISCL)",
    keywords = "kindle comic mobipocket mobi cbz cbr manga",
    url = "http://github.com/ciromattia/kcc",
    options = {"build_exe": buildEXEOptions},
    executables = [Executable(MAIN, base=base, icon=icon, appendScriptToExe=True, appendScriptToLibrary=False, compress=True)]
)
