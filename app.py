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
        # Use the directory where the executable is located
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

VERSION = "0.2.0"  # Flask version

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def _create_simple_svg(page_image, page_number):
    """Create simple SVG with embedded PNG for puzzle mode"""
    width_px, height_px = page_image.size
    buffer = io.BytesIO()
    page_image.save(buffer, format='PNG')
    img_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width_px}px" height="{height_px}px" 
     viewBox="0 0 {width_px} {height_px}"
     xmlns="http://www.w3.org/2000/svg" 
     xmlns:xlink="http://www.w3.org/1999/xlink">
  <title>PyPotteryLayout - Page {page_number}</title>
  <rect id="background" x="0" y="0" width="{width_px}" height="{height_px}" 
        fill="white" stroke="none"/>
  <image x="0" y="0" width="{width_px}" height="{height_px}" 
         href="data:image/png;base64,{img_data}"
         style="image-rendering:auto"/>
</svg>'''
    
    return svg_content

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
        # Get column headers (not row keys!)
        headers = backend_logic.get_metadata_headers(filepath)
        if not headers:
            return jsonify({'error': 'Could not read headers from metadata file'}), 400
        
        # Load metadata to count records
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
        
        # Extract parameters
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
        
        # Load images
        image_data = backend_logic.load_images_with_info(session_folder)
        
        if not image_data:
            return jsonify({'error': 'No valid images found'}), 400
        
        # Limit to first 100 images for preview (don't process entire dataset)
        total_images_count = len(image_data)
        image_data = image_data[:25]
        
        # Load metadata if exists
        metadata_files = [f for f in os.listdir(session_folder) if f.startswith('metadata_')]
        metadata = None
        if metadata_files:
            metadata_path = os.path.join(session_folder, metadata_files[0])
            metadata = backend_logic.load_metadata(metadata_path)
        
        # Sort images
        image_data = backend_logic.sort_images_hierarchical(
            image_data, sort_by, sort_by_secondary, metadata
        )
        
        # Create primary sort key function for page breaks
        primary_sort_key_func = None
        if page_break_on_primary_change:
            def get_primary_sort_value(img_data):
                """Extract primary sort value from image data."""
                if sort_by == 'alphabetical':
                    return img_data['name'].lower()
                elif sort_by == 'natural_name':
                    return backend_logic.natural_sort_key(img_data['name'])
                elif sort_by == 'size':
                    return img_data.get('size', 0)
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
        
        # Create scale bar
        scale_bar = None
        if add_scale_bar:
            scale_bar = backend_logic.create_scale_bar(
                scale_bar_cm, pixels_per_cm, scale_factor
            )
        
        # Get page dimensions
        page_w, page_h = backend_logic.get_page_dimensions_px(page_size)
        
        # Generate layout
        if mode == 'grid':
            pages = backend_logic.place_images_grid(
                image_data, 
                (page_w, page_h),
                (grid_rows, grid_cols),
                margin_px, 
                spacing_px,
                page_break_on_primary_change=page_break_on_primary_change,
                primary_sort_key=primary_sort_key_func,
                primary_break_type=primary_break_type,
                show_primary_sort_header=show_primary_sort_header,
                divider_thickness=divider_thickness,
                divider_width_percent=divider_width_percent,
                vertical_alignment=vertical_alignment
            )
        else:  # puzzle mode
            pages = backend_logic.place_images_puzzle(
                image_data,
                (page_w, page_h),
                margin_px, 
                spacing_px,
                page_break_on_primary_change=page_break_on_primary_change,
                primary_sort_key=primary_sort_key_func
            )
        
        if not pages or len(pages) == 0:
            return jsonify({'error': 'Failed to generate layout'}), 500
        
        # Save up to 20 preview pages
        num_preview_pages = min(20, len(pages))
        preview_urls = []
        
        for page_idx in range(num_preview_pages):
            page = pages[page_idx]
            
            # Add scale bar to page
            if scale_bar:
                bar_x = page_w - scale_bar.width - margin_px
                bar_y = page_h - scale_bar.height - margin_px
                page.paste(scale_bar, (bar_x, bar_y), scale_bar if scale_bar.mode == 'RGBA' else None)
            
            # Add table number to page
            if add_table_number:
                page = backend_logic.add_table_number_to_page(
                    page, table_start_number + page_idx, table_position, 
                    table_font_size, margin_px, table_prefix
                )
            
            # Add margin border if requested
            if show_margin_border:
                page = backend_logic.draw_margin_border(page, margin_px)
            
            # Resize for preview (max 1200px width)
            preview_width = 1200
            if page.width > preview_width:
                ratio = preview_width / page.width
                preview_height = int(page.height * ratio)
                page = page.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
            
            # Save preview image
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
            'total_pages': len(pages)
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
        print(f"DEBUG: Received data: {json.dumps(data, indent=2)}")  # Debug log
        
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
        
        # Load images
        image_data = backend_logic.load_images_with_info(session_folder)
        
        # Load metadata if exists
        metadata_files = [f for f in os.listdir(session_folder) if f.startswith('metadata_')]
        metadata = None
        if metadata_files:
            metadata_path = os.path.join(session_folder, metadata_files[0])
            metadata = backend_logic.load_metadata(metadata_path)
        
        # Sort images
        image_data = backend_logic.sort_images_hierarchical(
            image_data, sort_by, sort_by_secondary, metadata
        )
        
        # Create primary sort key function for page breaks
        primary_sort_key_func = None
        if page_break_on_primary_change:
            def get_primary_sort_value(img_data):
                """Extract primary sort value from image data."""
                if sort_by == 'alphabetical':
                    return img_data['name'].lower()
                elif sort_by == 'natural_name':
                    return backend_logic.natural_sort_key(img_data['name'])
                elif sort_by == 'size':
                    return img_data.get('size', 0)
                elif metadata and img_data['name'] in metadata:
                    value = metadata[img_data['name']].get(sort_by, '')
                    return value if value is not None else ''
                return ''
            primary_sort_key_func = get_primary_sort_value
        
        # Get page dimensions
        page_w, page_h = backend_logic.get_page_dimensions_px(page_size)
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # === SVG EDITABLE PIPELINE ===
        if export_format == 'SVG':
            # For SVG, we need positions not rendered pages
            # Store original images BEFORE any modification (required for SVG export)
            for data in image_data:
                data['original_img'] = data['img'].copy()
            
            # Scale images
            image_data = backend_logic.scale_images(image_data, scale_factor)
            
            # Add captions to images
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
            
            # Prepare params dict for SVG generation
            params = {
                'scale_factor': scale_factor,
                'margin_px': margin_px,
                'spacing_px': spacing_px,
                'add_caption': add_caption,
                'caption_font_size': caption_font_size,
                'caption_padding': caption_padding,
                'add_scale_bar': add_scale_bar,
                'scale_bar_cm': scale_bar_cm,
                'pixels_per_cm': pixels_per_cm,
                'add_table_number': add_table_number,
                'table_start_number': table_start_number,
                'table_position': table_position,
                'table_font_size': table_font_size,
                'table_prefix': table_prefix,
                'show_margin_border': data.get('show_margin_border', False)
            }
            
            # Calculate image positions
            if mode == 'grid':
                image_positions = backend_logic.create_editable_layout_positions_grid(
                    image_data,
                    (page_w, page_h),
                    (grid_rows, grid_cols),
                    margin_px,
                    spacing_px,
                    params,
                    metadata,
                    page_break_on_primary_change=page_break_on_primary_change,
                    primary_sort_key=primary_sort_key_func,
                    primary_break_type=primary_break_type,
                    show_primary_sort_header=show_primary_sort_header,
                    divider_thickness=divider_thickness,
                    divider_width_percent=divider_width_percent,
                    vertical_alignment=vertical_alignment
                )
            else:
                # Puzzle mode doesn't support editable layout - fall back to simple embedded SVG
                pages = backend_logic.place_images_puzzle(
                    image_data,
                    (page_w, page_h),
                    margin_px,
                    spacing_px,
                    page_break_on_primary_change=page_break_on_primary_change,
                    primary_sort_key=primary_sort_key_func
                )
                
                output_filename = f'layout_{timestamp}.zip' if len(pages) > 1 else f'layout_{timestamp}.svg'
                output_path = os.path.join(output_folder, output_filename)
                
                if len(pages) > 1:
                    with zipfile.ZipFile(output_path, 'w') as zipf:
                        for i, page in enumerate(pages, 1):
                            svg_content = _create_simple_svg(page, i)
                            page_filename = f'layout_page{i}.svg'
                            page_path = os.path.join(output_folder, page_filename)
                            
                            with open(page_path, 'w', encoding='utf-8') as f:
                                f.write(svg_content)
                            
                            zipf.write(page_path, page_filename)
                            os.remove(page_path)
                else:
                    svg_content = _create_simple_svg(pages[0], 1)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                
                return jsonify({
                    'success': True,
                    'filename': output_filename,
                    'pages': len(pages),
                    'download_url': f'/api/download/{output_filename}'
                })
            
            # Group positions by page
            from pathlib import Path
            pages_data = {}
            for pos in image_positions:
                page_num = pos.get('page', 0)
                if page_num not in pages_data:
                    pages_data[page_num] = []
                pages_data[page_num].append(pos)
            
            # Create ZIP with editable SVG files
            output_filename = f'layout_{timestamp}_editable.zip'
            output_path = os.path.join(output_folder, output_filename)
            
            with zipfile.ZipFile(output_path, 'w') as zipf:
                for page_num, page_positions in sorted(pages_data.items()):
                    # Create temp folder for this page
                    page_folder = Path(output_folder) / f"temp_page_{page_num+1}"
                    page_folder.mkdir(parents=True, exist_ok=True)
                    
                    # Create editable SVG
                    svg_element = backend_logic.create_lightweight_editable_svg(
                        page_positions,
                        (page_w, page_h),
                        params,
                        page_folder,
                        page_num,
                        metadata
                    )
                    
                    # Save SVG
                    svg_filename = f'layout_page{page_num+1}.svg'
                    svg_path = page_folder / svg_filename
                    backend_logic._save_svg_element_to_file(svg_element, svg_path)
                    
                    # Add SVG to ZIP (in page subfolder)
                    zipf.write(svg_path, f'page_{page_num+1}/{svg_filename}')
                    
                    # Add all images in the images subfolder to ZIP
                    images_dir = page_folder / "images"
                    if images_dir.exists():
                        for img_file in images_dir.iterdir():
                            if img_file.is_file():
                                zipf.write(img_file, f'page_{page_num+1}/images/{img_file.name}')
                    
                    # Clean up temp folder
                    shutil.rmtree(page_folder)
            
            return jsonify({
                'success': True,
                'filename': output_filename,
                'pages': len(pages_data),
                'download_url': f'/api/download/{output_filename}'
            })
        
        # === PDF/JPG PIPELINE ===
        # Scale images
        image_data = backend_logic.scale_images(image_data, scale_factor)
        
        # Add captions
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
        
        # Create scale bar
        scale_bar = None
        if add_scale_bar:
            scale_bar = backend_logic.create_scale_bar(
                scale_bar_cm, pixels_per_cm, scale_factor
            )
        
        # Generate layout pages
        if mode == 'grid':
            pages = backend_logic.place_images_grid(
                image_data, 
                (page_w, page_h),
                (grid_rows, grid_cols),
                margin_px, 
                spacing_px,
                page_break_on_primary_change=page_break_on_primary_change,
                primary_sort_key=primary_sort_key_func,
                primary_break_type=primary_break_type,
                show_primary_sort_header=show_primary_sort_header,
                divider_thickness=divider_thickness,
                divider_width_percent=divider_width_percent,
                vertical_alignment=vertical_alignment
            )
        else:  # puzzle mode
            pages = backend_logic.place_images_puzzle(
                image_data,
                (page_w, page_h),
                margin_px, 
                spacing_px,
                page_break_on_primary_change=page_break_on_primary_change,
                primary_sort_key=primary_sort_key_func
            )
        
        # Add scale bar to each page
        if scale_bar:
            for page in pages:
                # Paste scale bar at bottom right
                bar_x = page_w - scale_bar.width - margin_px
                bar_y = page_h - scale_bar.height - margin_px
                page.paste(scale_bar, (bar_x, bar_y), scale_bar if scale_bar.mode == 'RGBA' else None)
        
        # Add table numbers if requested
        if add_table_number:
            for i, page in enumerate(pages):
                table_number = table_start_number + i
                backend_logic.add_table_number_to_page(
                    page,
                    table_number,
                    table_position,
                    table_font_size,
                    margin_px,
                    table_prefix
                )
        
        # Draw margin border if requested
        show_margin_border = data.get('show_margin_border', False)
        if show_margin_border:
            for page in pages:
                backend_logic.draw_margin_border(page, margin_px)
        
        # Save pages (PDF or JPG only - SVG handled above)
        if export_format == 'PDF':
            # PDF can handle multiple pages in one file
            output_filename = f'layout_{timestamp}.pdf'
            output_path = os.path.join(output_folder, output_filename)
            pages[0].save(output_path, "PDF", resolution=300.0, 
                         save_all=True, append_images=pages[1:] if len(pages) > 1 else [])
            
        elif export_format == 'JPG':
            # For JPG with multiple pages, create a ZIP
            if len(pages) > 1:
                output_filename = f'layout_{timestamp}.zip'
                output_path = os.path.join(output_folder, output_filename)
                
                with zipfile.ZipFile(output_path, 'w') as zipf:
                    for i, page in enumerate(pages, 1):
                        page_filename = f'layout_page{i}.jpg'
                        page_path = os.path.join(output_folder, page_filename)
                        page.save(page_path, 'JPEG', dpi=(300, 300), quality=95)
                        
                        # Add to ZIP
                        zipf.write(page_path, page_filename)
                        # Remove temporary file
                        os.remove(page_path)
            else:
                # Single page JPG
                output_filename = f'layout_{timestamp}.jpg'
                output_path = os.path.join(output_folder, output_filename)
                pages[0].save(output_path, 'JPEG', dpi=(300, 300), quality=95)
        else:
            return jsonify({'error': f'Unsupported export format: {export_format}'}), 400
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'pages': len(pages),
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
        
        print(f"DEBUG: Download requested for: {filename}")
        print(f"DEBUG: Output folder: {output_folder}")
        print(f"DEBUG: Full path: {filepath}")
        print(f"DEBUG: File exists: {os.path.exists(filepath)}")
        
        if not os.path.exists(filepath):
            print(f"ERROR: File not found: {filepath}")
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR in download_file: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/api/metadata-headers', methods=['GET'])
def get_metadata_headers():
    """Get headers from uploaded metadata file"""
    session_folder = get_session_folder()
    metadata_files = [f for f in os.listdir(session_folder) if f.startswith('metadata_')] if os.path.exists(session_folder) else []
    
    if not metadata_files:
        return jsonify({'headers': []})
    
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
    
    if os.path.exists(session_folder):
        shutil.rmtree(session_folder)
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    
    session.clear()
    
    return jsonify({'success': True})

@app.route('/api/preview', methods=['POST'])
def generate_preview():
    """Generate a quick preview of the layout with up to 20 images"""
    try:
        session_folder = get_session_folder()
        if not os.path.exists(session_folder):
            return jsonify({'error': 'No images uploaded'}), 400
        
        # Get settings from request
        settings = request.get_json()
        print(f"DEBUG Preview: Settings = {json.dumps(settings, indent=2)}")
        
        # Load images using backend_logic
        image_data = backend_logic.load_images_with_info(session_folder)
        
        if not image_data:
            return jsonify({'error': 'No valid images found'}), 400
        
        # Limit to first 100 images for quick preview (don't process entire dataset)
        total_images_count = len(image_data)
        image_data = image_data[:100]
        
        # Get metadata if exists
        metadata_files = [f for f in os.listdir(session_folder) if f.startswith('metadata_')]
        metadata = None
        if metadata_files:
            metadata_path = os.path.join(session_folder, metadata_files[0])
            metadata = backend_logic.load_metadata(metadata_path)
        
        # Parse settings
        mode = settings.get('mode', 'grid')
        page_size = settings.get('pageSize', 'A4')
        sort_by = settings.get('sortBy', 'alphabetical')
        sort_by_secondary = settings.get('sortBySecondary', 'none')
        scale_factor = float(settings.get('scaleFactor', 0.4))
        margin_px = int(settings.get('marginPx', 50))
        spacing_px = int(settings.get('spacingPx', 10))
        grid_rows = int(settings.get('gridRows', 4))
        grid_cols = int(settings.get('gridCols', 3))
        show_margin_border = settings.get('showMarginBorder', False)
        page_break_on_primary_change = settings.get('pageBreakOnPrimaryChange', False)
        primary_break_type = settings.get('primaryBreakType', 'new_page')
        show_primary_sort_header = settings.get('showPrimarySortHeader', False)
        divider_thickness = int(settings.get('dividerThickness', 5))
        divider_width_percent = int(settings.get('dividerWidth', 80))
        vertical_alignment = settings.get('verticalAlignment', 'center')
        
        print(f"DEBUG Preview: margin={margin_px}, show_border={show_margin_border}")
        
        # Sort images
        image_data = backend_logic.sort_images_hierarchical(
            image_data, sort_by, sort_by_secondary, metadata
        )
        
        # Create primary sort key function for page breaks
        primary_sort_key_func = None
        if page_break_on_primary_change:
            def get_primary_sort_value(img_data):
                """Extract primary sort value from image data."""
                if sort_by == 'alphabetical':
                    return img_data['name'].lower()
                elif sort_by == 'natural_name':
                    return backend_logic.natural_sort_key(img_data['name'])
                elif sort_by == 'size':
                    return img_data.get('size', 0)
                elif metadata and img_data['name'] in metadata:
                    value = metadata[img_data['name']].get(sort_by, '')
                    return value if value is not None else ''
                return ''
            primary_sort_key_func = get_primary_sort_value
        
        # Scale images
        image_data = backend_logic.scale_images(image_data, scale_factor)
        
        # Get page dimensions
        page_w, page_h = backend_logic.get_page_dimensions_px(page_size)
        
        # Generate layout
        if mode == 'grid':
            pages = backend_logic.place_images_grid(
                image_data, 
                (page_w, page_h),
                (grid_rows, grid_cols),
                margin_px, 
                spacing_px,
                page_break_on_primary_change=page_break_on_primary_change,
                primary_sort_key=primary_sort_key_func,
                primary_break_type=primary_break_type,
                show_primary_sort_header=show_primary_sort_header,
                divider_thickness=divider_thickness,
                divider_width_percent=divider_width_percent,
                vertical_alignment=vertical_alignment
            )
        else:  # puzzle mode
            pages = backend_logic.place_images_puzzle(
                image_data,
                (page_w, page_h),
                margin_px, 
                spacing_px,
                page_break_on_primary_change=page_break_on_primary_change,
                primary_sort_key=primary_sort_key_func
            )
        
        print(f"DEBUG Preview: Generated {len(pages)} page(s)")
        
        # Draw margin border if requested
        if show_margin_border and pages:
            from PIL import ImageDraw
            for page in pages:
                backend_logic.draw_margin_border(page, margin_px)
        
        # Save preview (only first page, compressed for speed)
        output_folder = get_output_folder(create=True)
        preview_filename = f'preview_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.jpg'
        preview_path = os.path.join(output_folder, preview_filename)
        
        if pages:
            # Save at lower resolution for faster loading
            preview_page = pages[0]
            # Resize to 1200px width max for preview
            max_width = 1200
            if preview_page.width > max_width:
                ratio = max_width / preview_page.width
                new_size = (max_width, int(preview_page.height * ratio))
                preview_page = preview_page.resize(new_size, Image.Resampling.LANCZOS)
            
            preview_page.save(preview_path, 'JPEG', quality=85, optimize=True)
            print(f"DEBUG Preview: Saved to {preview_filename}")
        
        return jsonify({
            'success': True,
            'preview_url': f'/api/download/{preview_filename}'
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

def show_error(message):
    """Show error message in a dialog (Windows only)"""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "PyPotteryLayout Error", 0x10)
    except:
        pass

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
            show_error(error_msg + "\n\nCheck pypotterylayout.log for details")
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
