# KCC

**Kindle Comic Converter** is a Python app to convert comic files or folders to ePub, Panel View MOBI or E-Ink optimized CBZ.
It was initally developed for Kindle but since v2.2 it outputs valid ePub 2.0 so _**despite its name, KCC is
actually a comic to EPUB converter that every e-reader owner can happily use**_.
It can also optionally optimize images by applying a number of transformations.

### A word of warning
**KCC** _is not_ [Amazon's Kindle Comic Creator](http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1001103761) nor is in any way endorsed by Amazon.  
Amazon's tool is for comic publishers and involves a lot of manual effort, while **KCC** is for comic readers.
_KC2_ in no way is a replacement for **KCC** so you can be quite confident we'll going to carry on developing our little monster ;-)

### Issues / new features / donations
If you have general questions about usage, feedback etc. please [post it here](http://www.mobileread.com/forums/showthread.php?t=207461).
If you have some **technical** problems using KCC please [file an issue here](https://github.com/ciromattia/kcc/issues/new).
If you can fix an open issue, fork & make a pull request.  
If you want more chances an issue is fixes or your wanted feature added, consider [placing a bounty](https://www.bountysource.com/trackers/65571-ciromattia-kcc)!  

If you find **KCC** valuable you can consider donating to the authors:
  * Ciro Mattia Gonano: [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=D8WNYNPBGDAS2) [![Flattr this](http://api.flattr.com/button/flattr-badge-large.png)](http://flattr.com/thing/2260449/ciromattiakcc-on-GitHub)
  * Paweł Jastrzębski: [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=YTTJ4LK2JDHPS) [![1W15wwqsfd7wbaZ6wvSJf1LW1bz6q5L8b](http://s30.postimg.org/6z3kwvdlp/BC_Rnd.png)](bitcoin:1W15wwqsfd7wbaZ6wvSJf1LW1bz6q5L8b?label=KCC) [1W15wwqsfd7wbaZ6wvSJf1LW1bz6q5L8b](bitcoin:1W15wwqsfd7wbaZ6wvSJf1LW1bz6q5L8b?label=KCC)

## BINARY RELEASES
You can find the latest released binary at the following links:
- **Windows:** [http://kcc.iosphe.re/Windows/](http://kcc.iosphe.re/Windows/)
- **Linux:** [http://kcc.iosphe.re/Linux/](http://kcc.iosphe.re/Linux/)
- **OS X (10.8+):** [http://kcc.iosphe.re/OSX/](http://kcc.iosphe.re/OSX/)

## INPUT FORMATS
**KCC** can understand and convert, at the moment, the following input types:
- Folders containing: PNG, JPG, GIF, TIFF or BMP files
- CBZ, ZIP
- CBR, RAR *(With `unrar` executable)*
- CB7, 7Z *(With `7za` executable)*
- PDF *(Extracting only contained JPG images)*

## OPTIONAL REQUIREMENTS
- [KindleGen](http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211) v2.9+ in a directory reachable by your _PATH_ or in _KCC_ directory *(For MOBI generation)*
- [UnRAR](http://www.rarlab.com/download.htm) *(For CBR/RAR support)*
- [7za](http://www.7-zip.org/download.html) *(For 7z/CB7 support)*

### For running from source:
- Python 3.3+
- [PyQt5](http://www.riverbankcomputing.co.uk/software/pyqt/download5) 5.2.0+
- [Pillow](http://pypi.python.org/pypi/Pillow/) 2.3.0+
- [psutil](https://pypi.python.org/pypi/psutil) 2.0+
- [python-slugify](http://pypi.python.org/pypi/python-slugify)

On Debian based distributions these two commands should install all dependencies:
```
sudo apt-get install python3 python3-dev python3-pip python3-pyqt5 libtiff-dev libpng-dev libjpeg-dev p7zip-full unrar
sudo pip3 install pillow python-slugify psutil
```

### For freezing code:
- Windows - [py2exe](https://pypi.python.org/pypi/py2exe) 0.9.2+
- OS X - [py2app](https://bitbucket.org/ronaldoussoren/py2app) 0.8+

## USAGE

Should be pretty self-explanatory. All options have detailed informations in tooltips.
After completed conversion you should find ready file alongside the original input file (same directory).

Please check [our wiki](https://github.com/ciromattia/kcc/wiki/) for more details.

### Standalone `kcc-c2e.py` usage:

```
Usage: kcc-c2e [options] comic_file|comic_folder

Options:
  MAIN:
    -p PROFILE, --profile=PROFILE
                        Device profile (Choose one among K1, K2, K345, KDX, KHD, KF, KFHD, KFHD8, KFHDX, KFHDX8, KFA, KoMT, KoG, KoA, KoAHD) [Default=KHD]
    -q QUALITY, --quality=QUALITY
                        Quality of Panel View. 0 - Normal 1 - High 2 - Ultra [Default=0]
    -m, --manga-style   Manga style (Right-to-left reading and splitting)
    -w, --webtoon       Webtoon processing mode

  OUTPUT SETTINGS:
    -o OUTPUT, --output=OUTPUT
                        Output generated file to specified directory or file
    -t TITLE, --title=TITLE
                        Comic title [Default=filename or directory name]
    --cbz-output        Outputs a CBZ archive and does not generate EPUB
    --batchsplit        Split output into multiple files

  PROCESSING:
    --blackborders      Disable autodetection and force black borders
    --whiteborders      Disable autodetection and force white borders
    --forcecolor        Don't convert images to grayscale
    --forcepng          Create PNG files instead JPEG
    --gamma=GAMMA       Apply gamma correction to linearize the image [Default=Auto]
    --nocutpagenumbers  Don't try to cut page numbering on images
    --noprocessing      Don't apply image preprocessing
    --nosplitrotate     Disable splitting and rotation
    --rotate            Rotate landscape pages instead of splitting them
    --stretch           Stretch images to device's resolution
    --upscale           Resize images smaller than device's resolution

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

The app relies and includes the following scripts/binaries:

 - `DualMetaFix` script by **K. Hendricks**. Released with GPL-3 License.
 - `rarfile.py` script &copy; 2005-2011 **Marko Kreen** <markokr@gmail.com>. Released with ISC License.
 - `image.py` class from **Alex Yatskov**'s [Mangle](https://github.com/FooSoft/mangle/) with subsequent [proDOOMman](https://github.com/proDOOMman/Mangle)'s and [Birua](https://github.com/Birua/Mangle)'s patches.
 - Icon is by **Nikolay Verin** ([http://ncrow.deviantart.com/](http://ncrow.deviantart.com/)) and released under [CC BY-NC-SA 3.0](http://creativecommons.org/licenses/by-nc-sa/3.0/) License.

## SAMPLE FILES CREATED BY KCC
* [Kindle Paperwhite](http://kcc.iosphe.re/Samples/Ubunchu!-KPW.mobi)
* [Kindle](http://kcc.iosphe.re/Samples/Ubunchu!-K345.mobi)
* [Kindle DX/DXG](http://kcc.iosphe.re/Samples/Ubunchu!-KDX.mobi)
* [Kindle Fire HD](http://kcc.iosphe.re/Samples/Ubunchu!-KFHD.mobi)
* [Kindle Fire HD 8.9"](http://kcc.iosphe.re/Samples/Ubunchu!-KFHD8.mobi)
* [Kindle Fire HDX](http://kcc.iosphe.re/Samples/Ubunchu!-KFHDX.mobi)
* [Kindle Fire HDX 8.9"](http://kcc.iosphe.re/Samples/Ubunchu!-KFHDX8.mobi)
* [Kobo Mini/Touch](http://kcc.iosphe.re/Samples/Ubunchu!-KoMT.cbz)
* [Kobo Glow](http://kcc.iosphe.re/Samples/Ubunchu!-KoG.cbz)
* [Kobo Aura](http://kcc.iosphe.re/Samples/Ubunchu!-KoA.cbz)
* [Kobo Aura HD](http://kcc.iosphe.re/Samples/Ubunchu!-KoAHD.cbz)

## CHANGELOG
####1.0
* Initial version

####1.1
* Added support for CBZ/CBR files in comic2ebook.py

####1.1.1
* Added support for CBZ/CBR files in Kindle Comic Converter

####1.2
* Comic optimizations! Split pages not target-oriented (landscape with portrait target or portrait with landscape target), add palette and other image optimizations from Mangle. WARNING: PIL is required for all image mangling!

####1.3
* Fixed an issue in OPF generation for device resolution  
* Reworked options system (call with -h option to get the inline help)

####1.4
* Added some options for controlling image optimization  
* Further optimization (ImageOps, page numbering cut, autocontrast)

####1.4.1
* Fixed a serious bug on resizing when img ratio was bigger than device one

####1.5
* Added subfolder support for multiple chapters.

####2.0
* GUI! AppleScript is gone and Tk is used to provide cross-platform GUI support.

####2.1
* Added basic error reporting

####2.2:
* Added (valid!) ePub 2.0 output  
* Rename .zip files to .cbz to avoid overwriting

####2.3
* Fixed win32 ePub generation, folder handling, filenames with spaces and subfolders

####2.4
* Use temporary directory as workdir (fixes converting from external volumes and zipfiles renaming)  
* Fixed "add folders" from GUI.

####2.5
* Added --black-borders option to set added borders black when page's ratio is not the device's one (#11).  
* Fixes epub containing zipped itself (#10)  

####2.6
* Added --rotate option to rotate landscape images instead of splitting them (#16, #24)  
* Added --output option to customize ePub output dir/file (#22)  
* Add rendition:layout and rendition:orientation ePub meta tags (supported by new kindlegen 2.8)  
* Fixed natural sorting for files (#18)

####2.7
* Lots of GUI improvements (#27, #13)  
* Added gamma support within --gamma option (defaults to profile-specified gamma) (#26, #27)  
* Added --nodithering option to prevent dithering optimizations (#27)  
* Epub margins support (#30)  
* Fixed no file added if file has no spaces on Windows (#25)  
* Gracefully exit if unrar missing (#15)  
* Do not call kindlegen if source epub is bigger than 320MB (#17)  
* Get filetype from magic number (#14)   
* PDF conversion works again  

####2.8
* Updated rarfile library  
* Panel View support + HQ support (#36) - new option: --nopanelviewhq
* Split profiles for K4NT and K4T  
* Rewrite of Landscape Mode support (huge readability improvement for KPW)  
* Upscale use now BILINEAR method  
* Added generic CSS file  
* Optimized archive extraction for zip/rar files (#40)  

####2.9
* Added support for generating a plain CBZ (skipping all the EPUB/Mobi generation) (#45)  
* Prevent output file overwriting the source one: if a duplicate name is detected, append _kcc to the name  
* Rarfile library updated to 2.6  
* Added GIF, TIFF and BMP to supported formats (#42)  
* Filenames slugifications (#28, #31, #9, #8)

####2.10:
* Multiprocessing support
* Kindle Fire support (color ePub/Mobi)
* Panel View support for horizontal content
* Fixed panel order for horizontal pages when --rotate is enabled
* Disabled cropping and page number cutting for blank pages
* Fixed some slugify issues with specific file naming conventions (#50, #51)

####3.0:
* New QT GUI
* Merge with AWKCC
* Added ultra quality mode
* Added support for custom width/height
* Added option to disable color conversion

####3.1:
* Added profile: Kindle for Android
* Add file/directory dialogs now support multiselect
* Many small fixes and tweaks

####3.2:
* Too big EPUB files are now splitted before conversion to MOBI
* Added experimental parser of manga webtoons
* Improved error handling

####3.2.1:
* Hotfixed crash occurring on OS with Russian locale

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

####3.4:
* Improved PNG output
* Increased quality of upscaling
* Added support of file association - KCC can now open CBZ, CBR, CB7, ZIP, RAR, 7Z and PDF files directly
* Paths that contain UTF-8 characters are now supported
* Migrated to new version of Pillow library
* Merged DX and DXG profiles
* Many other minor bug fixes and GUI tweaks

####3.5:
* Added simple content server - Converted files can be now delivered wireless
* Added proper Windows installer
* Improved multiprocessing speed
* GUI tweaks and minor bug fixes

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

####3.6.1:
* Fixed PNG output

####3.6.2:
* Fixed previous PNG output fix
* Fixed Panel View anomalies

####3.7:
* Added profiles for KOBO devices
* Improved Panel View support
* Improved WebToon splitter
* Improved margin color autodetection
* Tweaked EPUB output
* Fixed stretching option
* GUI tweaks and minor bugfixes

####3.7.1:
* Hotfixed Kobo profiles

####3.7.2:
* Fixed problems with HQ mode

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

####4.0.1:
* Fixed file lock problems that plagued some Windows users
* Fixed content server failing to start on Windows
* Improved performance of WebToon splitter
* Tweaked margin color detection

####4.0.2:
* Fixed some Windows and OSX specific bugs
* Fixed problem with marigns when using HQ mode

## KNOWN ISSUES
Please check [wiki page](https://github.com/ciromattia/kcc/wiki/Known-issues).

## COPYRIGHT
Copyright (c) 2012-2014 Ciro Mattia Gonano and Paweł Jastrzębski.
**KCC** is released under ISC LICENSE; see LICENSE.txt for further details.
