"""
cx_Freeze build script for KCC.

Usage (Windows):
    python setup.py build

Usage (Linux):
    python setup.py build

Usage (OS X):
    python setup.py bdist_mac
"""
from sys import platform
from cx_Freeze import setup, Executable

NAME = "KindleComicConverter"
VERSION = "3.0"
MAIN = "kcc.py"

includefiles = ['LICENSE.txt']
includes = []
excludes = []

if platform == "darwin":
    extra_options = dict(
        options={"build_exe": {"include_files": includefiles, "excludes": excludes, "compressed": True},
                 "bdist_mac": {"iconfile": "icons/comic2ebook.icns"}},
        executables=[Executable(MAIN,
                                copyDependentFiles=True,
                                appendScriptToExe=True,
                                appendScriptToLibrary=False,
                                compress=True)])
elif platform == "win32":
    base = "Win32GUI"
    extra_options = dict(
        options={"build_exe": {"include_files": includefiles, "excludes": excludes, "compressed": True}},
        executables=[Executable(MAIN,
                                base=base,
                                targetName="KCC.exe",
                                icon="icons/comic2ebook.ico",
                                copyDependentFiles=True,
                                appendScriptToExe=True,
                                appendScriptToLibrary=False,
                                compress=True)])
else:
    extra_options = dict(
        options={"build_exe": {"include_files": includefiles, "excludes": excludes, "compressed": True}},
        executables=[Executable(MAIN,
                                icon="icons/comic2ebook.png",
                                copyDependentFiles=True,
                                appendScriptToExe=True,
                                appendScriptToLibrary=False,
                                compress=True)])

setup(
    name=NAME,
    version=VERSION,
    author="Ciro Mattia Gonano, Pawel Jastrzebski",
    author_email="ciromattia@gmail.com, pawelj@vulturis.eu",
    description="A tool to convert comics (CBR/CBZ/PDFs/image folders) to MOBI.",
    license="ISC License (ISCL)",
    keywords="kindle comic mobipocket mobi cbz cbr manga",
    url="http://github.com/ciromattia/kcc",
    packages=['kcc'], requires=['PIL'],
    **extra_options
)