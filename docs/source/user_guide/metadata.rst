Metadata and Captions Guide
============================

This guide explains how to use metadata files to add rich captions and custom sorting to your pottery catalogs.

Understanding Metadata
----------------------

Metadata provides additional information about your images:

* **Captions**: Descriptions, measurements, dates
* **Sorting fields**: Categories, periods, types
* **References**: Catalog numbers, locations
* **Attributes**: Material, technique, provenance

Metadata File Format
--------------------

PyPotteryLayout accepts Excel (.xlsx) files with specific structure:

Basic Structure
~~~~~~~~~~~~~~~

.. code-block:: text

    | Filename      | Description        | Period      | Location    | Catalog_No |
    |---------------|-------------------|-------------|-------------|------------|
    | bowl_001.jpg  | Red-figure bowl   | 450-400 BCE | Athens      | CAT-0234   |
    | jar_002.jpg   | Storage amphora   | 500-450 BCE | Corinth     | CAT-0235   |
    | plate_003.jpg | Black-glaze plate | 400-350 BCE | Athens      | CAT-0236   |

**Requirements:**

1. **First column**: Must contain image filenames
2. **Headers**: First row contains field names
3. **Matching**: Filenames must match exactly (case-insensitive)

Creating Metadata Files
------------------------

Using Excel
~~~~~~~~~~~

1. Open Microsoft Excel or LibreOffice Calc
2. Create headers in row 1
3. Enter filenames in column A
4. Add metadata in subsequent columns
5. Save as .xlsx format

Using CSV (Alternative)
~~~~~~~~~~~~~~~~~~~~~~~~

1. Create CSV with comma separation
2. Include headers as first line
3. Save with .csv extension
4. Import to Excel if needed

Example Templates
~~~~~~~~~~~~~~~~~

**Archaeological Catalog:**

.. code-block:: text

    Filename | Type | Period | Culture | Dimensions | Find_Location | Catalog_ID
    pot1.jpg | Amphora | LBA | Minoan | H:45cm | Knossos | KN-1234

**Museum Collection:**

.. code-block:: text

    Filename | Accession | Artist | Date | Medium | Provenance | Condition
    vase1.jpg | 2024.1.1 | Unknown | 450 BCE | Ceramic | Donated 1925 | Good

Using Metadata in Captions
---------------------------

Simple Captions
~~~~~~~~~~~~~~~

With "Add Captions" checked, metadata appears as:

.. code-block:: text

    filename.jpg
    Field1: Value1
    Field2: Value2

Formatting Captions
~~~~~~~~~~~~~~~~~~~

Caption appearance is controlled by:

* **Font Size**: Text size (8-24pt)
* **Caption Padding**: Space around text
* **First Line**: Filename (bold)
* **Subsequent Lines**: Metadata fields

Selective Fields
~~~~~~~~~~~~~~~~~

Not all metadata needs to appear in captions:

* Include display fields: Description, Date
* Exclude internal fields: Internal_ID, Notes
* Use meaningful headers: "Period" not "col_B"

Custom Sorting with Metadata
-----------------------------

Primary and Secondary Sorting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyPotteryLayout supports two-level hierarchical sorting:

**Primary Sort:**
    * Main grouping criteria
    * Options: Any metadata field

**Secondary Sort:**
    * Sorting within groups
    * Applied after primary sort

Sorting Examples
~~~~~~~~~~~~~~~~

**Chronological Catalog:**

.. code-block:: text

    Primary: Period
    Secondary: Type
    Result: Images grouped by period, then by type within each period

**Geographic Organization:**

.. code-block:: text

    Primary: Region
    Secondary: Site
    Result: Images grouped by region, then by site

**Typological Arrangement:**

.. code-block:: text

    Primary: Category
    Secondary: natural_name
    Result: Images grouped by category, naturally sorted within

Special Sorting Options
~~~~~~~~~~~~~~~~~~~~~~~~

* **alphabetical**: A-Z by filename
* **natural_name**: Handles numbers properly (1, 2, 10, not 1, 10, 2)
* **random**: Randomize order
* **none**: Maintain existing order

Advanced Metadata Techniques
-----------------------------

Multi-line Captions
~~~~~~~~~~~~~~~~~~~~

Create rich captions with multiple fields:

.. code-block:: text

    Metadata columns:
    - Description: "Red-figure kylix"
    - Artist: "Python Painter"
    - Date: "350-340 BCE"
    - Museum: "British Museum"

    Result caption:
    kylix_001.jpg
    Description: Red-figure kylix
    Artist: Python Painter
    Date: 350-340 BCE
    Museum: British Museum

Conditional Fields
~~~~~~~~~~~~~~~~~~

Leave cells empty to exclude from captions:

* Blank cells don't appear
* Useful for varied collections
* Maintains clean appearance

Special Characters
~~~~~~~~~~~~~~~~~~

Supports Unicode for special characters:

* Greek: alpha, beta, gamma, delta
* Measurements: diameter, plus/minus, approximately
* Symbols: dagger, double dagger, section, paragraph

Metadata Best Practices
------------------------

File Naming Conventions
~~~~~~~~~~~~~~~~~~~~~~~~

**Recommended patterns:**

.. code-block:: text

    Simple:       pot_001.jpg, pot_002.jpg
    Descriptive:  amphora_corinth_01.jpg
    Catalog:      BM_1842_0728_784.jpg
    Hierarchical: type_period_number.jpg

Data Organization
~~~~~~~~~~~~~~~~~

**Essential Fields:**

1. Identification (catalog number)
2. Classification (type, category)
3. Dating (period, specific date)
4. Measurements (height, diameter)
5. Provenance (findspot, collection)

**Optional Fields:**

1. Description (free text)
2. Condition (preservation state)
3. Bibliography (references)
4. Technical (fabric, technique)
5. Notes (additional info)

Data Validation
~~~~~~~~~~~~~~~

Ensure consistency:

* **Dates**: Use consistent format (BCE/CE or BC/AD)
* **Measurements**: Include units (cm, mm)
* **Names**: Standardize spelling
* **Categories**: Use controlled vocabulary

Troubleshooting Metadata Issues
--------------------------------

Common Problems
~~~~~~~~~~~~~~~

**Images not matching metadata:**

* Check filename spelling exactly
* Remove file extensions if included
* Ensure no extra spaces
* Case doesn't matter

**Metadata not loading:**

* Verify Excel file format (.xlsx)
* Check first column has filenames
* Ensure headers in first row
* No merged cells

**Sorting not working:**

* Check field name matches exactly
* Remove special characters from headers
* Ensure data type consistency
* No empty header cells

Excel File Tips
~~~~~~~~~~~~~~~

**Optimization:**

1. Keep files under 10MB
2. Avoid complex formulas
3. Remove formatting/colors
4. Use simple sheet names

**Compatibility:**

* Save as .xlsx (not .xls)
* Avoid macros
* No password protection
* Single sheet preferred

Metadata Workflow Examples
--------------------------

Academic Publication
~~~~~~~~~~~~~~~~~~~~

1. **Prepare Excel** with scholarly data
2. **Include fields**: Type, Date, Provenance, Museum number
3. **Sort by**: Period (primary), Type (secondary)
4. **Export with**: Full captions for reference

Museum Display
~~~~~~~~~~~~~~~

1. **Simple metadata**: Name, Date, Gallery location
2. **Large captions**: 16pt font for readability
3. **Sort by**: Gallery, then accession number
4. **Clean layout**: Minimal technical details

Digital Archive
~~~~~~~~~~~~~~~~

1. **Comprehensive metadata**: All available fields
2. **Small captions**: Space-efficient
3. **Sort by**: Catalog number
4. **Include**: Database IDs for cross-reference

Field Excavation
~~~~~~~~~~~~~~~~~

1. **Field data**: Context, Level, Find number
2. **Technical info**: Fabric, Weight, Dimensions
3. **Sort by**: Context, then find number
4. **Document**: Stratigraphic relationships