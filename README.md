# KCC



[![GitHub release](https://img.shields.io/github/release/ciromattia/kcc.svg)](https://github.com/ciromattia/kcc/releases) 
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/ciromattia/kcc/docker-publish.yml?label=docker%20build)](https://github.com/ciromattia/kcc/pkgs/container/kcc) 


**Kindle Comic Converter** is a Python app to convert comic/manga files or folders to EPUB, Panel View MOBI or E-Ink optimized CBZ.
It was initially developed for Kindle but since version 4.6 it outputs valid EPUB 3.0 so _**despite its name, KCC is
actually a comic/manga to EPUB converter that every e-reader owner can happily use**_.
It can also optionally optimize images by applying a number of transformations.

### A word of warning
**KCC** _is not_ [Amazon's Kindle Comic Creator](http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1001103761) nor is in any way endorsed by Amazon.
Amazon's tool is for comic publishers and involves a lot of manual effort, while **KCC** is for comic/manga readers.
_KC2_ in no way is a replacement for **KCC** so you can be quite confident we are going to carry on developing our little monster ;-)

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


## INSTALLATION 

### DOWNLOADS

- **https://github.com/ciromattia/kcc/releases**

Click on **Assets** of the latest release. 

You probably want either 
- `kcc_*.*.*.exe` (Windows)
- `KindleComicConverter_osx_*.*.*.dmg` (Mac)

Installation Wiki: https://github.com/ciromattia/kcc/wiki/Installation

- flatpak : https://flathub.org/apps/details/io.github.ciromattia.kcc
- Docker: https://github.com/ciromattia/kcc/pkgs/container/kcc

### DEPENDENCIES
Following software is required to run Linux version of **KCC** and/or bare sources:
- Python 3.3+
- [PyQt5](https://pypi.python.org/pypi/PyQt5) 5.6.0+ (only needed for GUI)
- [Pillow](https://pypi.python.org/pypi/Pillow/) 4.0.0+ (5.2.0+ needed for WebP support)
- [psutil](https://pypi.python.org/pypi/psutil) 5.0.0+
- [python-slugify](https://pypi.python.org/pypi/python-slugify) 1.2.1+, <8.0.0
- [raven](https://pypi.python.org/pypi/raven) 6.0.0+ (only needed for GUI)

On Debian based distributions these two commands should install all needed dependencies:



```bash
$ sudo apt-get install -y python3 python3-dev libpng-dev libjpeg-dev p7zip-full p7zip-rar unrar-free libgl1 python3-pyqt5 && \
    python -m pip install --upgrade pip && \
    python -m pip install --upgrade -r requirements.txt
```


#### Optional dependencies
- Qt platform integration plugin for Deepin Desktop Environment
```bash
$ sudo apt-get install qt5dxcb-plugin
```

- KindleGen ~~[(deprecated link)](http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211)~~ v2.9+  (For MOBI generation) 
  - should be placed in a directory reachable by your _PATH_ or in _KCC_ directory
  - `KindleGen` can be found in [Kindle Previewer](https://www.amazon.com/Kindle-Previewer/b?ie=UTF8&node=21381691011)
  - `KindleGen` can be also be found in [Kindle Comic Creator](https://www.amazon.com/b?node=23496309011)
- [7z](http://www.7-zip.org/download.html) *(For CBZ/ZIP, CBR/RAR, 7z/CB7 support)*
- Unrar (no rar in 7z on Fedora)



## INPUT FORMATS
**KCC** can understand and convert, at the moment, the following input types:
- Folders containing: PNG, JPG, GIF or WebP files
- CBZ, ZIP *(With `7z` executable)*
- CBR, RAR *(With `7z` executable)*
- CB7, 7Z *(With `7z` executable)*
- PDF *(Only extracting JPG images)*

## USAGE

Should be pretty self-explanatory. All options have detailed information in tooltips.
After completed conversion, you should find ready file alongside the original input file (same directory).

Please check [our wiki](https://github.com/ciromattia/kcc/wiki/) for more details.

CLI version of **KCC** is intended for power users. It allows using options that might not be compatible and decrease the quality of output.
CLI version has reduced dependencies, on Debian based distributions this commands should install all needed dependencies:
```
sudo apt-get install python3 p7zip-full python3-pil python3-psutil python3-slugify
```

### Profiles:

```
        'K1': ("Kindle 1", (600, 670), Palette4, 1.8),
        'K11': ("Kindle 11", (1072, 1448), Palette16, 1.8),
        'K2': ("Kindle 2", (600, 670), Palette15, 1.8),
        'K34': ("Kindle Keyboard/Touch", (600, 800), Palette16, 1.8),
        'K578': ("Kindle", (600, 800), Palette16, 1.8),
        'KDX': ("Kindle DX/DXG", (824, 1000), Palette16, 1.8),
        'KPW': ("Kindle Paperwhite 1/2", (758, 1024), Palette16, 1.8),
        'KV': ("Kindle Paperwhite 3/4/Voyage/Oasis", (1072, 1448), Palette16, 1.8),
        'KPW5': ("Kindle Paperwhite 5/Signature Edition", (1236, 1648), Palette16, 1.8),
        'KO': ("Kindle Oasis 2/3", (1264, 1680), Palette16, 1.8),
        'KS': ("Kindle Scribe", (1860, 2480), Palette16, 1.8),
        'KoMT': ("Kobo Mini/Touch", (600, 800), Palette16, 1.8),
        'KoG': ("Kobo Glo", (768, 1024), Palette16, 1.8),
        'KoGHD': ("Kobo Glo HD", (1072, 1448), Palette16, 1.8),
        'KoA': ("Kobo Aura", (758, 1024), Palette16, 1.8),
        'KoAHD': ("Kobo Aura HD", (1080, 1440), Palette16, 1.8),
        'KoAH2O': ("Kobo Aura H2O", (1080, 1430), Palette16, 1.8),
        'KoAO': ("Kobo Aura ONE", (1404, 1872), Palette16, 1.8),
        'KoN': ("Kobo Nia", (758, 1024), Palette16, 1.8),
        'KoC': ("Kobo Clara HD/Kobo Clara 2E", (1072, 1448), Palette16, 1.8),
        'KoL': ("Kobo Libra H2O/Kobo Libra 2", (1264, 1680), Palette16, 1.8),
        'KoF': ("Kobo Forma", (1440, 1920), Palette16, 1.8),
        'KoS': ("Kobo Sage", (1440, 1920), Palette16, 1.8),
        'KoE': ("Kobo Elipsa", (1404, 1872), Palette16, 1.8),
        'OTHER': ("Other", (0, 0), Palette16, 1.8),
```


### Standalone `kcc-c2e.py` usage:

```
usage: kcc-c2e [options] [input]

MANDATORY:
  input                 Full path to comic folder or file(s) to be processed.

MAIN:
  -p PROFILE, --profile PROFILE
                        Device profile (Available options: K1, K2, K34, K578, KDX, KPW, KPW5, KV, KO, K11, KS, KoMT, KoG, KoGHD, KoA, KoAHD, KoAH2O, KoAO, KoN, KoC, KoL, KoF, KoS, KoE) [Default=KV]
  -m, --manga-style     Manga style (right-to-left reading and splitting)
  -q, --hq              Try to increase the quality of magnification
  -2, --two-panel       Display two not four panels in Panel View mode
  -w, --webtoon         Webtoon processing mode
  --ts TARGETSIZE, --targetsize TARGETSIZE
                        the maximal size of output file in MB. [Default=100MB for webtoon and 400MB for others]

PROCESSING:
  -n, --noprocessing    Do not modify image and ignore any profil or processing option
  -u, --upscale         Resize images smaller than device's resolution
  -s, --stretch         Stretch images to device's resolution
  -r SPLITTER, --splitter SPLITTER
                        Double page parsing mode. 0: Split 1: Rotate 2: Both [Default=0]
  -g GAMMA, --gamma GAMMA
                        Apply gamma correction to linearize the image [Default=Auto]
  -c CROPPING, --cropping CROPPING
                        Set cropping mode. 0: Disabled 1: Margins 2: Margins + page numbers [Default=2]
  --cp CROPPINGP, --croppingpower CROPPINGP
                        Set cropping power [Default=1.0]
  --cm CROPPINGM, --croppingminimum CROPPINGM
                        Set cropping minimum area ratio [Default=0.0]
  --blackborders        Disable autodetection and force black borders
  --whiteborders        Disable autodetection and force white borders
  --forcecolor          Don't convert images to grayscale
  --forcepng            Create PNG files instead JPEG
  --mozjpeg             Create JPEG files using mozJpeg
  --maximizestrips      Turn 1x4 strips to 2x2 strips
  -d, --delete          Delete source file(s) or a directory. It's not recoverable.

OUTPUT SETTINGS:
  -o OUTPUT, --output OUTPUT
                        Output generated file to specified directory or file
  -t TITLE, --title TITLE
                        Comic title [Default=filename or directory name]
  -f FORMAT, --format FORMAT
                        Output format (Available options: Auto, MOBI, EPUB, CBZ, KFX, MOBI+EPUB) [Default=Auto]
  -b BATCHSPLIT, --batchsplit BATCHSPLIT
                        Split output into multiple files. 0: Don't split 1: Automatic mode 2: Consider every subdirectory as separate volume [Default=0]

CUSTOM PROFILE:
  --customwidth CUSTOMWIDTH
                        Replace screen width provided by device profile
  --customheight CUSTOMHEIGHT
                        Replace screen height provided by device profile

OTHER:
  -h, --help            Show this help message and exit

```

### Standalone `kcc-c2p.py` usage:

```
usage: kcc-c2p [options] [input]

MANDATORY:
  input                 Full path to comic folder(s) to be processed. Separate multiple inputs with spaces.

MAIN:
  -y HEIGHT, --height HEIGHT
                        Height of the target device screen
  -i, --in-place        Overwrite source directory
  -m, --merge           Combine every directory into a single image before splitting

OTHER:
  -d, --debug           Create debug file for every split image
  -h, --help            Show this help message and exit
```

## CREDITS
**KCC** is made by [Ciro Mattia Gonano](http://github.com/ciromattia), [Paweł Jastrzębski](http://github.com/AcidWeb) and [Darodi](http://github.com/darodi)  .

This script born as a cross-platform alternative to `KindleComicParser` by **Dc5e** (published [here](http://www.mobileread.com/forums/showthread.php?t=192783)).

The app relies and includes the following scripts:

 - `DualMetaFix` script by **K. Hendricks**. Released with GPL-3 License.
 - `image.py` class from **Alex Yatskov**'s [Mangle](https://github.com/FooSoft/mangle/) with subsequent [proDOOMman](https://github.com/proDOOMman/Mangle)'s and [Birua](https://github.com/Birua/Mangle)'s patches.
 - Icon is by **Nikolay Verin** ([http://ncrow.deviantart.com/](http://ncrow.deviantart.com/)) and released under [CC BY-NC-SA 3.0](http://creativecommons.org/licenses/by-nc-sa/3.0/) License.

## SAMPLE FILES CREATED BY KCC
* [Kindle Oasis 2 / 3](http://kcc.iosphe.re/Samples/Ubunchu!-KO.mobi)
* [Kindle Paperwhite 3 / 4 / Voyage / Oasis](http://kcc.iosphe.re/Samples/Ubunchu!-KV.mobi)
* [Kindle Paperwhite 1 / 2](http://kcc.iosphe.re/Samples/Ubunchu!-KPW.mobi)
* [Kindle](http://kcc.iosphe.re/Samples/Ubunchu!-K578.mobi)
* [Kobo Aura](http://kcc.iosphe.re/Samples/Ubunchu-KoA.kepub.epub)
* [Kobo Aura HD](http://kcc.iosphe.re/Samples/Ubunchu-KoAHD.kepub.epub)
* [Kobo Aura H2O](http://kcc.iosphe.re/Samples/Ubunchu-KoAH2O.kepub.epub)
* [Kobo Aura ONE](http://kcc.iosphe.re/Samples/Ubunchu-KoAO.kepub.epub)
* [Kobo Forma](http://kcc.iosphe.re/Samples/Ubunchu-KoF.kepub.epub)

## PRIVACY
**KCC** is initiating internet connections in two cases:
* During startup - Version check.
* When error occurs - Automatic reporting on Windows and macOS.

## KNOWN ISSUES
Please check [wiki page](https://github.com/ciromattia/kcc/wiki/Known-issues).

## COPYRIGHT
Copyright (c) 2012-2023 Ciro Mattia Gonano, Paweł Jastrzębski and Darodi.   
**KCC** is released under ISC LICENSE; see [LICENSE.txt](./LICENSE.txt) for further details.
