#!/usr/bin/env python3
"""
pip/py2exe/py2app build script for KCC.

Usage (Windows):
    py -3.4 setup.py py2exe

Usage (Linux):
    python3 setup.py make_pyz or python3 setup.py install

Usage (Mac OS X):
    python3 setup.py py2app
"""

from sys import platform, version_info, argv
from kcc import __version__


NAME = 'KindleComicConverter'
VERSION = __version__
MAIN = 'kcc.py'
extra_options = {}


if platform == 'darwin':
    from setuptools import setup
    from os import chmod, makedirs, system
    from shutil import copyfile
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
                    CFBundleName='Kindle Comic Converter',
                    CFBundleShortVersionString=VERSION,
                    CFBundleGetInfoString=NAME + ' ' + VERSION +
                    ', written 2012-2015 by Ciro Mattia Gonano and Pawel Jastrzebski',
                    CFBundleExecutable=NAME,
                    CFBundleDocumentTypes=[
                        dict(
                            CFBundleTypeExtensions=['cbz', 'cbr', 'cb7', 'zip', 'rar', '7z', 'pdf'],
                            CFBundleTypeName='Comics',
                            CFBundleTypeIconFile='comic2ebook.icns',
                            CFBundleTypeRole='Editor',
                        )
                    ],
                    CFBundleIdentifier='re.iosphe.kcc',
                    LSMinimumSystemVersion='10.8.0',
                    LSEnvironment=dict(
                        PATH='./../Resources:/usr/local/bin:/usr/bin:/bin'
                    ),
                    NSHumanReadableCopyright='ISC License (ISCL)'
                )
            )
        )
    )
elif platform == 'win32':
    import py2exe
    from platform import architecture
    from distutils.core import setup
    if architecture()[0] == '64bit':
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
        options={'py2exe': {'bundle_files': 1,
                            'dist_dir': 'dist' + suffix,
                            'compressed': True,
                            'includes': ['sip'],
                            'excludes': ['tkinter'],
                            'optimize': 2}},
        windows=[{'script': MAIN,
                  'dest_base': 'KCC',
                  'version': VERSION,
                  'copyright': 'Ciro Mattia Gonano, Pawel Jastrzebski © 2012-2015',
                  'legal_copyright': 'ISC License (ISCL)',
                  'product_version': VERSION,
                  'product_name': 'Kindle Comic Converter',
                  'file_description': 'Kindle Comic Converter',
                  'icon_resources': [(1, 'icons\comic2ebook.ico')]}],
        zipfile=None,
        data_files=additional_files)
else:
    if len(argv) > 1 and argv[1] == 'make_pyz':
        from os import system
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

        tar --xform s:^.*/:: --xform s/LICENSE.txt/LICENSE/ --xform s/kcc-bin/kcc/ --xform s/kcc-c2p-bin/kcc-c2p/ \
        --xform s/kcc-c2e-bin/kcc-c2e/ --xform s/comic2ebook/kcc/ -czf KindleComicConverter_linux_'''\
        + VERSION + '''.tar.gz kcc-bin kcc-c2e-bin kcc-c2p-bin LICENSE.txt README.md icons/comic2ebook.png
        rm __main__.py kcc.zip kcc-c2e.zip kcc-c2p.zip kcc-bin kcc-c2e-bin kcc-c2p-bin
        '''
        system("bash -c '%s'" % script)
        exit(0)
    else:
        from setuptools import setup
        from os import makedirs
        from shutil import copyfile
        makedirs('build/_scripts/', exist_ok=True)
        copyfile('kcc.py', 'build/_scripts/kcc')
        copyfile('kcc-c2e.py', 'build/_scripts/kcc-c2e')
        copyfile('kcc-c2p.py', 'build/_scripts/kcc-c2p')
        extra_options = dict(
            scripts=['build/_scripts/kcc', 'build/_scripts/kcc-c2e', 'build/_scripts/kcc-c2p'],
            packages=['kcc'],
            install_requires=[
                'Pillow>=2.8.2',
                'psutil>=3.0.0',
                'python-slugify>=1.1.3',
            ],
            zip_safe=False,
        )
        if version_info[1] < 5:
            extra_options['install_requires'].append('scandir>=1.1.0')


setup(
    name=NAME,
    version=VERSION,
    author='Ciro Mattia Gonano, Pawel Jastrzebski',
    author_email='ciromattia@gmail.com, pawelj@iosphe.re',
    description='Comic and manga converter for E-Book readers.',
    license='ISC License (ISCL)',
    keywords='kindle comic mobipocket mobi cbz cbr manga',
    url='http://github.com/ciromattia/kcc',
    **extra_options
)

if platform == 'darwin':
    makedirs('dist/Kindle Comic Converter.app/Contents/PlugIns/platforms', exist_ok=True)
    copyfile('other/libqcocoa.dylib', 'dist/Kindle Comic Converter.app/Contents/PlugIns/platforms/libqcocoa.dylib')
    chmod('dist/Kindle Comic Converter.app/Contents/Resources/unrar', 0o777)
    chmod('dist/Kindle Comic Converter.app/Contents/Resources/7za', 0o777)
    system('appdmg setup.json dist/KindleComicConverter_osx_' + VERSION + '.dmg')
