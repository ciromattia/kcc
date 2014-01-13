#!/bin/bash
# Linux Python package build script

VERSION="3.7.1"

cp kcc.py __main__.py
zip kcc.zip __main__.py kcc/*.py
echo "#!/usr/bin/env python2" > kcc-bin
cat kcc.zip >> kcc-bin
chmod +x kcc-bin
tar --xform s:^.*/:: --xform s/kcc-bin/kcc/ --xform s/comic2ebook/kcc/ -czf KindleComicConverter_linux_$VERSION.tar.gz kcc-bin LICENSE.txt icons/comic2ebook.png
rm __main__.py kcc.zip kcc-bin 
