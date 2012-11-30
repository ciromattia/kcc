# KindleComicConverter

`KindleComicConverter` is a MacOS X AppleScript droplet to convert image folders to a comic-type Mobipocket ebook to take advantage of the new Panel View mode on Amazon's Kindle.

## REQUIREMENTS
- Python (included in MacOS and Linux, follow the [official documentation](http://www.python.org/getit/windows/) to install on Windows)  
- `kindlegen` in /usr/local/bin/

### for standalone `comic2ebook.py` script:
- [unrar](http://www.rarlab.com/download.htm) and [rarfile.py](http://developer.berlios.de/project/showfiles.php?group_id=5373&release_id=18844) for `calibre2ebook.py` automatic CBR extracting.  

The app and the standalone `comic2ebook.py` script can optionally use the [Python Imaging Library](http://www.pythonware.com/products/pil/) to correctly set the image resolution on OPF file, please refer to official documentation for installing into your system.

## USAGE
Drop a folder or a CBZ/CBR file over the droplet, after a while you'll get a comic-type .mobi to sideload on your Kindle.  
The script takes care of calling `comic2ebook.py`, `kindlegen` and `kindlestrip.py`.

**WARNING:** at the moment the script does not perform image manipulation. Image optimization and resizing (HD Kindles want 758x1024, non-HD ones 600x800) is up to you.

### standalone `comic2ebook.py` usage:
1. Prepare image folder resizing the images to 758x1024 for HD or 600x800 for non-HD readers, in .png or .jpg formats
2. Organize the images into the folders (Use leading 0's to avoid file ordering problems). For example,

	> Legs Weaver 51/  
	> Legs Weaver 51/001.png  
	> Legs Weaver 51/002.png  
	> etc...

3. Launch

	```python comic2ebook.py <directory> <title>```

	The directory should be then filled with a `.opf`, `.ncx`, and many `.html` files.
4. Run `Kindlegen` on `content.opf`. Depending on how many images you have, this may take awhile. Once completed, the `.mobi` file should be in the directory.
5. Remove the SRCS record to reduce the `.mobi` filesize in half. You can use [Kindlestrip](http://www.mobileread.com/forums/showthread.php?t=96903).
6. Copy the `.mobi` file to your Kindle!

## CREDITS
This script exists as a cross-platform alternative to `KindleComicParser` by **Dc5e**
(published in [this mobileread forum thread](http://www.mobileread.com/forums/showthread.php?t=192783))  


The app relies and includes the following scripts/binaries:

 - the `KindleStrip` script &copy; 2010-2012 by **Paul Durrant** and released in public domain
([mobileread forum thread](http://www.mobileread.com/forums/showthread.php?t=96903))
 - the `rarfile.py` script &copy; 2005-2011 **Marko Kreen** <markokr@gmail.com>, released with ISC License
 - the free version `unrar` executable (downloadable from [here](http://www.rarlab.com/rar_add.htm), refer to `LICENSE_unrar.txt` for further details)
 - the icon is by **Nikolay Verin** ([http://ncrow.deviantart.com/](http://ncrow.deviantart.com/)) and released under [CC Attribution-NonCommercial-ShareAlike 3.0 Unported](http://creativecommons.org/licenses/by-nc-sa/3.0/) License

Also, you need to have `kindlegen` v2.7 (with KF8 support) which is downloadable from Amazon website
and installed in `/usr/local/bin/`


## CHANGELOG
  - 1.00 - Initial version
  - 1.10 - Added support for CBZ/CBR files in comic2ebook.py
  - 1.11 - Added support for CBZ/CBR files in KindleComicConverter

## TODO
  - bundle a script to manipulate images (to get rid of Mangle/E-nki/whatsoever)

#### calibre2ebook.py
  - Add gracefully exit for CBR if no rarfile.py and no unrar executable are found
  - Improve error reporting

## COPYRIGHT

Copyright (c) 2012 Ciro Mattia Gonano. See LICENSE.txt for further details.