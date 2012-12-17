"""
py2app/py2exe build script for MyApplication.

Will automatically ensure that all build prerequisites are available
via ez_setup

Usage (Mac OS X):
    python setup.py py2app

Usage (Windows):
    python setup.py py2exe
"""
import ez_setup
ez_setup.use_setuptools()

import sys
from setuptools import setup

NAME="KindleComicConverter"
VERSION="1.2.0"
IDENTIFIER="com.github.ciromattia.kcc"
EXENAME="KindleComicConverter"

APP = ['kcc.py']
DATA_FILES = []
OPTIONS = { 'argv_emulation': True,
            'iconfile': 'resources/comic2ebook.icns',
            'includes': 'kcc/*.py'}

if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires=['py2app'],
        options=dict(
            py2app=dict(OPTIONS,
                resources=['LICENSE.txt','resources/Scripts','resources/description.rtfd'],
                plist=dict(
                    CFBundleName               = NAME,
                    CFBundleShortVersionString = VERSION,
                    CFBundleGetInfoString      = NAME + " " + VERSION + ", written 2012 by Ciro Mattia Gonano",
                    CFBundleExecutable         = EXENAME,
                    CFBundleIdentifier         = IDENTIFIER,
                    CFBundleSignature       = 'dplt'
                )
            )
        )
    )
elif sys.platform == 'win32':
    extra_options = dict(
        setup_requires=['py2exe'],
    )
else:
    extra_options = dict(
        # Normally unix-like platforms will use "setup.py install"
        # and install the main script as such
        scripts=APP,
    )

setup(
    name=NAME,
    app=APP,
    data_files=DATA_FILES,
    classifiers=[
        # make sure to use :: Python *and* :: Python :: 3 so
        # that pypi can list the package on the python 3 page
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ],
    packages=['kcc'],
    # make sure to add custom_fixers to the MANIFEST.in
    include_package_data=True,
    **extra_options
)
