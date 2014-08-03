#!/bin/bash
# Linux Python package build script

VERSION="4.2.1"

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

tar --xform s:^.*/:: --xform s/kcc-bin/kcc/ --xform s/kcc-c2p-bin/kcc-c2p/ --xform s/kcc-c2e-bin/kcc-c2e/ --xform s/comic2ebook/kcc/ -czf KindleComicConverter_linux_$VERSION.tar.gz kcc-bin kcc-c2e-bin kcc-c2p-bin LICENSE.txt icons/comic2ebook.png
rm __main__.py kcc.zip kcc-c2e.zip kcc-c2p.zip kcc-bin kcc-c2e-bin kcc-c2p-bin