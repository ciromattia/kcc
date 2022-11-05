#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pip/pyinstaller build script for KCC.

Install as Python package:
    python3 setup.py install

Create EXE/APP:
    python3 setup.py build_binary
"""

import os
import sys
import shutil
import setuptools
import distutils.cmd
from kindlecomicconverter import __version__

NAME = 'KindleComicConverter'
MAIN = 'kcc.py'
VERSION = __version__


# noinspection PyUnresolvedReferences
class BuildBinaryCommand(distutils.cmd.Command):
    description = 'build binary release'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    # noinspection PyShadowingNames
    def run(self):
        VERSION = __version__
        if sys.platform == 'darwin':
            os.system('pyinstaller -y -F -i icons/comic2ebook.icns -n "Kindle Comic Converter" -w -s kcc.py')
            os.makedirs('dist/Kindle Comic Converter.app/Contents/Resources/Codecs')
            shutil.copy('other/osx/7z', 'dist/Kindle Comic Converter.app/Contents/Resources')
            shutil.copy('other/osx/7z.so', 'dist/Kindle Comic Converter.app/Contents/Resources')
            shutil.copy('other/osx/Rar.so', 'dist/Kindle Comic Converter.app/Contents/Resources/Codecs')
            shutil.copy('other/osx/Info.plist', 'dist/Kindle Comic Converter.app/Contents')
            shutil.copy('LICENSE.txt', 'dist/Kindle Comic Converter.app/Contents/Resources')
            shutil.copy('other/windows/Additional-LICENSE.txt', 'dist/Kindle Comic Converter.app/Contents/Resources')
            os.chmod('dist/Kindle Comic Converter.app/Contents/Resources/7z', 0o777)
            os.system('appdmg kcc.json dist/KindleComicConverter_osx_' + VERSION + '.dmg')
            exit(0)
        elif sys.platform == 'win32':
            os.system('pyinstaller -y -F -i icons\\comic2ebook.ico -n KCC -w --noupx kcc.py')
            exit(0)
        else:
            exit(0)


setuptools.setup(
    cmdclass={
        'build_binary': BuildBinaryCommand,
    },
    name=NAME,
    version=VERSION,
    author='Ciro Mattia Gonano, Pawel Jastrzebski',
    author_email='ciromattia@gmail.com, pawelj@iosphe.re',
    description='Comic and Manga converter for e-book readers.',
    license='ISC License (ISCL)',
    keywords=['kindle', 'kobo', 'comic', 'manga', 'mobi', 'epub', 'cbz'],
    url='http://github.com/ciromattia/kcc',
    entry_points={
        'console_scripts': [
            'kcc-c2e = kindlecomicconverter.startup:startC2E',
            'kcc-c2p = kindlecomicconverter.startup:startC2P',
        ],
        'gui_scripts': [
            'kcc = kindlecomicconverter.startup:start',
        ],
    },
    packages=['kindlecomicconverter'],
    install_requires=[
        'PyQt5>=5.6.0',
        'Pillow>=5.2.0',
        'psutil>=5.0.0',
        'python-slugify>=1.2.1,<3.0.0',
        'raven>=6.0.0',
    ],
    classifiers=[],
    zip_safe=False,
)
