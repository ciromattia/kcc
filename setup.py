#!/usr/bin/env python3
"""
pip/pyinstaller build script for KCC.

Usage (Windows):
    py -3 setup.py build_binary

Usage (Linux/OS X):
    python3 setup.py build_binary or python3 setup.py build_binary --pyz
"""

import os
import sys
import shutil
import setuptools
import distutils.cmd
from distutils.command.build import build
from kcc import __version__

NAME = 'KindleComicConverter'
MAIN = 'kcc.py'
VERSION = __version__
OPTIONS = {}


class BuildBinaryCommand(distutils.cmd.Command):
    description = 'build binary release'
    user_options = [
        ('pyz', None, 'build PYZ package'),
    ]

    def initialize_options(self):
        # noinspection PyAttributeOutsideInit
        self.pyz = False

    def finalize_options(self):
        pass

    def run(self):
        if sys.platform == 'darwin':
            os.system('pyinstaller -y -F -i icons/comic2ebook.icns -n "Kindle Comic Converter" -w -s --noupx kcc.py')
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
            os.system('pyinstaller -y -F -i icons\comic2ebook.ico -n KCC -w --noupx kcc.py')
            if os.path.isfile('setup.bat'):
                os.system('setup.bat')
            exit(0)
        else:
            if self.pyz:
                script = '''
                cp kcc.py __main__.py
                zip kcc.zip __main__.py kcc/*.py
                echo "#!/usr/bin/env python3" > kcc-bin
                cat kcc.zip >> kcc-bin
                chmod +x kcc-bin

                cp kcc-c2e.py __main__.py
                zip kcc-c2e.zip __main__.py kcc/*.py
                echo "#!/usr/bin/env python3" > kcc-c2e-bin
                cat kcc-c2e.zip >> kcc-c2e-bin
                chmod +x kcc-c2e-bin

                cp kcc-c2p.py __main__.py
                zip kcc-c2p.zip __main__.py kcc/*.py
                echo "#!/usr/bin/env python3" > kcc-c2p-bin
                cat kcc-c2p.zip >> kcc-c2p-bin
                chmod +x kcc-c2p-bin

                mkdir dist
                tar --xform s:^.*/:: \
                --xform s/LICENSE.txt/LICENSE/ \
                --xform s/kcc-bin/kcc/ \
                --xform s/kcc-c2p-bin/kcc-c2p/ \
                --xform s/kcc-c2e-bin/kcc-c2e/ \
                --xform s/comic2ebook/kcc/ \
                -czf dist/KindleComicConverter_linux_''' + VERSION + '''.tar.gz \
                kcc-bin kcc-c2e-bin kcc-c2p-bin LICENSE.txt README.md icons/comic2ebook.png
                rm __main__.py kcc.zip kcc-c2e.zip kcc-c2p.zip kcc-bin kcc-c2e-bin kcc-c2p-bin
                '''
                os.system("bash -c '%s'" % script)
                exit(0)
            else:
                os.system('docker run --rm -v ' + os.getcwd() + ':/app -e KCCVER=' + VERSION + ' acidweb/kcc')
                exit(0)


class BuildCommand(build):
    def run(self):
        os.makedirs('build/_scripts/', exist_ok=True)
        shutil.copyfile('kcc.py', 'build/_scripts/kcc')
        shutil.copyfile('kcc-c2e.py', 'build/_scripts/kcc-c2e')
        shutil.copyfile('kcc-c2p.py', 'build/_scripts/kcc-c2p')
        # noinspection PyShadowingNames
        OPTIONS = dict(
            scripts=['build/_scripts/kcc',
                     'build/_scripts/kcc-c2e',
                     'build/_scripts/kcc-c2p'],
            packages=['kcc'],
            install_requires=[
                'PyQt5>=5.6.0'
                'Pillow>=3.2.0',
                'psutil>=4.1.0',
                'python-slugify>=1.2.0',
                'raven>=5.13.0',
            ],
            zip_safe=False,
        )
        if sys.version_info[1] < 5:
            OPTIONS['install_requires'].append('scandir>=1.2.0')
        build.run(self)


setuptools.setup(
    cmdclass={
        'build_binary': BuildBinaryCommand,
        'build': BuildCommand,
    },
    name=NAME,
    version=VERSION,
    author='Ciro Mattia Gonano, Pawel Jastrzebski',
    author_email='ciromattia@gmail.com, pawelj@iosphe.re',
    description='Comic and Manga converter for e-book readers.',
    license='ISC License (ISCL)',
    keywords='kindle comic mobipocket mobi cbz cbr manga',
    url='http://github.com/ciromattia/kcc',
    **OPTIONS
)
