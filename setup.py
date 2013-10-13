"""
cx_Freeze build script for KCC.

Usage (Mac OS X):
    python setup.py py2app

Usage (Windows):
    python setup.py build
"""
from sys import platform

NAME = "KindleComicConverter"
VERSION = "3.4"
MAIN = "kcc.py"

if platform == "darwin":
    from setuptools import setup
    extra_options = dict(
        setup_requires=['py2app'],
        app=[MAIN],
        options=dict(
            py2app=dict(
                argv_emulation=True,
                iconfile='icons/comic2ebook.icns',
                includes=['PIL', 'sip', 'PyQt4', 'PyQt4.QtCore', 'PyQt4.QtGui', 'PyQt4.QtNetwork'],
                excludes=['PyQt4.QtDeclarative', 'PyQt4.QtDesigner', 'PyQt4.QtHelp', 'PyQt4.QtMultimedia',
                          'PyQt4.QtOpenGL', 'PyQt4.QtScript', 'PyQt4.QtScriptTools', 'PyQt4.QtSql', 'PyQt4.QtSvg',
                          'PyQt4.QtXmlPatterns', 'PyQt4.QtXml', 'PyQt4.QtWebKit', 'PyQt4.QtTest'],
                resources=['LICENSE.txt', 'other/Additional-LICENSE.txt'],
                plist=dict(
                    CFBundleName=NAME,
                    CFBundleShortVersionString=VERSION,
                    CFBundleGetInfoString=NAME + " " + VERSION +
                    ", written 2012-2013 by Ciro Mattia Gonano and Pawel Jastrzebski",
                    CFBundleExecutable=NAME,
                    CFBundleIdentifier='com.github.ciromattia.kcc',
                    CFBundleSignature='dplt',
                    CFBundleDocumentTypes=[
                        dict(
                            CFBundleTypeExtensions=['cbz', 'cbr', 'cb7', 'zip', 'rar', '7z', 'pdf'],
                            CFBundleTypeIconFile='comic2ebook.icns',
                            CFBundleTypeRole='Viewer',
                        )
                    ],
                    NSHumanReadableCopyright='ISC License (ISCL)'
                )
            )
        )
    )
elif platform == "win32":
    from cx_Freeze import setup, Executable
    base = "Win32GUI"
    extra_options = dict(
        options={"build_exe": {"include_files": ['LICENSE.txt',
                                                 ['other/UnRAR.exe', 'UnRAR.exe'],
                                                 ['other/7za.exe', '7za.exe'],
                                                 ['other/Additional-LICENSE.txt', 'Additional-LICENSE.txt']
                                                 ], "compressed": True}},
        executables=[Executable(MAIN,
                                base=base,
                                targetName="KCC.exe",
                                icon="icons/comic2ebook.ico",
                                copyDependentFiles=True,
                                appendScriptToExe=True,
                                appendScriptToLibrary=False,
                                compress=True)])
else:
    from cx_Freeze import setup, Executable
    extra_options = dict(
        options={"build_exe": {"include_files": ['LICENSE.txt',
                                                 ['other/Additional-LICENSE.txt', 'Additional-LICENSE.txt']
                                                 ], "compressed": True}},
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
    packages=['kcc'], requires=['Pillow'],
    **extra_options
)
