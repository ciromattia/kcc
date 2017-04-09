#!/usr/bin/env python3
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

    def run(self):
        if sys.platform == 'darwin':
            if os.path.isfile('Kindle Comic Converter.spec'):
                os.system('pyinstaller "Kindle Comic Converter.spec"')
            else:
                os.system('pyinstaller -y -F -i icons/comic2ebook.icns -n "Kindle Comic Converter" -w -s kcc.py')
            shutil.copy('other/osx/7za', 'dist/Kindle Comic Converter.app/Contents/Resources')
            shutil.copy('other/osx/unrar', 'dist/Kindle Comic Converter.app/Contents/Resources')
            shutil.copy('other/osx/Info.plist', 'dist/Kindle Comic Converter.app/Contents')
            shutil.copy('LICENSE.txt', 'dist/Kindle Comic Converter.app/Contents/Resources')
            shutil.copy('other/windows/Additional-LICENSE.txt', 'dist/Kindle Comic Converter.app/Contents/Resources')
            os.chmod('dist/Kindle Comic Converter.app/Contents/Resources/unrar', 0o777)
            os.chmod('dist/Kindle Comic Converter.app/Contents/Resources/7za', 0o777)
            if os.path.isfile('setup.sh'):
                os.system('./setup.sh')
            os.system('appdmg kcc.json dist/KindleComicConverter_osx_' + VERSION + '.dmg')
            exit(0)
        elif sys.platform == 'win32':
            if os.path.isfile('KCC.spec'):
                os.system('pyinstaller KCC.spec')
            else:
                os.system('pyinstaller -y -F -i icons\comic2ebook.ico -n KCC -w --noupx kcc.py')
            if os.path.isfile('setup.bat'):
                os.system('setup.bat')
            exit(0)
        else:
            os.system('docker run --rm -v ' + os.getcwd() + ':/app -e KCCVER=' + VERSION + ' acidweb/kcc')
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
