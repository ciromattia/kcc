# CHANGELOG


#### 5.6.2:
* build pipeline : drop pypi by @darodi in [#465](https://github.com/ciromattia/kcc/pull/465)
* supporting Kindle Previewer by @darodi in [#466](https://github.com/ciromattia/kcc/pull/466)
* Bump actions/upload-artifact from 2 to 3 by @dependabot in [#468](https://github.com/ciromattia/kcc/pull/468)
* new appImage by @darodi in [#483](https://github.com/ciromattia/kcc/pull/483)
* Bump actions/checkout from 2 to 3 by @dependabot in [#484](https://github.com/ciromattia/kcc/pull/484)
* supporting Kindle Previewer by @darodi in [#486](https://github.com/ciromattia/kcc/pull/486)
* comic2ebook/func: Add a delete option (closes #458) by @Constantin1489 in [#485](https://github.com/ciromattia/kcc/pull/485)
* Add command line executables to CI/pipelines by @darodi in [#487](https://github.com/ciromattia/kcc/pull/487)
* gui/func: Add a 'delete after conversion' button (closes #458) by @Constantin1489 in [#488](https://github.com/ciromattia/kcc/pull/488)
* fix crashes on png transparency by @axu2 in [#494](https://github.com/ciromattia/kcc/pull/494)
* Update python-slugify requirement from <8.0.0,>=1.2.1 to >=1.2.1,<9.0.0 by @dependabot in [#473](https://github.com/ciromattia/kcc/pull/473)
* Updates GUI text for new Homebrew version by @thatrobotdev in [#491](https://github.com/ciromattia/kcc/pull/491)
* Even with EPUB-200MB option selected, created file is above 200MB by @darodi in [#503](https://github.com/ciromattia/kcc/pull/503)
* limit kindle scribe image size to (1440, 1920) when using kindlegen by @darodi in [#514](https://github.com/ciromattia/kcc/pull/514)
* add 7z to PATH by @axu2 in [#513](https://github.com/ciromattia/kcc/pull/513)
* use unrar for fedora only by @darodi in [#515](https://github.com/ciromattia/kcc/pull/515)


#### 5.6.1:
* Fix pillow backwards compatibility, add mozjpeg-lossless-optimization to setup.py by @corylk in #461
* fix in fedora: 7z doesn't support rar archives, use unrar by @AlicesReflexion in #370
* Using communicate instead of terminate by @catsout in #459
* use copyfile and delete instead of shutil.move fix #386 by @StudioEtrange in #387


#### 5.6.0:
* Fix Docker 7z missing  [darodi/kcc#31](https://github.com/darodi/kcc/issues/31), thanks [@darodi](https://github.com/darodi)
* update to python 3.11, thanks [@darodi](https://github.com/darodi)
* Bump python from 3.8-slim-buster to 3.11-slim-buster dependabot[bot]
* More precise type in slugify dependency check, thanks [@bamless](https://github.com/bamless)
* Fix 'slugify' dependency check, thanks [@bamless](https://github.com/bamless)
* Update python-slugify requirement from <3.0.0,>=1.2.1 to >=1.2.1,<8.0.0 dependabot[bot]
* Bump actions/setup-python from 3 to 4 [darodi/kcc#32](https://github.com/darodi/kcc/issues/32) dependabot[bot]
* Bump actions/setup-node from 2 to 3 [darodi/kcc#34](https://github.com/darodi/kcc/issues/34) dependabot[bot]
* Fix Docker 7z missing  [darodi/kcc#31](https://github.com/darodi/kcc/issues/31), thanks [@darodi](https://github.com/darodi)
* Spread splitter not keeping aspect ratio    [darodi/kcc#27](https://github.com/darodi/kcc/issues/27), thanks [@darodi](https://github.com/darodi)
* activate batchsplit only for EPUB-200  [darodi/kcc#24](https://github.com/darodi/kcc/issues/24), thanks [@darodi](https://github.com/darodi)
* Feature Request: allow split for epub and set target (email, web upload)  [darodi/kcc#21](https://github.com/darodi/kcc/issues/21), thanks [@darodi](https://github.com/darodi)
* Adding a switch on GUI interface in order to control cropping options  [darodi/kcc#18](https://github.com/darodi/kcc/issues/18), thanks [@darodi](https://github.com/darodi)
* profiles: add Kindle11 and Kindle Scribe  [darodi/kcc#16](https://github.com/darodi/kcc/issues/16), thanks [@darodi](https://github.com/darodi)
* Update with new Kobo models   [darodi/kcc#15](https://github.com/darodi/kcc/issues/15), thanks [@lennie420](https://github.com/lennie420)
* Keep epub file when selecting another type of output file [darodi/kcc#12](https://github.com/darodi/kcc/issues/12), thanks [@darodi](https://github.com/darodi)
* fix Using 'Disable processing' option using my processed image get an error [darodi/kcc#1](https://github.com/darodi/kcc/issues/1), thanks [@darodi](https://github.com/darodi)
* KFX Output in GUI [darodi/kcc#9](https://github.com/darodi/kcc/issues/9), thanks [@darodi](https://github.com/darodi)
* Linux version and appImage [darodi/kcc#6](https://github.com/darodi/kcc/issues/6), thanks [@darodi](https://github.com/darodi)
* docker image for command line [darodi/kcc#5](https://github.com/darodi/kcc/issues/5), thanks [@darodi](https://github.com/darodi)
* Fix type error in autocontrastImage [ciromattia/kcc#432](https://github.com/ciromattia/kcc/issues/432), thanks [@darodi](https://github.com/darodi)
* Option to turn 1x4 strips into 2x2 strips [ciromattia/kcc#439](https://github.com/ciromattia/kcc/issues/439), thanks [@darodi](https://github.com/darodi)
* Option in GUI to have PNG instead of jpg images [darodi/kcc#3](https://github.com/darodi/kcc/issues/3), thanks [@darodi](https://github.com/darodi)
* Use MozJPEG as the JPEG encoder : cli and GUI option [ciromattia/kcc#416](https://github.com/ciromattia/kcc/pull/416), thanks [@darodi](https://github.com/darodi)
* Disable all image transformation : cli and GUI option [ciromattia/kcc#388](https://github.com/ciromattia/kcc/pull/388), thanks [@StudioEtrange](https://github.com/StudioEtrange)
* file selector add All `*.*` [ciromattia/kcc#412](https://github.com/ciromattia/kcc/pull/412), thanks [@StudioEtrange](https://github.com/StudioEtrange)
* Clarify Pillow version requirement [ciromattia/kcc#366](https://github.com/ciromattia/kcc/pull/366), thanks [@clach04](https://github.com/clach04)
* sync requirements between setup.py and requirements.txt [ciromattia/kcc#411](https://github.com/ciromattia/kcc/pull/411), thanks [@StudioEtrange](https://github.com/StudioEtrange)
* Add profile for Kindle PW5/Signature [ciromattia/kcc#405](https://github.com/ciromattia/kcc/pull/405), thanks [@Einlar](https://github.com/Einlar), [@darodi](https://github.com/darodi)
* Fixed the skipped/missed images and/or panels [ciromattia/kcc#393](https://github.com/ciromattia/kcc/pull/393), thanks [@FulyaDemirkan](https://github.com/FulyaDemirkan)
* Add profiles for the Kobo Clara HD and Libra H2O [ciromattia/kcc#331](https://github.com/ciromattia/kcc/pull/331), thanks [@fbriere](https://github.com/fbriere)

#### 5.5.2:
* Fixed KindleGen detection on macOS 10.15
* Fixed multiple smaller issues

#### 5.5.1:
* Fixes some stability issues 

#### 5.5.0:
* Added support for WebP format
* Added profiles for Kindle Paperwhite 4 and Kobo Forma
* All archives are now handled by 7z
* Removed MCD support
* Fixed multiple smaller issues

#### 5.4.5:
* Fixed EPUB output for non-Kindle devices

#### 5.4.4:
* Minor bug fixes

#### 5.4.3:
* Fixed conversion crash on Windows

#### 5.4.2:
* Added Kindle Oasis 2 profile
* Allowed metadata editor to edit directories
* Fixed image stretching when HQ Panel View option was enabled
* Fixed possible problem with directory sort order

#### 5.4.1:
* Minor bug fixes and tweaks
* Implemented new binary build pipeline

#### 5.4:
* Reimplemented high quality Panel View option
* Improved webtoon splitter
* Fixed page splitter

#### 5.3.1:
* Small increase of output quality
* Improved error reporting
* Internal changes and tweaks

#### 5.3:
* Vastly improved output compatibility for non-Kindle devices
* Enabled old pinch zoom for Kindle devices
* Re-enabled Panel View support for Kindle Keyboard
* Partially re-enabled OS X file association mechanism
* Fixed multiple smaller issues

#### 5.2.1:
* Improved directory parsing
* Tweaked margin detection algorithm
* Improved error reporting

#### 5.2:
* Added new Panel View options
* Implemented new margin detection algorithm
* Removed HQ Panel View mode
* Fixed multiple smaller issues

#### 5.1.3:
* Added Kobo Aura ONE profile
* Fixed few small bugs

#### 5.1.2:
* Fixed error reporting

#### 5.1.1:
* Fixed multiple GUI bugs

#### 5.1:
* GUI now can be resized and high DPI support was somewhat improved
* Added profile for Kindle Oasis
* Implemented new error reporting mechanism
* CLI version now support additional cropping options
* Fixed permission issues on Windows
* Fixed multiple smaller issues

#### 5.0.1:
* Fixed Panel View placement issues
* Decreased application startup time
* Fixed multiple smaller issues

#### 5.0:
* Major overhaul of internal mechanisms and GUI
* Added cover upload feature
* Tweaked Webtoon parsing mode
* Fixed multiple smaller issues
* Migrated build enviroment to PyInstaller

#### 4.6.5:
* Fixed multiple Windows and OS X issues
* Allowed Linux release to use older PyQT5 version

#### 4.6.4:
* Fixed multiple Windows specific problems
* Improved error handling
* Improved color detection algorithm
* New, slimmer OS X release

#### 4.6.3:
* Implemented remote bug reporting
* Minor bug fixes and GUI tweaks

#### 4.6.2:
* Fixed critical MOBI header bug
* Fixed metadata encoding error

#### 4.6.1:
* Fixed KEPUB TOC generator
* Added warning about too small input files
* ComicRack Summary metadata field is now parsed
* Small tweaks of KEPUB output

#### 4.6:
* KEPUB is now default output for all Kobo profiles
* EPUB output now produce fully valid EPUB 3.0.1
* Added profile for Kindle Paperwhite 3
* Dropped official support of all Kindle Fire models and Kindle for Android
* Other minor tweaks

#### 4.5.1:
* Added Kobo Glo HD profile
* Fixed RAR/CBR parsing anomalies
* Minor bug fixes and tweaks

#### 4.5:
* Added simple ComicRack metadata editor
* Re-enabled Manga Cover Database support
* ComicRack bookmarks are now parsed
* Fixed glitches in Kindle Voyage profile
* Fixed problems with directory locks on Windows
* Fixed sorting anomalies
* Improved conversion speed

#### 4.4.1:
* Fixed problems with OSX GUI
* Added one missing DLL to Windows installer

#### 4.4:
* Improved speed and quality of conversion
* Added RAR5 support
* Dropped BMP and TIFF support
* Fixed some WebToon mode bugs
* Fixed CBR parsing on OSX

#### 4.3.1:
* Fixed Kindle Voyage profile
* Fixed some bugs in OS X release
* CLI version now support multiple input files at once
* Disabled MCB support
* Other minor tweaks

#### 4.3:
* Added profiles for Kindle Voyage and Kobo Aura H2O
* Added missing features to CLI version
* Other minor bug fixes

#### 4.2.1:
* Improved margin color detection
* Fixed random crashes of MOBI processing step
* Fixed resizing problems in high quality mode
* Fixed some MCD support bugs
* Default output format for Kindle DX is now CBZ

#### 4.2:
* Added [Manga Cover Database](http://manga.joentjuh.nl/) support
* Officially dropped Windows XP support
* Fixed _Other_ profile
* Fixed problems with page order on stock KOBO CBZ reader
* Many other small bug fixes and tweaks

#### 4.1:
* Thanks to code contributed by Kevin Hendricks speed of MOBI creation was greatly increased
* Improved performance on Windows
* Improved MOBI splitting and changed maximal size of output file
* Fixed _No optimization_ mode
* Multiple small tweaks nad minor bug fixes

#### 4.0.2:
* Fixed some Windows and OSX specific bugs
* Fixed problem with marigns when using HQ mode

#### 4.0.1:
* Fixed file lock problems that plagued some Windows users
* Fixed content server failing to start on Windows
* Improved performance of WebToon splitter
* Tweaked margin color detection

#### 4.0:
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

#### 3.7.2:
* Fixed problems with HQ mode

#### 3.7.1:
* Hotfixed Kobo profiles

#### 3.7:
* Added profiles for KOBO devices
* Improved Panel View support
* Improved WebToon splitter
* Improved margin color autodetection
* Tweaked EPUB output
* Fixed stretching option
* GUI tweaks and minor bugfixes

#### 3.6.2:
* Fixed previous PNG output fix
* Fixed Panel View anomalies

#### 3.6.1:
* Fixed PNG output

#### 3.6:
* Increased quality of Panel View zoom
* Creation of multipart MOBI output is now faster on machines with 4GB+ RAM
* Automatic gamma correction now distinguishes color and grayscale images
* Added ComicRack metadata parser
* Implemented new method to detect border color in non-webtoon comics
* Upscaling is now enabled by default for Kindle Fire HD/HDX
* Windows nad Linux releases now have tray icon
* Fixed Kindle Fire HDX 7" output
* Increased target resolution for Kindle DX/DXG CBZ output

#### 3.5:
* Added simple content server - Converted files can be now delivered wireless
* Added proper Windows installer
* Improved multiprocessing speed
* GUI tweaks and minor bug fixes

#### 3.4:
* Improved PNG output
* Increased quality of upscaling
* Added support of file association - KCC can now open CBZ, CBR, CB7, ZIP, RAR, 7Z and PDF files directly
* Paths that contain UTF-8 characters are now supported
* Migrated to new version of Pillow library
* Merged DX and DXG profiles
* Many other minor bug fixes and GUI tweaks

#### 3.3:
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

#### 3.2:
* Too big EPUB files are now splitted before conversion to MOBI
* Added experimental parser of manga webtoons
* Improved error handling

#### 3.2.1:
* Hotfixed crash occurring on OS with Russian locale

#### 3.1:
* Added profile: Kindle for Android
* Add file/directory dialogs now support multiselect
* Many small fixes and tweaks

#### 3.0:
* New QT GUI
* Merge with AWKCC
* Added ultra quality mode
* Added support for custom width/height
* Added option to disable color conversion

#### 2.10:
* Multiprocessing support
* Kindle Fire support (color EPUB/MOBI)
* Panel View support for horizontal content
* Fixed panel order for horizontal pages when --rotate is enabled
* Disabled cropping and page number cutting for blank pages
* Fixed some slugify issues with specific file naming conventions (#50, #51)

#### 2.9
* Added support for generating a plain CBZ (skipping all the EPUB/MOBI generation) (#45)  
* Prevent output file overwriting the source one: if a duplicate name is detected, append _kcc to the name  
* Rarfile library updated to 2.6  
* Added GIF, TIFF and BMP to supported formats (#42)  
* Filenames slugifications (#28, #31, #9, #8)

#### 2.8
* Updated rarfile library  
* Panel View support + HQ support (#36) - new option: --nopanelviewhq
* Split profiles for K4NT and K4T  
* Rewrite of Landscape Mode support (huge readability improvement for KPW)  
* Upscale use now BILINEAR method  
* Added generic CSS file  
* Optimized archive extraction for zip/rar files (#40)  

#### 2.7
* Lots of GUI improvements (#27, #13)  
* Added gamma support within --gamma option (defaults to profile-specified gamma) (#26, #27)  
* Added --nodithering option to prevent dithering optimizations (#27)  
* EPUB margins support (#30)  
* Fixed no file added if file has no spaces on Windows (#25)  
* Gracefully exit if unrar missing (#15)  
* Do not call kindlegen if source EPUB is bigger than 320MB (#17)  
* Get filetype from magic number (#14)   
* PDF conversion works again  

#### 2.6
* Added --rotate option to rotate landscape images instead of splitting them (#16, #24)  
* Added --output option to customize EPUB output dir/file (#22)  
* Add rendition:layout and rendition:orientation EPUB meta tags (supported by new kindlegen 2.8)  
* Fixed natural sorting for files (#18)

#### 2.5
* Added --black-borders option to set added borders black when page's ratio is not the device's one (#11).  
* Fixes EPUB containing zipped itself (#10)  

#### 2.4
* Use temporary directory as workdir (fixes converting from external volumes and zipfiles renaming)  
* Fixed "add folders" from GUI.

#### 2.3
* Fixed win32 EPUB generation, folder handling, filenames with spaces and subfolders

#### 2.2:
* Added (valid!) EPUB 2.0 output  
* Rename .zip files to .cbz to avoid overwriting

#### 2.1
* Added basic error reporting

#### 2.0
* GUI! AppleScript is gone and Tk is used to provide cross-platform GUI support.

#### 1.5
* Added subfolder support for multiple chapters.

#### 1.4.1
* Fixed a serious bug on resizing when img ratio was bigger than device one

#### 1.4
* Added some options for controlling image optimization  
* Further optimization (ImageOps, page numbering cut, autocontrast)

#### 1.3
* Fixed an issue in OPF generation for device resolution  
* Reworked options system (call with -h option to get the inline help)

#### 1.2
* Comic optimizations! Split pages not target-oriented (landscape with portrait target or portrait with landscape target), add palette and other image optimizations from Mangle. WARNING: PIL is required for all image mangling!

#### 1.1.1
* Added support for CBZ/CBR files in Kindle Comic Converter

#### 1.1
* Added support for CBZ/CBR files in comic2ebook.py

#### 1.0
* Initial version
