"""
py2app/cx_Freeze build script for KCC.

Will automatically ensure that all build prerequisites are available via ez_setup

Usage (Mac OS X):
    python setup.py py2app

Usage (Windows):
    python setup.py build
"""
from ez_setup import use_setuptools
use_setuptools()

import sys

NAME = "KindleComicConverter"
VERSION = "2.8-dev"
MAIN = "kcc.py"

includefiles = ['README.md', 'MANIFEST.in', 'LICENSE.txt', 'comic2ebook.ico', 'comic2ebook.icns']
includes = []
excludes = []

if sys.platform == "darwin":
    from setuptools import setup
    extra_options = dict(
        setup_requires=['py2app'],
        app=[MAIN],
        options=dict(
            py2app=dict(
                argv_emulation=True,
                iconfile='comic2ebook.icns',
                plist=dict(
                    CFBundleName=NAME,
                    CFBundleShortVersionString=VERSION,
                    CFBundleGetInfoString=NAME + " " + VERSION + ", written 2012-2013 by Ciro Mattia Gonano",
                    CFBundleExecutable=NAME,
                    CFBundleIdentifier='com.github.ciromattia.kcc',
                    CFBundleSignature='dplt'
                )
            )
        )
    )
elif sys.platform == 'win32':
    from cx_Freeze import setup, Executable
    base = "Win32GUI"
    extra_options = dict(
        options={"build_exe": {"include_files": includefiles, 'excludes': excludes, 'compressed': True}},
        executables=[Executable(MAIN,
                                base=base,
                                icon="comic2ebook.ico",
                                copyDependentFiles=True,
                                appendScriptToExe=True,
                                appendScriptToLibrary=False,
                                compress=True)])
else:
    extra_options = dict(
        scripts=[MAIN],
    )

setup(
    name=NAME,
    version=VERSION,
    author="Ciro Mattia Gonano",
    author_email="ciromattia@gmail.com",
    description="A tool to convert comics (CBR/CBZ/PDFs/image folders) to Mobipocket.",
    license="ISC License (ISCL)",
    keywords="kindle comic mobipocket mobi cbz cbr manga",
    url="http://github.com/ciromattia/kcc",
    classifiers=[
        'Development Status :: 4 - Beta'
        'License :: OSI Approved :: ISC License (ISCL)',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Utilities'
    ],
    packages=['kcc'],
    **extra_options
)
