Installation Guide
==================

This guide will walk you through installing PyPotteryLayout on your system.

System Requirements
-------------------

* Python 3.7 or higher
* Operating System: Windows, macOS, or Linux
* At least 4GB RAM (8GB recommended for large image collections)
* 500MB free disk space

Installing from Source
----------------------

1. **Clone the repository**::

    git clone https://github.com/enzococca/PyPotteryLayout.git
    cd PyPotteryLayout

2. **Create a virtual environment** (recommended)::

    python -m venv venv

    # On Windows:
    venv\Scripts\activate

    # On macOS/Linux:
    source venv/bin/activate

3. **Install dependencies**::

    pip install -r requirements.txt

Dependencies
------------

PyPotteryLayout requires the following Python packages:

* **Pillow** (>=9.0.0): Image processing and manipulation
* **tkinter**: GUI framework (usually included with Python)
* **rectpack** (>=0.2.2): Rectangle packing algorithms for puzzle layouts
* **openpyxl** (>=3.0.0): Excel file reading for metadata
* **reportlab** (optional): PDF generation with vector graphics
* **cairosvg** (optional): SVG to other format conversion

Installing Optional Dependencies
---------------------------------

For enhanced PDF and SVG support::

    pip install reportlab cairosvg

For development and documentation::

    pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

Platform-Specific Notes
------------------------

Windows
~~~~~~~

* Ensure Python is added to your PATH during installation
* You may need to install Visual C++ Redistributable for some dependencies

macOS
~~~~~

* Install Python via Homebrew for best compatibility::

    brew install python

* Tkinter should be included with the Python installation

Linux
~~~~~

* Install tkinter if not present::

    # Ubuntu/Debian:
    sudo apt-get install python3-tk

    # Fedora:
    sudo dnf install python3-tkinter

    # Arch:
    sudo pacman -S tk

Verifying Installation
----------------------

To verify that PyPotteryLayout is properly installed::

    python -c "import backend_logic; print('Backend OK')"
    python -c "import gui_app; print('GUI OK')"

If both commands print "OK", the installation is successful.

Running the Application
-----------------------

To launch the GUI application::

    python gui_app.py

Building Standalone Executable
------------------------------

To create a standalone executable for distribution:

1. **Install PyInstaller**::

    pip install pyinstaller

2. **Run the build script**::

    python build_exe.py

The executable will be created in the ``dist`` folder.

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**ImportError: No module named 'PIL'**
    Install Pillow: ``pip install Pillow``

**ImportError: No module named '_tkinter'**
    Install tkinter for your platform (see Platform-Specific Notes)

**Font-related warnings**
    The application will use fallback fonts if system fonts are not found.
    This is normal and doesn't affect functionality.

**Memory errors with large images**
    Try reducing the scale factor or processing fewer images at once.

Getting Help
~~~~~~~~~~~~

If you encounter issues:

1. Check the GitHub Issues page
2. Ensure all dependencies are correctly installed
3. Try running in a fresh virtual environment