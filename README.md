# PyPotteryLayout
Create artefacts table effortless

<br>

**Archaeological Pottery Cataloging System**

A professional tool for creating layouts of archaeological pottery images with advanced hierarchical sorting, metadata integration, and multiple export formats.

## Features

### 🏺 **Professional Archaeological Focus**
- Designed specifically for pottery and artifact cataloging
- Support for inventory numbers and artifact metadata
- Professional export formats (PNG, JPG, PDF, SVG)

### 📊 **Advanced Hierarchical Sorting**
- **Two-level sorting system**: Primary and secondary sort criteria
- **Primary sorting**: Metadata fields, alphabetical, random, natural ordering
- **Secondary sorting**: None, metadata fields, alphabetical, random, natural ordering
- **Natural ordering**: Smart sorting for inventory numbers (e.g., "Item1", "Item2", "Item10")
- **Random sorting**: For blind study layouts

### 🖼️ **Flexible Layout Modes**
- **Grid Layout**: Organize images in regular rows and columns
- **Puzzle Mode**: Optimize space usage with intelligent packing

### 🎨 **Visual Enhancements**
- **Margin borders**: Visualize page margins with frame overlay
- **Scale bars**: Configurable scale bars with pixels-per-cm control
- **Captions**: Automatic image labeling with metadata
- **Font control**: Adjustable caption font sizes

### 🔧 **Professional Controls**
- **Manual scale entry**: Type exact scale values or use slider
- **DPI control**: Fixed at 300 DPI for publication quality
- **Metadata integration**: Excel (.xlsx) and CSV support
- **Multi-page output**: Automatic page generation for large datasets

### 📤 **Export Formats**
- **PNG**: High-quality raster images
- **JPG**: Compressed raster format
- **PDF**: Multi-page document format
- **SVG**: Vector format for scalable graphics

## Installation

1. **Clone or download** the project files
2. **Install Python dependencies**:
   ```bash
   pip install Pillow openpyxl rectpack
   ```
3. **Run the application**:
   ```bash
   python gui_app.py
   ```

## Usage

### Basic Workflow

1. **Select Images Folder**: Choose folder containing your pottery images
2. **Choose Export Format**: PNG, JPG, PDF, or SVG
3. **Select Output File**: Where to save the final layout
4. **Optional**: Load metadata Excel file for enhanced sorting and captions

### Layout Configuration

- **Mode**: Choose Grid or Puzzle layout
- **Page Format**: A4 or A3
- **Primary Sorting**: How to order images initially
- **Secondary Sorting**: How to order within primary groups

### Visual Settings

- **Image Scale**: Manual entry + slider control (0.1x to 3.0x)
- **Page Margins**: Spacing around page edges
- **Show Margin Border**: Visual frame to see margins
- **Image Spacing**: Gap between images

### Additional Features

- **Add Captions**: Label images with filenames/metadata
- **Font Size**: Adjustable caption text size
- **Add Scale Bar**: Reference scale for measurements
- **Pixels per cm**: Calibrate scale bar accuracy

## Metadata Format

Create an Excel file (.xlsx) with:
- **Column A**: Image filename (with extension)
- **Column B+**: Any metadata fields (e.g., "Type", "Period", "Inventory_Number")

Example:
```
Filename        | Type    | Period  | Inventory_Number
0001.jpg        | Bowl    | Roman   | INV-001
0002.jpg        | Jar     | Roman   | INV-002
0003.jpg        | Bowl    | Medieval| INV-010
```

## Hierarchical Sorting Examples

### Example 1: Type → Inventory Number
- **Primary**: "Type" (metadata field)
- **Secondary**: "Inventory_Number" (metadata field)
- **Result**: All bowls together, then jars, with inventory numbers in order within each group

### Example 2: Period → Random
- **Primary**: "Period" (metadata field) 
- **Secondary**: "random"
- **Result**: Items grouped by period, but random order within each period (useful for blind studies)

### Example 3: Natural Name Sorting
- **Primary**: "natural_name"
- **Result**: Smart sorting of filenames like "Item1.jpg", "Item2.jpg", "Item10.jpg" in correct numerical order

## Technical Details

### File Support
- **Images**: JPG, PNG, TIFF, BMP, GIF
- **Metadata**: Excel (.xlsx), CSV
- **Output**: PNG, JPG, PDF, SVG

### System Requirements
- **Python**: 3.7+
- **Platform**: macOS, Windows, Linux
- **Memory**: Sufficient for loading all images simultaneously

### Font Handling
- Automatic font discovery across platforms
- macOS: System fonts in `/System/Library/Fonts/`
- Cross-platform fallbacks ensure consistent rendering

## Advanced Features

### SVG Export
- Vector format for infinite scalability
- Embedded high-quality raster images
- Professional metadata in SVG headers
- Fallback to PNG if SVG export fails

### Margin Visualization
- Optional border overlay shows exactly where margins are
- Helps with layout planning and print preparation
- Light gray outer border, gray inner content area

### Scale Bar Calibration
- Configure pixels-per-cm for accurate measurements
- Scale bars automatically adjust for image scaling
- Essential for archaeological documentation

## Troubleshooting

### Common Issues

1. **"No images found"**: Check that image folder contains supported formats
2. **Font sizing not working**: Verify system fonts are accessible
3. **Metadata not loading**: Ensure Excel file has proper column structure
4. **SVG export fails**: Will automatically fallback to PNG format

### Performance Tips

- For large image sets, use lower scale factors
- Puzzle mode may be slower than Grid mode for many images
- Close other applications if running low on memory

## Version History

### v1.0 (Current)
- Complete English translation
- Professional header with app branding
- SVG export support
- Hierarchical sorting system
- Margin border visualization
- Manual scale controls
- Fixed 300 DPI output
- Archaeological workflow optimization

## Credits

Developed for archaeological pottery cataloging and documentation workflows.

**Technologies**: Python, Pillow (PIL), tkinter, openpyxl, rectpack

**License**: See LICENSE file

---

