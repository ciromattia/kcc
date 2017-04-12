# KCC

[![GitHub release](https://img.shields.io/github/release/ciromattia/kcc.svg)](https://github.com/ciromattia/kcc/releases) [![PyPI](https://img.shields.io/pypi/v/KindleComicConverter.svg)](https://pypi.python.org/pypi/KindleComicConverter) [![AUR](https://img.shields.io/aur/version/kcc.svg)](https://aur.archlinux.org/packages/kcc/)

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
  - [![Donate PayPal](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=D8WNYNPBGDAS2)
  - [![Donate Flattr](https://img.shields.io/badge/Donate-Flattr-green.svg)](http://flattr.com/thing/2260449/ciromattiakcc-on-GitHub)
- Paweł Jastrzębski:
  - [![Donate PayPal](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=YTTJ4LK2JDHPS)
  - [![Donate Bitcoin](https://img.shields.io/badge/Donate-Bitcoin-green.svg)](https://jastrzeb.ski/donate/)

## BINARY RELEASES
You can find the latest released binary at the following links:
- **Windows (64-bit only):** [http://kcc.iosphe.re/Windows/](http://kcc.iosphe.re/Windows/)
- **Linux (Glibc 2.19+):** [http://kcc.iosphe.re/Linux/](http://kcc.iosphe.re/Linux/)
- **OS X (10.9+):** [http://kcc.iosphe.re/OSX/](http://kcc.iosphe.re/OSX/)

## PYPI
**KCC** is also available on PyPI.
```
pip install KindleComicConverter
```

## DEPENDENCIES
Following software is required to run Linux version of **KCC** and/or bare sources:
- Python 3.3+
- [PyQt5](https://pypi.python.org/pypi/PyQt5) 5.6.0+
- [Pillow](https://pypi.python.org/pypi/Pillow/) 4.0.0+
- [psutil](https://pypi.python.org/pypi/psutil) 5.0.0+
- [python-slugify](https://pypi.python.org/pypi/python-slugify) 1.2.1+
- [raven](https://pypi.python.org/pypi/raven) 6.0.0+

On Debian based distributions these two commands should install all needed dependencies:
```
sudo apt-get install python3 python3-dev python3-pip libpng-dev libjpeg-dev p7zip-full unrar
sudo pip3 install --upgrade pillow python-slugify psutil pyqt5 raven
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

CLI version of **KCC** is intended for power users. It allow to use options that might not be compatible and decrease quality of output. 

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
    -q, --hq            Try to increase the quality of magnification
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

## PRIVACY
**KCC** is initiating internet connections in three cases:
* During startup - Version check
* When MCD metadata are used - Cover download
* When error occurs - Automatic reporting

## KNOWN ISSUES
Please check [wiki page](https://github.com/ciromattia/kcc/wiki/Known-issues).

## COPYRIGHT
Copyright (c) 2012-2017 Ciro Mattia Gonano and Paweł Jastrzębski.
**KCC** is released under ISC LICENSE; see LICENSE.txt for further details.
