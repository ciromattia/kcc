# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Kindle Comic Converter (KCC) is a cross-platform tool that optimizes black & white comics and manga for E-ink ereaders (Kindle, Kobo, reMarkable, etc.). It converts comic files (folders, archives, PDFs) to various ebook formats (MOBI/AZW3, EPUB, KEPUB, CBZ, PDF) with specialized image processing for e-ink displays.

## Development Setup

### Initial Setup

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python kcc.py
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python kcc.py
```

### Running the Application

After initial setup, reactivate the venv each time:
- Windows: `venv\Scripts\activate.bat`
- macOS/Linux: `source venv/bin/activate`

Then run: `python kcc.py` (GUI) or `python kcc-c2e.py` (CLI)

### Building Binaries

Build platform-specific executables:
```bash
python setup.py build_binary  # GUI version
python setup.py build_c2e     # CLI c2e version
python setup.py build_c2p     # CLI c2p version
```

### UI Development

The GUI is built with PySide6 (Qt6). UI files are in `gui/`:
- `gui/KCC.ui` - Main application UI
- `gui/MetaEditor.ui` - Metadata editor UI
- `gui/KCC.qrc` - Qt resource file

After editing `.ui` files with `pyside6-designer`, regenerate Python files:
```bash
./gen_ui_files.sh       # Linux/macOS
gen_ui_files.bat        # Windows
```

This regenerates:
- `kindlecomicconverter/KCC_ui.py`
- `kindlecomicconverter/KCC_ui_editor.py`
- `kindlecomicconverter/KCC_rc.py`

**Never manually edit the generated `*_ui.py` or `*_rc.py` files.**

## Architecture

### Entry Points

- `kcc.py` - GUI launcher
- `kcc-c2e.py` - CLI comic-to-ebook converter
- `kcc-c2p.py` - CLI comic-to-panel converter

All entry points use `multiprocessing.spawn` for cross-platform compatibility and call functions in `kindlecomicconverter/startup.py`.

### Core Modules

**`kindlecomicconverter/` package:**

- **`comic2ebook.py`** (1800+ lines) - Main conversion engine. Orchestrates the entire comic-to-ebook pipeline: file extraction, image processing, HTML generation, and final packaging. Contains the core `makeBook()` function.

- **`image.py`** - Image manipulation layer. Handles resizing, cropping, rotation, palette reduction, gamma correction, contrast adjustments, and format conversions. Contains the `ProfileData` class with device profiles and the `ComicPage` class for image operations.

- **`KCC_gui.py`** - Qt6 GUI implementation. Manages user interactions, drag-and-drop, conversion queue, and progress reporting.

- **`comic2panel.py`** - Panel splitting algorithm for webtoon/vertical manga processing.

- **`comicarchive.py`** - Archive extraction handling (ZIP, RAR, 7Z, CBZ, CBR, CB7) with 7-Zip integration.

- **`metadata.py`** - Metadata extraction and embedding (ComicInfo.xml, EPUB/MOBI metadata).

- **`kindle.py`** - Kindle-specific output formatting and KindleGen integration.

- **`dualmetafix.py`** - MOBI/AZW3 dual-format metadata handling.

- **`page_number_crop_alg.py`** - Page number detection and cropping algorithm.

- **`inter_panel_crop_alg.py`** - Empty space detection between panels for cropping.

- **`rainbow_artifacts_eraser.py`** - Color e-ink rainbow artifact reduction via frequency attenuation.

- **`common_crop.py`** - Shared utilities for crop algorithms (threshold calculation, value grouping).

- **`shared.py`** - Cross-module utilities: file walking with natural sort, dependency version checks, HTML stripping, macOS dot-file cleanup.

### Key Workflows

**Conversion Pipeline (comic2ebook.py):**
1. Extract source files (archive/PDF/folder)
2. Process images (resize, crop, rotate, adjust contrast/gamma)
3. Generate EPUB/MOBI structure (HTML pages, metadata, navigation)
4. Package output (ZIP for EPUB, KindleGen for MOBI)
5. Optional post-processing (KEPUB transformation, DualMetaFix)

**Image Processing (image.py):**
- Device profile selection determines target resolution and palette
- Gamma correction (default 1.8) for better contrast on e-ink
- Auto-cropping with configurable power/minimum area
- Double-page spread detection and splitting
- Palette quantization for older e-ink devices
- Format conversion (PNG/JPEG) with optional mozJPEG optimization

## Device Profiles

Profiles are defined in `image.py` as `ProfileData` class. Each profile specifies:
- Device name
- Screen resolution (width, height)
- Grayscale palette (4/15/16 colors)
- Gamma value

Examples: `KS` (Kindle Scribe: 1860x2480), `KV` (Kindle Voyage: 1072x1448), `KoAO` (Kobo Aura ONE: 1404x1872), `RmkPP` (reMarkable Paper Pro: 1620x2160)

## Important Development Notes

### File Splitting and Chunking

When making changes that affect file size or page count, consider impact on:
- MOBI file size limits (older Kindles have strict limits)
- Batch splitting logic (`--batchsplit` option)
- Chapter boundary alignment
- Memory usage during conversion

### Testing Changes

There is no automated test suite. Manual testing before PRs:
1. Test with multiple input formats (folder, ZIP, CBZ, PDF)
2. Test with different device profiles (especially Kindle Scribe and older devices)
3. Test image processing options (cropping, gamma, contrast)
4. Verify output opens correctly on target devices
5. Check for memory leaks with large files

### Pull Request Guidelines

- Use GitHub's "Sync fork" button to update your fork (not `git merge`)
- Reference example PR for adding UI elements: https://github.com/ciromattia/kcc/pull/785
- Video tutorial for adding checkbox: https://youtu.be/g3I8DU74C7g

## External Dependencies

**Required:**
- Python 3.8+
- PySide6 (Qt6)
- Pillow (PIL)
- PyMuPDF (PDF handling)
- psutil, requests, python-slugify, raven, natsort

**Optional but recommended:**
- 7-Zip (`7z` executable) - for archive extraction (CBR, CB7)
- KindleGen - for MOBI output (auto-detected from Kindle Previewer)
- mozJPEG - for optimized JPEG compression

## Version and Release

Current version is in `kindlecomicconverter/__init__.py` as `__version__`.

Build workflows are defined in `.github/workflows/` for Windows, macOS, and Linux packaging.
