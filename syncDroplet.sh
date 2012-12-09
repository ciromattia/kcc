#!/bin/bash
rm -rf KindleComicConverter.app/Contents/Resources/*
cp -a resources/Scripts resources/description.rtfd resources/droplet.rsrc KindleComicConverter.app/Contents/Resources/
cp resources/Info.plist KindleComicConverter.app/Contents/
cp resources/comic2ebook.icns KindleComicConverter.app/Contents/Resources/droplet.icns
cp kcc/*.py KindleComicConverter.app/Contents/Resources/
