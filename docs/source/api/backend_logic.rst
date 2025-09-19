backend_logic module
====================

.. automodule:: backend_logic
   :members:
   :undoc-members:
   :show-inheritance:

Core Functions
--------------

Image Loading and Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: backend_logic.load_images_with_info
.. autofunction:: backend_logic.scale_images
.. autofunction:: backend_logic.calculate_optimal_scale

Metadata Handling
~~~~~~~~~~~~~~~~~

.. autofunction:: backend_logic.load_metadata
.. autofunction:: backend_logic.get_metadata_headers
.. autofunction:: backend_logic.sort_images_hierarchical

Layout Functions
~~~~~~~~~~~~~~~~

.. autofunction:: backend_logic.place_images_grid
.. autofunction:: backend_logic.place_images_puzzle
.. autofunction:: backend_logic.place_images_masonry
.. autofunction:: backend_logic.place_images_manual

Caption and Scale Bar
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: backend_logic.add_captions_to_images
.. autofunction:: backend_logic.create_scale_bar
.. autofunction:: backend_logic.draw_margin_border

Export Functions
~~~~~~~~~~~~~~~~

.. autofunction:: backend_logic.save_output
.. autofunction:: backend_logic.save_editable_output
.. autofunction:: backend_logic.create_lightweight_editable_svg

Main Process
~~~~~~~~~~~~

.. autofunction:: backend_logic.run_layout_process

Utility Functions
~~~~~~~~~~~~~~~~~

.. autofunction:: backend_logic.get_page_dimensions_px
.. autofunction:: backend_logic.get_font
.. autofunction:: backend_logic.natural_sort_key