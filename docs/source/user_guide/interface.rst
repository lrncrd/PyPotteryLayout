User Interface Guide
====================

This guide provides a detailed overview of the PyPotteryLayout graphical user interface.

Main Window Layout
------------------

The application window is divided into three main areas:

1. **Control Panel** (Left): Contains all settings in tabbed sections
2. **Preview Panel** (Right): Real-time preview of your layout
3. **Status Bar** (Bottom): Shows progress and messages

Control Panel Sections
----------------------

The control panel uses tabs to organize features:

Input/Output Tab
~~~~~~~~~~~~~~~~

**Images Folder**
    * Select the folder containing your pottery images
    * Displays the selected path
    * Updates preview automatically

**Metadata File** (Optional)
    * Load Excel file with image metadata
    * Must have filenames in first column
    * Additional columns for captions and sorting

**Sort Images**
    * Primary sorting field
    * Secondary sorting field (hierarchical)
    * Options: Alphabetical, Natural, Random, or metadata fields

**Output File**
    * Choose save location and filename
    * Extension determines format (.pdf, .svg, .jpg)
    * Saves to ``export`` subfolder

**Output Settings**
    * DPI: Resolution for raster exports (default: 300)
    * Page Format: A4, A3, HD, 4K, Letter, or Custom
    * Custom Size: Width × Height in pixels

Layout Configuration Tab
~~~~~~~~~~~~~~~~~~~~~~~~~

**Layout Mode**
    * Grid: Regular rows and columns
    * Puzzle: Optimized packing
    * Masonry: Vertical columns
    * Manual: Drag-and-drop positioning

**Grid Settings** (Grid mode only)
    * Rows: Number of rows per page
    * Columns: Number of columns per row

**Spacing and Margins**
    * Margins (px): Distance from page edges
    * Image Spacing (px): Gap between images
    * Show Margin Border: Visual guide in output

**Scale Settings**
    * Scale Factor: Resize multiplier (0.1-5.0)
    * Images per Page: Auto-scaling trigger
    * Auto-scale indicator in preview

**Caption Settings**
    * Add Captions: Include text under images
    * Font Size: Caption text size
    * Caption Padding: Space around text

**Scale Bar Settings**
    * Add Scale Bar: Include measurement reference
    * Bar Length (cm): Physical measurement
    * Pixels per cm: Calibration value

Preview Panel Features
----------------------

The preview panel provides immediate visual feedback:

Navigation Controls
~~~~~~~~~~~~~~~~~~~

Located at the top of the preview:

* **Page Counter**: Shows "Page X of Y"
* **Previous/Next Buttons**: Navigate multi-page layouts
* **Status Text**: Shows loading info and auto-scale factor

Preview Canvas
~~~~~~~~~~~~~~

The main preview area shows:

* **White background**: Represents the page
* **Margin guides**: Dotted lines (if enabled)
* **Image thumbnails**: Scaled representations
* **Layout preview**: Real-time arrangement

Manual Mode Features
~~~~~~~~~~~~~~~~~~~~

When Manual layout is selected:

1. **Drag to Move**: Click and drag images
2. **Visual Feedback**: Selected image highlighted
3. **Position Memory**: Preserves custom positions
4. **Reset Option**: Return to automatic layout

Working with Different Tabs
----------------------------

Efficient Tab Usage
~~~~~~~~~~~~~~~~~~~

1. **Start with Input/Output**: Set files and basic options
2. **Move to Layout Configuration**: Fine-tune appearance
3. **Return to Input/Output**: Final export settings

Tab Memory
~~~~~~~~~~

The application remembers your settings between tabs:

* Changes are preserved when switching
* Preview updates reflect all settings
* Export uses current configuration

Status Messages and Progress
-----------------------------

The status bar provides feedback:

**During Loading**
    * "Loading images from: [path]"
    * "Loaded X images"
    * "Loading metadata..."

**During Processing**
    * Progress percentage
    * Current operation
    * Completion message

**Error Messages**
    * Clear error descriptions
    * Suggested solutions
    * File path information

Advanced Interface Features
---------------------------

Responsive Design
~~~~~~~~~~~~~~~~~

* Preview scales to window size
* Controls adjust to content
* Scrollable sections for small screens

Value Validation
~~~~~~~~~~~~~~~~

Entry fields validate input:

* Numeric fields accept only numbers
* Ranges enforced (e.g., scale 0.1-5.0)
* Invalid input highlighted

Dynamic Updates
~~~~~~~~~~~~~~~

Changes trigger immediate updates:

* Preview refreshes on setting changes
* Page count updates with layout
* Auto-scale calculates in real-time

Context-Sensitive Controls
~~~~~~~~~~~~~~~~~~~~~~~~~~

Controls show/hide based on mode:

* Grid settings only in Grid mode
* Manual controls only in Manual mode
* Relevant options stay visible

Tooltips and Help
-----------------

Hover Information
~~~~~~~~~~~~~~~~~

Key controls include tooltips:

* Scale factor explanation
* Metadata file format
* Export format details

Visual Indicators
~~~~~~~~~~~~~~~~~

* **Checkboxes**: Clear on/off states
* **Radio buttons**: Exclusive selection
* **Entry fields**: Focused highlighting

Color Coding
~~~~~~~~~~~~

* **Active controls**: Standard colors
* **Disabled controls**: Grayed out
* **Error states**: Red highlighting

Best Practices for Interface Use
---------------------------------

Workflow Tips
~~~~~~~~~~~~~

1. **Preview First**: Always check preview before export
2. **Test Settings**: Try different modes with preview
3. **Save Configurations**: Note successful settings

Performance Tips
~~~~~~~~~~~~~~~~

* **Large Collections**: Process in batches
* **High Resolution**: Reduce scale for preview
* **Multiple Pages**: Use page navigation

Troubleshooting Interface Issues
---------------------------------

Common Problems
~~~~~~~~~~~~~~~

**Preview not updating**
    * Check if images loaded successfully
    * Verify folder contains valid images
    * Try refreshing with different settings

**Controls not responding**
    * Ensure process isn't running
    * Check for error messages
    * Restart application if needed

**Layout looks wrong**
    * Verify scale factor is appropriate
    * Check margins aren't too large
    * Ensure images fit page size

Keyboard Navigation
-------------------

The interface supports standard keyboard navigation:

* **Tab**: Move forward through controls
* **Shift+Tab**: Move backward
* **Space**: Toggle checkboxes/radio buttons
* **Enter**: Apply entry field values
* **Arrow keys**: Navigate dropdowns

Accessibility Features
----------------------

The interface includes accessibility support:

* **High contrast**: Clear control boundaries
* **Font scaling**: Readable at various sizes
* **Logical tab order**: Sequential navigation
* **Status announcements**: Clear feedback