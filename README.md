KindleComicConverter
=============

KindleComicConverter is a MacOS X AppleScript droplet to convert image folders to a comic-type Mobipocket ebook to take advantage of the new Panel View mode on Amazon's Kindle.

REQUIREMENTS
-------------
  - kindlegen in /usr/local/bin/  
  - [http://www.rarlab.com/download.htm](unrar) and [http://developer.berlios.de/project/showfiles.php?group_id=5373&release_id=18844](rarfile.py) for calibre2ebook.py automatic CBR extracting

USAGE
-------------
Drop a folder over the droplet, after a while you'll get a comic-type .mobi to sideload on your kindle.  
The script takes care of calling comic2ebook.py, kindlegen and kindlestrip.py.  
For the standalone comic2ebook.py script, please refer to CLI help.

WARNING: at the moment the script does not perform image manipulation. Image optimization and resizing (HD Kindles want 758x1024, non-HD ones 600x800) is up to you.


CREDITS
-------------
This script exists as a cross-platform alternative to KindleComicParser by Dc5e
(published in [http://www.mobileread.com/forums/showthread.php?t=192783](http://www.mobileread.com/forums/showthread.php?t=192783))

This droplet relies and includes KindleStrip (C) by Paul Durrant and released in public domain
([http://www.mobileread.com/forums/showthread.php?t=96903](http://www.mobileread.com/forums/showthread.php?t=96903))

The icon for the droplet is by Nikolay Verin ([http://ncrow.deviantart.com/](http://ncrow.deviantart.com/)) and released under CC Attribution-NonCommercial-ShareAlike 3.0 Unported License

Also, you need to have kindlegen v2.7 (with KF8 support) which is downloadable from Amazon website
and installed in /usr/local/bin/


CHANGELOG
-------------
  - 1.00 - Initial version
  - 1.10 - Added support for CBZ/CBR files in comic2ebook.py

TODO
-------------
  - add transparent support for CBZ/CBR archives
  - bundle a script to manipulate images (to get rid of Mangle/E-nki/whatsoever)

TODO for calibre2ebook.py
-------------
  - Add gracefully exit for CBR if no rarfile.py and no unrar executable are found
  - Improve error reporting