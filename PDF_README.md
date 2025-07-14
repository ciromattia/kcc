# KCC PDF Output Support for reMarkable

This enhanced version of KCC (Kindle Comic Converter) adds support for direct PDF output, specifically optimized for reMarkable devices.

## 🆕 What's New

- **PDF Output Format**: Convert CBR/CBZ comics directly to PDF
- **reMarkable Optimization**: Automatic PDF format selection for reMarkable devices
- **Device-Specific Sizing**: Proper resolution targeting for reMarkable 1, 2, and Paper Pro

## 📱 Supported reMarkable Devices

- **reMarkable 1** (`Rmk1`): 1404×1872 resolution
- **reMarkable 2** (`Rmk2`): 1404×1872 resolution  
- **reMarkable Paper Pro** (`RmkPP`): 1620×2160 resolution

## 🚀 Quick Start

### Command Line Usage

```bash
# Convert CBZ to PDF for reMarkable Paper Pro (default)
python3 kcc-c2e.py --format PDF --profile RmkPP your_comic.cbz

# Convert CBR to PDF for reMarkable 2
python3 kcc-c2e.py --format PDF --profile Rmk2 your_comic.cbr

# Use the convenience script
python3 convert_to_pdf.py your_comic.cbz
```

### GUI Usage

1. Launch KCC GUI: `python3 kcc.py`
2. Select your reMarkable device from the device dropdown
3. The format will automatically default to PDF
4. Add your CBR/CBZ files and click Convert

## 📋 Format Options

The `--format` parameter now accepts:
- `Auto` - Automatically selects PDF for reMarkable devices
- `MOBI` - Amazon Kindle format
- `EPUB` - Standard e-book format
- `CBZ` - Comic archive format
- `PDF` - **NEW**: Portable Document Format (great for reMarkable!)
- `KFX` - Kindle KFX format
- `MOBI+EPUB` - Generate both formats

## 🔧 Implementation Details

### PDF Generation

The PDF output is created using PIL/Pillow with the following optimizations:

- **Color Management**: Automatic RGB conversion for compatibility
- **Resolution**: Device-specific targeting (100 DPI base)
- **Compression**: Optimized for file size while maintaining quality
- **Page Order**: Maintains original comic reading order

### File Structure

The PDF conversion happens in the `buildPDF()` function in `comic2ebook.py`:

```python
def buildPDF(path, title, cover=None):
    """Build a PDF file from processed comic images"""
    # Processes images from the OEBPS/Images directory
    # Converts to RGB format for PDF compatibility  
    # Combines into multi-page PDF with proper ordering
```

### Device Profiles

reMarkable devices now default to PDF format:

```python
# In KCC_gui.py
"reMarkable Paper Pro": {
    'DefaultFormat': 3,  # PDF format index
    'Label': 'RmkPP'
}
```

## 🎯 Optimizations for reMarkable

1. **Grayscale Conversion**: Automatic for reMarkable 1 & 2
2. **Color Support**: Enabled for reMarkable Paper Pro
3. **Resolution Targeting**: Device-specific pixel dimensions
4. **File Size**: Optimized PDF compression

## 🧪 Testing

Run the included test script to verify PDF functionality:

```bash
python3 test_pdf_conversion.py
```

This will:
- Create sample comic images
- Test PDF generation
- Verify output quality and file size

## 📝 Example Conversion

```bash
# Input: manga_volume_01.cbz (50 MB)
# Output: manga_volume_01.pdf (12 MB, optimized for reMarkable Paper Pro)

python3 kcc-c2e.py --format PDF --profile RmkPP manga_volume_01.cbz
```

## 🔍 Troubleshooting

### Common Issues

**PDF not created**: Check that Pillow is installed: `pip install Pillow`

**Large file size**: Use `--targetsize` to limit MB: `--targetsize 50`

**Image quality**: Adjust gamma correction: `--gamma 1.0`

### Dependencies

The PDF functionality requires:
- `Pillow >= 11.3.0` (for PDF generation)
- Standard KCC dependencies

## 🤝 Contributing

The PDF implementation includes:

1. **Format Support** (`comic2ebook.py`):
   - Added PDF to format choices
   - Implemented `buildPDF()` function
   - Updated `makeBook()` workflow

2. **GUI Integration** (`KCC_gui.py`):
   - Added PDF to format dropdown
   - Set PDF as default for reMarkable devices
   - Updated progress messages

3. **Profile Configuration**:
   - Auto-select PDF for reMarkable profiles
   - Maintain backward compatibility

This implementation follows KCC's existing patterns and integrates seamlessly with the current workflow.

## 📄 License

Same as the original KCC project - see LICENSE.txt for details.
