gui_app module
==============

.. automodule:: gui_app
   :members:
   :undoc-members:
   :show-inheritance:

LayoutApp Class
---------------

.. autoclass:: gui_app.LayoutApp
   :members:
   :private-members:
   :show-inheritance:

   Main GUI Application Class
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~

   The LayoutApp class inherits from tk.Tk and provides the complete graphical interface
   for PyPotteryLayout. It manages:

   * User input through various widgets
   * Preview panel with real-time updates
   * File selection dialogs
   * Layout parameter configuration
   * Process execution in separate threads

   Key Methods
   ~~~~~~~~~~~

   .. automethod:: _create_widgets
   .. automethod:: _update_preview
   .. automethod:: _start_process
   .. automethod:: _run_backend_in_thread

   Preview Methods
   ~~~~~~~~~~~~~~~

   .. automethod:: _preview_grid_layout
   .. automethod:: _preview_puzzle_layout
   .. automethod:: _preview_masonry_layout
   .. automethod:: _preview_manual_layout

   Manual Layout Methods
   ~~~~~~~~~~~~~~~~~~~~~

   .. automethod:: _enable_manual_mode
   .. automethod:: _on_drag_start
   .. automethod:: _on_drag_motion
   .. automethod:: _on_drag_release