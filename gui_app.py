# gui_app.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.constants import *
from PIL import Image, ImageTk
import threading
import os

VERSION = "0.1.0"

# Make sure backend_logic.py is in the same folder
import backend_logic

class LayoutApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PyPotteryLayout - Create artefacts table effortlessly")
        self.geometry("800x600")
        self.resizable(True, True)
        
        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "imgs", "icon_app.png")
            if os.path.exists(icon_path):
                # Load icon for window title bar
                icon_image = Image.open(icon_path)
                # Convert to ICO format for window icon (Windows specific)
                self.window_icon = ImageTk.PhotoImage(icon_image)
                self.iconphoto(True, self.window_icon)
        except Exception:
            pass  # Continue without window icon if loading fails

        # State variables for widgets
        self.vars = {
            'input_folder': tk.StringVar(),
            'output_file': tk.StringVar(),
            'metadata_file': tk.StringVar(),
            'mode': tk.StringVar(value="grid"),
            'page_size': tk.StringVar(value="A4"),
            'sort_by': tk.StringVar(value="alphabetical"),
            'sort_by_secondary': tk.StringVar(value="none"),  # Secondary sorting
            'scale_factor': tk.DoubleVar(value=0.4),
            'output_dpi': tk.IntVar(value=300),  # Default to 300, hidden control
            'margin_px': tk.IntVar(value=50),
            'spacing_px': tk.IntVar(value=10),
            'grid_rows': tk.IntVar(value=4),
            'grid_cols': tk.IntVar(value=3),
            'add_caption': tk.BooleanVar(value=True),
            'caption_font_size': tk.IntVar(value=12),
            'caption_padding': tk.IntVar(value=5),
            'add_scale_bar': tk.BooleanVar(value=True),
            'scale_bar_cm': tk.IntVar(value=5),
            'pixels_per_cm': tk.IntVar(value=118), # ~300DPI equivalent
            'show_margin_border': tk.BooleanVar(value=False),  # New feature for margin borders
            'export_format': tk.StringVar(value="PDF"),  # Export format selection
        }

        # Variable to show formatted scale value
        self.scale_display = tk.StringVar(value="1.00x")

        # Preview-related variables
        self.preview_images = []  # Store loaded image thumbnails
        self.preview_update_pending = False
        self.preview_update_timer = None

        # Manual layout variables
        self.manual_positions = {}  # Store manual positions for images
        self.dragging_item = None
        self.drag_start_x = 0
        self.drag_start_y = 0

        self._create_widgets()
        self._update_ui_for_mode() # Set initial state
        self._update_sort_options() # Set initial sort options

        # Bind variable changes to preview update
        self._setup_preview_bindings()

    def _create_widgets(self):
        # Update window size to accommodate preview panel and larger terminal
        self.geometry("1400x900")

        # Main vertical container
        main_vertical_container = ttk.Frame(self)
        main_vertical_container.pack(fill="both", expand=True)

        # Top container with horizontal paned window
        top_container = ttk.PanedWindow(main_vertical_container, orient=tk.HORIZONTAL)
        top_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel with tabs
        left_panel = ttk.Frame(top_container)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 1: Input/Output
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="Input/Output")

        # Create scrollable content for tab1
        tab1_canvas = tk.Canvas(tab1)
        tab1_scrollbar = ttk.Scrollbar(tab1, orient="vertical", command=tab1_canvas.yview)
        tab1_frame = ttk.Frame(tab1_canvas)

        tab1_frame.bind(
            "<Configure>",
            lambda e: tab1_canvas.configure(scrollregion=tab1_canvas.bbox("all"))
        )

        tab1_canvas.create_window((0, 0), window=tab1_frame, anchor="nw")
        tab1_canvas.configure(yscrollcommand=tab1_scrollbar.set)

        # Pack canvas and scrollbar
        tab1_canvas.pack(side="left", fill="both", expand=True)
        tab1_scrollbar.pack(side="right", fill="y")

        # Add content to tab1
        tab1_content = ttk.Frame(tab1_frame, padding="10")
        tab1_content.pack(fill="both", expand=True)

        # Header
        self._create_header(tab1_content)

        # Files & Folders Section
        path_frame = ttk.Labelframe(tab1_content, text="Files and Folders", padding="10")
        path_frame.pack(fill=X, expand=NO, pady=5)
        self._create_path_widgets(path_frame)

        # Export Button
        self.run_button = ttk.Button(tab1_content, text="Export Layout", command=self._start_process)
        self.run_button.pack(pady=15, fill=X, ipady=8)

        # Tab 2: Layout Configuration
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text="Layout Configuration")

        # Create scrollable content for tab2
        tab2_canvas = tk.Canvas(tab2)
        tab2_scrollbar = ttk.Scrollbar(tab2, orient="vertical", command=tab2_canvas.yview)
        tab2_frame = ttk.Frame(tab2_canvas)

        tab2_frame.bind(
            "<Configure>",
            lambda e: tab2_canvas.configure(scrollregion=tab2_canvas.bbox("all"))
        )

        tab2_canvas.create_window((0, 0), window=tab2_frame, anchor="nw")
        tab2_canvas.configure(yscrollcommand=tab2_scrollbar.set)

        # Pack canvas and scrollbar
        tab2_canvas.pack(side="left", fill="both", expand=True)
        tab2_scrollbar.pack(side="right", fill="y")

        # Add content to tab2
        tab2_content = ttk.Frame(tab2_frame, padding="10")
        tab2_content.pack(fill="both", expand=True)

        # Layout Section
        layout_frame = ttk.Labelframe(tab2_content, text="Layout Settings", padding="10")
        layout_frame.pack(fill=X, expand=NO, pady=5)
        self._create_layout_widgets(layout_frame)

        # Details Section
        details_frame = ttk.Labelframe(tab2_content, text="Details and Additions", padding="10")
        details_frame.pack(fill=X, expand=NO, pady=5)
        self._create_details_widgets(details_frame)

        # Bind mouse wheel scrolling for both tabs
        def _on_mousewheel(event):
            # Determine which tab is active and scroll accordingly
            current_tab = self.notebook.index(self.notebook.select())
            if current_tab == 0:
                tab1_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif current_tab == 1:
                tab2_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.bind_all("<MouseWheel>", _on_mousewheel)

        # Add left panel to horizontal paned window
        top_container.add(left_panel, weight=1)

        # Right panel for preview and additional controls
        right_panel = ttk.Frame(top_container)
        self._create_preview_panel(right_panel)

        # Add controls under preview
        self._create_preview_controls(right_panel)

        top_container.add(right_panel, weight=2)

        # Set initial sash position to prevent overlap
        self.after(100, lambda: top_container.sashpos(0, 650))

        # Bottom terminal-style log
        self._create_terminal_log(main_vertical_container)

    def _create_header(self, parent):
        """Create application header with icon and title"""
        header_frame = ttk.Frame(parent, relief="ridge", borderwidth=2)
        header_frame.pack(fill=X, pady=(0, 10))
        
        # Create icon placeholder (you can replace with actual icon)
        icon_frame = ttk.Frame(header_frame)
        icon_frame.pack(side=LEFT, padx=10, pady=5)
        
        # Try to load icon, fallback to text if not found
        try:
            # Load the actual icon from imgs folder
            icon_path = os.path.join(os.path.dirname(__file__), "imgs", "icon_app.png")
            if os.path.exists(icon_path):
                # Load and resize the icon
                icon_image = Image.open(icon_path)
                # Resize to 32x32 pixels for the header
                icon_image = icon_image.resize((32, 32), Image.Resampling.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(icon_image)
                icon_label = ttk.Label(icon_frame, image=self.icon_photo)
                icon_label.pack()
            else:
                # Fallback to emoji if icon file not found
                icon_label = ttk.Label(icon_frame, text="🏺", font=("Arial", 24))
                icon_label.pack()
        except Exception as e:
            # Fallback to emoji if any error occurs
            icon_label = ttk.Label(icon_frame, text="🏺", font=("Arial", 24))
            icon_label.pack()
        
        # Title and version info
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=LEFT, fill=X, expand=YES, padx=10, pady=5)
        
        title_label = ttk.Label(title_frame, text="PyPotteryLayout", 
                               font=("Arial", 16, "bold"))
        title_label.pack(anchor=W)

        subtitle_label = ttk.Label(title_frame, text=f"Create artefacts table effortlessly - v{VERSION}", 
                                  font=("Arial", 10), foreground="gray")
        subtitle_label.pack(anchor=W)

    def _create_path_widgets(self, parent):
        # Input Folder
        ttk.Label(parent, text="Images Folder:").grid(row=0, column=0, sticky=W, padx=5, pady=2)
        ttk.Entry(parent, textvariable=self.vars['input_folder'], state='readonly').grid(row=0, column=1, sticky=EW, padx=5)
        ttk.Button(parent, text="Browse...", command=self._browse_input_folder).grid(row=0, column=2, padx=5)
        # Output File
        ttk.Label(parent, text="Output File:").grid(row=1, column=0, sticky=W, padx=5, pady=2)
        ttk.Entry(parent, textvariable=self.vars['output_file'], state='readonly').grid(row=1, column=1, sticky=EW, padx=5)
        ttk.Button(parent, text="Save as...", command=self._browse_output_file).grid(row=1, column=2, padx=5)
        # Export Format
        ttk.Label(parent, text="Export Format:").grid(row=2, column=0, sticky=W, padx=5, pady=2)
        format_combo = ttk.Combobox(parent, textvariable=self.vars['export_format'], 
                                   values=["PDF", "SVG", "JPEG"], state='readonly', width=10)
        format_combo.grid(row=2, column=1, sticky=W, padx=5)
        format_combo.bind('<<ComboboxSelected>>', self._on_format_change)
        # Metadata File
        ttk.Label(parent, text="Metadata File (opt.):").grid(row=3, column=0, sticky=W, padx=5, pady=2)
        ttk.Entry(parent, textvariable=self.vars['metadata_file'], state='readonly').grid(row=3, column=1, sticky=EW, padx=5)
        ttk.Button(parent, text="Browse...", command=self._browse_metadata_file).grid(row=3, column=2, padx=5)
        parent.columnconfigure(1, weight=1)

    def _create_layout_widgets(self, parent):
        # Single column layout for cleaner organization
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=5)

        # Mode selection
        mode_frame = ttk.Labelframe(main_frame, text="Layout Mode", padding="10")
        mode_frame.pack(fill=X, expand=NO, pady=5)

        ttk.Radiobutton(mode_frame, text="Grid Layout", variable=self.vars['mode'], value="grid", command=self._update_ui_for_mode).pack(anchor=W, pady=2)
        ttk.Radiobutton(mode_frame, text="Puzzle (Optimized)", variable=self.vars['mode'], value="puzzle", command=self._update_ui_for_mode).pack(anchor=W, pady=2)
        ttk.Radiobutton(mode_frame, text="Masonry Layout", variable=self.vars['mode'], value="masonry", command=self._update_ui_for_mode).pack(anchor=W, pady=2)
        ttk.Radiobutton(mode_frame, text="Manual (Drag & Drop)", variable=self.vars['mode'], value="manual", command=self._update_ui_for_mode).pack(anchor=W, pady=2)

        # Page settings
        page_frame = ttk.Labelframe(main_frame, text="Page Settings", padding="10")
        page_frame.pack(fill=X, expand=NO, pady=5)

        ttk.Label(page_frame, text="Page Format:").grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.page_size_combo = ttk.Combobox(page_frame, textvariable=self.vars['page_size'], values=["A4", "A3"], state='readonly', width=15)
        self.page_size_combo.grid(row=0, column=1, sticky=W, padx=5, pady=2)

        ttk.Label(page_frame, text="Page Margin (px):").grid(row=1, column=0, sticky=W, padx=5, pady=2)
        ttk.Spinbox(page_frame, from_=0, to=500, textvariable=self.vars['margin_px'], width=15).grid(row=1, column=1, sticky=W, padx=5, pady=2)

        ttk.Label(page_frame, text="Image Spacing (px):").grid(row=2, column=0, sticky=W, padx=5, pady=2)
        ttk.Spinbox(page_frame, from_=0, to=200, textvariable=self.vars['spacing_px'], width=15).grid(row=2, column=1, sticky=W, padx=5, pady=2)

        ttk.Checkbutton(page_frame, text="Show Margin Border", variable=self.vars['show_margin_border']).grid(row=3, column=0, columnspan=2, sticky=W, padx=5, pady=5)

        page_frame.columnconfigure(1, weight=1)

        # Sorting options
        sort_frame = ttk.Labelframe(main_frame, text="Sorting Options", padding="10")
        sort_frame.pack(fill=X, expand=NO, pady=5)

        ttk.Label(sort_frame, text="Primary Sorting:").grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.sort_by_combo = ttk.Combobox(sort_frame, textvariable=self.vars['sort_by'], state='readonly', width=20)
        self.sort_by_combo.grid(row=0, column=1, sticky=EW, padx=5, pady=2)

        ttk.Label(sort_frame, text="Secondary Sorting:").grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.sort_by_secondary_combo = ttk.Combobox(sort_frame, textvariable=self.vars['sort_by_secondary'], state='readonly', width=20)
        self.sort_by_secondary_combo.grid(row=1, column=1, sticky=EW, padx=5, pady=2)

        sort_frame.columnconfigure(1, weight=1)

        # Scale settings
        scale_frame = ttk.Labelframe(main_frame, text="Image Scale", padding="10")
        scale_frame.pack(fill=X, expand=NO, pady=5)

        # Combined scale controls
        controls_frame = ttk.Frame(scale_frame)
        controls_frame.pack(fill=X)

        self.scale_entry = ttk.Entry(controls_frame, textvariable=self.vars['scale_factor'], width=6)
        self.scale_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.scale_entry.bind('<Return>', self._on_scale_entry_change)
        self.scale_entry.bind('<FocusOut>', self._on_scale_entry_change)

        self.scale_slider = ttk.Scale(controls_frame, from_=0.1, to=3.0, variable=self.vars['scale_factor'],
                                     orient=HORIZONTAL, command=self._on_scale_change)
        self.scale_slider.pack(side=tk.LEFT, fill=X, expand=True)

        self.scale_label = ttk.Label(controls_frame, textvariable=self.scale_display)
        self.scale_label.pack(side=tk.LEFT, padx=(5, 0))

        # Caption settings
        caption_frame = ttk.Labelframe(main_frame, text="Caption Settings", padding="10")
        caption_frame.pack(fill=X, expand=NO, pady=5)

        ttk.Checkbutton(caption_frame, text="Add Captions", variable=self.vars['add_caption']).pack(anchor=W, pady=2)

        # Note: Grid frame will be created but managed elsewhere
        self.grid_frame = ttk.Frame(parent)
        # Don't pack it here
        
    def _create_details_widgets(self, parent):
        # This section now only contains remaining details not moved elsewhere
        # Empty for now as most controls have been reorganized
        pass

    def _browse_input_folder(self):
        folder = filedialog.askdirectory(title="Select Images Folder")
        if folder: 
            self.vars['input_folder'].set(folder)
            self._update_sort_options()

    def _browse_output_file(self):
        # Get the selected export format
        format_value = self.vars['export_format'].get()
        format_ext = format_value.lower()
        
        # Set file types and extension based on format
        filetypes = []
        if format_value == "PDF":
            filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
            default_ext = ".pdf"
        elif format_value == "SVG":
            filetypes = [("SVG files", "*.svg"), ("All files", "*.*")]
            default_ext = ".svg"
        elif format_value == "JPEG":
            filetypes = [("JPEG files", "*.jpg"), ("All files", "*.*")]
            default_ext = ".jpg"
        else:
            filetypes = [("All files", "*.*")]
            default_ext = ".pdf"  # Default fallback
        
        file = filedialog.asksaveasfilename(
            title="Save Output File As",
            filetypes=filetypes,
            defaultextension=default_ext
        )
        if file: self.vars['output_file'].set(file)

    def _browse_metadata_file(self):
        file = filedialog.askopenfilename(
            title="Select Metadata File",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file: 
            self.vars['metadata_file'].set(file)
            self._update_sort_options()

    def _on_format_change(self, event=None):
        """Called when export format changes - updates output file extension."""
        current_output = self.vars['output_file'].get()
        if not current_output:
            return
            
        # Get new format and corresponding extension
        format_value = self.vars['export_format'].get()
        if format_value == "PDF":
            new_ext = ".pdf"
        elif format_value == "SVG":
            new_ext = ".svg"
        elif format_value == "JPEG":
            new_ext = ".jpg"
        else:
            return
            
        # Update file path with new extension
        from pathlib import Path
        output_path = Path(current_output)
        new_path = output_path.with_suffix(new_ext)
        self.vars['output_file'].set(str(new_path))
        
        # Show info about editable formats
        if format_value == "SVG":
            self._update_log("✨ SVG Export: Creates lightweight, fully editable files!", "success")
            self._update_log("   • Small file sizes (images linked externally)", "info")
            self._update_log("   • Each element is separately editable", "info")
            self._update_log("   • Compatible with all vector editors", "info")
        elif format_value == "PDF":
            self._update_log("📄 PDF Export: Creates final publication-ready files", "header")
            self._update_log("   • High-quality immutable output", "info")
            self._update_log("   • Perfect for printing and distribution", "info")

    def _update_sort_options(self):
        metadata_file = self.vars['metadata_file'].get()
        primary_options = ["alphabetical", "random", "natural_name"]
        secondary_options = ["none", "alphabetical", "random", "natural_name"]  # Include all base options + "none"
        
        if metadata_file:
            headers = backend_logic.get_metadata_headers(metadata_file)
            if headers:
                metadata_columns = headers[1:]  # Exclude first column (filename)
                primary_options.extend(metadata_columns)
                secondary_options.extend(metadata_columns)
        
        # Update first sorting options
        self.sort_by_combo['values'] = primary_options
        if self.vars['sort_by'].get() not in primary_options:
            self.vars['sort_by'].set("alphabetical")
        
        # Update second sorting options
        self.sort_by_secondary_combo['values'] = secondary_options
        if self.vars['sort_by_secondary'].get() not in secondary_options:
            self.vars['sort_by_secondary'].set("none")

    def _update_ui_for_mode(self):
        # Grid controls are now in the preview controls section
        mode = self.vars['mode'].get()
        if mode == "manual":
            self._update_log("[INFO] Manual mode: Drag images in preview to position them", "info")
            self._enable_manual_mode()
        else:
            self._disable_manual_mode()

    def _on_scale_change(self, value):
        """Callback when scale slider changes."""
        try:
            # Update value with 2 decimals for readability
            rounded_value = round(float(value), 2)
            self.vars['scale_factor'].set(rounded_value)
            self.scale_display.set(f"{rounded_value:.2f}x")
        except ValueError:
            pass

    def _on_scale_entry_change(self, event=None):
        """Callback when scale entry changes."""
        try:
            value = float(self.scale_entry.get())
            # Limit value to slider bounds
            value = max(0.1, min(3.0, value))
            rounded_value = round(value, 2)
            self.vars['scale_factor'].set(rounded_value)
            self.scale_display.set(f"{rounded_value:.2f}x")
            # Update slider
            self.scale_slider.set(rounded_value)
        except ValueError:
            # If value is invalid, restore current value
            current_value = round(self.vars['scale_factor'].get(), 2)
            self.scale_entry.delete(0, tk.END)
            self.scale_entry.insert(0, str(current_value))
            self.scale_display.set(f"{current_value:.2f}x")

    def _create_terminal_log(self, parent):
        """Create terminal-style log at the bottom."""
        log_frame = ttk.Labelframe(parent, text="Terminal Output", padding="5")
        log_frame.pack(fill=BOTH, expand=NO, padx=5, pady=(0, 5))

        # Container for text and scrollbar
        terminal_container = ttk.Frame(log_frame)
        terminal_container.pack(fill=BOTH, expand=True)

        # Create text widget with terminal styling (much taller for better readability)
        self.log_text = tk.Text(terminal_container, height=15, wrap=tk.WORD,
                                bg="black", fg="#00ff00",
                                insertbackground="#00ff00",
                                font=("Courier", 11),
                                relief="sunken", borderwidth=2)

        # Add scrollbar outside the text widget
        log_scrollbar = ttk.Scrollbar(terminal_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        # Pack scrollbar first, then text widget
        log_scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

        # Configure text tags for different message types
        self.log_text.tag_configure("info", foreground="#00ff00")  # Green
        self.log_text.tag_configure("warning", foreground="#ffff00")  # Yellow
        self.log_text.tag_configure("error", foreground="#ff0000")  # Red
        self.log_text.tag_configure("success", foreground="#00ffff")  # Cyan
        self.log_text.tag_configure("header", foreground="#ff00ff")  # Magenta

        # Initial message
        self._update_log("[SYSTEM] PyPotteryLayout Terminal Ready", "header")
        self._update_log("[INFO] Waiting for user input...", "info")

    def _update_log(self, message, tag="info"):
        """Update terminal-style log with colored output."""
        # Determine tag based on message content if not specified
        if tag == "info":
            if "ERROR" in message or "CRITICAL" in message:
                tag = "error"
            elif "WARNING" in message or "⚠" in message:
                tag = "warning"
            elif "SUCCESS" in message or "✓" in message or "✨" in message:
                tag = "success"
            elif "📄" in message or "Processing" in message:
                tag = "header"

        self.log_text.insert(tk.END, f"> {message}\n", tag)
        self.log_text.see(tk.END)  # Auto-scroll
        self.update_idletasks()

    def _start_process(self):
        # Collect all parameters from GUI
        params = {key: var.get() for key, var in self.vars.items()}
        
        if not params['input_folder'] or not params['output_file']:
            messagebox.showerror("Error", "Please select an input folder and output file.")
            return
            
        # Validate that input folder exists and contains images
        if not os.path.isdir(params['input_folder']):
            messagebox.showerror("Error", f"Folder '{params['input_folder']}' does not exist.")
            return
            
        self.run_button.config(state='disabled', text="Processing...")
        self.log_text.delete('1.0', tk.END)
        self._update_log("[SYSTEM] Starting layout process...", "header")

        # Run backend in separate thread to avoid blocking GUI
        thread = threading.Thread(target=self._run_backend_in_thread, args=(params,))
        thread.start()

    def _run_backend_in_thread(self, params):
        try:
            # Add manual positions if in manual mode
            if params['mode'] == 'manual' and self.manual_positions:
                params['manual_positions'] = self.manual_positions

            backend_logic.run_layout_process(params, self._update_log)
            messagebox.showinfo("Success", f"Process completed!\nFile saved to:\n{params['output_file']}")
        except Exception as e:
            self._update_log(f"CRITICAL ERROR: {e}")
            messagebox.showerror("Error", f"An error occurred during processing:\n\n{e}")
        finally:
            self.run_button.config(state='normal', text="Start Layout Process")

    def _create_preview_panel(self, parent):
        """Create the preview panel for layout visualization."""
        # Preview title and controls
        preview_header = ttk.Frame(parent)
        preview_header.pack(fill=X, padx=10, pady=5)

        ttk.Label(preview_header, text="Layout Preview", font=("Arial", 12, "bold")).pack(side=LEFT)
        ttk.Button(preview_header, text="Refresh Preview", command=self._update_preview).pack(side=RIGHT, padx=5)

        # Create scrollable preview area
        preview_container = ttk.Frame(parent)
        preview_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Canvas for preview with scrollbars
        self.preview_canvas = tk.Canvas(preview_container, bg="white", relief="sunken", borderwidth=2)
        preview_vscroll = ttk.Scrollbar(preview_container, orient="vertical", command=self.preview_canvas.yview)
        preview_hscroll = ttk.Scrollbar(preview_container, orient="horizontal", command=self.preview_canvas.xview)

        self.preview_canvas.configure(
            yscrollcommand=preview_vscroll.set,
            xscrollcommand=preview_hscroll.set
        )

        # Pack scrollbars and canvas
        preview_vscroll.pack(side="right", fill="y")
        preview_hscroll.pack(side="bottom", fill="x")
        self.preview_canvas.pack(side="left", fill="both", expand=True)

        # Info label for preview status
        self.preview_info = ttk.Label(parent, text="No images loaded", foreground="gray")
        self.preview_info.pack(fill=X, padx=10, pady=(0, 5))

    def _create_preview_controls(self, parent):
        """Create control panel under the preview."""
        controls_frame = ttk.Labelframe(parent, text="Preview Controls", padding="10")
        controls_frame.pack(fill=X, padx=10, pady=(0, 10))

        # Create three columns for controls
        col1 = ttk.Frame(controls_frame)
        col1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        col2 = ttk.Frame(controls_frame)
        col2.grid(row=0, column=1, sticky="nsew", padx=10)
        col3 = ttk.Frame(controls_frame)
        col3.grid(row=0, column=2, sticky="nsew", padx=(10, 0))

        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(2, weight=1)

        # Column 1: Grid controls
        grid_label = ttk.Label(col1, text="Grid Settings:", font=("Arial", 10, "bold"))
        grid_label.pack(anchor=W, pady=(0, 5))

        grid_rows_frame = ttk.Frame(col1)
        grid_rows_frame.pack(fill=X, pady=2)
        ttk.Label(grid_rows_frame, text="Rows:").pack(side=LEFT)
        ttk.Spinbox(grid_rows_frame, from_=1, to=100, textvariable=self.vars['grid_rows'], width=10).pack(side=LEFT, padx=(5, 0))

        grid_cols_frame = ttk.Frame(col1)
        grid_cols_frame.pack(fill=X, pady=2)
        ttk.Label(grid_cols_frame, text="Columns:").pack(side=LEFT)
        ttk.Spinbox(grid_cols_frame, from_=1, to=100, textvariable=self.vars['grid_cols'], width=10).pack(side=LEFT, padx=(5, 0))

        # Column 2: Caption controls
        caption_label = ttk.Label(col2, text="Caption Settings:", font=("Arial", 10, "bold"))
        caption_label.pack(anchor=W, pady=(0, 5))

        font_frame = ttk.Frame(col2)
        font_frame.pack(fill=X, pady=2)
        ttk.Label(font_frame, text="Font Size:").pack(side=LEFT)
        ttk.Spinbox(font_frame, from_=8, to=48, textvariable=self.vars['caption_font_size'], width=10).pack(side=LEFT, padx=(5, 0))

        padding_frame = ttk.Frame(col2)
        padding_frame.pack(fill=X, pady=2)
        ttk.Label(padding_frame, text="Padding:").pack(side=LEFT)
        ttk.Spinbox(padding_frame, from_=0, to=20, textvariable=self.vars['caption_padding'], width=10).pack(side=LEFT, padx=(5, 0))

        # Column 3: Scale bar controls
        scale_label = ttk.Label(col3, text="Scale Bar Settings:", font=("Arial", 10, "bold"))
        scale_label.pack(anchor=W, pady=(0, 5))

        ttk.Checkbutton(col3, text="Add Scale Bar", variable=self.vars['add_scale_bar']).pack(anchor=W, pady=2)

        scalebar_frame = ttk.Frame(col3)
        scalebar_frame.pack(fill=X, pady=2)
        ttk.Label(scalebar_frame, text="Length (cm):").pack(side=LEFT)
        ttk.Spinbox(scalebar_frame, from_=1, to=50, textvariable=self.vars['scale_bar_cm'], width=10).pack(side=LEFT, padx=(5, 0))

        pixels_frame = ttk.Frame(col3)
        pixels_frame.pack(fill=X, pady=2)
        ttk.Label(pixels_frame, text="Pixels/cm:").pack(side=LEFT)
        ttk.Spinbox(pixels_frame, from_=10, to=500, textvariable=self.vars['pixels_per_cm'], width=10).pack(side=LEFT, padx=(5, 0))

    def _setup_preview_bindings(self):
        """Bind variable changes to preview updates with debouncing."""
        # Track changes for preview update
        for key, var in self.vars.items():
            if key not in ['output_file', 'metadata_file']:  # Skip non-layout parameters
                if isinstance(var, (tk.StringVar, tk.IntVar, tk.DoubleVar, tk.BooleanVar)):
                    var.trace('w', lambda *args: self._schedule_preview_update())

        # Also update preview when folder is selected
        self.vars['input_folder'].trace('w', lambda *args: self._load_preview_images())

    def _schedule_preview_update(self):
        """Schedule a preview update with debouncing to avoid too frequent updates."""
        if self.preview_update_timer:
            self.after_cancel(self.preview_update_timer)

        # Schedule update after 500ms of no changes
        self.preview_update_timer = self.after(500, self._update_preview)

    def _load_preview_images(self):
        """Load thumbnail images for preview."""
        folder = self.vars['input_folder'].get()
        if not folder or not os.path.isdir(folder):
            self.preview_images = []
            self.preview_info.config(text="No images loaded")
            return

        # Find image files
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
        image_files = []
        for file in os.listdir(folder):
            if file.lower().endswith(image_extensions):
                image_files.append(os.path.join(folder, file))

        # Load thumbnails (limit to first 20 for performance)
        self.preview_images = []
        max_images = min(20, len(image_files))

        for i in range(max_images):
            try:
                img = Image.open(image_files[i])
                # Create small thumbnail for preview
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                self.preview_images.append((image_files[i], img))
            except Exception as e:
                print(f"Error loading image {image_files[i]}: {e}")

        self.preview_info.config(text=f"Loaded {len(self.preview_images)} of {len(image_files)} images for preview")
        self._update_preview()

    def _update_preview(self):
        """Update the preview canvas with current layout settings."""
        if not self.preview_images:
            return

        # Clear canvas
        self.preview_canvas.delete("all")

        # Get page dimensions in preview scale (1/10 of actual size)
        page_size = self.vars['page_size'].get()
        page_width, page_height = backend_logic.get_page_dimensions_px(page_size)
        preview_scale = 0.2  # Scale down for preview
        canvas_width = int(page_width * preview_scale)
        canvas_height = int(page_height * preview_scale)

        # Draw page background
        self.preview_canvas.create_rectangle(
            0, 0, canvas_width, canvas_height,
            fill="white", outline="black", width=2
        )

        # Draw margins if enabled
        margin = int(self.vars['margin_px'].get() * preview_scale)
        if self.vars['show_margin_border'].get() and margin > 0:
            self.preview_canvas.create_rectangle(
                margin, margin,
                canvas_width - margin, canvas_height - margin,
                outline="gray", dash=(5, 5)
            )

        # Layout images based on mode
        mode = self.vars['mode'].get()
        spacing = int(self.vars['spacing_px'].get() * preview_scale)
        scale_factor = self.vars['scale_factor'].get()

        if mode == "grid":
            self._preview_grid_layout(canvas_width, canvas_height, margin, spacing, scale_factor, preview_scale)
        elif mode == "puzzle":
            self._preview_puzzle_layout(canvas_width, canvas_height, margin, spacing, scale_factor, preview_scale)
        elif mode == "masonry":
            self._preview_masonry_layout(canvas_width, canvas_height, margin, spacing, scale_factor, preview_scale)
        elif mode == "manual":
            self._preview_manual_layout(canvas_width, canvas_height, margin, spacing, scale_factor, preview_scale)

        # Update scroll region
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

    def _preview_grid_layout(self, canvas_width, canvas_height, margin, spacing, scale_factor, preview_scale):
        """Preview grid layout."""
        rows = self.vars['grid_rows'].get()
        cols = self.vars['grid_cols'].get()

        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin

        cell_width = (available_width - (cols - 1) * spacing) / cols
        cell_height = (available_height - (rows - 1) * spacing) / rows

        img_idx = 0
        for row in range(rows):
            for col in range(cols):
                if img_idx >= len(self.preview_images):
                    break

                x = margin + col * (cell_width + spacing)
                y = margin + row * (cell_height + spacing)

                # Draw image placeholder
                self.preview_canvas.create_rectangle(
                    x, y, x + cell_width, y + cell_height,
                    fill="lightgray", outline="darkgray"
                )

                # Add image number
                self.preview_canvas.create_text(
                    x + cell_width/2, y + cell_height/2,
                    text=f"{img_idx + 1}",
                    font=("Arial", int(12 * preview_scale * 5))
                )

                img_idx += 1

    def _preview_puzzle_layout(self, canvas_width, canvas_height, margin, spacing, scale_factor, preview_scale):
        """Preview puzzle/optimized layout using simple packing."""
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin

        # Simple rectangle packing visualization
        x = margin
        y = margin
        row_height = 0

        for idx, (path, img) in enumerate(self.preview_images):
            # Scale image size
            img_width = int(img.width * scale_factor * preview_scale)
            img_height = int(img.height * scale_factor * preview_scale)

            # Check if image fits in current row
            if x + img_width > canvas_width - margin:
                x = margin
                y += row_height + spacing
                row_height = 0

            # Draw image placeholder
            if y + img_height <= canvas_height - margin:
                self.preview_canvas.create_rectangle(
                    x, y, x + img_width, y + img_height,
                    fill="lightblue", outline="darkblue"
                )

                # Add image number
                self.preview_canvas.create_text(
                    x + img_width/2, y + img_height/2,
                    text=f"{idx + 1}",
                    font=("Arial", int(10 * preview_scale * 5))
                )

                row_height = max(row_height, img_height)
                x += img_width + spacing

    def _preview_masonry_layout(self, canvas_width, canvas_height, margin, spacing, scale_factor, preview_scale):
        """Preview masonry layout (vertical columns with varied heights)."""
        cols = self.vars['grid_cols'].get() if self.vars['mode'].get() == "grid" else 3
        available_width = canvas_width - 2 * margin
        col_width = (available_width - (cols - 1) * spacing) / cols

        # Track the current y position for each column
        col_heights = [margin] * cols

        for idx, (path, img) in enumerate(self.preview_images):
            # Find the shortest column
            min_col = col_heights.index(min(col_heights))

            # Calculate position
            x = margin + min_col * (col_width + spacing)
            y = col_heights[min_col]

            # Random height for masonry effect
            img_height = int((50 + (idx * 37) % 100) * preview_scale)  # Varied heights

            # Draw image placeholder
            if y + img_height <= canvas_height - margin:
                self.preview_canvas.create_rectangle(
                    x, y, x + col_width, y + img_height,
                    fill="lightyellow", outline="orange"
                )

                # Add image number
                self.preview_canvas.create_text(
                    x + col_width/2, y + img_height/2,
                    text=f"{idx + 1}",
                    font=("Arial", int(10 * preview_scale * 5))
                )

                # Update column height
                col_heights[min_col] = y + img_height + spacing

    def _preview_manual_layout(self, canvas_width, canvas_height, margin, spacing, scale_factor, preview_scale):
        """Preview manual layout with drag-and-drop functionality."""
        # Initialize positions if empty
        if not self.manual_positions:
            # Place images in a simple grid initially
            x = margin
            y = margin
            for idx, (path, img) in enumerate(self.preview_images):
                img_width = int(img.width * scale_factor * preview_scale)
                img_height = int(img.height * scale_factor * preview_scale)

                if x + img_width > canvas_width - margin:
                    x = margin
                    y += 100 * preview_scale + spacing

                self.manual_positions[idx] = (x, y, img_width, img_height)
                x += img_width + spacing

        # Draw images at their manual positions
        for idx, (path, img) in enumerate(self.preview_images):
            if idx in self.manual_positions:
                x, y, w, h = self.manual_positions[idx]

                # Create draggable rectangle
                rect_id = self.preview_canvas.create_rectangle(
                    x, y, x + w, y + h,
                    fill="lightgreen", outline="darkgreen", width=2,
                    tags=(f"image_{idx}", "draggable")
                )

                # Add image number
                text_id = self.preview_canvas.create_text(
                    x + w/2, y + h/2,
                    text=f"{idx + 1}",
                    font=("Arial", int(10 * preview_scale * 5)),
                    tags=(f"image_{idx}", "draggable")
                )

    def _enable_manual_mode(self):
        """Enable drag-and-drop functionality in preview canvas."""
        self.preview_canvas.bind("<Button-1>", self._on_drag_start)
        self.preview_canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.preview_canvas.bind("<ButtonRelease-1>", self._on_drag_release)
        self.preview_canvas.config(cursor="hand2")

    def _disable_manual_mode(self):
        """Disable drag-and-drop functionality."""
        self.preview_canvas.unbind("<Button-1>")
        self.preview_canvas.unbind("<B1-Motion>")
        self.preview_canvas.unbind("<ButtonRelease-1>")
        self.preview_canvas.config(cursor="")

    def _on_drag_start(self, event):
        """Handle drag start for manual positioning."""
        # Find which item was clicked
        x = self.preview_canvas.canvasx(event.x)
        y = self.preview_canvas.canvasy(event.y)

        # Get the closest item with "draggable" tag
        item = self.preview_canvas.find_closest(x, y)[0]
        tags = self.preview_canvas.gettags(item)

        if "draggable" in tags:
            self.dragging_item = item
            self.drag_start_x = x
            self.drag_start_y = y

            # Find image index from tags
            for tag in tags:
                if tag.startswith("image_"):
                    self.dragging_index = int(tag.split("_")[1])
                    break

    def _on_drag_motion(self, event):
        """Handle drag motion for manual positioning."""
        if self.dragging_item:
            x = self.preview_canvas.canvasx(event.x)
            y = self.preview_canvas.canvasy(event.y)

            dx = x - self.drag_start_x
            dy = y - self.drag_start_y

            # Move all items with the same image tag
            tags = self.preview_canvas.gettags(self.dragging_item)
            for tag in tags:
                if tag.startswith("image_"):
                    items = self.preview_canvas.find_withtag(tag)
                    for item in items:
                        self.preview_canvas.move(item, dx, dy)
                    break

            self.drag_start_x = x
            self.drag_start_y = y

    def _on_drag_release(self, event):
        """Handle drag release for manual positioning."""
        if self.dragging_item and hasattr(self, 'dragging_index'):
            # Get the new position of the dragged item
            tags = self.preview_canvas.gettags(self.dragging_item)
            for tag in tags:
                if tag.startswith("image_"):
                    # Find all items with this tag and get the rectangle bounds
                    items = self.preview_canvas.find_withtag(tag)
                    for item in items:
                        if self.preview_canvas.type(item) == "rectangle":
                            x1, y1, x2, y2 = self.preview_canvas.coords(item)
                            # Update stored position
                            self.manual_positions[self.dragging_index] = (x1, y1, x2-x1, y2-y1)
                            break
                    break

            self.dragging_item = None
            delattr(self, 'dragging_index')
            self._update_log(f"[INFO] Image {self.dragging_index + 1 if hasattr(self, 'dragging_index') else '?'} repositioned", "info")

    def _browse_input_folder(self):
        folder = filedialog.askdirectory(title="Select Images Folder")
        if folder:
            self.vars['input_folder'].set(folder)
            self._update_sort_options()
            self._load_preview_images()

if __name__ == "__main__":
    app = LayoutApp()
    app.mainloop()