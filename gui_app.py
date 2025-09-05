# gui_app.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
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

        self._create_widgets()
        self._update_ui_for_mode() # Set initial state
        self._update_sort_options() # Set initial sort options

    def _create_widgets(self):
        # Create main frame with scrollable content
        main_canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        # Bind mouse wheel scrolling
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.bind_all("<MouseWheel>", _on_mousewheel)

        # Pack canvas and scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Main content frame
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill=X, expand=NO)

        # --- Header Section ---
        self._create_header(main_frame)

        # --- Files & Folders Section ---
        path_frame = ttk.Labelframe(main_frame, text="1. Files and Folders", padding="10")
        path_frame.pack(fill=X, expand=NO, pady=5)
        self._create_path_widgets(path_frame)

        # --- Layout Section ---
        layout_frame = ttk.Labelframe(main_frame, text="2. Layout Settings", padding="10")
        layout_frame.pack(fill=X, expand=NO, pady=5)
        self._create_layout_widgets(layout_frame)

        # --- Details Section ---
        details_frame = ttk.Labelframe(main_frame, text="3. Details and Additions", padding="10")
        details_frame.pack(fill=X, expand=NO, pady=5)
        self._create_details_widgets(details_frame)
        
        # --- Export Button ---
        self.run_button = ttk.Button(main_frame, text="Export Layout", command=self._start_process)
        self.run_button.pack(pady=15, fill=X, ipady=8)

        # --- Status Log ---
        log_frame = ttk.Labelframe(main_frame, text="Process Log", padding="10")
        log_frame.pack(fill=X, expand=NO, pady=5)
        self.log_text = ScrolledText(log_frame, height=6, wrap=tk.WORD, state='disabled')
        self.log_text.pack(fill=X, expand=NO)

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
        left_frame = ttk.Frame(parent)
        left_frame.grid(row=0, column=0, sticky=NSEW, padx=5)
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=0, column=1, sticky=NSEW, padx=5, ipadx=20)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        # Left Column
        ttk.Label(left_frame, text="Mode:").pack(anchor=W, pady=(0,2))
        ttk.Radiobutton(left_frame, text="Grid Layout", variable=self.vars['mode'], value="grid", command=self._update_ui_for_mode).pack(anchor=W)
        ttk.Radiobutton(left_frame, text="Puzzle (Optimized)", variable=self.vars['mode'], value="puzzle", command=self._update_ui_for_mode).pack(anchor=W)

        ttk.Label(left_frame, text="Page Format:").pack(anchor=W, pady=(10,2))
        self.page_size_combo = ttk.Combobox(left_frame, textvariable=self.vars['page_size'], values=["A4", "A3"], state='readonly')
        self.page_size_combo.pack(fill=X)
        
        ttk.Label(left_frame, text="Primary Sorting:").pack(anchor=W, pady=(10,2))
        self.sort_by_combo = ttk.Combobox(left_frame, textvariable=self.vars['sort_by'], state='readonly')
        self.sort_by_combo.pack(fill=X)
        
        ttk.Label(left_frame, text="Secondary Sorting:").pack(anchor=W, pady=(10,2))
        self.sort_by_secondary_combo = ttk.Combobox(left_frame, textvariable=self.vars['sort_by_secondary'], state='readonly')
        self.sort_by_secondary_combo.pack(fill=X)

        # Right Column (Grid-specific)
        self.grid_frame = ttk.Frame(right_frame)
        self.grid_frame.pack(fill=X)
        ttk.Label(self.grid_frame, text="Grid Rows:").grid(row=0, column=0, sticky=W)
        ttk.Spinbox(self.grid_frame, from_=1, to=100, textvariable=self.vars['grid_rows']).grid(row=0, column=1, sticky=EW, padx=5)
        ttk.Label(self.grid_frame, text="Grid Columns:").grid(row=1, column=0, sticky=W)
        ttk.Spinbox(self.grid_frame, from_=1, to=100, textvariable=self.vars['grid_cols']).grid(row=1, column=1, sticky=EW, padx=5)
        self.grid_frame.columnconfigure(1, weight=1)
        
    def _create_details_widgets(self, parent):
        f1 = ttk.Frame(parent)
        f1.grid(row=0, column=0, sticky=NSEW, padx=5)
        f2 = ttk.Frame(parent)
        f2.grid(row=0, column=1, sticky=NSEW, padx=5)
        f3 = ttk.Frame(parent)
        f3.grid(row=0, column=2, sticky=NSEW, padx=5)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(2, weight=1)
        
        # Column 1
        ttk.Label(f1, text="Image Scale:").pack(anchor=W)
        # Frame for combined scale controls
        scale_frame = ttk.Frame(f1)
        scale_frame.pack(fill=X, pady=2)
        
        # Entry for manual value input
        self.scale_entry = ttk.Entry(scale_frame, textvariable=self.vars['scale_factor'], width=6)
        self.scale_entry.pack(side=tk.LEFT)
        self.scale_entry.bind('<Return>', self._on_scale_entry_change)
        self.scale_entry.bind('<FocusOut>', self._on_scale_entry_change)
        
        # Slider for visual control
        self.scale_slider = ttk.Scale(scale_frame, from_=0.1, to=3.0, variable=self.vars['scale_factor'], 
                                     orient=HORIZONTAL, command=self._on_scale_change)
        self.scale_slider.pack(side=tk.LEFT, fill=X, expand=True, padx=(5,0))
        
        # Label to show current value
        self.scale_label = ttk.Label(f1, textvariable=self.scale_display)
        self.scale_label.pack(anchor=W)
        
        # Note: DPI is fixed at 300, control hidden
        
        # Column 2
        ttk.Label(f2, text="Page Margin (px):").pack(anchor=W)
        ttk.Spinbox(f2, from_=0, to=500, textvariable=self.vars['margin_px']).pack(fill=X, pady=2)
        
        ttk.Checkbutton(f2, text="Show Margin Border", variable=self.vars['show_margin_border']).pack(anchor=W, pady=(5,0))
        
        ttk.Label(f2, text="Spacing Between Images (px):").pack(anchor=W, pady=(10,0))
        ttk.Spinbox(f2, from_=0, to=200, textvariable=self.vars['spacing_px']).pack(fill=X, pady=2)

        # Column 3
        ttk.Checkbutton(f3, text="Add Captions", variable=self.vars['add_caption']).pack(anchor=W)
        
        # Font Size for captions
        ttk.Label(f3, text="Font Size:").pack(anchor=W, pady=(5,0))
        ttk.Spinbox(f3, from_=8, to=48, textvariable=self.vars['caption_font_size']).pack(fill=X, pady=2)
        
        ttk.Checkbutton(f3, text="Add Scale Bar", variable=self.vars['add_scale_bar']).pack(anchor=W, pady=(10,0))
        
        # Scale bar parameters
        ttk.Label(f3, text="Scale Bar (cm):").pack(anchor=W, pady=(5,0))
        ttk.Spinbox(f3, from_=1, to=50, textvariable=self.vars['scale_bar_cm']).pack(fill=X, pady=2)
        
        ttk.Label(f3, text="Pixels per cm:").pack(anchor=W, pady=(5,0))
        ttk.Spinbox(f3, from_=10, to=500, textvariable=self.vars['pixels_per_cm']).pack(fill=X, pady=2)

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
            self._update_log("✨ SVG Export: Creates lightweight, fully editable files!")
            self._update_log("   • Small file sizes (images linked externally)")
            self._update_log("   • Each element is separately editable")
            self._update_log("   • Compatible with all vector editors")
        elif format_value == "PDF":
            self._update_log("📄 PDF Export: Creates final publication-ready files")
            self._update_log("   • High-quality immutable output")
            self._update_log("   • Perfect for printing and distribution")

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
        if self.vars['mode'].get() == "grid":
            self.grid_frame.pack(fill=X)
        else:
            self.grid_frame.pack_forget()

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

    def _update_log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END) # Auto-scroll
        self.log_text.config(state='disabled')
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
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')

        # Run backend in separate thread to avoid blocking GUI
        thread = threading.Thread(target=self._run_backend_in_thread, args=(params,))
        thread.start()

    def _run_backend_in_thread(self, params):
        try:
            backend_logic.run_layout_process(params, self._update_log)
            messagebox.showinfo("Success", f"Process completed!\nFile saved to:\n{params['output_file']}")
        except Exception as e:
            self._update_log(f"CRITICAL ERROR: {e}")
            messagebox.showerror("Error", f"An error occurred during processing:\n\n{e}")
        finally:
            self.run_button.config(state='normal', text="Start Layout Process")

if __name__ == "__main__":
    app = LayoutApp()
    app.mainloop()