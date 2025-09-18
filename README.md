# PyPotteryLayout

<div align="center">

<img src="imgs/LogoLayout.png" width="500"/>

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE) 
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/lrncrd/PyPotteryLayout)

Create artefacts table effortless

</div>


## Introduction

Producing publication-quality catalogues of archaeological artefacts is often a time-consuming process, requiring both precision in presentation and consistency across large datasets. **PyPotteryLayout** is designed to streamline this workflow by combining automation with professional publishing standards.

Instead of manually arranging artefact images, adjusting captions, and aligning scale bars, researchers can generate layouts in minutes while retaining full control over the final output. The software produces clean, publication-ready figures that meet the expectations of academic journals, site reports, and edited volumes. Its vector-based exports (SVG) ensure that images, scale bars, and captions remain sharp and editable at any stage of the editorial process.

This efficiency makes the tool particularly valuable for projects with large assemblages, where hundreds of objects must be documented quickly without sacrificing visual quality. At the same time, the flexibility of SVG editing allows archaeologists and illustrators to refine details, translate captions, or adjust layouts for specific publication styles.


## 🏺 Features

### Core Functionality
- **Automatic Layout Generation**: Grid-based and optimized puzzle layouts
- **Multi-Format Export**: SVG, PDF and JPG
- **Effortless Output**: Quick export with minimal clicks
- **Metadata Integration**: Excel/CSV metadata support for captions and sorting
- **Flexible Sorting**: Multiple sorting options including custom metadata fields

### Advanced Layout Options
- **Grid Layout**: Customizable rows and columns with precise control
- **Puzzle Layout**: Optimized space utilization algorithm
- **Scale Bars**: Automatic generation with customizable measurements
- **Caption System**: Editable text with metadata integration
- **Margin Management**: Professional borders and spacing controls

## 🚀 Quick Start

### Download & Run (Windows)

<div align="center">

<img src="imgs/icon_app.png" width="250"/>

</div>

1. Download `PyPotteryLayout.exe` from [Releases](../../releases)
2. Run directly - no installation required
3. Select image folder and configure layout
4. Export as SVG or PDF

### From Source
```bash
# Clone repository
git clone https://github.com/lrncrd/PyPotteryLayout.git
cd PyPotteryLayout

# Install dependencies
pip install -r requirements.txt

# Run application
python gui_app.py
```

## 📋 System Requirements

- **Python**: 3.11+ (if running from source)
- **Operating System**: Windows 10+ (executable), Windows/macOS/Linux (source)
- **Memory**: 2GB+ RAM recommended for large image sets
- **Dependencies**: PIL/Pillow, tkinter, openpyxl

## 🎯 Usage Guide

### Basic Workflow
1. **Select Images**: Choose folder containing pottery images
2. **Configure Layout**: Set grid dimensions or use puzzle optimization
3. **Add Metadata**: Optional Excel file with captions and sorting data
4. **Customize Output**: Scale, margins, captions, scale bars
5. **Export**: Choose SVG for editing or PDF for publication

### Metadata Format

Excel/CSV files should have:
- First column: Image filenames (with extensions)
- Additional columns: Custom data for captions and sorting

```
Filename    | Site     | Period  | Description
IMG001.jpg  | Site A   | Roman   | Storage jar
IMG002.jpg  | Site B   | Medieval| Bowl fragment
```


## 🔧 Advanced Features

### SVG Editing Workflow
1. Export as SVG format
2. Open in Inkscape (free, recommended) or Illustrator
3. Edit text, move objects, adjust colors
4. Keep `images/` folder next to SVG file
5. All elements remain fully editable


## 📊 Recent Updates

### v0.1.1

- Improved SVG export quality (all elements are now editable)
- Added option to show table numbering
- Added Masonry layout option (experimental)
- Added preview of layout in GUI

### v0.1.0

- First public release with core features

## 🎯 Future Plans

* [ ] Add usage examples
* [ ] We're looking for your suggestions!

If you have suggestions or need help, please open an issue on GitHub!







## 👥 Contributors

<a href="https://github.com/lrncrd/PyPotteryLayout/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=lrncrd/PyPotteryLayout" />
</a>

---

Developed with ❤️ by [Lorenzo Cardarelli](https://github.com/lrncrd)
