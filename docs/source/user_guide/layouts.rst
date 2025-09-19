Layout Modes Guide
==================

PyPotteryLayout offers four distinct layout modes, each optimized for different presentation needs.

Grid Layout
-----------

The Grid layout arranges images in a regular matrix of rows and columns.

Features
~~~~~~~~

* **Regular arrangement**: Uniform rows and columns
* **Center alignment**: Rows centered on page
* **Flexible sizing**: Adapts to image dimensions
* **Multi-page support**: Automatic pagination

Configuration
~~~~~~~~~~~~~

**Essential Settings:**

* **Rows**: Number of rows per page (1-10)
* **Columns**: Maximum images per row (1-10)
* **Auto-fit**: Images smaller than cell size center automatically

**When to Use:**

* Catalog presentations requiring uniformity
* Comparative displays of similar artifacts
* Academic publications with standard formats
* When consistent spacing is important

**Example Configuration:**

.. code-block:: text

    Mode: Grid
    Rows: 4
    Columns: 3
    Result: Up to 12 images per page in a 4×3 grid

Tips for Grid Layout
~~~~~~~~~~~~~~~~~~~~

1. **Aspect Ratios**: Works best with similar aspect ratios
2. **Scaling**: Use consistent scale factor for uniform appearance
3. **Spacing**: Increase spacing for visual breathing room
4. **Page Breaks**: Set images per page for controlled pagination

Puzzle Layout
-------------

The Puzzle layout uses rectangle packing algorithms to maximize space utilization.

Features
~~~~~~~~

* **Optimized packing**: Minimal wasted space
* **Mixed sizes**: Handles varied image dimensions
* **Automatic arrangement**: Algorithm determines positions
* **Efficient use**: Fits more images per page

Configuration
~~~~~~~~~~~~~

**How it Works:**

The puzzle algorithm (MaxRectsBssf) finds optimal positions by:

1. Sorting images by area
2. Finding best position for each image
3. Minimizing gaps between images
4. Creating new pages when full

**When to Use:**

* Collections with varied image sizes
* Maximizing images per page
* Creating compact catalogs
* When space efficiency matters most

**Advantages:**

* 20-30% more efficient than grid
* Handles mixed orientations well
* Reduces page count

Tips for Puzzle Layout
~~~~~~~~~~~~~~~~~~~~~~~

1. **Similar Scales**: Pre-scale images for better packing
2. **Spacing**: Minimal spacing works best (5-10px)
3. **Page Size**: Larger pages show algorithm benefits
4. **Sorting**: Size-based sorting improves results

Masonry Layout
--------------

The Masonry layout arranges images in vertical columns, like Pinterest.

Features
~~~~~~~~

* **Vertical flow**: Images stack in columns
* **Dynamic heights**: Preserves aspect ratios
* **Balanced columns**: Distributes images evenly
* **Natural appearance**: Organic, magazine-style layout

Configuration
~~~~~~~~~~~~~

**Column Settings:**

* Uses the "Columns" value from grid settings
* Default: 3 columns
* Range: 2-6 columns recommended

**Algorithm:**

1. Images placed in shortest column
2. Column heights tracked
3. New page when all columns full
4. Maintains reading order

**When to Use:**

* Web-style presentations
* Mixed portrait/landscape images
* Modern, dynamic layouts
* When variety is desired

Tips for Masonry Layout
~~~~~~~~~~~~~~~~~~~~~~~~

1. **Column Count**: 3-4 columns usually optimal
2. **Image Order**: Important images first
3. **Consistent Widths**: All images sized to column width
4. **Vertical Space**: Allows varied heights

Manual Layout
-------------

The Manual layout provides complete control through drag-and-drop positioning.

Features
~~~~~~~~

* **Full control**: Place images anywhere
* **Drag and drop**: Interactive positioning
* **Overlap support**: Images can overlap
* **Creative freedom**: No algorithmic constraints

How to Use Manual Mode
~~~~~~~~~~~~~~~~~~~~~~~

1. **Enable**: Select "Manual" from layout modes
2. **Preview Panel**: Becomes interactive
3. **Drag Images**: Click and hold to move
4. **Position**: Drop at desired location
5. **Export**: Positions preserved exactly

**Controls:**

* **Left Click**: Select image
* **Drag**: Move selected image
* **Release**: Place at new position

**When to Use:**

* Custom artistic arrangements
* Specific positioning requirements
* Creating poster layouts
* When automation isn't sufficient

Tips for Manual Layout
~~~~~~~~~~~~~~~~~~~~~~~

1. **Grid Snapping**: Mentally align to grid
2. **Margins**: Respect page margins
3. **Overlapping**: Use for creative effects
4. **Templates**: Save successful layouts

Layout Mode Comparison
----------------------

.. list-table:: Layout Mode Comparison
   :header-rows: 1
   :widths: 20 20 20 20 20

   * - Feature
     - Grid
     - Puzzle
     - Masonry
     - Manual
   * - Space Efficiency
     - Moderate
     - High
     - Moderate
     - Variable
   * - Control Level
     - Low
     - Low
     - Low
     - Complete
   * - Best For
     - Catalogs
     - Mixed Sizes
     - Magazines
     - Art
   * - Speed
     - Fast
     - Fast
     - Fast
     - Slow
   * - Predictability
     - High
     - Moderate
     - Moderate
     - N/A

Choosing the Right Layout
--------------------------

Decision Factors
~~~~~~~~~~~~~~~~

**Choose Grid when:**

* Images have similar dimensions
* Formal presentation required
* Comparing similar artifacts
* Standard academic format needed

**Choose Puzzle when:**

* Space is limited
* Image sizes vary significantly
* Maximum efficiency required
* Creating compact catalogs

**Choose Masonry when:**

* Modern presentation desired
* Mixed orientations present
* Web/digital output planned
* Visual flow important

**Choose Manual when:**

* Specific arrangement needed
* Creating poster/display
* Artistic presentation
* Full control required

Multi-Page Handling
-------------------

All layouts support multi-page documents:

Automatic Pagination
~~~~~~~~~~~~~~~~~~~~

* **Grid**: Based on rows × columns
* **Puzzle**: When bin is full
* **Masonry**: When columns filled
* **Manual**: Based on position

Images Per Page Setting
~~~~~~~~~~~~~~~~~~~~~~~~

When set to a specific number:

1. Overrides automatic pagination
2. Enables auto-scaling
3. Consistent page density
4. Better for printing

Page Navigation
~~~~~~~~~~~~~~~

* Preview shows current page
* Navigate with arrow buttons
* Page count updates dynamically
* Export includes all pages

Advanced Layout Techniques
--------------------------

Combining Layouts
~~~~~~~~~~~~~~~~~

Process different image groups separately:

1. Archaeological finds: Grid layout
2. Site photos: Masonry layout
3. Special artifacts: Manual layout
4. Combine PDFs afterward

Layout Preprocessing
~~~~~~~~~~~~~~~~~~~~

Prepare images for better layouts:

1. **Standardize sizes**: Batch resize similar artifacts
2. **Crop consistently**: Remove unnecessary backgrounds
3. **Orient properly**: Rotate before importing
4. **Group by type**: Process categories separately

Optimization Strategies
~~~~~~~~~~~~~~~~~~~~~~~

**For Print:**

* Higher margins (100-150px)
* Moderate spacing (15-20px)
* Consider bleed areas
* Test with printer

**For Digital:**

* Smaller margins (50px)
* Tighter spacing (5-10px)
* Screen-optimized sizes
* Consider aspect ratios

**For Presentations:**

* Larger scale factors
* More spacing
* Fewer per page
* Bold captions