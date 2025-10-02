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
import platform
import sys
import setuptools
from kindlecomicconverter import __version__

NAME = 'KindleComicConverter'
MAIN = 'kcc.py'
VERSION = __version__


# noinspection PyUnresolvedReferences
class BuildBinaryCommand(setuptools.Command):
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
            os.system('pyinstaller --hidden-import=_cffi_backend -y -D -i icons/comic2ebook.icns -n "Kindle Comic Converter" -w -s kcc.py')
            # TODO /usr/bin/codesign --force -s "$MACOS_CERTIFICATE_NAME" --options runtime dist/Applications/Kindle\ Comic\ Converter.app -v
            min_os = os.getenv('MACOSX_DEPLOYMENT_TARGET')
            if min_os:
                os.system(f'appdmg kcc.json dist/kcc_osx_{min_os.replace(".", "_")}_legacy_{VERSION}.dmg')
            else:
                os.system(f'appdmg kcc.json dist/kcc_macos_{platform.processor()}_{VERSION}.dmg')
            sys.exit(0)
        elif sys.platform == 'win32':
            if os.getenv('WINDOWS_7'):
                os.system('pyinstaller --hidden-import=_cffi_backend -y -F -i icons\\comic2ebook.ico -n kcc_win7_legacy_' + VERSION + ' -w --noupx kcc.py')
            else:
                os.system('pyinstaller --hidden-import=_cffi_backend -y -F -i icons\\comic2ebook.ico -n KCC_' + VERSION + ' -w --noupx kcc.py')
            sys.exit(0)
        elif sys.platform == 'linux':
            os.system(
                'pyinstaller --hidden-import=_cffi_backend --hidden-import=queue -y -F -i icons/comic2ebook.ico -n kcc_linux_' + VERSION + ' kcc.py')
            sys.exit(0)
        else:
            sys.exit(0)


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
        'pyside6>=6.0.0',
        'Pillow>=9.3.0',
        'PyMuPDF>=1.18.0',
        'psutil>=5.9.5',
        'python-slugify>=1.2.1,<9.0.0',
        'raven>=6.0.0',
        'requests>=2.31.0',
        'mozjpeg-lossless-optimization>=1.1.2',
        'natsort>=8.4.0',
        'distro',
        'numpy>=1.22.4',
        'PyMuPDF>=1.16.1',
    ],
    classifiers=[],
    zip_safe=False,
)
