# backend_logic.py

import os
import re
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import rectpack
import openpyxl

# Dimensioni predefinite in pixel per formati comuni
PAGE_SIZES_PX = {
    'A4': (2480, 3508),  # A4 a 300 DPI
    'A3': (3508, 4961),  # A3 a 300 DPI
    'HD': (1920, 1080),  # Full HD
    '4K': (3840, 2160),  # 4K
    'LETTER': (2550, 3300),  # Letter US a 300 DPI
}

def get_page_dimensions_px(size_name, custom_size_str):
    """Ottiene le dimensioni della pagina in pixel."""
    if size_name.lower() == 'custom':
        if not custom_size_str: 
            raise ValueError("Specificare --custom-size.")
        try: 
            width, height = map(int, custom_size_str.split('x'))
            return (width, height)
        except ValueError: 
            raise ValueError("Formato --custom-size non valido. Usare formato: WIDTHxHEIGHT")
    
    size_px = PAGE_SIZES_PX.get(size_name.upper())
    if not size_px: 
        raise ValueError(f"Formato pagina non supportato: {size_name}. Formati disponibili: {', '.join(PAGE_SIZES_PX.keys())}")
    return size_px

def get_metadata_headers(filepath):
    """Funzione helper per ottenere solo le intestazioni dall'Excel per la GUI."""
    if not filepath or not os.path.exists(filepath):
        return []
    try:
        workbook = openpyxl.load_workbook(filepath, read_only=True)
        sheet = workbook.active
        return [cell.value for cell in sheet[1] if cell.value]
    except Exception as e:
        print(f"Impossibile leggere le intestazioni da Excel: {e}")
        return []

def run_layout_process(params, status_callback=print):
    """
    Funzione principale che esegue l'intero processo di layout.
    Accetta un dizionario di parametri e una funzione per i messaggi di stato.
    """
    try:
        # 1. Caricamento Dati
        metadata = load_metadata(params['metadata_file'])
        image_data = load_images_with_info(params['input_folder'])
        if not image_data:
            status_callback("Nessuna immagine trovata. Processo interrotto.")
            return

        # 2. ORDINAMENTO
        sort_by = params['sort_by']
        status_callback(f"Ordinamento immagini tramite: '{sort_by or 'alfabetico'}'...")
        if sort_by == "random":
            random.shuffle(image_data)
        elif sort_by == "natural_name":
            image_data.sort(key=lambda d: natural_sort_key(d['name']))
        elif sort_by and sort_by not in ["", "alphabetical", "random", "natural_name"] and metadata:
            image_data.sort(key=lambda d: (str(metadata.get(d['name'], {}).get(sort_by, 'zz_fallback')), natural_sort_key(d['name'])))

        # 3. Scalatura
        scale_factor = params['scale_factor']
        if scale_factor != 1.0:
            status_callback(f"Applicazione scala: {scale_factor}x")
            image_data = scale_images(image_data, scale_factor)

        # 4. Aggiunta Didascalie
        if params['add_caption']:
            status_callback("Aggiunta didascalie...")
            image_data = add_captions_to_images(image_data, metadata, params['caption_font_size'], params['caption_padding'])
        
        # 5. Esecuzione Layout
        status_callback("Calcolo dimensioni pagina...")
        page_dims = get_page_dimensions_px(params['page_size'], params.get('custom_size'))
        
        final_pages = []
        status_callback(f"Avvio posizionamento in modalità '{params['mode']}'...")
        if params['mode'] == 'grid':
            grid_size = (params['grid_rows'], params['grid_cols'])
            final_pages = place_images_grid(image_data, page_dims, (params['grid_rows'], params['grid_cols']), params['margin_px'], params['spacing_px'])
        elif params['mode'] == 'puzzle':
            final_pages = place_images_puzzle(image_data, page_dims, params['margin_px'], params['spacing_px'])
        
        status_callback(f"Generate {len(final_pages)} pagine.")

        # 6. Aggiunta Scala Grafica
        if params['add_scale_bar'] and final_pages:
            status_callback("Aggiunta scala grafica...")
            scale_bar = create_scale_bar(params['scale_bar_length_px'], scale_factor, params['scale_bar_real_size_text'])
            for page in final_pages:
                x_pos = params['margin_px']
                y_pos = page.height - params['margin_px'] - scale_bar.height
                page.paste(scale_bar, (x_pos, y_pos), scale_bar)

        # 7. Salvataggio
        status_callback(f"Salvataggio output in '{params['output_file']}'...")
        save_output(final_pages, params['output_file'])
        status_callback("--- PROCESSO COMPLETATO CON SUCCESSO ---")

    except Exception as e:
        status_callback(f"--- ERRORE: {e} ---")
        raise e
    
def load_metadata(filepath):
    """Carica i metadati da un file Excel."""
    if not filepath: 
        return None
    print(f"Caricamento metadati da: {filepath}...")
    try:
        workbook = openpyxl.load_workbook(filepath)
        sheet = workbook.active
        metadata = {}
        header = [cell.value for cell in sheet[1]]
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[0]: 
                metadata[row[0]] = {header[i]: row[i] for i in range(1, len(row))}
        print(f"Caricati metadati per {len(metadata)} elementi.")
        return metadata
    except FileNotFoundError: 
        print(f"Attenzione: File metadati '{filepath}' non trovato.")
        return None
    except Exception as e: 
        print(f"Errore nel caricamento del file Excel: {e}")
        return None

def load_images_with_info(folder_path):
    """Carica tutte le immagini dalla cartella specificata."""
    image_data, supported_formats = [], ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')
    print(f"Caricamento immagini da: {folder_path}...")
    if not os.path.isdir(folder_path): 
        raise FileNotFoundError(f"'{folder_path}' non esiste.")
    
    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(supported_formats):
            try:
                filepath = os.path.join(folder_path, filename)
                img = Image.open(filepath)
                image_data.append({'img': img.copy(), 'name': filename})
                img.close()
            except IOError: 
                print(f"Attenzione: Impossibile caricare {filename}.")
    
    print(f"Caricati {len(image_data)} immagini.")
    return image_data

def natural_sort_key(s):
    """Chiave per ordinamento naturale (numeri in ordine numerico)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def create_scale_bar(length_px, scale_factor, real_size_text):
    """
    Crea un'immagine contenente la barra della scala.
    
    Args:
        length_px: Lunghezza della barra in pixel
        scale_factor: Fattore di scala applicato alle immagini
        real_size_text: Testo che indica la misura reale (es. "5 cm", "10 mm")
    """
    print(f"Creazione scala grafica: {length_px}px = {real_size_text} (scala: {scale_factor:.3f})...")
    
    try: 
        font = ImageFont.truetype("arial.ttf", 14)
    except IOError: 
        font = ImageFont.load_default()
    
    # Calcola la lunghezza effettiva della barra considerando la scala
    effective_length = int(length_px * scale_factor)
    bar_height_px = 10
    total_height = bar_height_px + 25

    bar_img = Image.new('RGBA', (effective_length + 40, total_height), (0,0,0,0))
    draw = ImageDraw.Draw(bar_img)

    # Disegna la barra con segmenti alternati
    num_segments = max(2, effective_length // 20)  # Almeno 2 segmenti
    segment_width = effective_length / num_segments
    
    for i in range(num_segments):
        color = "black" if i % 2 == 0 else "white"
        x0 = i * segment_width
        x1 = (i + 1) * segment_width
        draw.rectangle([x0, 0, x1, bar_height_px], fill=color, outline="black")
    
    # Aggiungi le etichette
    draw.text((0, bar_height_px + 2), "0", fill="black", font=font)
    
    end_label_bbox = draw.textbbox((0,0), real_size_text, font=font)
    end_label_width = end_label_bbox[2] - end_label_bbox[0]
    draw.text((effective_length - end_label_width, bar_height_px + 2), real_size_text, fill="black", font=font)
    
    return bar_img

def scale_images(image_data, scale_factor):
    """
    Scala tutte le immagini secondo il fattore specificato.
    
    Args:
        image_data: Lista di dizionari con le immagini
        scale_factor: Fattore di scala (1.0 = dimensione originale)
    """
    if scale_factor == 1.0: 
        return image_data
    
    print(f"Applicazione fattore di scala: {scale_factor}")
    
    for data in image_data:
        new_width = int(data['img'].width * scale_factor)
        new_height = int(data['img'].height * scale_factor)
        data['img'] = data['img'].resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image_data

def place_images_grid(image_data, page_size_px, grid_size, margin_px, spacing_px):
    """
    Posiziona le immagini in righe regolari (come una griglia flessibile).
    Le immagini mantengono le loro dimensioni originali.
    Ogni riga ha la stessa altezza (determinata dall'immagine più alta della riga).
    Le colonne si adattano dinamicamente alla larghezza delle immagini.
    """
    rows, suggested_cols = grid_size
    page_width, page_height = page_size_px
    available_width = page_width - (2 * margin_px)
    available_height = page_height - (2 * margin_px)
    
    pages = []
    image_index = 0
    
    while image_index < len(image_data):
        current_page = Image.new('RGB', page_size_px, 'white')
        current_y = margin_px
        page_has_images = False
        
        # Processa riga per riga
        rows_on_page = 0
        while current_y < available_height and image_index < len(image_data) and rows_on_page < rows:
            # Determina quante immagini stanno in questa riga
            row_images = []
            current_width = 0
            row_height = 0
            
            # Raccoglie immagini per la riga corrente
            temp_index = image_index
            while (temp_index < len(image_data) and 
                   len(row_images) < suggested_cols and
                   current_width + image_data[temp_index]['img'].width <= available_width):
                
                img = image_data[temp_index]['img']
                
                # Controlla se c'è spazio (considerando la spaziatura)
                needed_width = current_width + img.width
                if len(row_images) > 0:
                    needed_width += spacing_px
                
                if needed_width <= available_width:
                    row_images.append(image_data[temp_index])
                    current_width = needed_width
                    row_height = max(row_height, img.height)
                    temp_index += 1
                else:
                    break
            
            # Se non riusciamo a mettere nemmeno una immagine, forza l'inserimento
            if not row_images and image_index < len(image_data):
                row_images.append(image_data[image_index])
                row_height = image_data[image_index]['img'].height
                image_index += 1
            else:
                image_index = temp_index
            
            # Controlla se la riga sta nella pagina
            if current_y + row_height > available_height + margin_px:
                break
            
            # Posiziona le immagini della riga
            if row_images:
                # Calcola la posizione X di partenza per centrare la riga
                total_row_width = sum(img_data['img'].width for img_data in row_images) + spacing_px * (len(row_images) - 1)
                start_x = margin_px + (available_width - total_row_width) // 2
                
                current_x = start_x
                for img_data in row_images:
                    img = img_data['img']
                    
                    # Centra verticalmente l'immagine nella riga
                    paste_y = current_y + (row_height - img.height) // 2
                    
                    current_page.paste(img, (current_x, paste_y), img if img.mode == 'RGBA' else None)
                    current_x += img.width + spacing_px
                    page_has_images = True
                
                current_y += row_height + spacing_px
                rows_on_page += 1
        
        if page_has_images:
            pages.append(current_page)
    
    return pages

def place_images_puzzle(image_data, page_size_px, margin_px, spacing_px):
    """
    Posiziona le immagini usando un algoritmo di impacchettamento rettangolare.
    Cerca di ottimizzare lo spazio disponibile.
    """
    page_width, page_height = page_size_px
    bin_width, bin_height = page_width - (2 * margin_px), page_height - (2 * margin_px)
    packer = rectpack.newPacker(rotation=False)
    images = [d['img'] for d in image_data]
    
    # Aggiunge i rettangoli (con spaziatura) al packer
    for i, img in enumerate(images): 
        packer.add_rect(img.width + spacing_px, img.height + spacing_px, rid=i)
    
    # Aggiunge i bin (pagine)
    for _ in range(len(images)): 
        packer.add_bin(bin_width, bin_height)
    
    packer.pack()
    pages = []
    
    for i, abin in enumerate(packer):
        if not abin: 
            break
        page = Image.new('RGB', page_size_px, 'white')
        for rect in abin:
            original_image = images[rect.rid]
            paste_x, paste_y = margin_px + rect.x, margin_px + rect.y
            page.paste(original_image, (paste_x, paste_y), original_image if original_image.mode == 'RGBA' else None)
        pages.append(page)
    
    return pages

def add_captions_to_images(image_data, metadata, font_size, caption_padding):
    """
    Aggiunge didascalie centrate alle immagini.
    """
    print("Aggiunta didascalie alle immagini...")
    try: 
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError: 
        font = ImageFont.load_default()
    
    for data in image_data:
        img = data['img']
        caption_lines = [data['name']]
        
        # Aggiungi metadati se disponibili
        img_metadata = metadata.get(data['name']) if metadata else None
        if img_metadata:
            for key, value in img_metadata.items():
                if value is not None: 
                    caption_lines.append(f"{key}: {value}")
        
        full_caption_text = "\n".join(caption_lines)
        
        # Calcola le dimensioni del testo
        temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        text_bbox = temp_draw.multiline_textbbox((0, 0), full_caption_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Crea la nuova immagine con spazio per la didascalia
        new_height = img.height + text_height + caption_padding * 2
        # Assicurati che la larghezza sia almeno quanto il testo + padding
        new_width = max(img.width, text_width + caption_padding * 2)
        
        captioned_img = Image.new('RGB', (new_width, new_height), 'white')
        
        # Incolla l'immagine originale centrata orizzontalmente
        img_paste_x = (new_width - img.width) // 2
        captioned_img.paste(img, (img_paste_x, 0))
        
        # Aggiungi il testo centrato
        draw = ImageDraw.Draw(captioned_img)
        text_x = (new_width - text_width) // 2  # Centra il testo orizzontalmente
        text_y = img.height + caption_padding
        
        draw.multiline_text((text_x, text_y), full_caption_text, font=font, fill="black", align="center")
        
        data['img'] = captioned_img
    
    return image_data

def save_output(pages, output_file):
    """Salva le pagine generate nel file specificato."""
    if not pages: 
        print("Nessuna pagina generata.")
        return
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Converti in RGB se necessario
    if not pages[0].mode == 'RGB': 
        pages = [p.convert('RGB') for p in pages]
    
    if output_path.suffix.lower() == '.pdf':
        # Salva come PDF multipagina
        pages[0].save(output_path, "PDF", resolution=100.0, save_all=True, append_images=pages[1:])
    else:
        # Salva come immagini separate
        if len(pages) > 1:
            base, ext = output_path.stem, output_path.suffix
            for i, page in enumerate(pages): 
                page.save(output_path.with_name(f"{base}_{i+1}{ext}"))
        else:
            pages[0].save(output_path)
    
    print(f"File salvato in: {output_path.resolve()}")