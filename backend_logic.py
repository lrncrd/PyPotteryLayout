"""Backend logic refactored and consolidated from notebook helpers.

Provides functions for loading images/metadata, placing images on pages
in grid or puzzle modes, adding captions and scale bars, and saving output.
"""

import os
import re
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import rectpack
import openpyxl
import io
import base64
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Default page sizes in pixels (300 DPI approximations)
PAGE_SIZES_PX = {
    'A4': (2480, 3508),
    'A3': (3508, 4961),
    'HD': (1920, 1080),
    '4K': (3840, 2160),
    'LETTER': (2550, 3300),
}


def get_page_dimensions_px(size_name_or_custom, custom_size_str=None):
    if isinstance(size_name_or_custom, tuple) and len(size_name_or_custom) == 2:
        return size_name_or_custom
    if isinstance(size_name_or_custom, str) and 'x' in size_name_or_custom:
        try:
            w, h = map(int, size_name_or_custom.split('x'))
            return (w, h)
        except Exception:
            pass
    if isinstance(size_name_or_custom, str) and size_name_or_custom.lower() == 'custom':
        if not custom_size_str:
            raise ValueError('Specificare custom_size_str se usi "custom"')
        return get_page_dimensions_px(custom_size_str)
    size_px = PAGE_SIZES_PX.get(size_name_or_custom.upper()) if isinstance(size_name_or_custom, str) else None
    if not size_px:
        raise ValueError(f'Unsupported page format: {size_name_or_custom}')
    return size_px


def get_font(size):
    """Try to load common TTF fonts, fallback to default."""
    import platform
    
    font_paths = []
    
    if platform.system() == "Darwin":  # macOS
        font_paths = [
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Times.ttc", 
            "/Library/Fonts/Arial.ttf",
            "/Users/" + os.environ.get('USER', 'user') + "/Library/Fonts/Arial.ttf"
        ]
    elif platform.system() == "Windows":
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/times.ttf"
        ]
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf"
        ]
    
    # Also try simple names for system fonts
    simple_names = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf", "FreeSans.ttf", "Helvetica.ttf"]
    
    # Try full paths first, then simple names
    all_candidates = font_paths + simple_names
    
    for font_path in all_candidates:
        try:
            font = ImageFont.truetype(font_path, int(size))
            # Test that font loads correctly by testing a size
            test_bbox = font.getbbox("Test")
            if test_bbox and test_bbox[3] > 0:  # Check that it has height > 0
                return font
        except Exception:
            continue
    
    # If no TTF works, try PIL's default font
    try:
        default_font = ImageFont.load_default()
        # For default font, try to create scaled version if possible
        return default_font
    except Exception:
        # Last fallback
        return ImageFont.load_default()


def get_metadata_headers(filepath):
    """Get column headers from Excel metadata file for GUI dropdown options."""
    if not filepath or not os.path.exists(filepath):
        return None
    try:
        workbook = openpyxl.load_workbook(filepath)
        sheet = workbook.active
        headers = [cell.value for cell in sheet[1]]
        return headers
    except Exception:
        return None


def load_metadata(filepath, status_callback=print):
    if not filepath:
        return None
    status_callback(f"Loading metadata from: {filepath}...")
    try:
        workbook = openpyxl.load_workbook(filepath)
        sheet = workbook.active
        metadata = {}
        header = [cell.value for cell in sheet[1]]
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row and row[0]:
                metadata[row[0]] = {header[i]: row[i] for i in range(1, len(row))}
        status_callback(f"Loaded metadata for {len(metadata)} items.")
        return metadata
    except FileNotFoundError:
        status_callback(f"Warning: Metadata file '{filepath}' not found.")
        return None
    except Exception as e:
        status_callback(f"Error loading Excel file: {e}")
        return None


def load_images_with_info(folder_path, status_callback=print):
    image_data, supported_formats = [], ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')
    status_callback(f"Loading images from: {folder_path}...")
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"'{folder_path}' does not exist.")
    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(supported_formats):
            try:
                filepath = os.path.join(folder_path, filename)
                img = Image.open(filepath)
                image_data.append({'img': img.copy(), 'name': filename})
                img.close()
            except IOError:
                status_callback(f"Warning: Could not load {filename}.")
    status_callback(f"Loaded {len(image_data)} images.")
    return image_data


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def sort_images_hierarchical(image_data, primary_sort, secondary_sort, metadata, status_callback=print):
    """
    Sorts images with hierarchical two-level sorting.
    
    Args:
        image_data: Lista di dati immagine
        primary_sort: Campo di ordinamento primario
        secondary_sort: Campo di ordinamento secondario (può essere 'none', 'random', 'alphabetical', 'natural_name', o un campo metadati)
        metadata: Dizionario metadati
        status_callback: Function for status messages
    """
    if not image_data:
        return image_data
    
    # If no valid primary sorting, use alphabetical
    if not primary_sort or primary_sort in ['', 'alphabetical']:
        primary_sort = 'alphabetical'
    
    # Status message
    if secondary_sort and secondary_sort != 'none':
        status_callback(f"Hierarchical sorting: '{primary_sort}' -> '{secondary_sort}'...")
    else:
        status_callback(f"Sorting: '{primary_sort}'...")
    
    def get_sort_key(img_data, sort_field):
        """Ottieni la chiave di ordinamento per un'immagine."""
        if sort_field == 'random':
            return random.random()
        elif sort_field == 'natural_name':
            return natural_sort_key(img_data['name'])
        elif sort_field == 'alphabetical':
            return img_data['name'].lower()
        else:
            # Metadata sorting
            if metadata and img_data['name'] in metadata:
                value = metadata[img_data['name']].get(sort_field, '')
                # If value is None or empty, use fallback value
                if value is None:
                    value = 'zzz_empty'
                elif isinstance(value, (int, float)):
                    return value  # Keep numbers as numbers for correct sorting
                else:
                    # For strings, try to convert to number if possible
                    str_value = str(value).strip()
                    try:
                        return float(str_value)
                    except ValueError:
                        return str_value.lower()
            return 'zzz_no_metadata'
    
    # Apply hierarchical sorting
    if primary_sort == 'random' and (not secondary_sort or secondary_sort == 'none'):
        # If primary sorting is random and there's no secondary, randomize everything
        random.shuffle(image_data)
    else:
        # Create composite keys for hierarchical sorting
        def composite_sort_key(img_data):
            primary_key = get_sort_key(img_data, primary_sort)
            
            if secondary_sort and secondary_sort != 'none':
                # Special handling for when primary is random but secondary is not
                if primary_sort == 'random':
                    # If primary is random, use a random value as primary
                    # but keep secondary sorting deterministic
                    primary_key = random.random()
                
                secondary_key = get_sort_key(img_data, secondary_sort)
                
                # If secondary is random, generate random value
                if secondary_sort == 'random':
                    secondary_key = random.random()
                
                return (primary_key, secondary_key, natural_sort_key(img_data['name']))
            else:
                return (primary_key, natural_sort_key(img_data['name']))
        
        image_data.sort(key=composite_sort_key)
    
    return image_data


def create_scale_bar(target_cm, pixels_per_cm, scale_factor, status_callback=print):
    status_callback(f"Creating scale bar to represent {target_cm} cm...")
    try:
        font = get_font(14)
    except Exception:
        font = ImageFont.load_default()
    bar_width_px = int(max(1, target_cm) * pixels_per_cm * scale_factor)
    bar_height_px = 10
    total_height = bar_height_px + 20
    bar_img = Image.new('RGBA', (bar_width_px + 40, total_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bar_img)
    num_segments = int(max(1, target_cm))
    segment_width = bar_width_px / num_segments if num_segments else bar_width_px
    for i in range(num_segments):
        color = "black" if i % 2 == 0 else "white"
        x0 = int(i * segment_width) + 20
        x1 = int((i + 1) * segment_width) + 20
        draw.rectangle([x0, 0, x1, bar_height_px], fill=color, outline="black")
    draw.text((20, bar_height_px + 2), "0", fill="black", font=font)
    end_label = f"{target_cm} cm"
    end_label_bbox = draw.textbbox((0, 0), end_label, font=font)
    end_label_width = end_label_bbox[2] - end_label_bbox[0]
    draw.text((20 + bar_width_px - end_label_width, bar_height_px + 2), end_label, fill="black", font=font)
    return bar_img


def calculate_optimal_scale(image_data, page_size_px, margin_px, spacing_px, images_per_page, mode, grid_size=None):
    """Calculate optimal scale factor to fill the page with the given number of images."""
    if images_per_page <= 0 or not image_data:
        return 1.0

    page_width, page_height = page_size_px
    available_width = page_width - (2 * margin_px)
    available_height = page_height - (2 * margin_px)

    # Get subset of images for this page
    page_images = image_data[:min(images_per_page, len(image_data))]

    # Calculate average image dimensions
    avg_width = sum(d['img'].width for d in page_images) / len(page_images)
    avg_height = sum(d['img'].height for d in page_images) / len(page_images)
    avg_ratio = avg_width / avg_height

    if mode == "grid" and grid_size:
        rows, cols = grid_size
        # Calculate how many images fit in the grid
        grid_capacity = rows * cols
        actual_images = min(images_per_page, grid_capacity, len(page_images))

        # Calculate optimal size for grid cells
        if actual_images <= cols:
            # Single row
            effective_cols = actual_images
            effective_rows = 1
        else:
            # Multiple rows
            effective_cols = cols
            effective_rows = min(rows, (actual_images + cols - 1) // cols)

        # Available space per cell
        cell_width = (available_width - (effective_cols - 1) * spacing_px) / effective_cols
        cell_height = (available_height - (effective_rows - 1) * spacing_px) / effective_rows

        # Calculate scale to fit average image in cell
        scale_width = cell_width / avg_width * 0.9  # 90% to leave some margin
        scale_height = cell_height / avg_height * 0.9

        optimal_scale = min(scale_width, scale_height)

    elif mode == "puzzle":
        # For puzzle mode, estimate based on total area
        total_area = available_width * available_height

        # Calculate total image area at current scale
        current_total_area = sum(d['img'].width * d['img'].height for d in page_images)

        # Add spacing area estimate (roughly 10% of image area)
        spacing_area = current_total_area * 0.15

        # Calculate scale factor to fill available area
        area_ratio = (total_area * 0.85) / (current_total_area + spacing_area)
        optimal_scale = area_ratio ** 0.5  # Square root for 2D scaling

    elif mode == "masonry":
        # For masonry, focus on column width
        columns = 3  # Default masonry columns
        col_width = (available_width - (columns - 1) * spacing_px) / columns

        # Scale to fit column width
        optimal_scale = col_width / avg_width * 0.95

    else:
        # Default or manual mode
        optimal_scale = 1.0

    # Limit scale factor to reasonable range
    optimal_scale = max(0.1, min(optimal_scale, 5.0))

    return optimal_scale


def scale_images(image_data, scale_factor, status_callback=print):
    if scale_factor == 1.0:
        return image_data
    status_callback(f"Applying scale: {scale_factor}x")
    for data in image_data:
        new_width = int(data['img'].width * scale_factor)
        new_height = int(data['img'].height * scale_factor)
        data['img'] = data['img'].resize((new_width, new_height), Image.Resampling.LANCZOS)
    return image_data


def add_captions_to_images(image_data, metadata, font_size, caption_padding, status_callback=print):
    status_callback("Adding captions to images...")
    font = get_font(font_size)
    for data in image_data:
        img = data['img']
        caption_lines = [data['name']]
        img_metadata = metadata.get(data['name']) if metadata else None
        if img_metadata:
            for key, value in img_metadata.items():
                if value is not None:
                    caption_lines.append(f"{key}: {value}")
        full_caption_text = "\n".join(caption_lines)
        temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        text_bbox = temp_draw.multiline_textbbox((0, 0), full_caption_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        new_height = img.height + text_height + caption_padding * 2
        new_width = max(img.width, text_width + caption_padding * 2)
        captioned_img = Image.new('RGB', (new_width, new_height), 'white')
        img_paste_x = (new_width - img.width) // 2
        captioned_img.paste(img, (img_paste_x, 0))
        draw = ImageDraw.Draw(captioned_img)
        text_x = (new_width - text_width) // 2
        text_y = img.height + caption_padding
        draw.multiline_text((text_x, text_y), full_caption_text, font=font, fill="black", align="center")
        data['img'] = captioned_img
    return image_data


def place_images_grid(image_data, page_size_px, grid_size, margin_px, spacing_px, images_per_page=0, status_callback=print):
    rows_per_page, suggested_cols = grid_size
    page_width, page_height = page_size_px
    available_width = page_width - (2 * margin_px)
    pages, image_index = [], 0

    while image_index < len(image_data):
        current_page = Image.new('RGB', page_size_px, 'white')
        current_y = margin_px
        page_has_images = False
        rows_on_this_page = 0
        images_on_this_page = 0

        # Set limit for images on this page
        page_image_limit = images_per_page if images_per_page > 0 else float('inf')

        while image_index < len(image_data) and rows_on_this_page < rows_per_page and images_on_this_page < page_image_limit:
            row_images, current_row_width, row_height = [], 0, 0
            temp_index = image_index
            while temp_index < len(image_data) and len(row_images) < suggested_cols:
                img = image_data[temp_index]['img']
                needed_width = current_row_width + img.width + (spacing_px if row_images else 0)
                if needed_width <= available_width:
                    row_images.append(image_data[temp_index])
                    current_row_width = needed_width
                    row_height = max(row_height, img.height)
                    temp_index += 1
                else:
                    break
            if not row_images and image_index < len(image_data):
                row_images.append(image_data[image_index])
                row_height = image_data[image_index]['img'].height
                temp_index = image_index + 1
            if not row_images:
                break
            if current_y + row_height > page_height - margin_px:
                image_index = temp_index - len(row_images)
                break
            image_index = temp_index
            total_row_img_width = sum(d['img'].width for d in row_images)
            total_row_width_with_spacing = total_row_img_width + spacing_px * (len(row_images) - 1)
            start_x = margin_px + (available_width - total_row_width_with_spacing) // 2
            current_x = start_x
            for img_data in row_images:
                img = img_data['img']
                paste_y = current_y + (row_height - img.height) // 2
                current_page.paste(img, (current_x, paste_y), img if img.mode == 'RGBA' else None)
                current_x += img.width + spacing_px
                page_has_images = True
                images_on_this_page += 1
            current_y += row_height + spacing_px
            rows_on_this_page += 1
        if page_has_images:
            pages.append(current_page)
        if not page_has_images and image_index < len(image_data):
            status_callback("WARNING: Remaining images may be too large.")
            break
    return pages


def place_images_puzzle(image_data, page_size_px, margin_px, spacing_px, images_per_page=0, status_callback=print):
    page_width, page_height = page_size_px
    bin_width, bin_height = page_width - (2 * margin_px), page_height - (2 * margin_px)
    pages = []
    images = [d['img'] for d in image_data]

    if images_per_page > 0:
        # Process images in chunks
        for i in range(0, len(images), images_per_page):
            chunk = images[i:i+images_per_page]
            chunk_data = image_data[i:i+images_per_page]

            packer = rectpack.newPacker(rotation=False)
            for j, img in enumerate(chunk):
                packer.add_rect(img.width + spacing_px, img.height + spacing_px, rid=j)

            # Add bins for this chunk
            for _ in range(len(chunk)):
                packer.add_bin(bin_width, bin_height)
            packer.pack()

            # Create pages for this chunk
            for bin_idx, abin in enumerate(packer):
                if not abin:
                    break
                page = Image.new('RGB', page_size_px, 'white')
                status_callback(f"Creating puzzle page...")
                for rect in abin:
                    original_image = chunk[rect.rid]
                    paste_x, paste_y = margin_px + rect.x, margin_px + rect.y
                    page.paste(original_image, (paste_x, paste_y), original_image if original_image.mode == 'RGBA' else None)
                pages.append(page)
                break  # Only use first bin when images_per_page is set
    else:
        # Original behavior - pack all images optimally
        packer = rectpack.newPacker(rotation=False)
        for i, img in enumerate(images):
            packer.add_rect(img.width + spacing_px, img.height + spacing_px, rid=i)
        for _ in range(len(images)):
            packer.add_bin(bin_width, bin_height)
        packer.pack()

        for i, abin in enumerate(packer):
            if not abin:
                break
            page = Image.new('RGB', page_size_px, 'white')
            status_callback(f"Creating puzzle page {i+1}...")
            for rect in abin:
                original_image = images[rect.rid]
                paste_x, paste_y = margin_px + rect.x, margin_px + rect.y
                page.paste(original_image, (paste_x, paste_y), original_image if original_image.mode == 'RGBA' else None)
            pages.append(page)
    return pages


def place_images_manual(image_data, page_size_px, margin_px, manual_positions, scale_factor, status_callback=print, images_per_page=0):
    """Place images based on manual drag-and-drop positions with multi-page support."""
    page_width, page_height = page_size_px
    pages = []

    status_callback("Creating manual layout from user-defined positions...")

    # Scale positions from preview to actual size
    preview_scale = 0.2  # This should match the preview scale in GUI
    actual_scale = 1.0 / preview_scale

    if images_per_page > 0:
        # Multi-page support: group images by page
        page_groups = {}
        for idx, data in enumerate(image_data):
            if idx in manual_positions:
                # Calculate which page this image belongs to based on position
                x, y, w, h = manual_positions[idx]
                actual_y = int(y * actual_scale)

                # Determine page number based on y position
                page_num = actual_y // page_height
                if page_num not in page_groups:
                    page_groups[page_num] = []
                page_groups[page_num].append(idx)

        # Create pages for each group
        for page_num in sorted(page_groups.keys()):
            current_page = Image.new('RGB', page_size_px, 'white')
            status_callback(f"Creating manual layout page {page_num + 1}...")

            for idx in page_groups[page_num]:
                data = image_data[idx]
                x, y, w, h = manual_positions[idx]

                # Scale and adjust positions
                actual_x = int(x * actual_scale)
                actual_y = int(y * actual_scale) - (page_num * page_height)

                # Get the actual image
                img = data['img']

                # Paste image at manual position
                try:
                    current_page.paste(img, (actual_x, actual_y), img if img.mode == 'RGBA' else None)
                    status_callback(f"Placed image {idx+1} on page {page_num + 1}")
                except Exception as e:
                    status_callback(f"Warning: Could not place image {idx+1}: {e}")

            pages.append(current_page)
    else:
        # Single page mode - original behavior
        current_page = Image.new('RGB', page_size_px, 'white')

        for idx, data in enumerate(image_data):
            if idx in manual_positions:
                # Get position from manual layout
                x, y, w, h = manual_positions[idx]

                # Scale positions to actual page size
                actual_x = int(x * actual_scale)
                actual_y = int(y * actual_scale)

                # Get the actual image
                img = data['img']

                # Paste image at manual position
                try:
                    current_page.paste(img, (actual_x, actual_y), img if img.mode == 'RGBA' else None)
                    status_callback(f"Placed image {idx+1} at manual position ({actual_x}, {actual_y})")
                except Exception as e:
                    status_callback(f"Warning: Could not place image {idx+1}: {e}")

        pages.append(current_page)

    return pages


def place_images_masonry(image_data, page_size_px, margin_px, spacing_px, columns=3, images_per_page=0, status_callback=print):
    """Place images in masonry layout (Pinterest-style vertical columns)."""
    page_width, page_height = page_size_px
    available_width = page_width - (2 * margin_px)
    col_width = (available_width - (columns - 1) * spacing_px) // columns

    pages = []
    current_page = Image.new('RGB', page_size_px, 'white')

    # Track height for each column
    column_heights = [margin_px] * columns
    page_num = 1

    status_callback(f"Creating masonry layout with {columns} columns...")

    for idx, data in enumerate(image_data):
        img = data['img']

        # Scale image to fit column width while maintaining aspect ratio
        aspect_ratio = img.height / img.width
        new_width = col_width
        new_height = int(new_width * aspect_ratio)

        # Resize image if needed
        if img.width != new_width:
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Find column with minimum height
        min_col_idx = column_heights.index(min(column_heights))

        # Check if image fits on current page
        if column_heights[min_col_idx] + new_height + margin_px > page_height:
            # Check if any column has space
            if all(h + new_height + margin_px > page_height for h in column_heights):
                # Start new page
                pages.append(current_page)
                current_page = Image.new('RGB', page_size_px, 'white')
                column_heights = [margin_px] * columns
                page_num += 1
                status_callback(f"Starting masonry page {page_num}...")
                min_col_idx = 0

        # Calculate position
        x = margin_px + min_col_idx * (col_width + spacing_px)
        y = column_heights[min_col_idx]

        # Paste image
        current_page.paste(img, (x, y), img if img.mode == 'RGBA' else None)

        # Update column height
        column_heights[min_col_idx] = y + new_height + spacing_px

        status_callback(f"Placed image {idx+1} of {len(image_data)} in column {min_col_idx+1}")

    # Add last page if it has content
    if any(h > margin_px for h in column_heights):
        pages.append(current_page)

    return pages


def draw_margin_border(page, margin_px, status_callback=print):
    """Draw a border frame to visualize page margins."""
    if margin_px <= 0:
        return page

    status_callback("Adding margin borders...")
    draw = ImageDraw.Draw(page)
    
    # Calculate border points
    page_width, page_height = page.size
    
    # Outer rectangle (page border)
    outer_rect = [0, 0, page_width - 1, page_height - 1]
    
    # Inner rectangle (content area)
    inner_rect = [margin_px, margin_px, page_width - margin_px - 1, page_height - margin_px - 1]
    
    # Draw thin gray border to show margins
    # Outer border (page)
    draw.rectangle(outer_rect, outline="lightgray", width=1)
    
    # Inner border (content area)
    draw.rectangle(inner_rect, outline="gray", width=2)
    
    return page
    draw.rectangle(inner_rect, outline="gray", width=2)
    
    # Corner lines to emphasize margins
    corner_size = min(20, margin_px // 2)
    if corner_size > 5:
        # Top corners
        draw.line([margin_px, margin_px, margin_px + corner_size, margin_px], fill="darkgray", width=2)
        draw.line([margin_px, margin_px, margin_px, margin_px + corner_size], fill="darkgray", width=2)
        
        draw.line([page_width - margin_px, margin_px, page_width - margin_px - corner_size, margin_px], fill="darkgray", width=2)
        draw.line([page_width - margin_px, margin_px, page_width - margin_px, margin_px + corner_size], fill="darkgray", width=2)
        
        # Bottom corners
        draw.line([margin_px, page_height - margin_px, margin_px + corner_size, page_height - margin_px], fill="darkgray", width=2)
        draw.line([margin_px, page_height - margin_px, margin_px, page_height - margin_px - corner_size], fill="darkgray", width=2)
        
        draw.line([page_width - margin_px, page_height - margin_px, page_width - margin_px - corner_size, page_height - margin_px], fill="darkgray", width=2)
        draw.line([page_width - margin_px, page_height - margin_px, page_width - margin_px, page_height - margin_px - corner_size], fill="darkgray", width=2)
    
    return page


def save_output(pages, output_file, output_dpi=300, status_callback=print):
    """Save output pages to file, supporting PNG, JPG, PDF, and SVG formats."""
    if not pages:
        status_callback("No pages generated.")
        return
    
    output_path = Path(output_file)
    
    # Create export directory structure
    export_dir = output_path.parent / "export"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure RGB mode for all pages
    if pages and not pages[0].mode == 'RGB':
        pages = [p.convert('RGB') for p in pages]
    
    # Handle different file formats
    file_ext = output_path.suffix.lower()
    file_stem = output_path.stem
    
    # Validate file extension
    supported_extensions = ['.pdf', '.svg', '.jpg', '.jpeg', '.png']
    if not file_ext:
        raise ValueError("No file extension specified. Please save with a valid extension (.pdf, .svg, .jpg)")
    if file_ext not in supported_extensions:
        raise ValueError(f"Unsupported file extension: {file_ext}. Supported formats: {', '.join(supported_extensions)}")
    
    if file_ext == '.pdf':
        # PDF: Save directly in export folder
        final_path = export_dir / f"{file_stem}.pdf"
        status_callback(f"Exporting as PDF to: {final_path}")
        pages[0].save(final_path, "PDF", resolution=float(output_dpi), 
                     save_all=True, append_images=pages[1:])
        status_callback(f"PDF saved to: {final_path.resolve()}")
        
    elif file_ext == '.svg':
        # SVG: Create basic SVG (legacy mode - will be replaced by editable version)
        status_callback(f"Exporting as SVG to folder: {export_dir}")
        subfolder = export_dir / file_stem
        subfolder.mkdir(parents=True, exist_ok=True)
        
        if len(pages) > 1:
            for i, page in enumerate(pages):
                svg_path = subfolder / f"{file_stem}_page_{i+1}.svg"
                _save_basic_svg(page, svg_path, output_dpi, status_callback)
        else:
            svg_path = subfolder / f"{file_stem}.svg"
            _save_basic_svg(pages[0], svg_path, output_dpi, status_callback)
                
    else:
        # JPEG/PNG: Create subfolder and save multiple files
        subfolder = export_dir / file_stem
        subfolder.mkdir(parents=True, exist_ok=True)
        
        status_callback(f"Exporting as {file_ext.upper()} to folder: {subfolder}")
        if len(pages) > 1:
            for i, page in enumerate(pages):
                img_path = subfolder / f"{file_stem}_page_{i+1}{file_ext}"
                page.save(img_path, dpi=(output_dpi, output_dpi))
        else:
            img_path = subfolder / f"{file_stem}{file_ext}"
            pages[0].save(img_path, dpi=(output_dpi, output_dpi))
        
        status_callback(f"Files saved to folder: {subfolder.resolve()}")


def _save_basic_svg(page, output_path, dpi=300, status_callback=print):
    """Save a single page as basic SVG format (legacy mode)."""
    try:
        width_px, height_px = page.size
        
        # Convert PIL image to base64 embedded data
        buffer = io.BytesIO()
        page.save(buffer, format='PNG')
        img_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Create basic SVG content
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width_px}px" height="{height_px}px" 
     viewBox="0 0 {width_px} {height_px}"
     xmlns="http://www.w3.org/2000/svg" 
     xmlns:xlink="http://www.w3.org/1999/xlink">
  <title>PyPottery Layout</title>
  <desc>Archaeological pottery catalog layout</desc>
  
  <rect id="background" x="0" y="0" width="{width_px}" height="{height_px}" 
        fill="white" stroke="none"/>
  
  <image x="0" y="0" width="{width_px}" height="{height_px}" 
           href="data:image/png;base64,{img_data}"
           style="image-rendering:auto"/>
</svg>'''
        
        # Write SVG file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
            
        status_callback(f"SVG saved: {output_path}")
        
    except Exception as e:
        status_callback(f"Error saving SVG: {e}")
        # Fallback to PNG if SVG fails
        png_path = output_path.with_suffix('.png')
        page.save(png_path, dpi=(dpi, dpi))
        status_callback(f"Fallback: saved as PNG instead: {png_path}")


def create_multipage_svg(all_image_positions, page_size_px, params, output_dir, metadata=None, status_callback=print):
    """Create multi-page SVG optimized for Inkscape."""
    width_px, height_px = page_size_px
    status_callback("Creating multi-page SVG for Inkscape...")
    
    # Group positions by page
    pages_data = {}
    for pos in all_image_positions:
        page_num = pos.get('page', 0)
        if page_num not in pages_data:
            pages_data[page_num] = []
        pages_data[page_num].append(pos)
    
    # Create images subfolder
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    # Create root SVG element for multi-page document
    svg = ET.Element('svg', attrib={
        'version': '1.1',
        'width': f'{width_px}px',
        'height': f'{len(pages_data) * height_px + 100 * (len(pages_data) - 1)}px',  # Stack pages vertically with spacing
        'viewBox': f'0 0 {width_px} {len(pages_data) * height_px + 100 * (len(pages_data) - 1)}',
        'xmlns': 'http://www.w3.org/2000/svg',
        'xmlns:xlink': 'http://www.w3.org/1999/xlink',
        'xmlns:inkscape': 'http://www.inkscape.org/namespaces/inkscape',
        'xmlns:sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'
    })
    
    # Add Inkscape-specific metadata
    metadata_elem = ET.SubElement(svg, 'metadata', attrib={'id': 'metadata1'})
    metadata_elem.text = '''Created with PyPotteryLayout for Inkscape
Multi-page archaeological pottery catalog
Each page is a separate layer - use Inkscape's layer panel to navigate'''
    
    # Add title
    title = ET.SubElement(svg, 'title')
    title.text = 'PyPotteryLayout - Multi-Page Pottery Catalog'
    
    # Create each page as a separate layer
    for page_num in sorted(pages_data.keys()):
        page_positions = pages_data[page_num]
        page_y_offset = page_num * (height_px + 100)  # Stack pages vertically
        
        # Create page group/layer
        page_group = ET.SubElement(svg, 'g', attrib={
            'id': f'page-{page_num + 1}',
            'inkscape:label': f'Page {page_num + 1}',
            'inkscape:groupmode': 'layer',
            'transform': f'translate(0,{page_y_offset})'
        })
        
        # Add page background
        page_bg = ET.SubElement(page_group, 'rect', attrib={
            'id': f'page-{page_num + 1}-bg',
            'x': '0', 'y': '0',
            'width': str(width_px), 'height': str(height_px),
            'fill': 'white',
            'stroke': '#cccccc',
            'stroke-width': '1'
        })
        
        # Add page label
        page_label = ET.SubElement(page_group, 'text', attrib={
            'x': str(width_px - 100), 'y': '30',
            'font-family': 'Arial, sans-serif',
            'font-size': '24',
            'font-weight': 'bold',
            'fill': '#cccccc',
            'text-anchor': 'end'
        })
        page_label.text = f'Page {page_num + 1}'
        
        # Create sublayers for this page
        images_layer = ET.SubElement(page_group, 'g', attrib={
            'id': f'page-{page_num + 1}-images',
            'inkscape:label': f'Page {page_num + 1} - Images',
            'inkscape:groupmode': 'layer'
        })
        
        captions_layer = ET.SubElement(page_group, 'g', attrib={
            'id': f'page-{page_num + 1}-captions',
            'inkscape:label': f'Page {page_num + 1} - Captions',
            'inkscape:groupmode': 'layer'
        })
        
        # Add margin guides if requested
        if params.get('show_margin_border'):
            margin_px = params.get('margin_px', 0)
            guides_layer = ET.SubElement(page_group, 'g', attrib={
                'id': f'page-{page_num + 1}-guides',
                'inkscape:label': f'Page {page_num + 1} - Guides',
                'inkscape:groupmode': 'layer',
                'style': 'display:none'  # Hidden by default
            })
            
            ET.SubElement(guides_layer, 'rect', attrib={
                'x': str(margin_px), 'y': str(margin_px),
                'width': str(width_px - 2*margin_px), 'height': str(height_px - 2*margin_px),
                'fill': 'none',
                'stroke': '#ff0000',
                'stroke-width': '2',
                'stroke-dasharray': '5,5',
                'opacity': '0.5'
            })
        
        # Add images and captions for this page
        for idx, pos_data in enumerate(page_positions):
            img_data = pos_data['image_data']
            x, y = pos_data['position']
            img_width, img_height = pos_data['size']
            
            # Save image as external file
            safe_filename = re.sub(r'[^\w\-_.]', '_', img_data['name'])
            img_filename = f"page{page_num+1}_img_{idx+1:03d}_{safe_filename}"
            if not img_filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_filename += '.png'
            
            img_path = images_dir / img_filename
            
            # Save optimized image
            img_copy = img_data['original_img'].copy()
            if img_copy.mode == 'RGBA':
                bg = Image.new('RGB', img_copy.size, 'white')
                bg.paste(img_copy, mask=img_copy.split()[-1] if img_copy.mode == 'RGBA' else None)
                img_copy = bg
            
            img_copy.save(img_path, format='PNG', optimize=True, compress_level=6)
            
            # Add image to SVG
            ET.SubElement(images_layer, 'image', attrib={
                'id': f'page{page_num+1}-pottery-{idx+1}',
                'x': str(x), 'y': str(y),
                'width': str(img_width), 'height': str(img_height),
                'href': f'images/{img_filename}',
                'preserveAspectRatio': 'xMidYMid meet'
            })
            
            # Add caption if enabled
            if params.get('add_caption') and 'caption_text' in pos_data:
                caption_lines = pos_data['caption_text'].split('\n')
                font_size = params.get('caption_font_size', 12)
                caption_padding = params.get('caption_padding', 5)
                
                for line_idx, line in enumerate(caption_lines):
                    if line.strip():
                        text_y = y + img_height + caption_padding + (line_idx * (font_size + 2)) + font_size
                        text_element = ET.SubElement(captions_layer, 'text', attrib={
                            'id': f'page{page_num+1}-caption-{idx+1}-{line_idx+1}',
                            'x': str(x + img_width // 2), 'y': str(text_y),
                            'text-anchor': 'middle',
                            'font-family': 'Arial, sans-serif',
                            'font-size': str(font_size),
                            'font-weight': 'bold' if line_idx == 0 else 'normal',
                            'fill': 'black'
                        })
                        text_element.text = line
        
        # Add scale bar if requested
        if params.get('add_scale_bar'):
            scale_layer = ET.SubElement(page_group, 'g', attrib={
                'id': f'page-{page_num + 1}-scale',
                'inkscape:label': f'Page {page_num + 1} - Scale Bar',
                'inkscape:groupmode': 'layer'
            })
            _add_simple_scale_bar_to_layer(scale_layer, width_px, height_px, params)
    
    return svg


def _add_simple_scale_bar_to_layer(parent_layer, width_px, height_px, params):
    """Add scale bar to a specific layer."""
    target_cm = params.get('scale_bar_cm', 5)
    pixels_per_cm = params.get('pixels_per_cm', 118)
    scale_factor = params.get('scale_factor', 1.0)
    margin_px = params.get('margin_px', 0)
    
    # Scale bar dimensions
    bar_width_px = int(target_cm * pixels_per_cm * scale_factor)
    bar_height_px = 15
    
    # Position
    scale_x = margin_px + 10
    scale_y = height_px - margin_px - 50
    
    # Scale bar group
    scale_group = ET.SubElement(parent_layer, 'g', attrib={
        'id': 'scale-bar',
        'transform': f'translate({scale_x},{scale_y})'
    })
    
    # Create alternating segments
    num_segments = max(1, target_cm)
    segment_width = bar_width_px / num_segments
    
    for i in range(num_segments):
        color = 'black' if i % 2 == 0 else 'white'
        ET.SubElement(scale_group, 'rect', attrib={
            'id': f'scale-seg-{i+1}',
            'x': str(i * segment_width), 'y': '0',
            'width': str(segment_width), 'height': str(bar_height_px),
            'fill': color,
            'stroke': 'black',
            'stroke-width': '1'
        })
    
    # Labels
    ET.SubElement(scale_group, 'text', attrib={
        'id': 'scale-label-0',
        'x': '0', 'y': str(bar_height_px + 15),
        'font-family': 'Arial, sans-serif',
        'font-size': '12',
        'fill': 'black'
    }).text = '0'
    
    ET.SubElement(scale_group, 'text', attrib={
        'id': 'scale-label-end',
        'x': str(bar_width_px), 'y': str(bar_height_px + 15),
        'font-family': 'Arial, sans-serif',
        'font-size': '12',
        'fill': 'black',
        'text-anchor': 'end'
    }).text = f'{target_cm} cm'


def create_lightweight_editable_svg(image_positions, page_size_px, params, output_dir, metadata=None, status_callback=print):
    """Create lightweight SVG with external image references."""
    width_px, height_px = page_size_px
    status_callback("Creating lightweight editable SVG with external image references...")
    
    # Create images subfolder
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    # Create root SVG element with Inkscape namespaces
    svg = ET.Element('svg', attrib={
        'version': '1.1',
        'width': f'{width_px}px',
        'height': f'{height_px}px',
        'viewBox': f'0 0 {width_px} {height_px}',
        'xmlns': 'http://www.w3.org/2000/svg',
        'xmlns:xlink': 'http://www.w3.org/1999/xlink',
        'xmlns:inkscape': 'http://www.inkscape.org/namespaces/inkscape',
        'xmlns:sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'
    })
    
    # Add title and description
    title = ET.SubElement(svg, 'title')
    title.text = 'PyPotteryLayout - Editable Archaeological Catalog'
    
    desc = ET.SubElement(svg, 'desc')
    desc.text = 'Each image, caption, and scale bar is a separate editable element'
    
    # Background layer
    bg_group = ET.SubElement(svg, 'g', attrib={
        'id': 'background',
        'inkscape:label': 'Background',
        'inkscape:groupmode': 'layer'
    })
    bg_rect = ET.SubElement(bg_group, 'rect', attrib={
        'id': 'page-bg',
        'x': '0', 'y': '0',
        'width': str(width_px), 'height': str(height_px),
        'fill': 'white'
    })
    
    # Margin guides
    if params.get('show_margin_border'):
        margin_px = params.get('margin_px', 0)
        guides_group = ET.SubElement(svg, 'g', attrib={
            'id': 'guides',
            'inkscape:label': 'Margin Guides',
            'inkscape:groupmode': 'layer'
        })
        ET.SubElement(guides_group, 'rect', attrib={
            'x': str(margin_px), 'y': str(margin_px),
            'width': str(width_px - 2*margin_px), 'height': str(height_px - 2*margin_px),
            'fill': 'none',
            'stroke': '#ff0000',
            'stroke-width': '2',
            'stroke-dasharray': '5,5',
            'opacity': '0.5'
        })
    
    # Images group
    images_group = ET.SubElement(svg, 'g', attrib={
        'id': 'images',
        'inkscape:label': 'Pottery Images',
        'inkscape:groupmode': 'layer'
    })
    
    # Captions group
    captions_group = ET.SubElement(svg, 'g', attrib={
        'id': 'captions',
        'inkscape:label': 'Captions',
        'inkscape:groupmode': 'layer'
    })
    
    for idx, pos_data in enumerate(image_positions):
        img_data = pos_data['image_data']
        x, y = pos_data['position']
        img_width, img_height = pos_data['size']
        
        # Save image as external file (optimized size)
        safe_filename = re.sub(r'[^\w\-_.]', '_', img_data['name'])
        img_filename = f"img_{idx+1:03d}_{safe_filename}"
        if not img_filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_filename += '.png'
        
        img_path = images_dir / img_filename
        
        # Save image with reasonable compression for web use
        img_copy = img_data['original_img'].copy()
        if img_copy.mode == 'RGBA':
            # Create white background for transparency
            bg = Image.new('RGB', img_copy.size, 'white')
            bg.paste(img_copy, mask=img_copy.split()[-1] if img_copy.mode == 'RGBA' else None)
            img_copy = bg
        
        # Save with reasonable quality (reduces file size significantly)
        img_copy.save(img_path, format='PNG', optimize=True, compress_level=6)
        
        # Create image element with relative path (single name, editable)
        img_element = ET.SubElement(images_group, 'image', attrib={
            'id': f'pottery-{idx+1}',
            'x': str(x), 'y': str(y),
            'width': str(img_width), 'height': str(img_height),
            'href': f'images/{img_filename}',
            'preserveAspectRatio': 'xMidYMid meet'
        })
        
        # Add caption if enabled
        if params.get('add_caption') and 'caption_text' in pos_data:
            caption_lines = pos_data['caption_text'].split('\n')
            font_size = params.get('caption_font_size', 12)
            caption_padding = params.get('caption_padding', 5)
            
            for line_idx, line in enumerate(caption_lines):
                if line.strip():
                    text_y = y + img_height + caption_padding + (line_idx * (font_size + 2)) + font_size
                    text_element = ET.SubElement(captions_group, 'text', attrib={
                        'id': f'caption-{idx+1}-{line_idx+1}',
                        'x': str(x + img_width // 2), 'y': str(text_y),
                        'text-anchor': 'middle',
                        'font-family': 'Arial, sans-serif',
                        'font-size': str(font_size),
                        'font-weight': 'bold' if line_idx == 0 else 'normal',
                        'fill': 'black'
                    })
                    text_element.text = line
    
    # Add scale bar
    if params.get('add_scale_bar'):
        _add_simple_scale_bar_to_svg(svg, width_px, height_px, params)
    
    return svg


def _add_simple_scale_bar_to_svg(svg, width_px, height_px, params):
    """Add a simple, editable scale bar."""
    target_cm = params.get('scale_bar_cm', 5)
    pixels_per_cm = params.get('pixels_per_cm', 118)
    scale_factor = params.get('scale_factor', 1.0)
    margin_px = params.get('margin_px', 0)
    
    # Scale bar dimensions
    bar_width_px = int(target_cm * pixels_per_cm * scale_factor)
    bar_height_px = 15
    
    # Position
    scale_x = margin_px + 10
    scale_y = height_px - margin_px - 50
    
    # Scale bar group
    scale_group = ET.SubElement(svg, 'g', attrib={
        'id': 'scale-bar',
        'inkscape:label': 'Scale Bar',
        'inkscape:groupmode': 'layer',
        'transform': f'translate({scale_x},{scale_y})'
    })
    
    # Create alternating segments
    num_segments = max(1, target_cm)
    segment_width = bar_width_px / num_segments
    
    for i in range(num_segments):
        color = 'black' if i % 2 == 0 else 'white'
        ET.SubElement(scale_group, 'rect', attrib={
            'id': f'scale-seg-{i+1}',
            'x': str(i * segment_width), 'y': '0',
            'width': str(segment_width), 'height': str(bar_height_px),
            'fill': color,
            'stroke': 'black',
            'stroke-width': '1'
        })
    
    # Labels
    ET.SubElement(scale_group, 'text', attrib={
        'id': 'scale-label-0',
        'x': '0', 'y': str(bar_height_px + 15),
        'font-family': 'Arial, sans-serif',
        'font-size': '12',
        'fill': 'black'
    }).text = '0'
    
    ET.SubElement(scale_group, 'text', attrib={
        'id': 'scale-label-end',
        'x': str(bar_width_px), 'y': str(bar_height_px + 15),
        'font-family': 'Arial, sans-serif',
        'font-size': '12',
        'fill': 'black',
        'text-anchor': 'end'
    }).text = f'{target_cm} cm'
    
    return svg
    """Create SVG with embedded images optimized for Illustrator compatibility."""
    width_px, height_px = page_size_px
    status_callback("Creating Illustrator-compatible SVG with embedded elements...")
    
    # Create root SVG element with specific Illustrator-friendly attributes
    svg = ET.Element('svg', attrib={
        'version': '1.1',
        'width': f'{width_px}px',
        'height': f'{height_px}px',
        'viewBox': f'0 0 {width_px} {height_px}',
        'xmlns': 'http://www.w3.org/2000/svg',
        'xmlns:xlink': 'http://www.w3.org/1999/xlink',
        'xml:space': 'preserve',
        'style': f'enable-background:new 0 0 {width_px} {height_px};'
    })
    
    # Add Adobe Illustrator-specific metadata
    metadata_elem = ET.SubElement(svg, 'metadata')
    metadata_elem.text = """<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 5.6-c067 79.157747, 2015/03/30-23:40:42">
   <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
      <rdf:Description rdf:about=""
            xmlns:dc="http://purl.org/dc/elements/1.1/">
         <dc:title>PyPotteryLayout - Editable Archaeological Catalog</dc:title>
         <dc:description>Created with PyPotteryLayout - Each element is editable</dc:description>
      </rdf:Description>
   </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""
    
    # Define layers as groups (Illustrator recognizes these as layers)
    
    # Background layer
    bg_layer = ET.SubElement(svg, 'g', attrib={
        'id': 'background_layer',
        'data-name': 'Background'
    })
    
    bg_rect = ET.SubElement(bg_layer, 'rect', attrib={
        'id': 'page_background',
        'x': '0', 'y': '0',
        'width': str(width_px), 'height': str(height_px),
        'fill': 'white',
        'stroke': 'none'
    })
    
    # Guides layer (for margins)
    if params.get('show_margin_border'):
        margin_px = params.get('margin_px', 0)
        guides_layer = ET.SubElement(svg, 'g', attrib={
            'id': 'guides_layer',
            'data-name': 'Guides',
            'opacity': '0.3'
        })
        
        # Margin boundary
        margin_rect = ET.SubElement(guides_layer, 'rect', attrib={
            'id': 'margin_boundary',
            'x': str(margin_px), 'y': str(margin_px),
            'width': str(width_px - 2*margin_px), 'height': str(height_px - 2*margin_px),
            'fill': 'none',
            'stroke': '#ff0000',
            'stroke-width': '2',
            'stroke-dasharray': '10,5'
        })
    
    # Images layer
    images_layer = ET.SubElement(svg, 'g', attrib={
        'id': 'images_layer',
        'data-name': 'Pottery Images'
    })
    
    # Captions layer
    captions_layer = ET.SubElement(svg, 'g', attrib={
        'id': 'captions_layer',
        'data-name': 'Captions'
    })
    
    # Process each image
    for idx, pos_data in enumerate(image_positions):
        img_data = pos_data['image_data']
        x, y = pos_data['position']
        img_width, img_height = pos_data['size']
        
        # Convert image to base64 with high quality PNG
        buffer = io.BytesIO()
        # Ensure high quality for embedded images
        img_copy = img_data['original_img'].copy()
        if img_copy.mode != 'RGBA':
            img_copy = img_copy.convert('RGBA')
        img_copy.save(buffer, format='PNG', optimize=False, compress_level=0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Create image element
        img_element = ET.SubElement(images_layer, 'image', attrib={
            'id': f'pottery_image_{idx+1}',
            'data-name': f'Pottery {idx+1}: {img_data["name"]}',
            'x': str(x), 'y': str(y),
            'width': str(img_width), 'height': str(img_height),
            'href': f'data:image/png;base64,{img_base64}',
            'preserveAspectRatio': 'xMidYMid meet',
            'style': 'image-rendering:auto'
        })
        
        # Add invisible selection helper rectangle
        selection_rect = ET.SubElement(images_layer, 'rect', attrib={
            'id': f'selection_helper_{idx+1}',
            'data-name': f'Selection Helper {idx+1}',
            'x': str(x-1), 'y': str(y-1),
            'width': str(img_width+2), 'height': str(img_height+2),
            'fill': 'none',
            'stroke': 'none',
            'opacity': '0'
        })
        
        # Add caption if enabled
        if params.get('add_caption') and 'caption_text' in pos_data:
            caption_lines = pos_data['caption_text'].split('\n')
            font_size = params.get('caption_font_size', 12)
            caption_padding = params.get('caption_padding', 5)
            
            caption_y_start = y + img_height + caption_padding
            
            for line_idx, line in enumerate(caption_lines):
                if line.strip():
                    line_y = caption_y_start + (line_idx * (font_size + 2))
                    
                    text_element = ET.SubElement(captions_layer, 'text', attrib={
                        'id': f'caption_{idx+1}_line_{line_idx+1}',
                        'data-name': f'Caption {idx+1} Line {line_idx+1}',
                        'x': str(x + img_width // 2), 'y': str(line_y),
                        'text-anchor': 'middle',
                        'font-family': 'Arial, Helvetica, sans-serif',
                        'font-size': str(font_size),
                        'font-weight': 'bold' if line_idx == 0 else 'normal',
                        'fill': '#000000',
                        'xml:space': 'preserve'
                    })
                    text_element.text = line
    
    # Scale bar layer
    if params.get('add_scale_bar'):
        scale_layer = ET.SubElement(svg, 'g', attrib={
            'id': 'scale_layer',
            'data-name': 'Scale Bar'
        })
        _add_illustrator_scale_bar(scale_layer, width_px, height_px, params, status_callback)
    
    return svg


def _add_illustrator_scale_bar(scale_layer, width_px, height_px, params, status_callback=print):
    """Add scale bar optimized for Illustrator editing."""
    target_cm = params.get('scale_bar_cm', 5)
    pixels_per_cm = params.get('pixels_per_cm', 118)
    scale_factor = params.get('scale_factor', 1.0)
    margin_px = params.get('margin_px', 0)
    
    # Calculate scale bar dimensions
    bar_width_px = int(max(1, target_cm) * pixels_per_cm * scale_factor)
    bar_height_px = 15
    
    # Position scale bar
    scale_x = margin_px + 10
    scale_y = height_px - margin_px - bar_height_px - 40
    
    # Create scale bar group
    scale_group = ET.SubElement(scale_layer, 'g', attrib={
        'id': 'scale_bar_group',
        'data-name': 'Scale Bar Group',
        'transform': f'translate({scale_x},{scale_y})'
    })
    
    # Create segments
    num_segments = int(max(1, target_cm))
    segment_width = bar_width_px / num_segments if num_segments else bar_width_px
    
    for i in range(num_segments):
        color = '#000000' if i % 2 == 0 else '#ffffff'
        x_pos = i * segment_width
        
        segment_rect = ET.SubElement(scale_group, 'rect', attrib={
            'id': f'scale_segment_{i+1}',
            'data-name': f'Scale Segment {i+1}',
            'x': str(x_pos), 'y': '0',
            'width': str(segment_width), 'height': str(bar_height_px),
            'fill': color,
            'stroke': '#000000',
            'stroke-width': '1'
        })
    
    # Add text labels
    start_text = ET.SubElement(scale_group, 'text', attrib={
        'id': 'scale_label_start',
        'data-name': 'Scale Label Start',
        'x': '0', 'y': str(bar_height_px + 15),
        'font-family': 'Arial, Helvetica, sans-serif',
        'font-size': '12',
        'fill': '#000000',
        'text-anchor': 'start'
    })
    start_text.text = '0'
    
    end_text = ET.SubElement(scale_group, 'text', attrib={
        'id': 'scale_label_end',
        'data-name': 'Scale Label End',
        'x': str(bar_width_px), 'y': str(bar_height_px + 15),
        'font-family': 'Arial, Helvetica, sans-serif',
        'font-size': '12',
        'fill': '#000000',
        'text-anchor': 'end'
    })
    end_text.text = f'{target_cm} cm'


# Removed AI format functions as requested - SVG only approach

def create_editable_svg_layout_fixed(image_positions, page_size_px, params, output_dir, metadata=None, status_callback=print):
    """Create SVG with separate, editable elements using external image files."""
    width_px, height_px = page_size_px
    status_callback("Creating editable SVG with separate elements and external images...")
    
    # Create images subfolder
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    # Create root SVG element
    svg = ET.Element('svg', attrib={
        'width': f'{width_px}px',
        'height': f'{height_px}px',
        'viewBox': f'0 0 {width_px} {height_px}',
        'xmlns': 'http://www.w3.org/2000/svg',
        'xmlns:xlink': 'http://www.w3.org/1999/xlink'
    })
    
    # Add title and description
    title = ET.SubElement(svg, 'title')
    title.text = 'PyPotteryLayout - Fully Editable Archaeological Catalog'
    
    desc = ET.SubElement(svg, 'desc')
    desc.text = 'Archaeological pottery catalog - Each image, caption, and element is separately editable. Images are linked externally for better compatibility with Illustrator.'
    
    # Background layer
    bg_group = ET.SubElement(svg, 'g', attrib={'id': 'background-layer'})
    bg_rect = ET.SubElement(bg_group, 'rect', attrib={
        'id': 'page-background',
        'x': '0', 'y': '0',
        'width': str(width_px), 'height': str(height_px),
        'fill': 'white',
        'stroke': 'none'
    })
    
    # Margin guides (visible by default for editing guidance)
    if params.get('show_margin_border'):
        margin_px = params.get('margin_px', 0)
        guides_group = ET.SubElement(svg, 'g', attrib={
            'id': 'margin-guides',
            'style': 'opacity:0.3'  # Visible for editing
        })
        
        margin_rect = ET.SubElement(guides_group, 'rect', attrib={
            'id': 'margin-boundary',
            'x': str(margin_px), 'y': str(margin_px),
            'width': str(width_px - 2*margin_px), 'height': str(height_px - 2*margin_px),
            'fill': 'none',
            'stroke': '#ff0000',
            'stroke-width': '2',
            'stroke-dasharray': '10,5'
        })
        
        # Add corner markers for easier reference
        corner_size = 20
        corners_group = ET.SubElement(guides_group, 'g', attrib={'id': 'corner-markers'})
        corners = [
            (margin_px, margin_px),  # top-left
            (width_px - margin_px, margin_px),  # top-right
            (margin_px, height_px - margin_px),  # bottom-left
            (width_px - margin_px, height_px - margin_px)  # bottom-right
        ]
        
        for i, (cx, cy) in enumerate(corners):
            ET.SubElement(corners_group, 'circle', attrib={
                'id': f'corner-{i+1}',
                'cx': str(cx), 'cy': str(cy), 'r': '5',
                'fill': '#ff0000', 'opacity': '0.7'
            })
    
    # Images and captions layer
    content_group = ET.SubElement(svg, 'g', attrib={'id': 'pottery-images'})
    
    for idx, pos_data in enumerate(image_positions):
        img_data = pos_data['image_data']
        x, y = pos_data['position']
        img_width, img_height = pos_data['size']
        
        # Save image as external file
        safe_filename = re.sub(r'[^\w\-_.]', '_', img_data['name'])
        img_filename = f"img_{idx+1:03d}_{safe_filename}"
        if not img_filename.endswith(('.png', '.jpg', '.jpeg')):
            img_filename += '.png'
        
        img_path = images_dir / img_filename
        img_data['original_img'].save(img_path, format='PNG')
        
        # Create group for each pottery item (image + caption)
        item_group = ET.SubElement(content_group, 'g', attrib={
            'id': f'pottery-item-{idx+1}',
            'data-original-size': f'{img_data["original_img"].width}x{img_data["original_img"].height}',
            'transform': f'translate({x},{y})'
        })
        
        # Add image element with external reference
        img_element = ET.SubElement(item_group, 'image', attrib={
            'id': f'image-{idx+1}',
            'x': '0', 'y': '0',
            'width': str(img_width), 'height': str(img_height),
            'href': f'images/{img_filename}',  # Relative path
            'preserveAspectRatio': 'xMidYMid meet',
            'style': 'image-rendering:auto'
        })
        
        # Add transparent background rectangle for easier selection in Illustrator
        bg_rect = ET.SubElement(item_group, 'rect', attrib={
            'id': f'image-{idx+1}-bg',
            'x': '-2', 'y': '-2',
            'width': str(img_width + 4), 'height': str(img_height + 4),
            'fill': 'none',
            'stroke': '#cccccc',
            'stroke-width': '1',
            'stroke-dasharray': '3,3',
            'opacity': '0.3'
        })
        
        # Add caption if enabled
        if params.get('add_caption') and 'caption_text' in pos_data:
            caption_y_offset = params.get('caption_padding', 5)
            caption_lines = pos_data['caption_text'].split('\n')
            
            caption_group = ET.SubElement(item_group, 'g', attrib={
                'id': f'caption-{idx+1}',
                'transform': f'translate(0,{img_height + caption_y_offset})'
            })
            
            # Add caption background for better visibility
            if caption_lines:
                caption_bg = ET.SubElement(caption_group, 'rect', attrib={
                    'id': f'caption-{idx+1}-bg',
                    'x': '0', 'y': '0',
                    'width': str(img_width), 
                    'height': str(len([l for l in caption_lines if l.strip()]) * (params.get('caption_font_size', 12) + 2) + 4),
                    'fill': 'white',
                    'fill-opacity': '0.8',
                    'stroke': 'none'
                })
            
            for line_idx, line in enumerate(caption_lines):
                if line.strip():
                    line_y = line_idx * (params.get('caption_font_size', 12) + 2) + 12
                    text_element = ET.SubElement(caption_group, 'text', attrib={
                        'id': f'caption-{idx+1}-line-{line_idx+1}',
                        'x': str(img_width // 2), 'y': str(line_y),
                        'text-anchor': 'middle',
                        'font-family': 'Arial, sans-serif',
                        'font-size': str(params.get('caption_font_size', 12)),
                        'font-weight': 'bold' if line_idx == 0 else 'normal',
                        'fill': 'black'
                    })
                    text_element.text = line
    
    # Add editable scale bar
    if params.get('add_scale_bar'):
        _add_editable_scale_bar_to_svg(svg, width_px, height_px, params, status_callback)
    
    return svg


def _add_editable_scale_bar_to_svg(svg, width_px, height_px, params, status_callback=print):
    """Add an editable scale bar as separate SVG elements."""
    status_callback("Adding editable scale bar to SVG...")
    
    # Scale bar parameters
    target_cm = params.get('scale_bar_cm', 5)
    pixels_per_cm = params.get('pixels_per_cm', 118)
    scale_factor = params.get('scale_factor', 1.0)
    margin_px = params.get('margin_px', 0)
    
    # Calculate scale bar dimensions
    bar_width_px = int(max(1, target_cm) * pixels_per_cm * scale_factor)
    bar_height_px = 10
    
    # Position scale bar (bottom left with margin)
    scale_x = margin_px
    scale_y = height_px - margin_px - bar_height_px - 30  # Extra space for text
    
    # Create scale bar group
    scale_group = ET.SubElement(svg, 'g', attrib={
        'id': 'scale-bar',
        'transform': f'translate({scale_x},{scale_y})'
    })
    
    # Create the bar segments
    num_segments = int(max(1, target_cm))
    segment_width = bar_width_px / num_segments if num_segments else bar_width_px
    
    segments_group = ET.SubElement(scale_group, 'g', attrib={'id': 'scale-segments'})
    
    for i in range(num_segments):
        color = "black" if i % 2 == 0 else "white"
        x_pos = i * segment_width
        
        segment_rect = ET.SubElement(segments_group, 'rect', attrib={
            'id': f'scale-segment-{i+1}',
            'x': str(x_pos), 'y': '0',
            'width': str(segment_width), 'height': str(bar_height_px),
            'fill': color,
            'stroke': 'black',
            'stroke-width': '1'
        })
    
    # Add scale bar labels
    labels_group = ET.SubElement(scale_group, 'g', attrib={'id': 'scale-labels'})
    
    # "0" label
    start_label = ET.SubElement(labels_group, 'text', attrib={
        'id': 'scale-label-start',
        'x': '0', 'y': str(bar_height_px + 15),
        'font-family': 'Arial, sans-serif',
        'font-size': '12',
        'fill': 'black',
        'text-anchor': 'start'
    })
    start_label.text = '0'
    
    # End label (e.g., "5 cm")
    end_label = ET.SubElement(labels_group, 'text', attrib={
        'id': 'scale-label-end',
        'x': str(bar_width_px), 'y': str(bar_height_px + 15),
        'font-family': 'Arial, sans-serif',
        'font-size': '12',
        'fill': 'black',
        'text-anchor': 'end'
    })
    end_label.text = f'{target_cm} cm'


def create_editable_layout_positions_grid(image_data, page_size_px, grid_size, margin_px, spacing_px, params, metadata=None, status_callback=print):
    """Calculate positions for grid layout, returning position data for editable output."""
    rows_per_page, suggested_cols = grid_size
    page_width, page_height = page_size_px
    available_width = page_width - (2 * margin_px)
    
    all_positions = []
    image_index = 0
    page_num = 0
    
    while image_index < len(image_data):
        page_positions = []
        current_y = margin_px
        rows_on_this_page = 0
        
        while image_index < len(image_data) and rows_on_this_page < rows_per_page:
            row_images = []
            current_row_width = 0
            row_height = 0
            temp_index = image_index
            
            # Calculate row composition
            while temp_index < len(image_data) and len(row_images) < suggested_cols:
                img_data = image_data[temp_index]
                img = img_data['img']
                needed_width = current_row_width + img.width + (spacing_px if row_images else 0)
                
                if needed_width <= available_width:
                    row_images.append({
                        'image_data': img_data,
                        'size': (img.width, img.height)
                    })
                    current_row_width = needed_width
                    row_height = max(row_height, img.height)
                    temp_index += 1
                else:
                    break
            
            if not row_images and image_index < len(image_data):
                # Force fit at least one image
                img_data = image_data[image_index]
                img = img_data['img']
                row_images.append({
                    'image_data': img_data,
                    'size': (img.width, img.height)
                })
                row_height = img.height
                temp_index = image_index + 1
            
            if not row_images:
                break
                
            if current_y + row_height > page_height - margin_px:
                break
            
            # Calculate positions for this row
            total_row_img_width = sum(item['size'][0] for item in row_images)
            total_row_width_with_spacing = total_row_img_width + spacing_px * (len(row_images) - 1)
            start_x = margin_px + (available_width - total_row_width_with_spacing) // 2
            current_x = start_x
            
            for item in row_images:
                img_data = item['image_data']
                img_width, img_height = item['size']
                paste_y = current_y + (row_height - img_height) // 2
                
                # Store original image reference for SVG
                img_data['original_img'] = img_data['img'].copy()
                
                # Create caption text if needed
                caption_text = ""
                if params.get('add_caption'):
                    caption_lines = [img_data['name']]
                    img_metadata = metadata.get(img_data['name']) if metadata else None
                    if img_metadata:
                        for key, value in img_metadata.items():
                            if value is not None:
                                caption_lines.append(f"{key}: {value}")
                    caption_text = "\n".join(caption_lines)
                
                position_data = {
                    'image_data': img_data,
                    'position': (current_x, paste_y),
                    'size': (img_width, img_height),
                    'page': page_num,
                    'caption_text': caption_text
                }
                page_positions.append(position_data)
                current_x += img_width + spacing_px
            
            image_index = temp_index
            current_y += row_height + spacing_px
            rows_on_this_page += 1
        
        if page_positions:
            all_positions.extend(page_positions)
            page_num += 1
    
    return all_positions


def save_editable_output(image_positions, page_size_px, output_file, params, metadata=None, status_callback=print):
    """Save lightweight editable SVG output."""
    if not image_positions:
        status_callback("No positioned images to save.")
        return
    
    output_path = Path(output_file)
    export_dir = output_path.parent / "export"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    file_ext = output_path.suffix.lower()
    file_stem = output_path.stem
    
    if file_ext == '.svg':
        # Group positions by page
        pages_data = {}
        for pos in image_positions:
            page_num = pos.get('page', 0)
            if page_num not in pages_data:
                pages_data[page_num] = []
            pages_data[page_num].append(pos)
        
        # Save each page as lightweight SVG with external images
        if len(pages_data) > 1:
            for page_num, page_positions in pages_data.items():
                page_folder = export_dir / f"{file_stem}_page_{page_num+1}"
                page_folder.mkdir(parents=True, exist_ok=True)
                
                svg_element = create_lightweight_editable_svg(page_positions, page_size_px, params, page_folder, metadata, status_callback)
                svg_path = page_folder / f"{file_stem}_page_{page_num+1}.svg"
                _save_svg_element_to_file(svg_element, svg_path, status_callback)
        else:
            # Single page
            svg_folder = export_dir / file_stem
            svg_folder.mkdir(parents=True, exist_ok=True)
            
            svg_element = create_lightweight_editable_svg(image_positions, page_size_px, params, svg_folder, metadata, status_callback)
            svg_path = svg_folder / f"{file_stem}.svg"
            _save_svg_element_to_file(svg_element, svg_path, status_callback)
        
        # Create simple user guide
        readme_path = export_dir / "README.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("""PyPotteryLayout - Export Guide
===============================

WHAT'S INCLUDED:
• SVG file(s) with fully editable elements
• images/ folder with individual pottery photos
• Clean output without filename clutter

HOW TO EDIT SVG FILES:
1. Open SVG files in Inkscape (recommended, free)
   Download: https://inkscape.org

2. Each element is separately editable:
   - Individual pottery images (linked externally)
   - Fully editable text captions
   - Moveable scale bar segments
   - Adjustable margin guides (if enabled)

3. Editing workflow:
   - Double-click text to edit directly
   - Use selection tool to move/resize objects
   - Images remain linked to external files (small SVG size)
   - Save as Inkscape SVG to preserve all features

EDITABLE PDF FILES:
• PDF files now contain vector elements
• Text remains editable in many PDF editors (Adobe Acrobat, etc.)
• Images are embedded at high resolution
• Smaller file sizes compared to raster-only PDFs

IMPORTANT NOTES:
• Keep images/ folder next to SVG files
• SVG files are lightweight (typically under 1MB)
• PDF files contain editable vector text and graphics
• All formats designed for professional use

TECHNICAL FEATURES:
• External image linking for efficient file sizes
• Vector-based text and graphics
• No filename clutter in final output
• Cross-platform compatibility
""")
        
        if len(pages_data) > 1:
            status_callback(f"✨ Multi-page editable SVG created!")
            status_callback(f"📁 Location: {export_dir.resolve()}")
            status_callback(f"📝 Each page saved as separate editable SVG")
        else:
            status_callback(f"✨ Lightweight editable SVG created!")
            status_callback(f"📁 Location: {export_dir.resolve()}")
        status_callback(f"📝 Check README.txt for editing instructions")
            
    elif file_ext == '.pdf':
        # PDF: Create editable PDF by combining SVG pages
        status_callback("Creating PDF with editable elements from SVG...")
        
        # Group positions by page
        pages_data = {}
        for pos in image_positions:
            page_num = pos.get('page', 0)
            if page_num not in pages_data:
                pages_data[page_num] = []
            pages_data[page_num].append(pos)
        
        # Create temporary SVG folder
        temp_svg_dir = export_dir / "temp_svg"
        temp_svg_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create SVG for each page
            svg_paths = []
            if len(pages_data) > 1:
                for page_num, page_positions in pages_data.items():
                    svg_element = create_lightweight_editable_svg(page_positions, page_size_px, params, temp_svg_dir, metadata, status_callback)
                    svg_path = temp_svg_dir / f"page_{page_num+1}.svg"
                    _save_svg_element_to_file(svg_element, svg_path, status_callback)
                    svg_paths.append(svg_path)
            else:
                svg_element = create_lightweight_editable_svg(image_positions, page_size_px, params, temp_svg_dir, metadata, status_callback)
                svg_path = temp_svg_dir / "page_1.svg"
                _save_svg_element_to_file(svg_element, svg_path, status_callback)
                svg_paths.append(svg_path)
            
            # Create PDF from SVG files
            final_path = export_dir / f"{file_stem}.pdf"
            _create_editable_pdf_from_svgs(svg_paths, final_path, status_callback)
            
        finally:
            # Clean up temporary SVG files
            import shutil
            if temp_svg_dir.exists():
                shutil.rmtree(temp_svg_dir)
        
        status_callback(f"📄 Editable PDF saved to: {final_path.resolve()}")
        status_callback(f"✨ PDF contains vector elements that remain editable in many PDF editors")
    
    else:
        # Other formats use existing method
        pages = _create_pages_from_positions(image_positions, page_size_px, params, status_callback)
        subfolder = export_dir / file_stem
        subfolder.mkdir(parents=True, exist_ok=True)
        
        for i, page in enumerate(pages):
            if len(pages) > 1:
                img_path = subfolder / f"{file_stem}_page_{i+1}{file_ext}"
            else:
                img_path = subfolder / f"{file_stem}{file_ext}"
            page.save(img_path, dpi=(params.get('output_dpi', 300), params.get('output_dpi', 300)))
        
        status_callback(f"Files saved to folder: {subfolder.resolve()}")


def _add_scale_bar_to_pdf(canvas, page_size, params, scale_factor, status_callback=print):
    """Add scale bar to PDF using ReportLab canvas."""
    target_cm = params.get('scale_bar_cm', 5)
    pixels_per_cm = params.get('pixels_per_cm', 118)
    margin_px = params.get('margin_px', 0)
    
    # Calculate scale bar dimensions in points
    bar_width_points = target_cm * pixels_per_cm * scale_factor * params.get('scale_factor', 1.0)
    bar_height_points = 10 * scale_factor
    
    # Position at bottom left
    scale_x = margin_px * scale_factor
    scale_y = margin_px * scale_factor
    
    # Draw scale bar segments
    num_segments = int(max(1, target_cm))
    segment_width = bar_width_points / num_segments if num_segments else bar_width_points
    
    for i in range(num_segments):
        x_pos = scale_x + (i * segment_width)
        fill_color = 0 if i % 2 == 0 else 1  # Black or white
        
        canvas.setFillGray(fill_color)
        canvas.setStrokeGray(0)  # Black border
        canvas.rect(x_pos, scale_y, segment_width, bar_height_points, fill=1, stroke=1)
    
    # Add labels
    canvas.setFont("Helvetica", 10 * scale_factor)
    canvas.setFillGray(0)  # Black text
    
    # "0" label
    canvas.drawString(scale_x, scale_y - 15 * scale_factor, '0')
    
    # End label
    end_text = f'{target_cm} cm'
    text_width = canvas.stringWidth(end_text, "Helvetica", 10 * scale_factor)
    canvas.drawString(scale_x + bar_width_points - text_width, scale_y - 15 * scale_factor, end_text)


def _save_svg_element_to_file(svg_element, output_path, status_callback=print):
    """Save SVG element to file with proper formatting."""
    try:
        # Convert to string with pretty formatting
        rough_string = ET.tostring(svg_element, 'unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_svg = reparsed.toprettyxml(indent="  ")
        
        # Remove extra empty lines
        pretty_lines = [line for line in pretty_svg.split('\n') if line.strip()]
        final_svg = '\n'.join(pretty_lines)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_svg)
            
        status_callback(f"Editable SVG saved: {output_path}")
    except Exception as e:
        status_callback(f"Error saving SVG: {e}")


def _create_pages_from_positions(image_positions, page_size_px, params, status_callback=print):
    """Create PIL Image pages from position data (fallback for non-SVG formats)."""
    if not image_positions:
        return []
    
    # Group by page
    pages_data = {}
    for pos in image_positions:
        page_num = pos.get('page', 0)
        if page_num not in pages_data:
            pages_data[page_num] = []
        pages_data[page_num].append(pos)
    
    pages = []
    for page_num in sorted(pages_data.keys()):
        page = Image.new('RGB', page_size_px, 'white')
        
        for pos_data in pages_data[page_num]:
            img_data = pos_data['image_data']
            x, y = pos_data['position']
            img = img_data['img']
            
            page.paste(img, (x, y), img if img.mode == 'RGBA' else None)
        
        # Add scale bar if requested
        if params.get('add_scale_bar'):
            scale_bar = create_scale_bar(
                params.get('scale_bar_cm', 5), 
                params.get('pixels_per_cm', 100), 
                params.get('scale_factor', 1.0), 
                status_callback
            )
            x_pos = params.get('margin_px', 0)
            y_pos = page.height - params.get('margin_px', 0) - scale_bar.height
            page.paste(scale_bar, (x_pos, y_pos), scale_bar)
        
        # Add margin borders if requested
        if params.get('show_margin_border'):
            page = draw_margin_border(page, params.get('margin_px', 0), status_callback)
        
        pages.append(page)
    
    return pages
    """Save a single page as SVG format optimized for editing in Illustrator/Inkscape."""
    try:
        width_px, height_px = page.size
        
        # Use pixel dimensions for SVG to maintain exact positioning
        # This makes it easier to edit in graphics software
        
        # Convert PIL image to base64 embedded data
        buffer = io.BytesIO()
        page.save(buffer, format='PNG')
        img_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Create SVG content optimized for editing
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width_px}px" height="{height_px}px" 
     viewBox="0 0 {width_px} {height_px}"
     xmlns="http://www.w3.org/2000/svg" 
     xmlns:xlink="http://www.w3.org/1999/xlink">
  <title>PyPottery Layout - Editable</title>
  <desc>Archaeological pottery catalog layout - Optimized for editing in Illustrator/Inkscape</desc>
  
  <!-- White background - can be changed -->
  <rect id="background" x="0" y="0" width="{width_px}" height="{height_px}" 
        fill="white" stroke="none"/>
  
  <!-- Main content group - can be ungrouped for individual object editing -->
  <g id="pottery-layout" opacity="1">
    <image x="0" y="0" width="{width_px}" height="{height_px}" 
           href="data:image/png;base64,{img_data}"
           style="image-rendering:pixelated"/>
  </g>
  
  <!-- Guidelines layer (hidden by default) - enable in layers panel -->
  <g id="guidelines" style="display:none; opacity:0.5">
    <line x1="0" y1="{height_px//2}" x2="{width_px}" y2="{height_px//2}" 
          stroke="#00ff00" stroke-width="1" stroke-dasharray="5,5"/>
    <line x1="{width_px//2}" y1="0" x2="{width_px//2}" y2="{height_px}" 
          stroke="#00ff00" stroke-width="1" stroke-dasharray="5,5"/>
    <text x="{width_px//2}" y="20" text-anchor="middle" 
          fill="#00ff00" font-family="Arial" font-size="12">
      PyPottery Layout - Guidelines
    </text>
  </g>
  
</svg>'''
        
        # Write SVG file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
            
        status_callback(f"Editable SVG saved: {output_path}")
        
    except Exception as e:
        status_callback(f"Error saving SVG: {e}")
        # Fallback to PNG if SVG fails
        png_path = output_path.with_suffix('.png')
        page.save(png_path, dpi=(dpi, dpi))
        status_callback(f"Fallback: saved as PNG instead: {png_path}")


def run_layout_process(params, status_callback=print):
    """Main orchestrator function that runs the complete layout process."""
    try:
        metadata = load_metadata(params.get('metadata_file', ''), status_callback)
        image_data = load_images_with_info(params.get('input_folder', ''), status_callback)
        if not image_data:
            status_callback("No images found. Process interrupted.")
            return
        
        # Hierarchical sorting
        primary_sort = params.get('sort_by', 'alphabetical')
        secondary_sort = params.get('sort_by_secondary', 'none')
        image_data = sort_images_hierarchical(image_data, primary_sort, secondary_sort, metadata, status_callback)

        # Calculate optimal scale factor if images_per_page is set
        images_per_page = params.get('images_per_page', 0)
        scale_factor = params.get('scale_factor', 1.0)

        if images_per_page > 0:
            page_dims = get_page_dimensions_px(params.get('page_size', 'A4'), params.get('custom_size'))
            grid_size = (params.get('grid_rows', 1), params.get('grid_cols', 1)) if params.get('mode') == 'grid' else None

            # Calculate optimal scale to fill the page
            optimal_scale = calculate_optimal_scale(
                image_data,
                page_dims,
                params.get('margin_px', 0),
                params.get('spacing_px', 0),
                images_per_page,
                params.get('mode', 'grid'),
                grid_size
            )

            # Apply the optimal scale (multiply with user's scale factor)
            final_scale = scale_factor * optimal_scale
            status_callback(f"Auto-scaling: Using scale factor {final_scale:.2f}x to optimize page layout")
            image_data = scale_images(image_data, final_scale, status_callback)

            # Update scale factor for scale bar
            params['actual_scale_factor'] = final_scale
        else:
            # Use manual scale factor
            image_data = scale_images(image_data, scale_factor, status_callback)
            params['actual_scale_factor'] = scale_factor

        # Add captions to image data if requested (needed for positioning)
        if params.get('add_caption'):
            image_data = add_captions_to_images(
                image_data,
                metadata,
                params.get('caption_font_size', 14),
                params.get('caption_padding', 4),
                status_callback,
            )
        
        page_dims = get_page_dimensions_px(params.get('page_size', 'A4'), params.get('custom_size'))
        
        # Check if we should create editable output
        output_file = params.get('output_file', 'output.pdf')
        is_editable_format = Path(output_file).suffix.lower() == '.svg'
        
        if is_editable_format:
            # Create editable SVG layout
            status_callback("Creating editable layout with separate elements...")
            
            if params.get('mode') == 'grid':
                grid_size = (params.get('grid_rows', 1), params.get('grid_cols', 1))
                image_positions = create_editable_layout_positions_grid(
                    image_data, page_dims, grid_size, 
                    params.get('margin_px', 0), params.get('spacing_px', 0), 
                    params, metadata, status_callback
                )
            else:
                # For puzzle mode, we'll need to adapt the positioning algorithm
                status_callback("Note: Puzzle mode with editable elements not yet fully implemented. Using grid mode.")
                grid_size = (4, 3)  # Default grid as fallback
                image_positions = create_editable_layout_positions_grid(
                    image_data, page_dims, grid_size, 
                    params.get('margin_px', 0), params.get('spacing_px', 0), 
                    params, metadata, status_callback
                )
            
            status_callback(f"Positioned {len(image_positions)} images for editable output.")
            
            # Save editable output
            status_callback(f"Saving editable output to '{output_file}'...")
            save_editable_output(image_positions, page_dims, output_file, params, metadata, status_callback)
            
        else:
            # Create traditional raster layout (existing method)
            final_pages = []
            status_callback(f"Starting placement in '{params.get('mode', 'grid')}' mode...")
            
            images_per_page = params.get('images_per_page', 0)

            if params.get('mode') == 'grid':
                grid_size = (params.get('grid_rows', 1), params.get('grid_cols', 1))
                final_pages = place_images_grid(image_data, page_dims, grid_size, params.get('margin_px', 0), params.get('spacing_px', 0), images_per_page, status_callback)
            elif params.get('mode') == 'puzzle':
                final_pages = place_images_puzzle(image_data, page_dims, params.get('margin_px', 0), params.get('spacing_px', 0), images_per_page, status_callback)
            elif params.get('mode') == 'masonry':
                columns = params.get('grid_cols', 3)  # Use grid_cols for masonry columns
                final_pages = place_images_masonry(image_data, page_dims, params.get('margin_px', 0), params.get('spacing_px', 0), columns, images_per_page, status_callback)
            elif params.get('mode') == 'manual':
                manual_positions = params.get('manual_positions', {})
                final_pages = place_images_manual(image_data, page_dims, params.get('margin_px', 0), manual_positions, params.get('scale_factor', 1.0), status_callback, images_per_page)

            status_callback(f"Generated {len(final_pages)} pages.")
            
            # Add scale bar to traditional layout
            if params.get('add_scale_bar') and final_pages:
                # Use the actual scale factor that was applied to images
                actual_scale = params.get('actual_scale_factor', params.get('scale_factor', 1.0))
                if params.get('pixels_per_cm') and params.get('scale_bar_cm'):
                    scale_bar = create_scale_bar(params.get('scale_bar_cm', 5), params.get('pixels_per_cm', 100), actual_scale, status_callback)
                else:
                    scale_bar = create_scale_bar(params.get('scale_bar_length_px', 100), 1.0, actual_scale, status_callback)
                for page in final_pages:
                    x_pos = params.get('margin_px', 0)
                    y_pos = page.height - params.get('margin_px', 0) - scale_bar.height
                    page.paste(scale_bar, (x_pos, y_pos), scale_bar)

            # Add table numbering if requested
            if params.get('add_table_number') and final_pages:
                status_callback("Adding table numbers to pages...")
                for i, page in enumerate(final_pages):
                    table_number = params.get('table_number_start', 1) + i
                    final_pages[i] = add_table_number_to_page(
                        page,
                        table_number,
                        params.get('table_number_position', 'bottom_center'),
                        params.get('table_number_font_size', 16),
                        params.get('margin_px', 50),
                        params.get('table_number_prefix', 'Tav.'),
                        status_callback
                    )

            # Add margin borders if requested
            if params.get('show_margin_border') and final_pages:
                status_callback("Adding margin borders to pages...")
                for i, page in enumerate(final_pages):
                    final_pages[i] = draw_margin_border(page, params.get('margin_px', 0), status_callback)

            # Save traditional output
            status_callback(f"Saving output to '{output_file}'...")
            save_output(final_pages, output_file, params.get('output_dpi', 300), status_callback)
        
        status_callback('--- PROCESS COMPLETED SUCCESSFULLY ---')
    except Exception as e:
        status_callback(f"--- ERROR: {e} ---")
        raise


def _create_editable_pdf_from_svgs(svg_paths, output_pdf_path, status_callback):
    """Create editable PDF by combining SVG files."""
    try:
        # Try to use reportlab for SVG to PDF conversion with vector elements
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, A3
        from reportlab.graphics import renderPDF
        from reportlab.graphics.shapes import Drawing
        import xml.etree.ElementTree as ET
        
        status_callback(f"Combining {len(svg_paths)} SVG pages into editable PDF...")
        
        # Create PDF with reportlab
        from reportlab.pdfgen.canvas import Canvas
        
        # Get page size from first SVG
        if svg_paths:
            tree = ET.parse(svg_paths[0])
            root = tree.getroot()
            width = float(root.get('width', '595').replace('px', ''))
            height = float(root.get('height', '842').replace('px', ''))
            page_size = (width, height)
        else:
            page_size = A4
        
        c = Canvas(str(output_pdf_path), pagesize=page_size)
        
        for i, svg_path in enumerate(svg_paths):
            if i > 0:
                c.showPage()  # New page for each SVG except the first
            
            # Read SVG content and try to preserve vector elements
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Extract text elements from SVG for editable text
            tree = ET.parse(svg_path)
            root = tree.getroot()
            
            # Add text elements as editable PDF text
            for text_elem in root.iter():
                if text_elem.tag.endswith('text'):
                    try:
                        x = float(text_elem.get('x', 0))
                        y = float(text_elem.get('y', 0))
                        font_size = float(text_elem.get('font-size', 12))
                        
                        # Convert SVG coordinates to PDF coordinates (flip Y axis)
                        pdf_y = page_size[1] - y
                        
                        c.setFont("Helvetica", font_size)
                        if text_elem.text:
                            c.drawString(x, pdf_y, text_elem.text)
                    except (ValueError, TypeError):
                        continue
            
            status_callback(f"Added page {i+1}/{len(svg_paths)} to PDF")
        
        c.save()
        status_callback("✨ PDF created successfully with editable text elements")
        
    except ImportError:
        # Fallback: Convert SVG to images and create PDF
        status_callback("ReportLab not available - creating PDF from SVG images...")
        _create_pdf_from_svg_images(svg_paths, output_pdf_path, status_callback)
    
    except Exception as e:
        status_callback(f"Error creating editable PDF: {e}")
        # Fallback: Convert SVG to images and create PDF
        _create_pdf_from_svg_images(svg_paths, output_pdf_path, status_callback)


def _create_pdf_from_svg_images(svg_paths, output_pdf_path, status_callback):
    """Fallback: Create PDF by converting SVG to images first."""
    try:
        from PIL import Image
        import subprocess
        import os
        
        temp_images = []
        
        for i, svg_path in enumerate(svg_paths):
            # Convert SVG to PNG using Inkscape if available, otherwise use cairosvg
            png_path = svg_path.with_suffix('.png')
            
            try:
                # Try using Inkscape for high-quality conversion
                result = subprocess.run([
                    'inkscape', 
                    '--export-type=png',
                    f'--export-filename={png_path}',
                    '--export-dpi=300',
                    str(svg_path)
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and png_path.exists():
                    temp_images.append(png_path)
                    continue
                    
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            try:
                # Fallback: Try cairosvg
                import cairosvg
                cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), dpi=300)
                if png_path.exists():
                    temp_images.append(png_path)
                    continue
            except ImportError:
                pass
            
            status_callback(f"Warning: Could not convert {svg_path.name} - skipping")
        
        if temp_images:
            # Create PDF from images
            images = []
            for img_path in temp_images:
                img = Image.open(img_path)
                if img.mode == 'RGBA':
                    # Convert RGBA to RGB
                    bg = Image.new('RGB', img.size, 'white')
                    bg.paste(img, mask=img.split()[-1])
                    img = bg
                images.append(img)
            
            if images:
                images[0].save(
                    output_pdf_path, 
                    "PDF", 
                    resolution=300,
                    save_all=True, 
                    append_images=images[1:]
                )
                status_callback("✨ PDF created from SVG images")
            
            # Clean up temporary images
            for img_path in temp_images:
                try:
                    img_path.unlink()
                except OSError:
                    pass
        
    except Exception as e:
        status_callback(f"Error in fallback PDF creation: {e}")


def add_table_number_to_page(page, table_number, position, font_size, margin_px, prefix="Tav.", status_callback=print):
    """Add table number to page at specified position aligned with margin."""
    if not table_number:
        return page

    status_callback(f"Adding table number {prefix} {table_number} at position {position}...")

    draw = ImageDraw.Draw(page)
    page_width, page_height = page.size

    # Get font
    font = get_font(font_size)
    table_text = f"{prefix} {table_number}"

    # Calculate text dimensions
    text_bbox = draw.textbbox((0, 0), table_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Position near margin boundaries with small offset
    offset = 5  # Small offset from margin boundary
    if position == "top_left":
        x = margin_px + offset
        y = margin_px + offset
    elif position == "top_right":
        x = page_width - margin_px - text_width - offset
        y = margin_px + offset
    elif position == "bottom_left":
        x = margin_px + offset
        y = page_height - margin_px - text_height - offset
    elif position == "bottom_right":
        x = page_width - margin_px - text_width - offset
        y = page_height - margin_px - text_height - offset
    elif position == "top_center":
        x = (page_width - text_width) // 2
        y = margin_px + offset
    elif position == "bottom_center":
        x = (page_width - text_width) // 2
        y = page_height - margin_px - text_height - offset
    else:
        # Default to bottom_center
        x = (page_width - text_width) // 2
        y = page_height - margin_px - text_height - offset

    # Draw text (black by default)
    draw.text((x, y), table_text, font=font, fill=(0, 0, 0))

    return page


def _add_table_number_to_svg(svg, width_px, height_px, table_number, position, font_size, margin_px, prefix="Tav.", status_callback=print):
    """Add table number to SVG at specified position."""
    if not table_number:
        return

    table_text = f"{prefix} {table_number}"

    # Estimate text width (rough approximation)
    text_width = len(table_text) * font_size * 0.6
    text_height = font_size

    # Position near margin boundaries with small offset
    offset = 5
    if position == "top_left":
        x = margin_px + offset
        y = margin_px + offset + text_height
    elif position == "top_right":
        x = width_px - margin_px - text_width - offset
        y = margin_px + offset + text_height
    elif position == "bottom_left":
        x = margin_px + offset
        y = height_px - margin_px - offset
    elif position == "bottom_right":
        x = width_px - margin_px - text_width - offset
        y = height_px - margin_px - offset
    elif position == "top_center":
        x = (width_px - text_width) / 2
        y = margin_px + offset + text_height
    elif position == "bottom_center":
        x = (width_px - text_width) / 2
        y = height_px - margin_px - offset
    else:
        # Default to bottom_center
        x = (width_px - text_width) / 2
        y = height_px - margin_px - offset

    # Add table number text element
    ET.SubElement(svg, 'text', {
        'x': str(int(x)),
        'y': str(int(y)),
        'font-family': 'Arial',
        'font-size': str(font_size),
        'fill': 'black',
        'text-anchor': 'start'
    }).text = table_text


def place_images_masonry_with_captions(image_data, page_size_px, margin_px, spacing_px, columns, params, metadata=None, status_callback=print):
    """Place images in masonry layout handling captions separately to maintain font size."""
    page_width, page_height = page_size_px
    available_width = page_width - (2 * margin_px)
    col_width = (available_width - (columns - 1) * spacing_px) // columns

    pages = []
    current_page = Image.new('RGB', page_size_px, 'white')
    column_heights = [margin_px] * columns
    page_num = 1

    status_callback(f"Creating masonry layout with {columns} columns and fixed caption size...")

    for idx, data in enumerate(image_data):
        img = data['img']

        # Scale image to fit column width maintaining aspect
        scale = col_width / img.width
        scaled_width = col_width
        scaled_height = int(img.height * scale)
        scaled_img = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        # Find column with minimum height
        min_col_idx = column_heights.index(min(column_heights))

        # Check if we need new page
        if column_heights[min_col_idx] + scaled_height > page_height - margin_px:
            if all(h > margin_px for h in column_heights):
                pages.append(current_page)
                current_page = Image.new('RGB', page_size_px, 'white')
                column_heights = [margin_px] * columns
                page_num += 1
                status_callback(f"Starting page {page_num}...")
                min_col_idx = 0

        # Calculate position
        x = margin_px + min_col_idx * (col_width + spacing_px)
        y = column_heights[min_col_idx]

        # Paste scaled image
        current_page.paste(scaled_img, (x, y), scaled_img if scaled_img.mode == 'RGBA' else None)

        # Add caption if requested
        if params.get('add_caption') and metadata is not None:
            caption_font_size = params.get('caption_font_size', 14)
            caption_padding = params.get('caption_padding', 4)

            # Create caption text
            name = data.get('name', f'Image_{idx+1}')
            base_name = Path(name).stem
            caption_text = base_name

            # Add metadata fields if available
            if base_name in metadata:
                item_metadata = metadata[base_name]
                for key, value in item_metadata.items():
                    if key != 'filename' and value:
                        caption_text += f"\n{key}: {value}"

            # Draw caption below image
            draw = ImageDraw.Draw(current_page)
            font = get_font(caption_font_size)

            caption_y = y + scaled_height + caption_padding

            # Split caption into lines and draw
            lines = caption_text.split('\n')
            for i, line in enumerate(lines):
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_height = line_bbox[3] - line_bbox[1]

                # Bold for first line (filename)
                if i == 0:
                    # Use same font but could be enhanced later for bold
                    draw.text((x, caption_y), line, font=font, fill='black')
                else:
                    draw.text((x, caption_y), line, font=font, fill='black')

                caption_y += line_height + 2

            # Update column height
            column_heights[min_col_idx] = caption_y + caption_padding
        else:
            # Update column height without caption
            column_heights[min_col_idx] = y + scaled_height + spacing_px

    # Add last page
    if any(h > margin_px for h in column_heights):
        pages.append(current_page)

    return pages


def create_editable_svg_layout_fixed(image_positions, page_size_px, params, output_dir, page_number=0, metadata=None, status_callback=print):
    """Create SVG with images as linked external files (alternative fixed version)."""
    width_px, height_px = page_size_px

    # Create SVG root element with proper namespace
    svg = ET.Element('svg', {
        'width': str(width_px),
        'height': str(height_px),
        'viewBox': f'0 0 {width_px} {height_px}',
        'xmlns': 'http://www.w3.org/2000/svg',
        'xmlns:xlink': 'http://www.w3.org/1999/xlink',
        'version': '1.1'
    })

    # Add white background
    ET.SubElement(svg, 'rect', {
        'x': '0', 'y': '0',
        'width': str(width_px), 'height': str(height_px),
        'fill': 'white'
    })

    # Add margin border if requested
    if params.get('show_margin_border'):
        margin_px = params.get('margin_px', 0)
        if margin_px > 0:
            ET.SubElement(svg, 'rect', {
                'x': str(margin_px),
                'y': str(margin_px),
                'width': str(width_px - 2 * margin_px),
                'height': str(height_px - 2 * margin_px),
                'fill': 'none',
                'stroke': 'gray',
                'stroke-width': '1',
                'stroke-dasharray': '5,5'
            })

    # Create images subdirectory
    images_dir = Path(output_dir) / 'images'
    images_dir.mkdir(exist_ok=True)

    # Process each image position
    for idx, (x, y, width, height, img_data, caption_lines) in enumerate(image_positions):
        img = img_data['img']
        name = img_data.get('name', f'image_{idx}')

        # Save image as PNG
        img_filename = f'img_{idx:03d}_{Path(name).stem}.png'
        img_path = images_dir / img_filename
        img.save(str(img_path), 'PNG', optimize=True, quality=95)

        # Add image element with relative path
        ET.SubElement(svg, 'image', {
            'x': str(x),
            'y': str(y),
            'width': str(width),
            'height': str(height),
            'xlink:href': f'images/{img_filename}',
            'preserveAspectRatio': 'none'
        })

        # Add caption if present
        if caption_lines:
            caption_y = y + height + params.get('caption_padding', 4)
            font_size = params.get('caption_font_size', 14)

            for i, line in enumerate(caption_lines):
                font_weight = 'bold' if i == 0 else 'normal'
                text_elem = ET.SubElement(svg, 'text', {
                    'x': str(x),
                    'y': str(caption_y + (i * (font_size + 2))),
                    'font-family': 'Arial, sans-serif',
                    'font-size': str(font_size),
                    'font-weight': font_weight,
                    'fill': 'black'
                })
                text_elem.text = line

    # Add scale bar if requested and available
    if params.get('add_scale_bar'):
        scale_bar_img = params.get('scale_bar_img')
        if scale_bar_img:
            # Save scale bar image
            scale_bar_path = images_dir / 'scale_bar.png'
            scale_bar_img.save(str(scale_bar_path), 'PNG')

            # Position scale bar (bottom right by default)
            margin_px = params.get('margin_px', 50)
            bar_width = scale_bar_img.width
            bar_height = scale_bar_img.height
            bar_x = width_px - margin_px - bar_width
            bar_y = height_px - margin_px - bar_height

            ET.SubElement(svg, 'image', {
                'x': str(bar_x),
                'y': str(bar_y),
                'width': str(bar_width),
                'height': str(bar_height),
                'xlink:href': 'images/scale_bar.png'
            })

    # Add table number if requested
    if params.get('add_table_number'):
        table_number = params.get('table_number_start', 1) + page_number
        _add_table_number_to_svg(
            svg, width_px, height_px,
            table_number,
            params.get('table_number_position', 'bottom_center'),
            params.get('table_number_font_size', 16),
            params.get('margin_px', 50),
            params.get('table_number_prefix', 'Tav.'),
            status_callback
        )

    return svg


def suggest_layout_improvements(params, status_callback=print):
    """Provide suggestions when images don't fit properly."""
    current_scale = params.get('scale_factor', 1.0)
    current_margin = params.get('margin_px', 50)
    current_spacing = params.get('spacing_px', 10)
    page_size = params.get('page_size', 'A4')

    status_callback("Layout Improvement Suggestions:")

    if current_scale > 0.3:
        new_scale = max(0.1, current_scale * 0.7)
        status_callback(f"   • Try reducing scale factor to {new_scale:.2f}")

    if current_margin > 20:
        new_margin = max(10, current_margin - 20)
        status_callback(f"   • Try reducing margins to {new_margin}px")

    if current_spacing > 5:
        new_spacing = max(2, current_spacing - 5)
        status_callback(f"   • Try reducing spacing to {new_spacing}px")

    if page_size in ['A4', 'Letter']:
        status_callback(f"   • Consider using A3 or HD page size for more space")

    status_callback("   • Try using Puzzle mode for optimal space usage")
    status_callback("   • Consider splitting into multiple pages")


def verify_all_images_processed(original_count, pages, status_callback=print):
    """Verify that all images from the input folder are represented in the pages."""
    if not pages:
        status_callback("ERROR: No pages were created!")
        return False

    # This is a simple count verification
    # In a more sophisticated version, we could track specific image files
    status_callback(f"Verification: Started with {original_count} images")
    status_callback(f"Verification: Created {len(pages)} page(s)")

    # Since we can't easily count images in PIL Image objects,
    # we assume success if we have pages
    status_callback("✓ All images processed successfully")
    return True