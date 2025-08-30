# gui_app.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from tkinter.constants import *
import threading
import os

# Assicurati che backend_logic.py sia nella stessa cartella
import backend_logic

class LayoutApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Layout Tool")
        self.geometry("800x850")

        # Variabili di stato per i widget
        self.vars = {
            'input_folder': tk.StringVar(),
            'output_file': tk.StringVar(),
            'metadata_file': tk.StringVar(),
            'mode': tk.StringVar(value="grid"),
            'page_size': tk.StringVar(value="A4"),
            'sort_by': tk.StringVar(value="alphabetical"),
            'scale_factor': tk.DoubleVar(value=1.0),
            'output_dpi': tk.IntVar(value=300),  # Default a 300, controllo nascosto
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
            'show_margin_border': tk.BooleanVar(value=False),  # Nuova feature per cornice margini
        }

        # Variabile per mostrare il valore formattato della scala
        self.scale_display = tk.StringVar(value="1.00x")

        self._create_widgets()
        self._update_ui_for_mode() # Imposta lo stato iniziale
        self._update_sort_options() # Imposta le opzioni iniziali di sort

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=BOTH, expand=YES)

        # --- Sezione File & Cartelle ---
        path_frame = ttk.Labelframe(main_frame, text="1. File e Cartelle", padding="10")
        path_frame.pack(fill=X, expand=NO, pady=5)
        self._create_path_widgets(path_frame)

        # --- Sezione Layout ---
        layout_frame = ttk.Labelframe(main_frame, text="2. Impostazioni di Layout", padding="10")
        layout_frame.pack(fill=X, expand=NO, pady=5)
        self._create_layout_widgets(layout_frame)

        # --- Sezione Dettagli ---
        details_frame = ttk.Labelframe(main_frame, text="3. Dettagli e Aggiunte", padding="10")
        details_frame.pack(fill=X, expand=NO, pady=5)
        self._create_details_widgets(details_frame)
        
        # --- Pulsante di Avvio ---
        self.run_button = ttk.Button(main_frame, text="Avvia Processo di Layout", command=self._start_process)
        self.run_button.pack(pady=20, fill=X, ipady=10)

        # --- Log di Stato ---
        log_frame = ttk.Labelframe(main_frame, text="Log di Processo", padding="10")
        log_frame.pack(fill=BOTH, expand=YES, pady=5)
        self.log_text = ScrolledText(log_frame, height=10, wrap=tk.WORD, state='disabled')
        self.log_text.pack(fill=BOTH, expand=YES)

    def _create_path_widgets(self, parent):
        # Input Folder
        ttk.Label(parent, text="Cartella Immagini:").grid(row=0, column=0, sticky=W, padx=5, pady=2)
        ttk.Entry(parent, textvariable=self.vars['input_folder'], state='readonly').grid(row=0, column=1, sticky=EW, padx=5)
        ttk.Button(parent, text="Sfoglia...", command=self._browse_input_folder).grid(row=0, column=2, padx=5)
        # Output File
        ttk.Label(parent, text="File di Output:").grid(row=1, column=0, sticky=W, padx=5, pady=2)
        ttk.Entry(parent, textvariable=self.vars['output_file'], state='readonly').grid(row=1, column=1, sticky=EW, padx=5)
        ttk.Button(parent, text="Salva come...", command=self._browse_output_file).grid(row=1, column=2, padx=5)
        # Metadata File
        ttk.Label(parent, text="File Metadati (opz.):").grid(row=2, column=0, sticky=W, padx=5, pady=2)
        ttk.Entry(parent, textvariable=self.vars['metadata_file'], state='readonly').grid(row=2, column=1, sticky=EW, padx=5)
        ttk.Button(parent, text="Sfoglia...", command=self._browse_metadata_file).grid(row=2, column=2, padx=5)
        parent.columnconfigure(1, weight=1)

    def _create_layout_widgets(self, parent):
        # ... (continua)
        left_frame = ttk.Frame(parent)
        left_frame.grid(row=0, column=0, sticky=NSEW, padx=5)
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=0, column=1, sticky=NSEW, padx=5, ipadx=20)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        # Colonna Sinistra
        ttk.Label(left_frame, text="Modalità:").pack(anchor=W, pady=(0,2))
        ttk.Radiobutton(left_frame, text="Griglia (Grid)", variable=self.vars['mode'], value="grid", command=self._update_ui_for_mode).pack(anchor=W)
        ttk.Radiobutton(left_frame, text="Puzzle (Ottimizzato)", variable=self.vars['mode'], value="puzzle", command=self._update_ui_for_mode).pack(anchor=W)

        ttk.Label(left_frame, text="Formato Pagina:").pack(anchor=W, pady=(10,2))
        self.page_size_combo = ttk.Combobox(left_frame, textvariable=self.vars['page_size'], values=["A4", "A3"], state='readonly')
        self.page_size_combo.pack(fill=X)
        
        ttk.Label(left_frame, text="Ordinamento Immagini:").pack(anchor=W, pady=(10,2))
        self.sort_by_combo = ttk.Combobox(left_frame, textvariable=self.vars['sort_by'], state='readonly')
        self.sort_by_combo.pack(fill=X)

        # Colonna Destra (Grid-specific)
        self.grid_frame = ttk.Frame(right_frame)
        self.grid_frame.pack(fill=X)
        ttk.Label(self.grid_frame, text="Righe Griglia:").grid(row=0, column=0, sticky=W)
        ttk.Spinbox(self.grid_frame, from_=1, to=100, textvariable=self.vars['grid_rows']).grid(row=0, column=1, sticky=EW, padx=5)
        ttk.Label(self.grid_frame, text="Colonne Griglia:").grid(row=1, column=0, sticky=W)
        ttk.Spinbox(self.grid_frame, from_=1, to=100, textvariable=self.vars['grid_cols']).grid(row=1, column=1, sticky=EW, padx=5)
        self.grid_frame.columnconfigure(1, weight=1)
        
    def _create_details_widgets(self, parent):
        # ... (continua)
        f1 = ttk.Frame(parent)
        f1.grid(row=0, column=0, sticky=NSEW, padx=5)
        f2 = ttk.Frame(parent)
        f2.grid(row=0, column=1, sticky=NSEW, padx=5)
        f3 = ttk.Frame(parent)
        f3.grid(row=0, column=2, sticky=NSEW, padx=5)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(2, weight=1)
        
        # Colonna 1
        ttk.Label(f1, text="Scala Immagini:").pack(anchor=W)
        # Frame per controlli scala combinati
        scale_frame = ttk.Frame(f1)
        scale_frame.pack(fill=X, pady=2)
        
        # Entry per inserire valore manuale
        self.scale_entry = ttk.Entry(scale_frame, textvariable=self.vars['scale_factor'], width=6)
        self.scale_entry.pack(side=tk.LEFT)
        self.scale_entry.bind('<Return>', self._on_scale_entry_change)
        self.scale_entry.bind('<FocusOut>', self._on_scale_entry_change)
        
        # Slider per controllo visuale
        self.scale_slider = ttk.Scale(scale_frame, from_=0.1, to=3.0, variable=self.vars['scale_factor'], 
                                     orient=HORIZONTAL, command=self._on_scale_change)
        self.scale_slider.pack(side=tk.LEFT, fill=X, expand=True, padx=(5,0))
        
        # Label per mostrare valore corrente
        self.scale_label = ttk.Label(f1, textvariable=self.scale_display)
        self.scale_label.pack(anchor=W)
        
        # Nota: DPI è fisso a 300, controllo nascosto
        
        # Colonna 2
        ttk.Label(f2, text="Margine Pagina (px):").pack(anchor=W)
        ttk.Spinbox(f2, from_=0, to=500, textvariable=self.vars['margin_px']).pack(fill=X, pady=2)
        
        ttk.Checkbutton(f2, text="Mostra Cornice Margini", variable=self.vars['show_margin_border']).pack(anchor=W, pady=(5,0))
        
        ttk.Label(f2, text="Spazio tra Immagini (px):").pack(anchor=W, pady=(10,0))
        ttk.Spinbox(f2, from_=0, to=200, textvariable=self.vars['spacing_px']).pack(fill=X, pady=2)

        # Colonna 3
        ttk.Checkbutton(f3, text="Aggiungi Didascalie", variable=self.vars['add_caption']).pack(anchor=W)
        
        # Font Size per didascalie
        ttk.Label(f3, text="Dimensione Font:").pack(anchor=W, pady=(5,0))
        ttk.Spinbox(f3, from_=8, to=48, textvariable=self.vars['caption_font_size']).pack(fill=X, pady=2)
        
        ttk.Checkbutton(f3, text="Aggiungi Scala Grafica", variable=self.vars['add_scale_bar']).pack(anchor=W, pady=(10,0))
        
        # Scale bar parameters
        ttk.Label(f3, text="Scala Bar (cm):").pack(anchor=W, pady=(5,0))
        ttk.Spinbox(f3, from_=1, to=50, textvariable=self.vars['scale_bar_cm']).pack(fill=X, pady=2)
        
        ttk.Label(f3, text="Pixel per cm:").pack(anchor=W, pady=(5,0))
        ttk.Spinbox(f3, from_=10, to=500, textvariable=self.vars['pixels_per_cm']).pack(fill=X, pady=2)

    def _browse_input_folder(self):
        folder = filedialog.askdirectory(title="Seleziona la Cartella delle Immagini")
        if folder: self.vars['input_folder'].set(folder)

    def _browse_output_file(self):
        file = filedialog.asksaveasfilename(title="Salva il File di Output", defaultextension=".pdf", filetypes=[("PDF Document", "*.pdf"), ("PNG Image", "*.png"), ("All Files", "*.*")])
        if file: self.vars['output_file'].set(file)

    def _browse_metadata_file(self):
        file = filedialog.askopenfilename(title="Seleziona il File Metadati", filetypes=[("Excel Files", "*.xlsx")])
        if file:
            self.vars['metadata_file'].set(file)
            self._update_sort_options()

    def _update_sort_options(self):
        metadata_file = self.vars['metadata_file'].get()
        options = ["alphabetical", "random", "natural_name"]
        if metadata_file:
            headers = backend_logic.get_metadata_headers(metadata_file)
            if headers:
                options.extend(headers[1:]) # Esclude la prima colonna (filename)
        self.sort_by_combo['values'] = options
        if self.vars['sort_by'].get() not in options:
            self.vars['sort_by'].set("alphabetical")

    def _update_ui_for_mode(self):
        if self.vars['mode'].get() == "grid":
            self.grid_frame.pack(fill=X)
        else:
            self.grid_frame.pack_forget()

    def _on_scale_change(self, value):
        """Callback quando il slider della scala cambia."""
        try:
            # Aggiorna il valore con 2 decimali per leggibilità
            rounded_value = round(float(value), 2)
            self.vars['scale_factor'].set(rounded_value)
            self.scale_display.set(f"{rounded_value:.2f}x")
        except ValueError:
            pass

    def _on_scale_entry_change(self, event=None):
        """Callback quando l'entry della scala cambia."""
        try:
            value = float(self.scale_entry.get())
            # Limita il valore ai bounds dello slider
            value = max(0.1, min(3.0, value))
            rounded_value = round(value, 2)
            self.vars['scale_factor'].set(rounded_value)
            self.scale_display.set(f"{rounded_value:.2f}x")
            # Aggiorna lo slider
            self.scale_slider.set(rounded_value)
        except ValueError:
            # Se il valore non è valido, ripristina il valore corrente
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
            messagebox.showerror("Errore", "Seleziona una cartella di input e un file di output.")
            return
            
        # Validate that input folder exists and contains images
        if not os.path.isdir(params['input_folder']):
            messagebox.showerror("Errore", f"La cartella '{params['input_folder']}' non esiste.")
            return
            
        self.run_button.config(state='disabled', text="Elaborazione in corso...")
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')

        # Esegui il backend in un thread separato per non bloccare la GUI
        thread = threading.Thread(target=self._run_backend_in_thread, args=(params,))
        thread.start()

    def _run_backend_in_thread(self, params):
        try:
            backend_logic.run_layout_process(params, self._update_log)
            messagebox.showinfo("Successo", f"Processo completato!\nFile salvato in:\n{params['output_file']}")
        except Exception as e:
            self._update_log(f"ERRORE CRITICO: {e}")
            messagebox.showerror("Errore", f"Si è verificato un errore durante il processo:\n\n{e}")
        finally:
            self.run_button.config(state='normal', text="Avvia Processo di Layout")

if __name__ == "__main__":
    app = LayoutApp()
    app.mainloop()