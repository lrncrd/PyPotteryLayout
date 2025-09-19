.. PyPotteryLayout documentation master file

=================================================
PyPotteryLayout Documentation
=================================================

Welcome to PyPotteryLayout's documentation! PyPotteryLayout is a comprehensive Python desktop application
designed for creating publication-quality layouts of archaeological pottery and artifact images.


Overview
========

PyPotteryLayout provides automated grid and puzzle layouts with captions, scale bars, and metadata integration
for academic publications. It offers both a user-friendly GUI and a powerful API for programmatic use.

Key Features
------------

* **Multiple Layout Modes**: Grid, Puzzle (optimized), Masonry, and Manual positioning
* **Automatic Image Scaling**: Optimizes image sizes to fill pages without empty spaces
* **Multi-page Support**: Handles large collections across multiple pages
* **Metadata Integration**: Excel/CSV support for captions and custom sorting
* **Scale Bar Generation**: Automatic scale bars with configurable measurements
* **Multiple Export Formats**: PDF, SVG (editable), JPEG with professional quality
* **Cross-platform**: Works on Windows, macOS, and Linux

Documentation Contents
======================

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/installation
   user_guide/quickstart
   user_guide/interface
   user_guide/layouts
   user_guide/metadata
   user_guide/export
   user_guide/tips

.. toctree::
   :maxdepth: 2
   :caption: API Documentation

   api/modules
   api/backend_logic
   api/gui_app

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources

   changelog
   contributing
   license

Quick Start Example
===================

Using the GUI
-------------

1. Launch the application::

    python gui_app.py

2. Select your images folder
3. Choose a layout mode (Grid, Puzzle, Masonry, or Manual)
4. Configure settings (margins, spacing, scale)
5. Export to your desired format

Using the API
-------------

.. code-block:: python

    import backend_logic

    # Set up parameters
    params = {
        'input_folder': '/path/to/images',
        'output_file': 'catalog.pdf',
        'mode': 'grid',
        'grid_rows': 4,
        'grid_cols': 3,
        'margin_px': 50,
        'spacing_px': 10,
        'add_scale_bar': True,
        'scale_bar_cm': 5,
        'pixels_per_cm': 118
    }

    # Run the layout process
    backend_logic.run_layout_process(params)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`