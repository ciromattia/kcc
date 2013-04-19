"""
cx_freeze build script for Windows KCC No-GUI release.

Usage (Windows):
    python setup_console.py build
"""
import sys
from cx_Freeze import setup, Executable
sys.path.insert(0, 'kcc')

setup(
    name = "KindleComicConverter",
    version = "2.9",
    author = "Ciro Mattia Gonano",
    author_email = "ciromattia@gmail.com",
    description = "A tool to convert comics (CBR/CBZ/PDFs/image folders) to MOBI.",
    license= "ISC License (ISCL)",
    keywords= "kindle comic mobipocket mobi cbz cbr manga",
    url = "http://github.com/ciromattia/kcc",
    executables = [Executable("kcc/comic2ebook.py", compress=True, copyDependentFiles=True, appendScriptToExe=True, appendScriptToLibrary=False),
                   Executable("kcc/kindlestrip.py", compress=True, copyDependentFiles=True, appendScriptToExe=True, appendScriptToLibrary=False)]
)