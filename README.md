# KindleComicConverter

`KindleComicConverter` is a Python app which aim is to convert image folders to a comic-type (Mobipocket) ebook to take advantage of the new Panel View mode on Amazon's Kindle.

## REQUIREMENTS
- `kindlegen` in /usr/local/bin/
- [unrar](http://www.rarlab.com/download.htm) and [rarfile.py](http://developer.berlios.de/project/showfiles.php?group_id=5373&release_id=18844) for `calibre2ebook.py` automatic CBR extracting.

### for compiling/running from source:
- Python 2.7+ (included in MacOS and Linux, follow the [official documentation](http://www.python.org/getit/windows/) to install on Windows)
- You are strongly encouraged to get the [Python Imaging Library](http://www.pythonware.com/products/pil/) that, altough optional, provides a bunch of comic optimizations like split double pages, resize to optimal resolution, improve contrast and palette, etc.
  Please refer to official documentation for installing into your system.

## USAGE
Drop a folder or a CBZ/CBR file over the app, after a while you'll get a comic-type .mobi to sideload on your Kindle.
The script takes care of calling `comic2ebook.py`, `kindlegen` and `kindlestrip.py`.

> **WARNING:** at the moment the droplet *ALWAYS* uses the **KHD** profile (*Kindle Paperwhite*).
> If you want to specify other profiles, please use the script from command line.

### standalone `comic2ebook.py` usage:
1. Launch

	```python comic2ebook.py <profile> <directory|file> <title>```

	The script takes care of unzipping/unrarring the file if it's an archive, creating a directory of images which should be then filled with a `.opf`, `.ncx`, and many `.html` files.
4. Run `Kindlegen` on `content.opf`. Depending on how many images you have, this may take awhile. Once completed, the `.mobi` file should be in the directory.
5. Remove the SRCS record to reduce the `.mobi` filesize in half. You can use [Kindlestrip](http://www.mobileread.com/forums/showthread.php?t=96903).
6. Copy the `.mobi` file to your Kindle!

## CREDITS
This script born as a cross-platform alternative to `KindleComicParser` by **Dc5e** (published in [this mobileread forum thread](http://www.mobileread.com/forums/showthread.php?t=192783))

The app relies and includes the following scripts/binaries:

 - the `KindleStrip` script &copy; 2010-2012 by **Paul Durrant** and released in public domain
([mobileread forum thread](http://www.mobileread.com/forums/showthread.php?t=96903))
 - the `rarfile.py` script &copy; 2005-2011 **Marko Kreen** <markokr@gmail.com>, released with ISC License
 - the free version `unrar` executable (downloadable from [here](http://www.rarlab.com/rar_add.htm), refer to `LICENSE_unrar.txt` for further details)
 - the icon is by **Nikolay Verin** ([http://ncrow.deviantart.com/](http://ncrow.deviantart.com/)) and released under [CC Attribution-NonCommercial-ShareAlike 3.0 Unported](http://creativecommons.org/licenses/by-nc-sa/3.0/) License
 - the `image.py` class from [Mangle](http://foosoft.net/mangle/)

Also, you need to have `kindlegen` v2.7 (with KF8 support) which is downloadable from Amazon website
and installed in `/usr/local/bin/`


## CHANGELOG
  - 1.00 - Initial version
  - 1.10 - Added support for CBZ/CBR files in comic2ebook.py
  - 1.11 - Added support for CBZ/CBR files in KindleComicConverter
  - 1.20 - Comic optimizations! Split pages not target-oriented (landscape with portrait target or portrait
   with landscape target), add palette and other image optimizations from Mangle.
   WARNING: PIL is required for all image mangling!
  - 2.00 - GUI! AppleScript is gone and Tk is used to provide cross-platform GUI support.

## TODO
  - Add gracefully exit for CBR if no rarfile.py and no unrar executable are found
  - Improve error reporting
  - Recurse into dirtree for multiple comics
  - Support pages extraction from PDF files

## COPYRIGHT

Copyright (c) 2012 Ciro Mattia Gonano. See LICENSE.txt for further details.