// PyPotteryLayout - Frontend JavaScript

// Global state
let uploadedImages = false;
let uploadedMetadata = false;
let metadataHeaders = [];

// DOM Elements (will be initialized in DOMContentLoaded)
let imageUpload, metadataUpload, generateBtn, clearBtn, terminalOutput;
let uploadStatus, metadataStatus, progressContainer, progressBar, progressText;
let resultSection, previewSection, scaleDisplay, scaleFactor;
let gridSettings, captionSettings, scaleBarSettings, tableNumberSettings;

// Splash Screen
document.addEventListener('DOMContentLoaded', function() {
    // Initialize DOM elements
    imageUpload = document.getElementById('imageUpload');
    metadataUpload = document.getElementById('metadataUpload');
    generateBtn = document.getElementById('generateBtn');
    clearBtn = document.getElementById('clearBtn');
    terminalOutput = document.getElementById('terminalOutput');
    uploadStatus = document.getElementById('uploadStatus');
    metadataStatus = document.getElementById('metadataStatus');
    progressContainer = document.getElementById('progressContainer');
    progressBar = document.getElementById('progressBar');
    progressText = document.getElementById('progressText');
    resultSection = document.getElementById('resultSection');
    previewSection = document.getElementById('previewSection');
    scaleDisplay = document.getElementById('scaleDisplay');
    scaleFactor = document.getElementById('scaleFactor');
    gridSettings = document.getElementById('gridSettings');
    captionSettings = document.getElementById('captionSettings');
    scaleBarSettings = document.getElementById('scaleBarSettings');
    tableNumberSettings = document.getElementById('tableNumberSettings');
    
    // Simulate loading process
    const splashScreen = document.getElementById('splash-screen');
    const splashProgressBar = document.getElementById('splash-progress-bar');
    const splashProgressText = document.getElementById('splash-progress-text');
    const splashMessage = document.getElementById('splash-message');
    
    const loadingSteps = [
        { progress: 20, message: 'Loading components...' },
        { progress: 40, message: 'Initializing interface...' },
        { progress: 60, message: 'Setting up controls...' },
        { progress: 80, message: 'Preparing workspace...' },
        { progress: 100, message: 'Ready!' }
    ];
    
    let currentStep = 0;
    
    function updateSplash() {
        if (currentStep < loadingSteps.length) {
            const step = loadingSteps[currentStep];
            splashProgressBar.style.width = step.progress + '%';
            splashProgressText.textContent = step.progress + '%';
            splashMessage.textContent = step.message;
            currentStep++;
            setTimeout(updateSplash, 300);
        } else {
            setTimeout(() => {
                splashScreen.classList.add('fade-out');
                setTimeout(() => {
                    splashScreen.style.display = 'none';
                    // Show main container
                    const mainContainer = document.getElementById('main-container');
                    if (mainContainer) {
                        mainContainer.style.display = 'block';
                    }
                }, 500);
            }, 500);
        }
    }
    
    // Start splash animation
    setTimeout(updateSplash, 100);
    
    // Initialize app after splash - make sure DOM is ready
    setTimeout(() => {
        setupEventListeners();
        updateUIState();
    }, 2000); // Increased timeout to ensure splash completes
});

function setupEventListeners() {
    // Verify all elements are loaded
    if (!imageUpload || !metadataUpload || !generateBtn || !clearBtn) {
        console.error('Critical DOM elements not found!');
        return;
    }
    
    // File uploads
    imageUpload.addEventListener('change', handleImageUpload);
    metadataUpload.addEventListener('change', handleMetadataUpload);
    
    // Mode selection
    document.querySelectorAll('input[name="mode"]').forEach(radio => {
        radio.addEventListener('change', handleModeChange);
    });
    
    // Checkboxes for showing/hiding sections
    document.getElementById('addCaption').addEventListener('change', function() {
        captionSettings.style.display = this.checked ? 'block' : 'none';
    });
    
    document.getElementById('addScaleBar').addEventListener('change', function() {
        scaleBarSettings.style.display = this.checked ? 'block' : 'none';
    });
    
    document.getElementById('addTableNumber').addEventListener('change', function() {
        tableNumberSettings.style.display = this.checked ? 'block' : 'none';
    });
    
    // Scale factor slider
    scaleFactor.addEventListener('input', function() {
        scaleDisplay.textContent = parseFloat(this.value).toFixed(2) + 'x';
    });
    
    // Sort by metadata
    document.getElementById('sortBy').addEventListener('change', updateSortOptions);
    
    // Metadata upload triggers sort option update
    metadataUpload.addEventListener('change', updateSortOptions);
    
    // Buttons
    generateBtn.addEventListener('click', handleGenerate);
    clearBtn.addEventListener('click', handleClear);
    
    // Auto-update preview when settings change
    setupPreviewAutoUpdate();
}

function setupPreviewAutoUpdate() {
    // Debounce function to avoid too many preview requests
    let previewTimeout;
    function schedulePreviewUpdate() {
        if (!uploadedImages) return;
        
        clearTimeout(previewTimeout);
        previewTimeout = setTimeout(() => {
            generateLayoutPreview();
        }, 500); // Wait 500ms after last change
    }
    
    // Listen to all settings that affect layout
    document.querySelectorAll('input[name="mode"]').forEach(radio => {
        radio.addEventListener('change', schedulePreviewUpdate);
    });
    
    document.getElementById('pageSize').addEventListener('change', schedulePreviewUpdate);
    document.getElementById('scaleFactor').addEventListener('input', schedulePreviewUpdate);
    document.getElementById('marginPx').addEventListener('input', schedulePreviewUpdate);
    document.getElementById('spacingPx').addEventListener('input', schedulePreviewUpdate);
    document.getElementById('gridRows').addEventListener('change', schedulePreviewUpdate);
    document.getElementById('gridCols').addEventListener('change', schedulePreviewUpdate);
    document.getElementById('sortBy').addEventListener('change', schedulePreviewUpdate);
    document.getElementById('sortBySecondary').addEventListener('change', schedulePreviewUpdate);
    document.getElementById('showMarginBorder').addEventListener('change', schedulePreviewUpdate);
}

function handleModeChange(e) {
    const mode = e.target.value;
    gridSettings.style.display = mode === 'grid' ? 'block' : 'none';
    logTerminal(`Mode changed to: ${mode}`, 'info');
}

async function handleImageUpload(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    logTerminal(`Uploading ${files.length} images...`, 'info');
    showProgress('Uploading images...');
    
    const formData = new FormData();
    for (let file of files) {
        formData.append('images', file);
    }
    
    try {
        const response = await fetch('/api/upload-images', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            uploadedImages = true;
            uploadStatus.innerHTML = `<span class="upload-success"><i class="bi bi-check-circle"></i> ${data.uploaded} images uploaded</span>`;
            logTerminal(`Successfully uploaded ${data.uploaded} images`, 'success');
            
            if (data.errors && data.errors.length > 0) {
                data.errors.forEach(err => logTerminal(err, 'warning'));
            }
        } else {
            uploadStatus.innerHTML = `<span class="upload-error"><i class="bi bi-x-circle"></i> Upload failed</span>`;
            logTerminal(`Upload failed: ${data.error}`, 'error');
        }
    } catch (error) {
        uploadStatus.innerHTML = `<span class="upload-error"><i class="bi bi-x-circle"></i> Upload error</span>`;
        logTerminal(`Error: ${error.message}`, 'error');
    } finally {
        hideProgress();
        updateUIState();
        
        // Generate preview after upload
        generateLayoutPreview();
    }
}

async function generateLayoutPreview() {
    const previewSection = document.getElementById('previewSection');
    const previewGrid = document.getElementById('previewGrid');
    
    if (!uploadedImages) {
        previewSection.style.display = 'none';
        return;
    }
    
    try {
        logTerminal('Generating layout preview...', 'info');
        
        // Collect selected metadata fields
        const selectedMetadataFields = [];
        document.querySelectorAll('#metadataFieldsCheckboxes input[type="checkbox"]:checked').forEach(cb => {
            selectedMetadataFields.push(cb.value);
        });
        
        // Collect current settings
        const settings = {
            mode: document.querySelector('input[name="mode"]:checked').value,
            pageSize: document.getElementById('pageSize').value,
            sortBy: document.getElementById('sortBy').value,
            sortBySecondary: document.getElementById('sortBySecondary').value,
            scaleFactor: document.getElementById('scaleFactor').value,
            marginPx: document.getElementById('marginPx').value,
            spacingPx: document.getElementById('spacingPx').value,
            gridRows: document.getElementById('gridRows').value,
            gridCols: document.getElementById('gridCols').value,
            addCaption: document.getElementById('addCaption').checked,
            captionFontSize: document.getElementById('captionFontSize').value,
            captionPadding: document.getElementById('captionPadding').value,
            removeExtension: document.getElementById('removeExtension').checked,
            hideFieldNames: document.getElementById('hideFieldNames').checked,
            selectedMetadataFields: selectedMetadataFields,
            addScaleBar: document.getElementById('addScaleBar').checked,
            scaleBarCm: document.getElementById('scaleBarCm').value,
            pixelsPerCm: document.getElementById('pixelsPerCm').value,
            addTableNumber: document.getElementById('addTableNumber').checked,
            tableStartNumber: document.getElementById('tableStartNumber').value,
            tablePosition: document.getElementById('tablePosition').value,
            tableFontSize: document.getElementById('tableFontSize').value,
            tablePrefix: document.getElementById('tablePrefix').value,
            captionColumn: document.getElementById('captionColumn')?.value,
            showMarginBorder: document.getElementById('showMarginBorder').checked
        };
        
        const response = await fetch('/api/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Display only the first preview image with large size
            const firstPreviewUrl = data.preview_urls[0];
            
            previewGrid.innerHTML = `
                <div class="preview-layout-single fade-in">
                    <div class="preview-single-container">
                        <img src="${firstPreviewUrl}?t=${new Date().getTime()}" 
                             alt="Layout Preview - Page 1" 
                             class="preview-single-image"
                             onclick="openPreviewModal('${firstPreviewUrl}', 1)">
                    </div>
                    <div class="text-center mt-3">
                        <p class="text-muted">
                            <i class="bi bi-eye"></i> Preview of Page 1 - Click to zoom<br>
                            <strong>${data.total_images} images</strong> distributed across <strong>${data.total_pages} page(s)</strong>
                        </p>
                    </div>
                </div>
            `;
            previewSection.style.display = 'block';
            logTerminal(`Preview generated: ${data.total_images} images on ${data.total_pages} page(s)`, 'success');
        } else {
            throw new Error(data.error || 'Preview generation failed');
        }
        
    } catch (error) {
        logTerminal(`Preview error: ${error.message}`, 'error');
        previewSection.style.display = 'none';
    }
}

async function handleMetadataUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    logTerminal(`Uploading metadata file: ${file.name}`, 'info');
    showProgress('Uploading metadata...');
    
    const formData = new FormData();
    formData.append('metadata', file);
    
    try {
        const response = await fetch('/api/upload-metadata', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            uploadedMetadata = true;
            metadataHeaders = data.headers || [];
            metadataStatus.innerHTML = `<span class="upload-success"><i class="bi bi-check-circle"></i> ${data.count} records loaded</span>`;
            logTerminal(`Metadata loaded: ${data.count} records, ${data.headers.length} columns`, 'success');
            updateSortOptions();
            updateMetadataFieldCheckboxes();
        } else {
            metadataStatus.innerHTML = `<span class="upload-error"><i class="bi bi-x-circle"></i> Load failed</span>`;
            logTerminal(`Metadata error: ${data.error}`, 'error');
        }
    } catch (error) {
        metadataStatus.innerHTML = `<span class="upload-error"><i class="bi bi-x-circle"></i> Upload error</span>`;
        logTerminal(`Error: ${error.message}`, 'error');
    } finally {
        hideProgress();
        updateUIState();
    }
}

async function handleGenerate() {
    if (!uploadedImages) {
        logTerminal('Please upload images first!', 'error');
        return;
    }
    
    logTerminal('Starting layout generation...', 'info');
    showProgress('Generating layout...');
    resultSection.style.display = 'none';
    
    // Collect selected metadata fields
    const selectedMetadataFields = [];
    document.querySelectorAll('#metadataFieldsCheckboxes input[type="checkbox"]:checked').forEach(cb => {
        selectedMetadataFields.push(cb.value);
    });
    
    // Collect all settings
    const settings = {
        mode: document.querySelector('input[name="mode"]:checked').value,
        page_size: document.getElementById('pageSize').value,
        scale_factor: parseFloat(document.getElementById('scaleFactor').value),
        margin_px: parseInt(document.getElementById('marginPx').value),
        spacing_px: parseInt(document.getElementById('spacingPx').value),
        grid_rows: parseInt(document.getElementById('gridRows').value),
        grid_cols: parseInt(document.getElementById('gridCols').value),
        add_caption: document.getElementById('addCaption').checked,
        caption_font_size: parseInt(document.getElementById('captionFontSize').value),
        caption_padding: parseInt(document.getElementById('captionPadding').value),
        remove_extension: document.getElementById('removeExtension').checked,
        hide_field_names: document.getElementById('hideFieldNames').checked,
        selected_metadata_fields: selectedMetadataFields,
        add_scale_bar: document.getElementById('addScaleBar').checked,
        scale_bar_cm: parseInt(document.getElementById('scaleBarCm').value),
        pixels_per_cm: parseInt(document.getElementById('pixelsPerCm').value),
        export_format: document.getElementById('exportFormat').value,
        add_table_number: document.getElementById('addTableNumber').checked,
        table_start_number: parseInt(document.getElementById('tableStartNumber').value),
        table_position: document.getElementById('tablePosition').value,
        table_font_size: parseInt(document.getElementById('tableFontSize').value),
        table_prefix: document.getElementById('tablePrefix').value,
        sort_by: document.getElementById('sortBy').value,
        sort_by_secondary: document.getElementById('sortBySecondary').value,
        show_margin_border: document.getElementById('showMarginBorder').checked
    };
    
    logTerminal(`Settings: ${JSON.stringify(settings, null, 2)}`, 'info');
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            logTerminal(`✓ Layout generated successfully!`, 'success');
            logTerminal(`  File: ${data.filename}`, 'success');
            logTerminal(`  Pages: ${data.pages}`, 'success');
            
            // Show download section
            document.getElementById('resultFilename').textContent = data.filename;
            document.getElementById('resultPages').textContent = data.pages;
            document.getElementById('downloadBtn').href = data.download_url;
            resultSection.style.display = 'block';
            resultSection.classList.add('fade-in');
        } else {
            logTerminal(`✗ Generation failed: ${data.error}`, 'error');
        }
    } catch (error) {
        logTerminal(`✗ Error: ${error.message}`, 'error');
    } finally {
        hideProgress();
    }
}

async function handleClear() {
    if (!confirm('Clear all uploaded files and reset settings?')) {
        return;
    }
    
    logTerminal('Clearing session...', 'info');
    
    try {
        await fetch('/api/clear-session', {
            method: 'POST'
        });
        
        // Reset form
        imageUpload.value = '';
        metadataUpload.value = '';
        uploadStatus.innerHTML = '';
        metadataStatus.innerHTML = '';
        resultSection.style.display = 'none';
        previewSection.style.display = 'none';
        
        // Clear preview grid
        const previewGrid = document.getElementById('previewGrid');
        if (previewGrid) {
            previewGrid.innerHTML = '';
        }
        
        uploadedImages = false;
        uploadedMetadata = false;
        metadataHeaders = [];
        
        // Clear terminal
        terminalOutput.innerHTML = '<p class="text-success">Ready to process images...</p>';
        
        updateUIState();
        logTerminal('Session cleared', 'success');
    } catch (error) {
        logTerminal(`Error clearing session: ${error.message}`, 'error');
    }
}

function updateSortOptions() {
    const sortBy = document.getElementById('sortBy');
    const currentValue = sortBy.value;
    
    // Clear current options
    sortBy.innerHTML = `
        <option value="alphabetical">Alphabetical</option>
        <option value="natural_name">Natural</option>
        <option value="random">Random</option>
    `;
    
    // Add metadata headers as options
    if (metadataHeaders.length > 0) {
        const optgroup = document.createElement('optgroup');
        optgroup.label = 'Metadata Fields';
        
        metadataHeaders.forEach(header => {
            const option = document.createElement('option');
            option.value = header;
            option.textContent = header;
            optgroup.appendChild(option);
        });
        
        sortBy.appendChild(optgroup);
    }
    
    // Restore previous value if still valid
    const options = Array.from(sortBy.options).map(opt => opt.value);
    if (options.includes(currentValue)) {
        sortBy.value = currentValue;
    }
    
    // Update secondary sort options
    const sortBySecondary = document.getElementById('sortBySecondary');
    const currentSecondary = sortBySecondary.value;
    
    sortBySecondary.innerHTML = '<option value="none">None</option>';
    
    if (metadataHeaders.length > 0) {
        sortBySecondary.innerHTML += `
            <option value="alphabetical">Alphabetical</option>
            <option value="natural_name">Natural</option>
        `;
        
        metadataHeaders.forEach(header => {
            if (header !== currentValue) {  // Don't include current primary sort
                sortBySecondary.innerHTML += `<option value="${header}">${header}</option>`;
            }
        });
    }
    
    if (currentSecondary !== 'none') {
        sortBySecondary.value = currentSecondary;
    }
}

function updateMetadataFieldCheckboxes() {
    const container = document.getElementById('metadataFieldsCheckboxes');
    
    if (metadataHeaders.length === 0) {
        container.innerHTML = '<em class="text-muted">Upload metadata to see options</em>';
        return;
    }
    
    container.innerHTML = '';
    metadataHeaders.forEach(header => {
        const div = document.createElement('div');
        div.className = 'form-check';
        
        const checkbox = document.createElement('input');
        checkbox.className = 'form-check-input';
        checkbox.type = 'checkbox';
        checkbox.id = `metaField_${header}`;
        checkbox.value = header;
        checkbox.checked = true; // Default to showing all fields
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = `metaField_${header}`;
        label.textContent = header;
        
        div.appendChild(checkbox);
        div.appendChild(label);
        container.appendChild(div);
    });
}

function updateUIState() {
    generateBtn.disabled = !uploadedImages;
}

function showProgress(message) {
    progressText.textContent = message;
    progressBar.style.width = '100%';
    progressContainer.style.display = 'block';
    generateBtn.disabled = true;
}

function hideProgress() {
    progressContainer.style.display = 'none';
    progressBar.style.width = '0%';
    updateUIState();
}

function logTerminal(message, type = 'info') {
    const p = document.createElement('p');
    
    switch(type) {
        case 'success':
            p.className = 'text-success';
            break;
        case 'error':
            p.className = 'text-danger';
            break;
        case 'warning':
            p.className = 'text-warning';
            break;
        case 'info':
        default:
            p.className = 'text-info';
            break;
    }
    
    const timestamp = new Date().toLocaleTimeString();
    p.textContent = `[${timestamp}] ${message}`;
    
    terminalOutput.appendChild(p);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

// Drag and drop support
const dropZone = document.querySelector('.card-body');

if (dropZone) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
        dropZone.classList.add('border-primary');
    }
    
    function unhighlight(e) {
        dropZone.classList.remove('border-primary');
    }
    
    dropZone.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            // Check if files are images
            const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
            
            if (imageFiles.length > 0) {
                imageUpload.files = dt.files;
                handleImageUpload({ target: { files: dt.files }});
            }
        }
    }
}

// Preview modal functions
function openPreviewModal(imageUrl, pageNumber) {
    const modal = document.getElementById('previewModal');
    const modalImg = document.getElementById('modalPreviewImage');
    const caption = document.getElementById('previewModalCaption');
    
    modalImg.src = imageUrl + '?t=' + new Date().getTime();
    caption.textContent = `Preview - Page ${pageNumber}`;
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}
