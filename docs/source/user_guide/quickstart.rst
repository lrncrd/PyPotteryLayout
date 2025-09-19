Quick Start Guide
=================

This guide will help you create your first pottery catalog layout in minutes.

Step 1: Prepare Your Images
----------------------------

1. **Organize your images** in a single folder
2. **Supported formats**: JPG, PNG, GIF, BMP, TIFF
3. **Naming convention**: Use descriptive filenames (they'll appear in captions)

.. tip::
   Use consistent naming like ``pottery_001.jpg``, ``pottery_002.jpg`` for natural sorting

Step 2: Launch the Application
-------------------------------

Run the application from the command line::

    python gui_app.py

The main window will open with two tabs:

* **Input/Output**: File selection and export settings
* **Layout Configuration**: Layout mode and parameters

Step 3: Select Your Images
---------------------------

1. Click **Browse...** next to "Images Folder"
2. Navigate to your images folder
3. Select the folder containing your pottery images

The preview panel will immediately load thumbnails of your images.

Step 4: Choose Layout Mode
---------------------------

In the Layout Configuration tab, select your preferred mode:

**Grid Layout** (Default)
    * Images arranged in rows and columns
    * Best for uniform presentations
    * Set rows and columns in Preview Controls

**Puzzle Layout**
    * Optimized space utilization
    * Automatically fits images like a puzzle
    * Great for mixed image sizes

**Masonry Layout**
    * Pinterest-style vertical columns
    * Images flow naturally
    * Good for varied aspect ratios

**Manual Layout**
    * Drag and drop images in preview
    * Full control over positioning
    * Perfect for custom arrangements

Step 5: Configure Basic Settings
---------------------------------

Essential settings to adjust:

Page Settings
~~~~~~~~~~~~~

* **Page Format**: A4 or A3 (default: A4)
* **Margins**: Space from page edge (default: 50px)
* **Image Spacing**: Gap between images (default: 10px)
* **Images per Page**: 0 for automatic, or specify exact number

Scale Settings
~~~~~~~~~~~~~~

* **Scale Factor**: Resize all images (default: 0.4x)
* **Auto-scaling**: Enabled when Images per Page > 0

.. note::
   With auto-scaling, images automatically resize to fill the page optimally

Step 6: Add Captions and Scale Bar
-----------------------------------

In the Details section:

**Captions**
    * Check "Add Captions" to include image filenames
    * Load metadata Excel for custom captions
    * Adjust font size and padding

**Scale Bar**
    * Check "Add Scale Bar" for archaeological scale
    * Set length in centimeters (default: 5cm)
    * Configure pixels per cm based on your images

Step 7: Export Your Layout
---------------------------

1. Click **Save as...** to choose output location
2. Select format:

   * **PDF**: Best for printing and sharing
   * **SVG**: Fully editable vector format
   * **JPEG**: Standard image format

3. Click **Export Layout**

The process will run and save to the ``export`` folder.

Complete Example Workflow
--------------------------

Here's a typical workflow for creating a pottery catalog:

.. code-block:: text

    1. Images folder: /Documents/pottery_photos/
       ├── bowl_001.jpg
       ├── bowl_002.jpg
       └── jar_001.jpg

    2. Settings:
       - Mode: Grid (3 columns × 4 rows)
       - Page: A4
       - Margins: 50px
       - Scale: 0.5x
       - Add Scale Bar: Yes (5cm)
       - Add Captions: Yes

    3. Output: catalog.pdf
       - Professional layout
       - Scale bar at bottom
       - Captions under each image

Tips for Best Results
----------------------

1. **Consistent Image Quality**: Use images with similar resolution
2. **Batch Processing**: Process similar artifacts together
3. **Test First**: Try with a few images before processing large collections
4. **Preview Usage**: Use preview to test settings before export
5. **Save Settings**: Keep note of successful configurations

Using the Preview Panel
------------------------

The preview panel shows real-time updates:

* **Navigation**: Use Previous/Next buttons to navigate pages
* **Page Info**: Shows current page and image count
* **Auto-scaling**: Displays calculated scale factor
* **Manual Mode**: Drag images to reposition

Keyboard Shortcuts
------------------

While the application doesn't have extensive shortcuts, you can:

* **Tab**: Navigate between controls
* **Enter**: Apply values in entry fields
* **Space**: Toggle checkboxes when focused

Next Steps
----------

Now that you've created your first layout:

1. Explore :doc:`layouts` for advanced layout options
2. Learn about :doc:`metadata` for custom captions
3. Read :doc:`export` for format-specific tips
4. Check :doc:`tips` for professional results