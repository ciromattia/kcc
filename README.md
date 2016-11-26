# KCC

**Kindle Comic Converter** is a Python app to convert comic/manga files or folders to EPUB, Panel View MOBI or E-Ink optimized CBZ.
It was initially developed for Kindle but since version 4.6 it outputs valid EPUB 3.0 so _**despite its name, KCC is
actually a comic/manga to EPUB converter that every e-reader owner can happily use**_.
It can also optionally optimize images by applying a number of transformations.

### A word of warning
**KCC** _is not_ [Amazon's Kindle Comic Creator](http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1001103761) nor is in any way endorsed by Amazon.
Amazon's tool is for comic publishers and involves a lot of manual effort, while **KCC** is for comic/manga readers.
_KC2_ in no way is a replacement for **KCC** so you can be quite confident we'll going to carry on developing our little monster ;-)

### Issues / new features / donations
If you have general questions about usage, feedback etc. please [post it here](http://www.mobileread.com/forums/showthread.php?t=207461).
If you have some **technical** problems using KCC please [file an issue here](https://github.com/ciromattia/kcc/issues/new).
If you can fix an open issue, fork & make a pull request.

If you find **KCC** valuable you can consider donating to the authors:
- Ciro Mattia Gonano:
 - [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=D8WNYNPBGDAS2)
 - [![Flattr this](http://api.flattr.com/button/flattr-badge-large.png)](http://flattr.com/thing/2260449/ciromattiakcc-on-GitHub)
- Paweł Jastrzębski:
 - [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=YTTJ4LK2JDHPS)
 - Bitcoin: 1W15wwqsfd7wbaZ6wvSJf1LW1bz6q5L8b

## BINARY RELEASES
You can find the latest released binary at the following links:
- **Windows (64-bit only):** [http://kcc.iosphe.re/Windows/](http://kcc.iosphe.re/Windows/)
- **Linux (Glibc 2.19+):** [http://kcc.iosphe.re/Linux/](http://kcc.iosphe.re/Linux/)
- **OS X (10.9+):** [http://kcc.iosphe.re/OSX/](http://kcc.iosphe.re/OSX/)

## DEPENDENCIES
Following software is required to run Linux version of **KCC** and/or bare sources:
- Python 3.3+
- [PyQt](https://pypi.python.org/pypi/PyQt5) 5.6.0+
- [Pillow](https://pypi.python.org/pypi/Pillow/) 3.2.0+
- [psutil](https://pypi.python.org/pypi/psutil) 4.1.0+
- [python-slugify](https://pypi.python.org/pypi/python-slugify) 1.2.0+
- [raven](https://pypi.python.org/pypi/raven) 5.13.0+
- [scandir](https://pypi.python.org/pypi/scandir) 1.2.0+ _(needed only when using Python 3.3 or 3.4)_

On Debian based distributions these two commands should install all needed dependencies:
```
sudo apt-get install python3 python3-dev python3-pip libpng-dev libjpeg-dev p7zip-full unrar
sudo pip3 install --upgrade pillow python-slugify psutil scandir raven pyqt5
```

### Optional dependencies
- [KindleGen](http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211) v2.9+ in a directory reachable by your _PATH_ or in _KCC_ directory *(For MOBI generation)*
- [UnRAR](http://www.rarlab.com/download.htm) *(For CBR/RAR support)*
- [7za](http://www.7-zip.org/download.html) *(For 7z/CB7 support)*

## INPUT FORMATS
**KCC** can understand and convert, at the moment, the following input types:
- Folders containing: PNG, JPG or GIF files
- CBZ, ZIP
- CBR, RAR *(With `unrar` executable)*
- CB7, 7Z *(With `7za` executable)*
- PDF *(Only extracting JPG images)*

## USAGE

Should be pretty self-explanatory. All options have detailed informations in tooltips.
After completed conversion you should find ready file alongside the original input file (same directory).

Please check [our wiki](https://github.com/ciromattia/kcc/wiki/) for more details.

CLI version of **KCC** is intended for power users. It is not idiot-proof like GUI :-)

### Standalone `kcc-c2e.py` usage:

```
Usage: kcc-c2e [options] comic_file|comic_folder

Options:
  MAIN:
    -p PROFILE, --profile=PROFILE
                        Device profile (Available options: K1, K2, K3, K45,
                        KDX, KPW, KV, KoMT, KoG, KoGHD, KoA, KoAHD, KoAH2O,
                        KoAO) [Default=KV]
    -m, --manga-style   Manga style (right-to-left reading and splitting)
    -2, --two-panel     Display two not four panels in Panel View mode
    -w, --webtoon       Webtoon processing mode

  OUTPUT SETTINGS:
    -o OUTPUT, --output=OUTPUT
                        Output generated file to specified directory or file
    -t TITLE, --title=TITLE
                        Comic title [Default=filename or directory name]
    -f FORMAT, --format=FORMAT
                        Output format (Available options: Auto, MOBI, EPUB,
                        CBZ) [Default=Auto]
    -b BATCHSPLIT, --batchsplit=BATCHSPLIT
                        Split output into multiple files. 0: Don't split 1:
                        Automatic mode 2: Consider every subdirectory as
                        separate volume [Default=0]

  PROCESSING:
    -u, --upscale       Resize images smaller than device's resolution
    -s, --stretch       Stretch images to device's resolution
    -r SPLITTER, --splitter=SPLITTER
                        Double page parsing mode. 0: Split 1: Rotate 2: Both
                        [Default=0]
    -g GAMMA, --gamma=GAMMA
                        Apply gamma correction to linearize the image
                        [Default=Auto]
    -c CROPPING, --cropping=CROPPING
                        Set cropping mode. 0: Disabled 1: Margins 2: Margins +
                        page numbers [Default=2]
    --cp=CROPPINGP, --croppingpower=CROPPINGP
                        Set cropping power [Default=1.0]
    --blackborders      Disable autodetection and force black borders
    --whiteborders      Disable autodetection and force white borders
    --forcecolor        Don't convert images to grayscale
    --forcepng          Create PNG files instead JPEG

  CUSTOM PROFILE:
    --customwidth=CUSTOMWIDTH
                        Replace screen width provided by device profile
    --customheight=CUSTOMHEIGHT
                        Replace screen height provided by device profile

  OTHER:
    -h, --help          Show this help message and exit
```

### Standalone `kcc-c2p.py` usage:

```
Usage: kcc-c2p [options] comic_folder

Options:
  MANDATORY:
    -y HEIGHT, --height=HEIGHT
                        Height of the target device screen
    -i, --in-place      Overwrite source directory
    -m, --merge         Combine every directory into a single image before splitting

  OTHER:
    -d, --debug         Create debug file for every splitted image
    -h, --help          Show this help message and exit
```

## CREDITS
**KCC** is made by [Ciro Mattia Gonano](http://github.com/ciromattia) and [Paweł Jastrzębski](http://github.com/AcidWeb).

This script born as a cross-platform alternative to `KindleComicParser` by **Dc5e** (published [here](http://www.mobileread.com/forums/showthread.php?t=192783)).

The app relies and includes the following scripts:

 - `DualMetaFix` script by **K. Hendricks**. Released with GPL-3 License.
 - `rarfile.py` script &copy; 2005-2014 **Marko Kreen** <markokr@gmail.com>. Released with ISC License.
 - `image.py` class from **Alex Yatskov**'s [Mangle](https://github.com/FooSoft/mangle/) with subsequent [proDOOMman](https://github.com/proDOOMman/Mangle)'s and [Birua](https://github.com/Birua/Mangle)'s patches.
 - Icon is by **Nikolay Verin** ([http://ncrow.deviantart.com/](http://ncrow.deviantart.com/)) and released under [CC BY-NC-SA 3.0](http://creativecommons.org/licenses/by-nc-sa/3.0/) License.

## SAMPLE FILES CREATED BY KCC
* [Kindle Paperwhite 3 / Voyage / Oasis](http://kcc.iosphe.re/Samples/Ubunchu!-KV.mobi)
* [Kindle Paperwhite 1 / 2](http://kcc.iosphe.re/Samples/Ubunchu!-KPW.mobi)
* [Kindle](http://kcc.iosphe.re/Samples/Ubunchu!-K45.mobi)
* [Kobo Aura](http://kcc.iosphe.re/Samples/Ubunchu-KoA.kepub.epub)
* [Kobo Aura HD](http://kcc.iosphe.re/Samples/Ubunchu-KoAHD.kepub.epub)
* [Kobo Aura H2O](http://kcc.iosphe.re/Samples/Ubunchu-KoAH2O.kepub.epub)
* [Kobo Aura ONE](http://kcc.iosphe.re/Samples/Ubunchu-KoAO.kepub.epub)

## CHANGELOG
####5.2.1:
* Improved directory parsing
* Tweaked margin detection algorithm
* Improved error reporting

####5.2:
* Added new Panel View options
* Implemented new margin detection algorithm
* Removed HQ Panel View mode
* Fixed multiple smaller issues

####5.1.3:
* Added Kobo Aura ONE profile
* Fixed few small bugs

####5.1.2:
* Fixed error reporting

####5.1.1:
* Fixed multiple GUI bugs

####5.1:
* GUI now can be resized and high DPI support was somewhat improved
* Added profile for Kindle Oasis
* Implemented new error reporting mechanism
* CLI version now support additional cropping options
* Fixed permission issues on Windows
* Fixed multiple smaller issues

####5.0.1:
* Fixed Panel View placement issues
* Decreased application startup time
* Fixed multiple smaller issues

####5.0:
* Major overhaul of internal mechanisms and GUI
* Added cover upload feature
* Tweaked Webtoon parsing mode
* Fixed multiple smaller issues
* Migrated build enviroment to PyInstaller

####4.6.5:
* Fixed multiple Windows and OS X issues
* Allowed Linux release to use older PyQT5 version

####4.6.4:
* Fixed multiple Windows specific problems
* Improved error handling
* Improved color detection algorithm
* New, slimmer OS X release

####4.6.3:
* Implemented remote bug reporting
* Minor bug fixes and GUI tweaks

####4.6.2:
* Fixed critical MOBI header bug
* Fixed metadata encoding error

####4.6.1:
* Fixed KEPUB TOC generator
* Added warning about too small input files
* ComicRack Summary metadata field is now parsed
* Small tweaks of KEPUB output

####4.6:
* KEPUB is now default output for all Kobo profiles
* EPUB output now produce fully valid EPUB 3.0.1
* Added profile for Kindle Paperwhite 3
* Dropped official support of all Kindle Fire models and Kindle for Android
* Other minor tweaks

####4.5.1:
* Added Kobo Glo HD profile
* Fixed RAR/CBR parsing anomalies
* Minor bug fixes and tweaks

####4.5:
* Added simple ComicRack metadata editor
* Re-enabled Manga Cover Database support
* ComicRack bookmarks are now parsed
* Fixed glitches in Kindle Voyage profile
* Fixed problems with directory locks on Windows
* Fixed sorting anomalies
* Improved conversion speed

####4.4.1:
* Fixed problems with OSX GUI
* Added one missing DLL to Windows installer

####4.4:
* Improved speed and quality of conversion
* Added RAR5 support
* Dropped BMP and TIFF support
* Fixed some WebToon mode bugs
* Fixed CBR parsing on OSX

####4.3.1:
* Fixed Kindle Voyage profile
* Fixed some bugs in OS X release
* CLI version now support multiple input files at once
* Disabled MCB support
* Other minor tweaks

####4.3:
* Added profiles for Kindle Voyage and Kobo Aura H2O
* Added missing features to CLI version
* Other minor bug fixes

####4.2.1:
* Improved margin color detection 
* Fixed random crashes of MOBI processing step
* Fixed resizing problems in high quality mode
* Fixed some MCD support bugs
* Default output format for Kindle DX is now CBZ

####4.2:
* Added [Manga Cover Database](http://manga.joentjuh.nl/) support
* Officially dropped Windows XP support
* Fixed _Other_ profile
* Fixed problems with page order on stock KOBO CBZ reader
* Many other small bug fixes and tweaks

####4.1:
* Thanks to code contributed by Kevin Hendricks speed of MOBI creation was greatly increased
* Improved performance on Windows
* Improved MOBI splitting and changed maximal size of output file
* Fixed _No optimization_ mode
* Multiple small tweaks nad minor bug fixes

####4.0.2:
* Fixed some Windows and OSX specific bugs
* Fixed problem with marigns when using HQ mode

####4.0.1:
* Fixed file lock problems that plagued some Windows users
* Fixed content server failing to start on Windows
* Improved performance of WebToon splitter
* Tweaked margin color detection

####4.0:
* KCC now use Python 3.3 and Qt 5.2
* Full UTF-8 awareness
* CBZ output now support Manga mode
* Improved Panel View support and margin color detection
* Added drag&drop support
* Output directory can be now selected
* Windows release now have auto-updater
* Names of chapters on Kindle should be now more user friendly
* Fixed OSX file association support
* Many extensive internal changes and tweaks

####3.7.2:
* Fixed problems with HQ mode

####3.7.1:
* Hotfixed Kobo profiles

####3.7:
* Added profiles for KOBO devices
* Improved Panel View support
* Improved WebToon splitter
* Improved margin color autodetection
* Tweaked EPUB output
* Fixed stretching option
* GUI tweaks and minor bugfixes

####3.6.2:
* Fixed previous PNG output fix
* Fixed Panel View anomalies

####3.6.1:
* Fixed PNG output

####3.6:
* Increased quality of Panel View zoom
* Creation of multipart MOBI output is now faster on machines with 4GB+ RAM
* Automatic gamma correction now distinguishes color and grayscale images
* Added ComicRack metadata parser
* Implemented new method to detect border color in non-webtoon comics
* Upscaling is now enabled by default for Kindle Fire HD/HDX
* Windows nad Linux releases now have tray icon
* Fixed Kindle Fire HDX 7" output
* Increased target resolution for Kindle DX/DXG CBZ output

####3.5:
* Added simple content server - Converted files can be now delivered wireless
* Added proper Windows installer
* Improved multiprocessing speed
* GUI tweaks and minor bug fixes

####3.4:
* Improved PNG output
* Increased quality of upscaling
* Added support of file association - KCC can now open CBZ, CBR, CB7, ZIP, RAR, 7Z and PDF files directly
* Paths that contain UTF-8 characters are now supported
* Migrated to new version of Pillow library
* Merged DX and DXG profiles
* Many other minor bug fixes and GUI tweaks

####3.3:
* Margins are now automatically omitted in Panel View mode
* Margin color fill is now autodetected
* Created MOBI files are not longer marked as _Personal_ on newer Kindle models
* Layout of panels in Panel View mode is now automatically adjusted to content
* Fixed Kindle 2/DX/DXG profiles - no more blank pages
* All Kindle Fire profiles now support hiqh quality Panel View
* Added support of 7z/CB7 files
* Added Kindle Fire HDX profile
* Support for Virtual Panel View was removed
* Profiles for Kindle Keyboard, Touch and Non-Touch are now merged
* Windows release is now bundled with UnRAR and 7za
* Small GUI tweaks

####3.2:
* Too big EPUB files are now splitted before conversion to MOBI
* Added experimental parser of manga webtoons
* Improved error handling

####3.2.1:
* Hotfixed crash occurring on OS with Russian locale

####3.1:
* Added profile: Kindle for Android
* Add file/directory dialogs now support multiselect
* Many small fixes and tweaks

####3.0:
* New QT GUI
* Merge with AWKCC
* Added ultra quality mode
* Added support for custom width/height
* Added option to disable color conversion

####2.10:
* Multiprocessing support
* Kindle Fire support (color EPUB/MOBI)
* Panel View support for horizontal content
* Fixed panel order for horizontal pages when --rotate is enabled
* Disabled cropping and page number cutting for blank pages
* Fixed some slugify issues with specific file naming conventions (#50, #51)

####2.9
* Added support for generating a plain CBZ (skipping all the EPUB/MOBI generation) (#45)  
* Prevent output file overwriting the source one: if a duplicate name is detected, append _kcc to the name  
* Rarfile library updated to 2.6  
* Added GIF, TIFF and BMP to supported formats (#42)  
* Filenames slugifications (#28, #31, #9, #8)

####2.8
* Updated rarfile library  
* Panel View support + HQ support (#36) - new option: --nopanelviewhq
* Split profiles for K4NT and K4T  
* Rewrite of Landscape Mode support (huge readability improvement for KPW)  
* Upscale use now BILINEAR method  
* Added generic CSS file  
* Optimized archive extraction for zip/rar files (#40)  

####2.7
* Lots of GUI improvements (#27, #13)  
* Added gamma support within --gamma option (defaults to profile-specified gamma) (#26, #27)  
* Added --nodithering option to prevent dithering optimizations (#27)  
* EPUB margins support (#30)  
* Fixed no file added if file has no spaces on Windows (#25)  
* Gracefully exit if unrar missing (#15)  
* Do not call kindlegen if source EPUB is bigger than 320MB (#17)  
* Get filetype from magic number (#14)   
* PDF conversion works again  

####2.6
* Added --rotate option to rotate landscape images instead of splitting them (#16, #24)  
* Added --output option to customize EPUB output dir/file (#22)  
* Add rendition:layout and rendition:orientation EPUB meta tags (supported by new kindlegen 2.8)  
* Fixed natural sorting for files (#18)

####2.5
* Added --black-borders option to set added borders black when page's ratio is not the device's one (#11).  
* Fixes EPUB containing zipped itself (#10)  

####2.4
* Use temporary directory as workdir (fixes converting from external volumes and zipfiles renaming)  
* Fixed "add folders" from GUI.

####2.3
* Fixed win32 EPUB generation, folder handling, filenames with spaces and subfolders

####2.2:
* Added (valid!) EPUB 2.0 output  
* Rename .zip files to .cbz to avoid overwriting

####2.1
* Added basic error reporting

####2.0
* GUI! AppleScript is gone and Tk is used to provide cross-platform GUI support.

####1.5
* Added subfolder support for multiple chapters.

####1.4.1
* Fixed a serious bug on resizing when img ratio was bigger than device one

####1.4
* Added some options for controlling image optimization  
* Further optimization (ImageOps, page numbering cut, autocontrast)

####1.3
* Fixed an issue in OPF generation for device resolution  
* Reworked options system (call with -h option to get the inline help)

####1.2
* Comic optimizations! Split pages not target-oriented (landscape with portrait target or portrait with landscape target), add palette and other image optimizations from Mangle. WARNING: PIL is required for all image mangling!

####1.1.1
* Added support for CBZ/CBR files in Kindle Comic Converter

####1.1
* Added support for CBZ/CBR files in comic2ebook.py

####1.0
* Initial version

## PRIVACY
**KCC** is initiating internet connections in three cases:
* During startup - Version check
* When MCD metadata are used - Cover download
* When error occurs - Automatic reporting

## KNOWN ISSUES
Please check [wiki page](https://github.com/ciromattia/kcc/wiki/Known-issues).

## COPYRIGHT
Copyright (c) 2012-2016 Ciro Mattia Gonano and Paweł Jastrzębski.
**KCC** is released under ISC LICENSE; see LICENSE.txt for further details.
