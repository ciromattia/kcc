"""
py2app/py2exe build script for KCC No-GUI release.

Usage (Windows):
    python setup.py py2exe
"""
from distutils.core import setup
import sys
import py2exe
sys.path.insert(0, 'kcc')

setup(
        console=['kcc/comic2ebook.py', 'kcc/kindlestrip.py'],
)
