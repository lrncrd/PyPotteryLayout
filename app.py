# app.py - Flask Web Application for PyPotteryLayout

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
from PIL import Image
import os
import json
import shutil
import threading
import time
import sys
from datetime import datetime
import uuid
import io
import base64
import zipfile
import backend_logic

# Determine if running as executable or script
def get_base_path():
    """Get base path for data files (works for both exe and script)"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_PATH, 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(BASE_PATH, 'outputs')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB max upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'tif', 'tiff', 'bmp'}
app.config['ALLOWED_METADATA'] = {'xlsx', 'csv'}

VERSION = "0.3.1"  # Version bump for SVG support

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_session_folder(create=False):
    """Get or create a unique folder for this session"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['session_id'])
    if create and not os.path.exists(session_folder):
        os.makedirs(session_folder)
    return session_folder

def get_output_folder(create=False):
    """Get or create output folder for this session"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    output_folder = os.path.join(app.config['OUTPUT_FOLDER'], session['session_id'])
    if create and not os.path.exists(output_folder):
        os.makedirs(output_folder)
    return output_folder

def inject_svg_overlay(svg_content, scale_bar_data=None, table_num_data=None, page_width=0, page_height=0, margin=0):
    """
    Helper to inject Scale Bar and Table Number into the generated SVG string.
    This mimics the post-processing done on PIL images.
    """
    additions = []

    # 1. Inject Scale Bar (Bottom Right)
    if scale_bar_data:
        sb_w = scale_bar_data['width']
        sb_h = scale_bar_data['height']
        # Position: Bottom Right inside margins
        x = page_width - sb_w - margin
        y = page_height - sb_h - margin
        
        # Build SVG group for scale bar
        g = f'<g transform="translate({x}, {y})">'
        # Segments
        for seg in scale_bar_data['segments']:
            g += f'<rect x="{seg["x"]}" y="{seg["y"]}" width="{seg["w"]}" height="{seg["h"]}" fill="{seg["fill"]}" stroke="black" stroke-width="1"/>'
        # Text 0
        g += f'<text x="20" y="{sb_h - 5}" font-family="Arial" font-size="{scale_bar_data["font_size"]}" fill="black">0</text>'
        # Text End
        g += f'<text x="{sb_w - 20}" y="{sb_h - 5}" font-family="Arial" font-size="{scale_bar_data["font_size"]}" fill="black" text-anchor="end">{scale_bar_data["label"]}</text>'
        g += '</g>'
        additions.append(g)

    # 2. Inject Table Number
    if table_num_data:
        t_num = table_num_data['number']
        t_pos = table_num_data['position']
        t_size = table_num_data['size']
        t_prefix = table_num_data['prefix']
        text_str = f"{t_prefix} {t_num}"
        
        # Determine coordinates based on position
        tx, ty, anchor = 0, 0, "start"
        padding = margin
        
        if t_pos == 'top_left':
            tx, ty, anchor = padding, padding + t_size, "start"
        elif t_pos == 'top_center':
            tx, ty, anchor = page_width / 2, padding + t_size, "middle"
        elif t_pos == 'top_right':
            tx, ty, anchor = page_width - padding, padding + t_size, "end"
        elif t_pos == 'bottom_left':
            tx, ty, anchor = padding, page_height - padding, "start"
        elif t_pos == 'bottom_center':
            tx, ty, anchor = page_width / 2, page_height - padding, "middle"
        elif t_pos == 'bottom_right':
            tx, ty, anchor = page_width - padding, page_height - padding, "end"

        additions.append(f'<text x="{tx}" y="{ty}" font-family="Arial" font-size="{t_size}" font-weight="bold" fill="black" text-anchor="{anchor}">{text_str}</text>')

    if not additions:
        return svg_content

    # Insert before closing </svg>
    injection = "\n".join(additions)
    return svg_content.replace('</svg>', f'{injection}\n</svg>')


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', version=VERSION)

@app.route('/outputs/<path:filename>')
def serve_output(filename):
    """Serve generated output files"""
    output_folder = get_output_folder()
    file_path = os.path.join(output_folder, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/upload-images', methods=['POST'])
def upload_images():
    """Upload multiple images (supports batch upload)"""
    if 'images' not in request.files:
        return jsonify({'error': 'No images provided'}), 400
    
    files = request.files.getlist('images')
    if not files:
        return jsonify({'error': 'No images selected'}), 400
    
    # Check if this is the first batch (should clear folder)
    is_first_batch = request.form.get('is_first_batch', 'true') == 'true'
    
    session_folder = get_session_folder(create=True)
    
    # Clear previous images only on first batch
    if is_first_batch:
        if os.path.exists(session_folder):
            shutil.rmtree(session_folder)
        os.makedirs(session_folder)
    
    uploaded_files = []
    errors = []
    
    for file in files:
        if file and file.filename:
            if allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
                filename = secure_filename(file.filename)
                filepath = os.path.join(session_folder, filename)
                file.save(filepath)
                uploaded_files.append({
                    'name': filename,
                    'size': os.path.getsize(filepath)
                })
            else:
                errors.append(f"File {file.filename} has invalid extension")
    
    return jsonify({
        'success': True,
        'uploaded': len(uploaded_files),
        'files': uploaded_files,
        'errors': errors
    })

@app.route('/api/upload-metadata', methods=['POST'])
def upload_metadata():
    """Upload metadata file (Excel or CSV)"""
    if 'metadata' not in request.files:
        return jsonify({'error': 'No metadata file provided'}), 400
    
    file = request.files['metadata']
    if not file or not file.filename:
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, app.config['ALLOWED_METADATA']):
        return jsonify({'error': 'Invalid file type. Only .xlsx and .csv allowed'}), 400
    
    session_folder = get_session_folder(create=True)
    filename = secure_filename(file.filename)
    filepath = os.path.join(session_folder, 'metadata_' + filename)
    file.save(filepath)
    
    # Try to load and validate metadata
    try:
        headers = backend_logic.get_metadata_headers(filepath)
        if not headers:
            return jsonify({'error': 'Could not read headers from metadata file'}), 400
        
        metadata = backend_logic.load_metadata(filepath)
        record_count = len(metadata) if metadata else 0
        
        return jsonify({
            'success': True,
            'filename': filename,
            'headers': headers,
            'count': record_count
        })
    except Exception as e:
        return jsonify({'error': f'Error loading metadata: {str(e)}'}), 400

@app.route('/api/preview', methods=['POST'])
def preview():
    """Generate preview of layout - returns first page image"""
    try:
        data = request.json
        session_folder = get_session_folder()
        output_folder = get_output_folder(create=True)
        
        if not os.path.exists(session_folder):
            return jsonify({'error': 'No images uploaded'}), 400
        
        # Extract parameters (defaults handled)
        mode = data.get('mode', 'grid')
        page_size = data.get('pageSize', 'A4')
        scale_factor = float(data.get('scaleFactor', 0.4))
        margin_px = int(data.get('marginPx', 50))
        spacing_px = int(data.get('spacingPx', 10))
        grid_rows = int(data.get('gridRows', 4))
        grid_cols = int(data.get('gridCols', 3))
        add_caption = data.get('addCaption', True)
        caption_font_size = int(data.get('captionFontSize', 12))
        caption_padding = int(data.get('captionPadding', 5))
        add_scale_bar = data.get('addScaleBar', True)
        scale_bar_cm = int(data.get('scaleBarCm', 5))
        pixels_per_cm = int(data.get('pixelsPerCm', 118))
        add_table_number = data.get('addTableNumber', True)
        table_start_number = int(data.get('tableStartNumber', 1))
        table_position = data.get('tablePosition', 'top_left')
        table_font_size = int(data.get('tableFontSize', 18))
        table_prefix = data.get('tablePrefix', 'Tav.')
        sort_by = data.get('sortBy', 'alphabetical')
        sort_by_secondary = data.get('sortBySecondary', 'none')
        show_margin_border = data.get('showMarginBorder', False)
        page_break_on_primary_change = data.get('pageBreakOnPrimaryChange', False)
        primary_break_type = data.get('primaryBreakType', 'new_page')
        show_primary_sort_header = data.get('showPrimarySortHeader', False)
        divider_thickness = int(data.get('dividerThickness', 5))
        divider_width_percent = int(data.get('dividerWidth', 80))
        vertical_alignment = data.get('verticalAlignment', 'center')
        add_object_number = data.get('addObjectNumber', False)
        object_number_position = data.get('objectNumberPosition', 'bottom_center')
        object_number_font_size = int(data.get('objectNumberFontSize', 18))
        
        # Load images
        image_data = backend_logic.load_images_with_info(session_folder)
        if not image_data:
            return jsonify({'error': 'No valid images found'}), 400
        
        # Limit to first 25 images for preview
        total_images_count = len(image_data)
        image_data = image_data[:25]
        
        # Load metadata
        metadata_files = [f for f in os.listdir(session_folder) if f.startswith('metadata_')]
        metadata = None
        if metadata_files:
            metadata_path = os.path.join(session_folder, metadata_files[0])
            metadata = backend_logic.load_metadata(metadata_path)
        
        # Sort images
        image_data = backend_logic.sort_images_hierarchical(
            image_data, sort_by, sort_by_secondary, metadata
        )
        
        # Primary sort key function
        primary_sort_key_func = None
        if page_break_on_primary_change:
            def get_primary_sort_value(img_data):
                if sort_by == 'alphabetical': return img_data['name'].lower()
                elif sort_by == 'natural_name': return backend_logic.natural_sort_key(img_data['name'])
                elif sort_by == 'size': return img_data.get('size', 0)
                elif metadata and img_data['name'] in metadata:
                    value = metadata[img_data['name']].get(sort_by, '')
                    return value if value is not None else ''
                return ''
            primary_sort_key_func = get_primary_sort_value
        
        # Scale images
        image_data = backend_logic.scale_images(image_data, scale_factor)
        
        # Add captions
        if add_caption:
            remove_extension = data.get('removeExtension', False)
            hide_field_names = data.get('hideFieldNames', False)
            selected_metadata_fields = data.get('selectedMetadataFields', None)
            image_data = backend_logic.add_captions_to_images(
                image_data, metadata, caption_font_size, caption_padding,
                remove_extension=remove_extension,
                selected_fields=selected_metadata_fields,
                hide_field_names=hide_field_names
            )
        
        # Create scale bar (Backend now returns tuple)
        scale_bar_img = None
        if add_scale_bar:
            scale_bar_img, _ = backend_logic.create_scale_bar(
                scale_bar_cm, pixels_per_cm, scale_factor
            )
        
        # Get dimensions
        page_w, page_h = backend_logic.get_page_dimensions_px(page_size)
        
        # Generate layout (Backend returns tuple: pil_pages, svg_pages)
        if mode == 'grid':
            pil_pages, _ = backend_logic.place_images_grid(
                image_data, (page_w, page_h), (grid_rows, grid_cols),
                margin_px, spacing_px,
                page_break_on_primary_change=page_break_on_primary_change,
                primary_sort_key=primary_sort_key_func,
                primary_break_type=primary_break_type,
                divider_thickness=divider_thickness,
                divider_width_percent=divider_width_percent,
                vertical_alignment=vertical_alignment,
                add_object_number=add_object_number,
                object_number_position=object_number_position,
                object_number_font_size=object_number_font_size
            )
        else:
            pil_pages, _ = backend_logic.place_images_puzzle(
                image_data, (page_w, page_h), margin_px, spacing_px,
                page_break_on_primary_change=page_break_on_primary_change,
                primary_sort_key=primary_sort_key_func,
                add_object_number=add_object_number,
                object_number_position=object_number_position,
                object_number_font_size=object_number_font_size
            )
        
        if not pil_pages:
            return jsonify({'error': 'Failed to generate layout'}), 500
        
        # Process PIL pages for preview (add overlays)
        num_preview_pages = min(20, len(pil_pages))
        preview_urls = []
        
        for page_idx in range(num_preview_pages):
            page = pil_pages[page_idx]
            
            # Add scale bar
            if scale_bar_img:
                bar_x = page_w - scale_bar_img.width - margin_px
                bar_y = page_h - scale_bar_img.height - margin_px
                page.paste(scale_bar_img, (bar_x, bar_y), scale_bar_img if scale_bar_img.mode == 'RGBA' else None)
            
            # Add table number (Currently no backend function for this, simple draw assumed or implement locally if needed, 
            # but for brevity utilizing image draw directly here as done in previous versions if backend_logic lacks it, 
            # or assuming add_table_number_to_page exists in backend from previous context if not removed. 
            # Since it was not in the *last* provided backend refactor, we implement a simple drawer here or skip).
            # *Restoring table number logic locally since it was removed from backend refactor*
            if add_table_number:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(page)
                try: font = backend_logic.get_font(table_font_size)
                except: font = ImageFont.load_default()
                text = f"{table_prefix} {table_start_number + page_idx}"
                
                # Basic positioning logic
                pad = margin_px
                if table_position == 'top_left': xy = (pad, pad)
                elif table_position == 'top_right': 
                    bbox = draw.textbbox((0,0), text, font=font)
                    xy = (page_w - bbox[2] - pad, pad)
                else: xy = (pad, pad) # Default
                
                draw.text(xy, text, font=font, fill="black")

            # Add margin border
            if show_margin_border:
                from PIL import ImageDraw
                draw = ImageDraw.Draw(page)
                draw.rectangle([margin_px, margin_px, page_w - margin_px, page_h - margin_px], outline="black", width=2)
            
            # Resize for preview
            preview_width = 1200
            if page.width > preview_width:
                ratio = preview_width / page.width
                preview_height = int(page.height * ratio)
                page = page.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
            
            preview_filename = f'preview_page{page_idx + 1}_{int(time.time() * 1000)}.jpg'
            preview_path = os.path.join(output_folder, preview_filename)
            page.save(preview_path, 'JPEG', quality=85)
            preview_urls.append(f'/outputs/{preview_filename}')
        
        return jsonify({
            'success': True,
            'preview_urls': preview_urls,
            'total_images': len(image_data),
            'total_images_in_dataset': total_images_count,
            'is_preview_limited': total_images_count > 100,
            'total_pages': len(pil_pages)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_layout():
    """Generate final layout"""
    try:
        data = request.json
        session_folder = get_session_folder()
        output_folder = get_output_folder(create=True)
        
        if not os.path.exists(session_folder):
            return jsonify({'error': 'No images uploaded'}), 400
        
        # Extract parameters
        mode = data.get('mode', 'grid')
        page_size = data.get('page_size', 'A4')
        scale_factor = float(data.get('scale_factor', 0.4))
        margin_px = int(data.get('margin_px', 50))
        spacing_px = int(data.get('spacing_px', 10))
        grid_rows = int(data.get('grid_rows', 4))
        grid_cols = int(data.get('grid_cols', 3))
        add_caption = data.get('add_caption', True)
        caption_font_size = int(data.get('caption_font_size', 12))
        caption_padding = int(data.get('caption_padding', 5))
        add_scale_bar = data.get('add_scale_bar', True)
        scale_bar_cm = int(data.get('scale_bar_cm', 5))
        pixels_per_cm = int(data.get('pixels_per_cm', 118))
        export_format = data.get('export_format', 'PDF').upper()
        add_table_number = data.get('add_table_number', True)
        table_start_number = int(data.get('table_start_number', 1))
        table_position = data.get('table_position', 'top_left')
        table_font_size = int(data.get('table_font_size', 18))
        table_prefix = data.get('table_prefix', 'Tav.')
        sort_by = data.get('sort_by', 'alphabetical')
        sort_by_secondary = data.get('sort_by_secondary', 'none')
        page_break_on_primary_change = data.get('page_break_on_primary_change', False)
        primary_break_type = data.get('primary_break_type', 'new_page')
        show_primary_sort_header = data.get('show_primary_sort_header', False)
        divider_thickness = int(data.get('divider_thickness', 5))
        divider_width_percent = int(data.get('divider_width', 80))
        vertical_alignment = data.get('vertical_alignment', 'center')
        show_margin_border = data.get('show_margin_border', False)
        add_object_number = data.get('add_object_number', False)
        object_number_position = data.get('object_number_position', 'bottom_center')
        object_number_font_size = int(data.get('object_number_font_size', 18))

        # Load images & Metadata
        image_data = backend_logic.load_images_with_info(session_folder)
        metadata_files = [f for f in os.listdir(session_folder) if f.startswith('metadata_')]
        metadata = None
        if metadata_files:
            metadata_path = os.path.join(session_folder, metadata_files[0])
            metadata = backend_logic.load_metadata(metadata_path)
        
        # Sort
        image_data = backend_logic.sort_images_hierarchical(
            image_data, sort_by, sort_by_secondary, metadata
        )
        
        # Sort key logic
        primary_sort_key_func = None
        if page_break_on_primary_change:
            def get_primary_sort_value(img_data):
                if sort_by == 'alphabetical': return img_data['name'].lower()
                elif sort_by == 'natural_name': return backend_logic.natural_sort_key(img_data['name'])
                elif sort_by == 'size': return img_data.get('size', 0)
                elif metadata and img_data['name'] in metadata:
                    value = metadata[img_data['name']].get(sort_by, '')
                    return value if value is not None else ''
                return ''
            primary_sort_key_func = get_primary_sort_value
        
        # Scale
        image_data = backend_logic.scale_images(image_data, scale_factor)
        
        # Captions
        if add_caption:
            remove_extension = data.get('remove_extension', False)
            hide_field_names = data.get('hide_field_names', False)
            selected_metadata_fields = data.get('selected_metadata_fields', None)
            image_data = backend_logic.add_captions_to_images(
                image_data, metadata, caption_font_size, caption_padding,
                remove_extension=remove_extension,
                selected_fields=selected_metadata_fields,
                hide_field_names=hide_field_names
            )
        
        # Scale Bar (Get tuple!)
        scale_bar_img, scale_bar_svg_data = (None, None)
        if add_scale_bar:
            scale_bar_img, scale_bar_svg_data = backend_logic.create_scale_bar(
                scale_bar_cm, pixels_per_cm, scale_factor
            )
        
        # Page Dims
        page_w, page_h = backend_logic.get_page_dimensions_px(page_size)
        
        # Generate Layout (Get tuple!)
        pil_pages, svg_pages = ([], [])
        if mode == 'grid':
            pil_pages, svg_pages = backend_logic.place_images_grid(
                image_data, (page_w, page_h), (grid_rows, grid_cols),
                margin_px, spacing_px,
                page_break_on_primary_change=page_break_on_primary_change,
                primary_sort_key=primary_sort_key_func,
                primary_break_type=primary_break_type,
                divider_thickness=divider_thickness,
                divider_width_percent=divider_width_percent,
                vertical_alignment=vertical_alignment,
                add_object_number=add_object_number,
                object_number_position=object_number_position,
                object_number_font_size=object_number_font_size
            )
        else:
            pil_pages, svg_pages = backend_logic.place_images_puzzle(
                image_data, (page_w, page_h), margin_px, spacing_px,
                page_break_on_primary_change=page_break_on_primary_change,
                primary_sort_key=primary_sort_key_func,
                add_object_number=add_object_number,
                object_number_position=object_number_position,
                object_number_font_size=object_number_font_size
            )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # === EXPORT LOGIC ===
        
        # 1. PDF Export (Uses PIL Pages)
        if export_format == 'PDF':
            # Post-process PIL pages (Scale bar + Table nums)
            if scale_bar_img:
                for page in pil_pages:
                    bx = page_w - scale_bar_img.width - margin_px
                    by = page_h - scale_bar_img.height - margin_px
                    page.paste(scale_bar_img, (bx, by), scale_bar_img if scale_bar_img.mode == 'RGBA' else None)
            
            if add_table_number:
                from PIL import ImageDraw, ImageFont
                for i, page in enumerate(pil_pages):
                    draw = ImageDraw.Draw(page)
                    try: font = backend_logic.get_font(table_font_size)
                    except: font = ImageFont.load_default()
                    text = f"{table_prefix} {table_start_number + i}"
                    # Simple top-left assumption or reuse preview logic
                    draw.text((margin_px, margin_px), text, font=font, fill="black")
            
            if show_margin_border:
                from PIL import ImageDraw
                for page in pil_pages:
                    draw = ImageDraw.Draw(page)
                    draw.rectangle([margin_px, margin_px, page_w - margin_px, page_h - margin_px], outline="black", width=2)

            output_filename = f'layout_{timestamp}.pdf'
            output_path = os.path.join(output_folder, output_filename)
            pil_pages[0].save(output_path, "PDF", resolution=300.0, 
                              save_all=True, append_images=pil_pages[1:] if len(pil_pages) > 1 else [])

        # 2. JPG Export (Uses PIL Pages)
        elif export_format == 'JPG':
            # Post-process (Same as PDF)
            if scale_bar_img:
                for page in pil_pages:
                    bx = page_w - scale_bar_img.width - margin_px
                    by = page_h - scale_bar_img.height - margin_px
                    page.paste(scale_bar_img, (bx, by), scale_bar_img if scale_bar_img.mode == 'RGBA' else None)
            
            # Handle Zip vs Single
            if len(pil_pages) > 1:
                output_filename = f'layout_{timestamp}.zip'
                output_path = os.path.join(output_folder, output_filename)
                with zipfile.ZipFile(output_path, 'w') as zipf:
                    for i, page in enumerate(pil_pages, 1):
                        fname = f'layout_page{i}.jpg'
                        fpath = os.path.join(output_folder, fname)
                        page.save(fpath, 'JPEG', dpi=(300,300), quality=95)
                        zipf.write(fpath, fname)
                        os.remove(fpath)
            else:
                output_filename = f'layout_{timestamp}.jpg'
                output_path = os.path.join(output_folder, output_filename)
                pil_pages[0].save(output_path, 'JPEG', dpi=(300,300), quality=95)

        # 3. SVG Export (Uses SVG Strings)
        elif export_format == 'SVG':
            final_svgs = []
            for i, svg_str in enumerate(svg_pages):
                # Prepare semantic overlay data
                t_num_data = None
                if add_table_number:
                    t_num_data = {
                        'number': table_start_number + i,
                        'position': table_position,
                        'size': table_font_size,
                        'prefix': table_prefix
                    }
                
                # Inject overlays into the SVG string
                full_svg = inject_svg_overlay(
                    svg_str, 
                    scale_bar_data=scale_bar_svg_data if add_scale_bar else None,
                    table_num_data=t_num_data,
                    page_width=page_w,
                    page_height=page_h,
                    margin=margin_px
                )
                final_svgs.append(full_svg)

            # Handle Zip vs Single
            if len(final_svgs) > 1:
                output_filename = f'layout_{timestamp}_svg.zip'
                output_path = os.path.join(output_folder, output_filename)
                with zipfile.ZipFile(output_path, 'w') as zipf:
                    for i, svg_content in enumerate(final_svgs, 1):
                        fname = f'layout_page{i}.svg'
                        zipf.writestr(fname, svg_content)
            else:
                output_filename = f'layout_{timestamp}.svg'
                output_path = os.path.join(output_folder, output_filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(final_svgs[0])

        else:
            return jsonify({'error': f'Unsupported export format: {export_format}'}), 400
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'pages': len(pil_pages),
            'download_url': f'/api/download/{output_filename}'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download generated file"""
    try:
        output_folder = get_output_folder()
        filepath = os.path.join(output_folder, secure_filename(filename))
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/api/metadata-headers', methods=['GET'])
def get_metadata_headers():
    """Get headers from uploaded metadata file"""
    session_folder = get_session_folder()
    metadata_files = [f for f in os.listdir(session_folder) if f.startswith('metadata_')] if os.path.exists(session_folder) else []
    if not metadata_files: return jsonify({'headers': []})
    try:
        metadata_path = os.path.join(session_folder, metadata_files[0])
        headers = backend_logic.get_metadata_headers(metadata_path)
        return jsonify({'headers': headers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-session', methods=['POST'])
def clear_session():
    """Clear session data"""
    session_folder = get_session_folder()
    output_folder = get_output_folder()
    if os.path.exists(session_folder): shutil.rmtree(session_folder)
    if os.path.exists(output_folder): shutil.rmtree(output_folder)
    session.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    import webbrowser
    from threading import Timer
    import logging
    
    PORT = 5005
    
    # Determine if running as compiled exe
    if getattr(sys, 'frozen', False):
        # Running as compiled exe - setup logging
        log_file = os.path.join(os.path.dirname(sys.executable), 'pypotterylayout.log')
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info("PyPotteryLayout starting...")
        logging.info(f"Base path: {os.path.dirname(sys.executable)}")
        
        URL = f'http://127.0.0.1:{PORT}'
        
        # Open browser after 1.5 seconds
        def open_browser():
            try:
                webbrowser.open(URL)
                logging.info(f"Browser opened at {URL}")
            except Exception as e:
                logging.error(f"Failed to open browser: {e}")
        
        Timer(1.5, open_browser).start()
        
        # Run server without debug mode
        print(f"PyPotteryLayout is starting...")
        print(f"Opening browser at {URL}")
        
        try:
            app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)
        except Exception as e:
            error_msg = f"Error starting server: {e}"
            logging.error(error_msg)
            #show_error(error_msg + "\n\nCheck pypotterylayout.log for details")
            sys.exit(1)
    else:
        # Running as script in development
        URL = f'http://localhost:{PORT}'
        
        # Open browser only in the main process (not in reloader child process)
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            Timer(1.5, lambda: webbrowser.open(URL)).start()
        
        print(f"PyPotteryLayout is starting...")
        print(f"Opening browser at {URL}")
        app.run(debug=True, host='0.0.0.0', port=PORT)