#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pip/pyinstaller build script for KCC.

Install as Python package:
    python3 setup.py install

Create EXE/APP/DEB:
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
            shutil.copy('other/osx/7za', 'dist/Kindle Comic Converter.app/Contents/Resources')
            shutil.copy('other/osx/unrar', 'dist/Kindle Comic Converter.app/Contents/Resources')
            shutil.copy('other/osx/Info.plist', 'dist/Kindle Comic Converter.app/Contents')
            shutil.copy('LICENSE.txt', 'dist/Kindle Comic Converter.app/Contents/Resources')
            shutil.copy('other/windows/Additional-LICENSE.txt', 'dist/Kindle Comic Converter.app/Contents/Resources')
            os.chmod('dist/Kindle Comic Converter.app/Contents/Resources/unrar', 0o777)
            os.chmod('dist/Kindle Comic Converter.app/Contents/Resources/7za', 0o777)
            os.system('appdmg kcc.json dist/KindleComicConverter_osx_' + VERSION + '.dmg')
            exit(0)
        elif sys.platform == 'win32':
            os.system('pyinstaller -y -F -i icons\comic2ebook.ico -n KCC -w --noupx kcc.py')
            exit(0)
        else:
            os.system('pyinstaller -y -F kcc.py')
            os.system('mkdir -p dist/usr/bin dist/usr/share/applications dist/usr/share/doc/kindlecomicconverter '
                      'dist/usr/share/kindlecomicconverter dist/usr/share/lintian/overrides')
            os.system('mv dist/kcc dist/usr/bin')
            os.system('cp icons/comic2ebook.png dist/usr/share/kindlecomicconverter')
            os.system('cp LICENSE.txt dist/usr/share/doc/kindlecomicconverter/copyright')
            os.system('cp other/linux/kindlecomicconverter.desktop dist/usr/share/applications')
            os.system('cp other/linux/kindlecomicconverter dist/usr/share/lintian/overrides')
            os.chdir('dist')
            os.system('fpm -f -s dir -t deb -n kindlecomicconverter -v ' + VERSION +
                      ' -m "Pawel Jastrzebski <pawelj@iosphe.re>" --license "ISC" '
                      '--description "$(printf "Comic and Manga converter for e-book '
                      'readers.\nThis app allows you to transform your PNG, JPG, GIF, '
                      'CBZ, CBR and CB7 files\ninto EPUB or MOBI format e-books.")" '
                      '--url "https://kcc.iosphe.re/" --deb-priority "optional" --vendor "" '
                      '--category "graphics" -d "unrar | unrar-free" -d "p7zip-full" -d "libc6" usr')
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
        'Pillow>=4.0.0',
        'psutil>=5.0.0',
        'python-slugify>=1.2.1',
        'raven>=6.0.0',
    ],
    classifiers=[],
    zip_safe=False,
)
