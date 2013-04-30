# KCC

`KCC` (a.k.a. `KindleComicConverter`) is a Python app to convert comic files or folders to ePub or Panel View MOBI.  
It was initally developed for Kindle but since v2.2 it outputs valid ePub 2.0 so _**despite its name, KCC is
actually a comic 2 epub converter that every ereader owner can happily use**_.  

It can also optionally optimize images by applying a number of transformations.

### A word of warning
**KCC** _is not_ [Amazon's Kindle Comic Creator](http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1001103761) nor is in any way endorsed by Amazon.  
Amazon's tool is for comic _publishers_ and involves a lot of manual effort, while **KCC** is for comic _readers_.  
If you want to read some comments over *Amazon's kc2* you can take a look at [this](http://www.mobileread.com/forums/showthread.php?t=207461&page=7#96) and [that](http://www.mobileread.com/forums/showthread.php?t=211047) threads on Mobileread.  
_kc2_ in no way is a replacement for **KCC** so you can be quite confident we'll going to carry on developing our little monster ;)  

## BINARY RELEASES
You can find the latest released binary at the following links:  
- OS X: [https://dl.dropbox.com/u/16806101/KindleComicConverter_osx_2.9.zip](https://dl.dropbox.com/u/16806101/KindleComicConverter_osx_2.9.zip)
- Win64: [https://dl.dropbox.com/u/16806101/KindleComicConverter_win-amd64_2.9.zip](https://dl.dropbox.com/u/16806101/KindleComicConverter_win-amd64_2.9.zip)
- Win32: [http://pawelj.vulturis.eu/Shared/KindleComicConverter_win-x86_2.9.zip](http://pawelj.vulturis.eu/Shared/KindleComicConverter_win-x86_2.9.zip) *(thanks to [AcidWeb](https://github.com/AcidWeb))*
- Linux: Just download sourcecode and launch `python kcc.py` *(Provided you have Python and Pillow installed)*

## INPUT FORMATS
`kcc` can understand and convert, at the moment, the following file types:
- PNG, JPG, GIF, TIFF, BMP
- Folders
- CBZ, ZIP
- CBR, RAR *(With `unrar` executable)*
- PDF *(Extracting only contained JPG images)*

## OPTIONAL REQUIREMENTS
- `kindlegen` v2.7+ in a directory reachable by your PATH or in KCC directory *(For .mobi generation)*
- [unrar](http://www.rarlab.com/download.htm) *(For CBR support)*

### For compiling/running from source:
- Python 2.7+ (Included in MacOS and Linux, follow the [official documentation](http://www.python.org/getit/windows/) to install on Windows)
- [Pillow](http://pypi.python.org/pypi/Pillow/) for comic optimizations like split double pages, resize to optimal resolution, improve contrast and palette, etc.
  Please refer to official documentation for installing into your system.

## USAGE

### GUI

Should be pretty self-explanatory, just keep in mind that it's still in development ;)
While working it seems frozen, I'll try to fix the aesthetics later.
Conversion being done, you should find an .epub and a .mobi files alongside the original input file (same directory)

### Standalone `comic2ebook.py` usage:

```
Usage: comic2ebook.py [options] comic_file|comic_folder

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -p PROFILE, --profile=PROFILE
                        Device profile (Choose one among K1, K2, K3, K4NT, K4T, KDX, KDXG or KHD) [Default=KHD]
  -t TITLE, --title=TITLE
                        Comic title [Default=filename]
  -m, --manga-style     Manga style (Right-to-left reading and splitting) [Default=False]
  -c, --cbz-output      Outputs a CBZ archive and does not generate EPUB
  --nopanelviewhq       Disable high quality Panel View [Default=False]
  --noprocessing        Do not apply image preprocessing (Page splitting and optimizations) [Default=True]
  --forcepng            Create PNG files instead JPEG (For non-Kindle devices) [Default=False]
  --gamma=GAMMA         Apply gamma correction to linearize the image [Default=Auto]
  --upscale             Resize images smaller than device's resolution [Default=False]
  --stretch             Stretch images to device's resolution [Default=False]
  --blackborders        Use black borders instead of white ones when not stretching and ratio is not like the device's one [Default=False]
  --rotate              Rotate landscape pages instead of splitting them [Default=False]
  --nosplitrotate       Disable splitting and rotation [Default=False]
  --nocutpagenumbers    Do not try to cut page numbering on images [Default=True]
  -o OUTPUT, --output=OUTPUT
                        Output generated file (EPUB or CBZ) to specified directory or file
  -v, --verbose         Verbose output [Default=False]
```

## CREDITS
KCC is made by [Ciro Mattia Gonano](http://github.com/ciromattia) and [Paweł Jastrzębski](http://github.com/AcidWeb)

This script born as a cross-platform alternative to `KindleComicParser` by **Dc5e** (published in [this mobileread forum thread](http://www.mobileread.com/forums/showthread.php?t=192783))

The app relies and includes the following scripts/binaries:

 - `KindleStrip` script &copy; 2010-2012 by **Paul Durrant** and released in public domain
([mobileread forum thread](http://www.mobileread.com/forums/showthread.php?t=96903))
 - `rarfile.py` script &copy; 2005-2011 **Marko Kreen** <markokr@gmail.com>, released with ISC License
 - the icon is by **Nikolay Verin** ([http://ncrow.deviantart.com/](http://ncrow.deviantart.com/)) and released under [CC Attribution-NonCommercial-ShareAlike 3.0 Unported](http://creativecommons.org/licenses/by-nc-sa/3.0/) License
 - `image.py` class from **Alex Yatskov**'s [Mangle](http://foosoft.net/mangle/) with subsequent [proDOOMman](https://github.com/proDOOMman/Mangle)'s and [Birua](https://github.com/Birua/Mangle)'s patches
 - `magic.py` from [python-magic](https://github.com/ahupp/python-magic) library

## CHANGELOG
  - 1.00: Initial version
  - 1.10: Added support for CBZ/CBR files in comic2ebook.py
  - 1.11: Added support for CBZ/CBR files in KindleComicConverter
  - 1.20: Comic optimizations! Split pages not target-oriented (landscape with portrait target or portrait
   with landscape target), add palette and other image optimizations from Mangle.  
   WARNING: PIL is required for all image mangling!
  - 1.30: Fixed an issue in OPF generation for device resolution  
   Reworked options system (call with -h option to get the inline help)
  - 1.40: Added some options for controlling image optimization  
        Further optimization (ImageOps, page numbering cut, autocontrast)
  - 1.41: Fixed a serious bug on resizing when img ratio was bigger than device one
  - 1.50: Added subfolder support for multiple chapters.
  - 2.0: GUI! AppleScript is gone and Tk is used to provide cross-platform GUI support.
  - 2.1: Added basic error reporting
  - 2.2: Added (valid!) ePub 2.0 output  
        Rename .zip files to .cbz to avoid overwriting
  - 2.3: Fixed win32 ePub generation, folder handling, filenames with spaces and subfolders
  - 2.4: Use temporary directory as workdir (fixes converting from external volumes and zipfiles renaming)  
        Fixed "add folders" from GUI.
  - 2.5: Added --black-borders option to set added borders black when page's ratio is not the device's one (#11).  
        Fixes epub containing zipped itself (#10)  
  - 2.6: Added --rotate option to rotate landscape images instead of splitting them (#16, #24)  
        Added --output option to customize ePub output dir/file (#22)  
        Add rendition:layout and rendition:orientation ePub meta tags (supported by new kindlegen 2.8)  
        Fixed natural sorting for files (#18)
  - 2.7: Lots of GUI improvements (#27, #13)  
        Added gamma support within --gamma option (defaults to profile-specified gamma) (#26, #27)  
        Added --nodithering option to prevent dithering optimizations (#27)  
        Epub margins support (#30)  
        Fixed no file added if file has no spaces on Windows (#25)  
        Gracefully exit if unrar missing (#15)  
        Do not call kindlegen if source epub is bigger than 320MB (#17)  
        Get filetype from magic number (#14)   
        PDF conversion works again  
  - 2.8: updated rarfile library  
        Panel View support + HQ support (#36) - new option: --nopanelviewhq
        Split profiles for K4NT and K4T  
        Rewrite of Landscape Mode support (huge readability improvement for KPW)  
        Upscale use now BILINEAR method  
        Added generic CSS file  
        Optimized archive extraction for zip/rar files (#40)  
  - 2.9: Added support for generating a plain CBZ (skipping all the EPUB/Mobi generation) (#45)  
        Prevent output file overwriting the source one: if a duplicate name is detected, append _kcc to the name  
        Rarfile library updated to 2.6  
        Added GIF, TIFF and BMP to supported formats (#42)  
        Filenames slugifications (#28, #31, #9, #8)
  - 2.10: Kindle Fire support (color ePub/Mobi)  


## COPYRIGHT

Copyright (c) 2012-2013 Ciro Mattia Gonano with further contributions by Paweł Jastrzębski.  
KCC is released under ISC LICENSE; see LICENSE.txt for further details.
