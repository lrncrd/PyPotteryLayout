Export Formats Guide
====================

PyPotteryLayout supports multiple export formats, each optimized for different use cases.

PDF Export
----------

The PDF format is ideal for printing and sharing finished catalogs.

Features
~~~~~~~~

* **Multi-page support**: All pages in single file
* **Vector text**: Searchable and selectable
* **Embedded images**: Self-contained document
* **Print-ready**: Professional quality output
* **Universal compatibility**: Opens everywhere

PDF Settings
~~~~~~~~~~~~

**Resolution (DPI):**
    * 300 DPI: Standard print quality
    * 600 DPI: High-quality printing
    * 150 DPI: Screen viewing/web

**Optimization:**
    * File size vs. quality balance
    * Compression applied automatically
    * Fonts embedded for consistency

Best Practices
~~~~~~~~~~~~~~

1. **For Print:**
   * Use 300+ DPI
   * Include margin borders for trim
   * Test print single page first
   * Consider bleed requirements

2. **For Digital:**
   * 150 DPI usually sufficient
   * Smaller file sizes
   * Optimized for screen viewing
   * Consider page orientation

SVG Export
----------

SVG creates fully editable vector graphics ideal for further editing.

Features
~~~~~~~~

* **Fully editable**: Every element separate
* **Vector format**: Infinite scaling
* **External images**: Linked, not embedded
* **Layer support**: Organized structure
* **Software compatible**: Inkscape, Illustrator

SVG Structure
~~~~~~~~~~~~~

The exported SVG contains:

.. code-block:: text

    /export/project_name/
    ├── project_name.svg
    └── images/
        ├── img_001_pottery.png
        ├── img_002_pottery.png
        └── ...

**Layers Created:**

1. Background layer
2. Images layer
3. Captions layer
4. Scale bar layer
5. Margin guides (if enabled)

Editing SVG Files
~~~~~~~~~~~~~~~~~

**In Inkscape (Recommended):**

1. Open SVG file
2. Ungroup elements if needed
3. Edit text directly
4. Move/resize images
5. Adjust colors/styles
6. Save as Inkscape SVG

**In Adobe Illustrator:**

1. Open SVG file
2. Release clipping masks
3. Edit as needed
4. Maintain links to images
5. Save as AI or SVG

SVG Advantages
~~~~~~~~~~~~~~

* **Editability**: Full post-processing control
* **Scalability**: Resolution independent
* **Flexibility**: Modify any aspect
* **Integration**: Import into other designs
* **Archival**: Future-proof format

JPEG Export
-----------

JPEG format provides standard raster images for broad compatibility.

Features
~~~~~~~~

* **Universal support**: Opens anywhere
* **Reasonable size**: Compressed format
* **Web-ready**: Direct upload capability
* **Simple sharing**: Email, social media

JPEG Settings
~~~~~~~~~~~~~

**Quality Considerations:**

* File size increases with DPI
* 300 DPI for print
* 96-150 DPI for web
* Compression affects quality

**Multi-page Handling:**

.. code-block:: text

    /export/catalog/
    ├── catalog_page_01.jpg
    ├── catalog_page_02.jpg
    └── catalog_page_03.jpg

Best Use Cases
~~~~~~~~~~~~~~

* Quick previews
* Web galleries
* Email attachments
* Social media sharing
* Documentation

PNG Export
----------

While not directly offered in the menu, PNG can be achieved:

1. Export as JPEG
2. Higher quality than JPEG
3. Supports transparency
4. Larger file sizes

Export Location Structure
-------------------------

PyPotteryLayout organizes exports systematically:

Default Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

    /your_project/
    ├── export/
    │   ├── catalog_2024/
    │   │   ├── catalog_2024.svg
    │   │   └── images/
    │   ├── final_pdf/
    │   │   └── final.pdf
    │   └── README.txt

**Organization Benefits:**

* Clean project structure
* Version management
* Easy backup
* No file clutter

Export Workflow Tips
--------------------

Pre-Export Checklist
~~~~~~~~~~~~~~~~~~~~

1. [x] Preview looks correct
2. [x] All images loaded
3. [x] Captions displaying properly
4. [x] Scale bar calibrated
5. [x] Page size appropriate
6. [x] Output format selected

Format Selection Guide
~~~~~~~~~~~~~~~~~~~~~~

**Choose PDF when:**
    * Final output needed
    * Printing required
    * Sharing complete document
    * Professional presentation

**Choose SVG when:**
    * Further editing planned
    * Need vector graphics
    * Custom modifications required
    * Creating templates

**Choose JPEG when:**
    * Quick sharing needed
    * Web upload planned
    * File size matters
    * Compatibility crucial

Post-Export Options
~~~~~~~~~~~~~~~~~~~

**After PDF Export:**
    * Open in PDF reader
    * Check all pages
    * Verify image quality
    * Print test page

**After SVG Export:**
    * Open in vector editor
    * Check layer structure
    * Verify image links
    * Make final adjustments

**After JPEG Export:**
    * Review image quality
    * Check file sizes
    * Batch process if needed
    * Upload or share

Advanced Export Techniques
--------------------------

Batch Processing
~~~~~~~~~~~~~~~~

For multiple catalogs:

1. Process each group separately
2. Use consistent settings
3. Organize by export folders
4. Maintain naming convention

Mixed Format Strategy
~~~~~~~~~~~~~~~~~~~~~

Create multiple formats:

1. **SVG**: Master editable version
2. **PDF**: Distribution version
3. **JPEG**: Preview/web version

Resolution Guidelines
~~~~~~~~~~~~~~~~~~~~~

.. list-table:: DPI Recommendations
   :header-rows: 1

   * - Use Case
     - Recommended DPI
     - File Size
   * - Professional Print
     - 600
     - Large
   * - Standard Print
     - 300
     - Medium
   * - Screen/Web
     - 150
     - Small
   * - Thumbnail
     - 72
     - Minimal

Export Troubleshooting
----------------------

Common Issues
~~~~~~~~~~~~~

**Large file sizes:**
    * Reduce DPI setting
    * Scale images before import
    * Use appropriate format
    * Consider compression

**Missing images in SVG:**
    * Keep images folder together
    * Don't rename image files
    * Use relative paths
    * Verify links intact

**Poor print quality:**
    * Increase DPI to 300+
    * Check original image quality
    * Verify scale settings
    * Test print settings

**Export fails:**
    * Check disk space
    * Verify write permissions
    * Close other applications
    * Try different location

Platform-Specific Notes
-----------------------

Windows
~~~~~~~
* Exports to Documents/export by default
* Paths use backslashes
* May need admin rights for some locations

macOS
~~~~~
* Exports to ~/Documents/export
* Maintains file attributes
* Preview app shows multi-page PDFs

Linux
~~~~~
* Exports to ~/Documents/export
* File permissions preserved
* Various PDF viewers available

Format Conversion
-----------------

Converting Between Formats
~~~~~~~~~~~~~~~~~~~~~~~~~~

**SVG to PDF:**
    * Use Inkscape export
    * Maintain vector quality
    * Embed fonts

**PDF to Images:**
    * Use PDF software
    * Set desired DPI
    * Export pages separately

**SVG to PNG:**
    * Higher quality than JPEG
    * Supports transparency
    * Larger files