"""
py2app/py2exe build script for KCC.

Will automatically ensure that all build prerequisites are available
via ez_setup

Usage (Mac OS X):
    python setup.py py2app

Usage (Windows):
    python setup.py build
"""
from ez_setup import use_setuptools
use_setuptools()

import sys
from setuptools import setup

NAME = 'KindleComicConverter'
VERSION = "2.6"
mainscript = 'kcc.py'

if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires=['py2app'],
        app=[mainscript],
        options=dict(
            py2app=dict(
                argv_emulation=True,
                iconfile='resources/comic2ebook.icns',
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
        executables=[Executable("kcc.py", base=base)]
    )
else:
    extra_options = dict(
        # Normally unix-like platforms will use "setup.py install"
        # and install the main script as such
        scripts=[mainscript],
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
    # make sure to add custom_fixers to the MANIFEST.in
    include_package_data=True,
    **extra_options
)
