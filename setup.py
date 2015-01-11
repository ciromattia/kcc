#!/usr/bin/env python3
"""
py2exe/py2app build script for KCC.

Usage (Windows):
    python setup.py py2exe

Usage (Mac OS X):
    python setup.py py2app
"""
from sys import platform, version_info
if version_info[0] != 3:
    print('ERROR: This is Python 3 script!')
    exit(1)

NAME = "KindleComicConverter"
VERSION = "4.4.1"
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
                includes=['sip', 'PyQt5.QtPrintSupport'],
                resources=['LICENSE.txt', 'other/qt.conf', 'other/Additional-LICENSE.txt', 'other/unrar', 'other/7za'],
                plist=dict(
                    CFBundleName=NAME,
                    CFBundleShortVersionString=VERSION,
                    CFBundleGetInfoString=NAME + " " + VERSION +
                    ", written 2012-2015 by Ciro Mattia Gonano and Pawel Jastrzebski",
                    CFBundleExecutable=NAME,
                    CFBundleDocumentTypes=[
                        dict(
                            CFBundleTypeExtensions=['cbz', 'cbr', 'cb7', 'zip', 'rar', '7z', 'pdf'],
                            CFBundleTypeName='Comics',
                            CFBundleTypeIconFile='comic2ebook.icns',
                            CFBundleTypeRole='Editor',
                        )
                    ],
                    LSMinimumSystemVersion='10.8.0',
                    LSEnvironment=dict(
                        PATH='./../Resources:/usr/local/bin:/usr/bin:/bin'
                    ),
                    NSHumanReadableCopyright='ISC License (ISCL)'
                )
            )
        )
    )
elif platform == "win32":
    # noinspection PyUnresolvedReferences
    import py2exe
    import platform as arch
    from distutils.core import setup
    if arch.architecture()[0] == '64bit':
        suffix = '_64'
    else:
        suffix = ''
    additional_files = [('platforms', ['C:\Python34' + suffix +
                                       '\Lib\site-packages\PyQt5\plugins\platforms\qwindows.dll']),
                        ('', ['LICENSE.txt',
                              'other\\7za.exe',
                              'other\\UnRAR.exe',
                              'other\\Additional-LICENSE.txt',
                              'C:\Python34' + suffix + '\Lib\site-packages\PyQt5\libGLESv2.dll',
                              'C:\Python34' + suffix + '\Lib\site-packages\PyQt5\libEGL.dll'])]
    extra_options = dict(
        options={'py2exe': {"bundle_files": 1,
                            "dll_excludes": ["tcl85.dll", "tk85.dll"],
                            "dist_dir": "dist" + suffix,
                            "compressed": True,
                            "includes": ["sip"],
                            "excludes": ["tkinter"],
                            "optimize": 2}},
        windows=[{"script": MAIN,
                  "dest_base": "KCC",
                  "version": VERSION,
                  "copyright": "Ciro Mattia Gonano, Pawel Jastrzebski © 2012-2015",
                  "legal_copyright": "ISC License (ISCL)",
                  "product_version": VERSION,
                  "product_name": "Kindle Comic Converter",
                  "file_description": "Kindle Comic Converter",
                  "icon_resources": [(1, "icons\comic2ebook.ico")]}],
        zipfile=None,
        data_files=additional_files)
else:
    print('Please use setup.sh to build Linux package.')
    exit()

# noinspection PyUnboundLocalVariable
setup(
    name=NAME,
    version=VERSION,
    author="Ciro Mattia Gonano, Pawel Jastrzebski",
    author_email="ciromattia@gmail.com, pawelj@iosphe.re",
    description="Kindle Comic Converter",
    license="ISC License (ISCL)",
    keywords="kindle comic mobipocket mobi cbz cbr manga",
    url="http://github.com/ciromattia/kcc",
    **extra_options
)

if platform == "darwin":
    from os import chmod, makedirs
    from shutil import copyfile
    makedirs('dist/' + NAME + '.app/Contents/PlugIns/platforms')
    copyfile('other/libqcocoa.dylib', 'dist/' + NAME + '.app/Contents/PlugIns/platforms/libqcocoa.dylib')
    chmod('dist/' + NAME + '.app/Contents/Resources/unrar', 0o777)
    chmod('dist/' + NAME + '.app/Contents/Resources/7za', 0o777)