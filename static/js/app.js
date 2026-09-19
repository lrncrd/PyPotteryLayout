// PyPotteryLayout - Frontend JavaScript

// Global state
let uploadedImages = false;
let uploadedMetadata = false;
let metadataHeaders = [];

// DOM Elements (will be initialized in DOMContentLoaded)
let imageUpload, metadataUpload, generateBtn, clearBtn, terminalOutput;
let uploadStatus, metadataStatus, progressContainer, progressBar, progressText;
let resultSection, previewSection, errorSection, errorMessage, emptyStateSection, scaleDisplay, scaleFactor;
let gridSettings, captionSettings, scaleBarSettings, tableNumberSettings, objectNumberSettings;

// Splash Screen
document.addEventListener('DOMContentLoaded', function () {
    // Initialize DOM elements
    imageUpload = document.getElementById('imageUpload');
    metadataUpload = document.getElementById('metadataUpload');
    generateBtn = document.getElementById('generateBtn');
    clearBtn = document.getElementById('clearBtn');
    terminalOutput = document.getElementById('terminalOutput');
    errorSection = document.getElementById('errorSection');
    errorMessage = document.getElementById('errorMessage');
    emptyStateSection = document.getElementById('emptyStateSection');
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
    objectNumberSettings = document.getElementById('objectNumberSettings');

    // Simulate loading process
    const splashScreen = document.getElementById('splash-screen');
    const splashProgressBar = document.getElementById('splash-progress-bar');
    const splashProgressText = document.getElementById('splash-progress-text');
    const splashMessage = document.getElementById('splash-message');

    const loadingSteps = [
        { progress: 20, message: 'Loading layout engine...' },
        { progress: 40, message: 'Initializing drafting grid...' },
        { progress: 60, message: 'Setting up metric scaling controls...' },
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
    document.getElementById('addCaption').addEventListener('change', function () {
        captionSettings.style.display = this.checked ? 'block' : 'none';
    });

    document.getElementById('addScaleBar').addEventListener('change', function () {
        scaleBarSettings.style.display = this.checked ? 'block' : 'none';
    });

    document.getElementById('addTableNumber').addEventListener('change', function () {
        tableNumberSettings.style.display = this.checked ? 'block' : 'none';
    });

    document.getElementById('addObjectNumber').addEventListener('change', function () {
        objectNumberSettings.style.display = this.checked ? 'block' : 'none';
    });

    // Show primary sort value as a per-image title - show/hide font size option
    document.getElementById('showPrimarySortHeader').addEventListener('change', function () {
        document.getElementById('sortHeaderOptions').style.display = this.checked ? 'block' : 'none';
    });

    // Scale input mode - decimal slider vs ratio (1:N)
    document.querySelectorAll('input[name="scaleInputMode"]').forEach(radio => {
        radio.addEventListener('change', function () {
            const isRatio = this.value === 'ratio';
            document.getElementById('scaleDecimalMode').style.display = isRatio ? 'none' : 'block';
            document.getElementById('scaleRatioMode').style.display = isRatio ? 'flex' : 'none';
            updateScaleRatioDisplay();
        });
    });
    document.getElementById('scaleRatioA').addEventListener('input', updateScaleRatioDisplay);
    document.getElementById('scaleRatioB').addEventListener('input', updateScaleRatioDisplay);

    // Page break on primary change - show/hide options
    document.getElementById('pageBreakOnPrimaryChange').addEventListener('change', function () {
        const primaryBreakOptions = document.getElementById('primaryBreakOptions');
        primaryBreakOptions.style.display = this.checked ? 'block' : 'none';
    });

    // Primary break type - show/hide divider settings
    document.querySelectorAll('input[name="primaryBreakType"]').forEach(radio => {
        radio.addEventListener('change', function () {
            const dividerSettings = document.getElementById('dividerSettings');
            dividerSettings.style.display = (this.value === 'divider') ? 'block' : 'none';
        });
    });

    // Scale factor slider
    scaleFactor.addEventListener('input', function () {
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

/** Resolved decimal scale factor, from whichever input mode (decimal slider
 * or A:B ratio) is currently active. Always returns a plain float so the
 * rest of the app (preview + generate payloads, scale bar sizing) can stay
 * unaware of which mode produced it. */
function getResolvedScaleFactor() {
    const isRatio = document.getElementById('scaleModeRatio').checked;
    if (isRatio) {
        const a = parseFloat(document.getElementById('scaleRatioA').value);
        const b = parseFloat(document.getElementById('scaleRatioB').value);
        if (a > 0 && b > 0) return a / b;
        return 1.0;
    }
    return parseFloat(document.getElementById('scaleFactor').value);
}

function updateScaleRatioDisplay() {
    const a = parseFloat(document.getElementById('scaleRatioA').value);
    const b = parseFloat(document.getElementById('scaleRatioB').value);
    const display = document.getElementById('scaleRatioDisplay');
    if (a > 0 && b > 0) {
        display.textContent = (a / b).toFixed(2) + 'x';
    } else {
        display.textContent = '--';
    }
}

function setupPreviewAutoUpdate() {
    // Debounce function to avoid too many preview requests
    let previewTimeout;
    function schedulePreviewUpdate() {
        if (!uploadedImages) return;

        showPreviewUpdatingState();
        clearTimeout(previewTimeout);
        previewTimeout = setTimeout(() => {
            generateLayoutPreview();
        }, 400); // Wait 400ms after last change
    }

    // Helper to attach multiple event types (e.g. input for typing/spinners and change for blur/selection)
    function bindAutoUpdate(elId, events = ['input', 'change']) {
        const el = document.getElementById(elId);
        if (el) {
            events.forEach(evt => el.addEventListener(evt, schedulePreviewUpdate));
        }
    }

    // 1. Layout Mode & Page Structure
    document.querySelectorAll('input[name="mode"]').forEach(radio => {
        radio.addEventListener('change', schedulePreviewUpdate);
    });
    bindAutoUpdate('pageSize', ['change']);
    bindAutoUpdate('gridRows', ['input', 'change']);
    bindAutoUpdate('gridCols', ['input', 'change']);

    // 2. Scale Controls
    document.querySelectorAll('input[name="scaleInputMode"]').forEach(radio => {
        radio.addEventListener('change', schedulePreviewUpdate);
    });
    bindAutoUpdate('scaleFactor', ['input', 'change']);
    bindAutoUpdate('scaleRatioA', ['input', 'change']);
    bindAutoUpdate('scaleRatioB', ['input', 'change']);

    // 3. Spacing & Dimensions
    bindAutoUpdate('marginPx', ['input', 'change']);
    bindAutoUpdate('topSpacingPx', ['input', 'change']);
    bindAutoUpdate('spacingPx', ['input', 'change']);
    bindAutoUpdate('verticalAlignment', ['change']);
    bindAutoUpdate('showMarginBorder', ['change']);

    // 4. Captions & Metadata
    bindAutoUpdate('addCaption', ['change']);
    bindAutoUpdate('captionFontSize', ['input', 'change']);
    bindAutoUpdate('captionPadding', ['input', 'change']);
    bindAutoUpdate('removeExtension', ['change']);
    bindAutoUpdate('hideFieldNames', ['change']);
    const metaContainer = document.getElementById('metadataFieldsCheckboxes');
    if (metaContainer) {
        metaContainer.addEventListener('change', schedulePreviewUpdate);
    }

    // 5. Object Numbering
    bindAutoUpdate('addObjectNumber', ['change']);
    bindAutoUpdate('objectNumberPosition', ['change']);
    bindAutoUpdate('objectNumberFontSize', ['input', 'change']);

    // 6. Table Numbers
    bindAutoUpdate('addTableNumber', ['change']);
    bindAutoUpdate('tablePrefix', ['input', 'change']);
    bindAutoUpdate('tableStartNumber', ['input', 'change']);
    bindAutoUpdate('tableFontSize', ['input', 'change']);
    bindAutoUpdate('tablePosition', ['change']);

    // 7. Sorting & Grouping
    bindAutoUpdate('sortBy', ['change']);
    bindAutoUpdate('sortBySecondary', ['change']);
    bindAutoUpdate('showPrimarySortHeader', ['change']);
    bindAutoUpdate('sortHeaderFontSize', ['input', 'change']);
    bindAutoUpdate('pageBreakOnPrimaryChange', ['change']);
    document.querySelectorAll('input[name="primaryBreakType"]').forEach(radio => {
        radio.addEventListener('change', schedulePreviewUpdate);
    });
    bindAutoUpdate('dividerThickness', ['input', 'change']);
    bindAutoUpdate('dividerWidth', ['input', 'change']);

    // 8. Scale Bar
    bindAutoUpdate('addScaleBar', ['change']);
    bindAutoUpdate('scaleBarCm', ['input', 'change']);
    bindAutoUpdate('pixelsPerCm', ['input', 'change']);
}

function handleModeChange(e) {
    const mode = e.target.value;
    gridSettings.style.display = mode === 'grid' ? 'block' : 'none';
    logTerminal(`Mode changed to: ${mode}`, 'info');
}

async function handleImageUpload(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    // 1. Show full-screen upload overlay IMMEDIATELY
    showUploadOverlay(files.length);

    // 2. Yield to browser render thread so the overlay is painted on screen instantly before heavy processing!
    await new Promise(resolve => setTimeout(resolve, 50));

    logTerminal(`Ready to process images...`, 'info');
    logTerminal(`Uploading ${files.length} images...`, 'info');

    // Prominent feedback next to file input
    imageUpload.disabled = true;
    uploadStatus.className = 'mt-2 alert alert-primary d-flex align-items-center gap-2 py-2 px-3 mb-0';
    uploadStatus.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> <span>Uploading ${files.length} images...</span>`;

    // Upload in batches of 100 images to avoid payload size issues
    const BATCH_SIZE = 100;
    const totalFiles = files.length;
    let uploadedCount = 0;
    let allErrors = [];

    try {
        // Upload in batches slice-by-slice without heavy upfront memory allocations
        for (let i = 0; i < totalFiles; i += BATCH_SIZE) {
            const batchNumber = Math.floor(i / BATCH_SIZE) + 1;
            const totalBatches = Math.ceil(totalFiles / BATCH_SIZE);
            const batchEnd = Math.min(i + BATCH_SIZE, totalFiles);
            const batch = [];
            for (let k = i; k < batchEnd; k++) {
                batch.push(files[k]);
            }

            showProgress(`Uploading batch ${batchNumber}/${totalBatches} (${batch.length} images)...`);
            uploadStatus.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> <span>Uploading batch ${batchNumber}/${totalBatches} (${batch.length} images)...</span>`;
            logTerminal(`Batch ${batchNumber}/${totalBatches}: ${batch.length} images`, 'info');

            updateUploadOverlay(uploadedCount, totalFiles, `Uploading batch ${batchNumber} of ${totalBatches} (${batch.length} images)...`);

            // Yield to browser UI thread to keep smooth progress bar animation and prevent UI freeze
            await new Promise(resolve => setTimeout(resolve, 40));

            const formData = new FormData();
            // Add flag to indicate if this is the first batch (should clear folder)
            formData.append('is_first_batch', i === 0 ? 'true' : 'false');

            for (let file of batch) {
                formData.append('images', file);
            }

            const response = await fetch('/api/upload-images', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                uploadedCount += data.uploaded;
                updateUploadOverlay(uploadedCount, totalFiles);
                await new Promise(resolve => setTimeout(resolve, 30));
                if (data.errors && data.errors.length > 0) {
                    allErrors = allErrors.concat(data.errors);
                }
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        }

        // All batches uploaded successfully
        uploadedImages = true;
        uploadStatus.className = 'mt-2';
        uploadStatus.innerHTML = `<span class="upload-success"><i class="bi bi-check-circle"></i> ${uploadedCount} images uploaded</span>`;
        logTerminal(`Successfully uploaded ${uploadedCount} images`, 'success');

        if (allErrors.length > 0) {
            allErrors.forEach(err => logTerminal(err, 'warning'));
        }

        // Update status text on overlay before preview generation
        updateUploadOverlayStatus('Generating preview...', 'Processing layout preview for uploaded images...');
        await new Promise(resolve => setTimeout(resolve, 50));

        // Generate preview after upload
        await generateLayoutPreview();

    } catch (error) {
        uploadStatus.className = 'mt-2';
        uploadStatus.innerHTML = `<span class="upload-error"><i class="bi bi-x-circle"></i> Upload error</span>`;
        logTerminal(`Error: ${error.message}`, 'error');
    } finally {
        imageUpload.disabled = false;
        hideProgress();
        updateUIState();
        hideUploadOverlay();
    }
}

function showPreviewUpdatingState() {
    const previewGrid = document.getElementById('previewGrid');
    const updateBtn = document.getElementById('updatePreviewBtn');
    if (previewGrid) {
        previewGrid.classList.add('preview-is-updating');
        let indicator = document.getElementById('previewUpdatingOverlay');
        if (!indicator && previewGrid.querySelector('.preview-paper-wrapper')) {
            indicator = document.createElement('div');
            indicator.id = 'previewUpdatingOverlay';
            indicator.className = 'preview-updating-overlay fade-in';
            indicator.innerHTML = `
                <div class="preview-spinner-pill">
                    <span class="spinner-border spinner-border-sm text-primary" role="status"></span>
                    <span>Updating preview...</span>
                </div>
            `;
            const wrapper = previewGrid.querySelector('.preview-paper-wrapper');
            if (wrapper) {
                wrapper.appendChild(indicator);
            } else {
                previewGrid.appendChild(indicator);
            }
        }
    }
    if (updateBtn) {
        const icon = updateBtn.querySelector('i');
        if (icon) icon.classList.add('spin-icon');
    }
}

function hidePreviewUpdatingState() {
    const previewGrid = document.getElementById('previewGrid');
    const updateBtn = document.getElementById('updatePreviewBtn');
    const indicator = document.getElementById('previewUpdatingOverlay');
    if (indicator) {
        indicator.remove();
    }
    if (previewGrid) {
        previewGrid.classList.remove('preview-is-updating');
    }
    if (updateBtn) {
        const icon = updateBtn.querySelector('i');
        if (icon) icon.classList.remove('spin-icon');
    }
}

async function generateLayoutPreview() {
    const previewSection = document.getElementById('previewSection');
    const previewGrid = document.getElementById('previewGrid');

    if (!uploadedImages) {
        previewSection.style.display = 'none';
        return;
    }

    showPreviewUpdatingState();

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
            scaleFactor: getResolvedScaleFactor(),
            marginPx: document.getElementById('marginPx').value,
            topSpacingPx: document.getElementById('topSpacingPx').value,
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
            showMarginBorder: document.getElementById('showMarginBorder').checked,
            pageBreakOnPrimaryChange: document.getElementById('pageBreakOnPrimaryChange').checked,
            primaryBreakType: document.querySelector('input[name="primaryBreakType"]:checked')?.value || 'new_page',
            showPrimarySortHeader: document.getElementById('showPrimarySortHeader').checked,
            sortHeaderFontSize: parseInt(document.getElementById('sortHeaderFontSize').value) || 16,
            dividerThickness: parseInt(document.getElementById('dividerThickness').value) || 5,
            dividerWidth: parseInt(document.getElementById('dividerWidth').value) || 80,
            verticalAlignment: document.getElementById('verticalAlignment').value,
            addObjectNumber: document.getElementById('addObjectNumber').checked,
            objectNumberPosition: document.getElementById('objectNumberPosition').value,
            objectNumberFontSize: parseInt(document.getElementById('objectNumberFontSize').value) || 18
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
            // Display only the first preview image with elegant paper design
            const firstPreviewUrl = data.preview_urls[0];

            // Build preview badges
            let limitedWarning = '';
            if (data.is_preview_limited) {
                limitedWarning = `
                    <div class="alert alert-warning py-2 px-3 mb-3" style="border-radius: 8px; font-size: 0.85rem;">
                        <i class="bi bi-exclamation-triangle"></i> 
                        Preview limited to first <strong>${data.total_images}</strong> of <strong>${data.total_images_in_dataset}</strong> total images
                    </div>
                `;
            }

            previewGrid.innerHTML = `
                <div class="preview-layout-single fade-in">
                    ${limitedWarning}
                    <div class="preview-paper-wrapper">
                        <div class="preview-paper">
                            <img src="${firstPreviewUrl}?t=${new Date().getTime()}" 
                                 alt="Layout Preview - Page 1" 
                                 class="preview-single-image"
                                 onclick="openPreviewModal('${firstPreviewUrl}', 1)">
                            <span class="zoom-hint"><i class="bi bi-zoom-in"></i> Click to zoom</span>
                        </div>
                        <div class="page-indicator">Page 1 of ${data.total_pages}</div>
                    </div>
                    <div class="preview-info-badge">
                        <i class="bi bi-images"></i>
                        <strong>${data.total_images}</strong> images
                        <span class="divider"></span>
                        <i class="bi bi-files"></i>
                        <strong>${data.total_pages}</strong> page${data.total_pages > 1 ? 's' : ''}
                    </div>
                </div>
            `;
            previewSection.style.display = 'block';
            if (emptyStateSection) emptyStateSection.style.display = 'none';

            if (data.is_preview_limited) {
                logTerminal(`Preview generated (limited to ${data.total_images}/${data.total_images_in_dataset} images): ${data.total_pages} page(s)`, 'warning');
            } else {
                logTerminal(`Preview generated: ${data.total_images} images on ${data.total_pages} page(s)`, 'success');
            }
        } else {
            throw new Error(data.error || 'Preview generation failed');
        }

    } catch (error) {
        logTerminal(`Preview error: ${error.message}`, 'error');
        previewSection.style.display = 'none';
        if (emptyStateSection && (!resultSection || resultSection.style.display === 'none')) {
            emptyStateSection.style.display = 'block';
        }
    } finally {
        hidePreviewUpdatingState();
    }
}

async function handleMetadataUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    logTerminal(`Uploading metadata file: ${file.name}`, 'info');
    showProgress('Uploading metadata...');
    metadataUpload.disabled = true;
    metadataStatus.className = 'mt-2 alert alert-primary d-flex align-items-center gap-2 py-2 px-3 mb-0';
    metadataStatus.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> <span>Loading ${file.name}...</span>`;
    metadataStatus.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    const formData = new FormData();
    formData.append('metadata', file);

    try {
        const response = await fetch('/api/upload-metadata', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        metadataStatus.className = 'mt-2';
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
        metadataStatus.className = 'mt-2';
        metadataStatus.innerHTML = `<span class="upload-error"><i class="bi bi-x-circle"></i> Upload error</span>`;
        logTerminal(`Error: ${error.message}`, 'error');
    } finally {
        metadataUpload.disabled = false;
        hideProgress();
        updateUIState();
    }
}

async function handleGenerate() {
    if (!uploadedImages) {
        logTerminal('Please upload images first!', 'error');
        showError('Please upload images first before generating layout!');
        return;
    }

    hideError();
    logTerminal('Starting layout generation...', 'info');
    showProgress('Generating layout...');
    if (resultSection) resultSection.style.display = 'none';
    if (emptyStateSection) emptyStateSection.style.display = 'none';

    // Collect selected metadata fields
    const selectedMetadataFields = [];
    document.querySelectorAll('#metadataFieldsCheckboxes input[type="checkbox"]:checked').forEach(cb => {
        selectedMetadataFields.push(cb.value);
    });

    // Collect all settings
    const settings = {
        mode: document.querySelector('input[name="mode"]:checked').value,
        page_size: document.getElementById('pageSize').value,
        scale_factor: getResolvedScaleFactor(),
        margin_px: parseInt(document.getElementById('marginPx').value),
        top_spacing_px: parseInt(document.getElementById('topSpacingPx').value) || 0,
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
        show_margin_border: document.getElementById('showMarginBorder').checked,
        page_break_on_primary_change: document.getElementById('pageBreakOnPrimaryChange').checked,
        primary_break_type: document.querySelector('input[name="primaryBreakType"]:checked')?.value || 'new_page',
        show_primary_sort_header: document.getElementById('showPrimarySortHeader').checked,
        sort_header_font_size: parseInt(document.getElementById('sortHeaderFontSize').value) || 16,
        divider_thickness: parseInt(document.getElementById('dividerThickness').value) || 5,
        divider_width: parseInt(document.getElementById('dividerWidth').value) || 80,
        vertical_alignment: document.getElementById('verticalAlignment').value,
        add_object_number: document.getElementById('addObjectNumber').checked,
        object_number_position: document.getElementById('objectNumberPosition').value,
        object_number_font_size: parseInt(document.getElementById('objectNumberFontSize').value) || 18
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
            logTerminal(`[OK] Layout generated successfully!`, 'success');
            logTerminal(`  File: ${data.filename}`, 'success');
            logTerminal(`  Pages: ${data.pages}`, 'success');

            // Show download section
            document.getElementById('resultFilename').textContent = data.filename;
            document.getElementById('resultPages').textContent = data.pages;
            document.getElementById('downloadBtn').href = data.download_url;
            if (emptyStateSection) emptyStateSection.style.display = 'none';
            if (errorSection) errorSection.style.display = 'none';
            resultSection.style.display = 'block';
            resultSection.classList.add('fade-in');
        } else {
            logTerminal(`[ERROR] Generation failed: ${data.error}`, 'error');
            showError(data.error || 'Failed to generate layout.');
            if (emptyStateSection && (!resultSection || resultSection.style.display === 'none')) {
                emptyStateSection.style.display = 'block';
            }
        }
    } catch (error) {
        logTerminal(`[ERROR] Error: ${error.message}`, 'error');
        showError(`Generation error: ${error.message}`);
        if (emptyStateSection && (!resultSection || resultSection.style.display === 'none')) {
            emptyStateSection.style.display = 'block';
        }
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
        if (resultSection) resultSection.style.display = 'none';
        if (previewSection) previewSection.style.display = 'none';
        hideError();
        if (emptyStateSection) emptyStateSection.style.display = 'block';

        // Clear preview grid
        const previewGrid = document.getElementById('previewGrid');
        if (previewGrid) {
            previewGrid.innerHTML = '';
        }

        uploadedImages = false;
        uploadedMetadata = false;
        metadataHeaders = [];

        // Clear terminal if it exists
        if (terminalOutput) {
            terminalOutput.innerHTML = '<p class="text-success">[READY] Ready to process images...</p>';
        }

        updateUIState();
        logTerminal('Session cleared', 'success');
    } catch (error) {
        logTerminal(`Error clearing session: ${error.message}`, 'error');
        showError(`Error clearing session: ${error.message}`);
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

// Full-Screen Upload Overlay Helper Functions
function showUploadOverlay(totalFiles) {
    const overlay = document.getElementById('imageUploadOverlay');
    const title = document.getElementById('uploadOverlayTitle');
    const subtitle = document.getElementById('uploadOverlaySubtitle');
    const progressBar = document.getElementById('uploadOverlayProgressBar');
    const statsText = document.getElementById('uploadOverlayStatsText');
    const percentText = document.getElementById('uploadOverlayPercentText');

    if (!overlay) return;

    if (title) title.textContent = 'Uploading images...';
    if (subtitle) subtitle.textContent = `Preparing ${totalFiles} images for upload...`;
    if (progressBar) progressBar.style.width = '0%';
    if (statsText) statsText.innerHTML = `<i class="bi bi-images"></i> 0 / ${totalFiles} images`;
    if (percentText) percentText.textContent = '0%';

    overlay.style.display = 'flex';
    void overlay.offsetWidth; // Force reflow for smooth CSS transition
    overlay.classList.add('active');
}

function updateUploadOverlay(uploadedCount, totalFiles, customSubtitle = null) {
    const subtitle = document.getElementById('uploadOverlaySubtitle');
    const progressBar = document.getElementById('uploadOverlayProgressBar');
    const statsText = document.getElementById('uploadOverlayStatsText');
    const percentText = document.getElementById('uploadOverlayPercentText');

    const percent = Math.min(100, Math.round((uploadedCount / totalFiles) * 100));

    if (progressBar) progressBar.style.width = `${percent}%`;
    if (percentText) percentText.textContent = `${percent}%`;
    if (statsText) statsText.innerHTML = `<i class="bi bi-images"></i> ${uploadedCount} / ${totalFiles} images`;
    if (subtitle && customSubtitle) subtitle.textContent = customSubtitle;
}

function updateUploadOverlayStatus(titleText, subtitleText) {
    const title = document.getElementById('uploadOverlayTitle');
    const subtitle = document.getElementById('uploadOverlaySubtitle');
    if (title) title.textContent = titleText;
    if (subtitle) subtitle.textContent = subtitleText;
}

function hideUploadOverlay() {
    const overlay = document.getElementById('imageUploadOverlay');
    if (!overlay) return;

    overlay.classList.remove('active');
    setTimeout(() => {
        overlay.style.display = 'none';
    }, 300);
}

function logTerminal(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    if (!terminalOutput) return;

    const p = document.createElement('p');

    switch (type) {
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

function showError(message) {
    if (errorMessage && errorSection) {
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
        errorSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        alert(message);
    }
}

function hideError() {
    if (errorSection) {
        errorSection.style.display = 'none';
    }
}

// Drag and drop support
const dropZones = document.querySelectorAll('.file-upload-box, .basic-settings-card');

dropZones.forEach(zone => {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        zone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        zone.addEventListener(eventName, () => zone.classList.add('border-primary'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        zone.addEventListener(eventName, () => zone.classList.remove('border-primary'), false);
    });

    zone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files && files.length > 0) {
            const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
            if (imageFiles.length > 0) {
                imageUpload.files = dt.files;
                handleImageUpload({ target: { files: dt.files } });
            }
        }
    }
});

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

// System Hardware Info & Citation Helper
window.copyCitation = function (elementId, btnElement) {
    const textEl = document.getElementById(elementId);
    if (!textEl) return;
    const text = textEl.innerText.replace(/^"|"$/g, '').trim();
    navigator.clipboard.writeText(text).then(() => {
        const btn = btnElement || (window.event && window.event.target ? window.event.target.closest('.mac-copy-link') : null) || document.querySelector('.mac-copy-link');
        if (btn) {
            const orig = btn.innerHTML;
            btn.innerHTML = '<i class="bi bi-check2"></i> Copied!';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.innerHTML = orig;
                btn.classList.remove('copied');
            }, 2000);
        }
    }).catch(err => {
        console.error('Failed to copy citation:', err);
    });
};

function fetchSystemInfo() {
    const cpuEl = document.getElementById('systemCPU');
    const gpuEl = document.getElementById('systemGPU');
    if (!cpuEl || !gpuEl) return;

    fetch('/api/system-info')
        .then(res => res.json())
        .then(data => {
            const cores = (data.cpu && data.cpu.cores) || data.cpu_count || 1;
            const platform = (data.cpu && data.cpu.platform) || data.platform || '';
            cpuEl.innerHTML = `<i class="bi bi-cpu me-1"></i> ${cores} Cores${platform ? ` (${platform})` : ''}`;

            const cuda = (data.gpu && data.gpu.cuda_available) || data.cuda_available;
            const gpuNames = (data.gpu && data.gpu.gpu_names) || (data.cuda_device_name ? [data.cuda_device_name] : []);
            const mps = (data.mps && data.mps.mps_available) || data.mps_available;

            if (cuda) {
                const name = gpuNames.length > 0 ? gpuNames[0] : 'NVIDIA CUDA';
                gpuEl.innerHTML = `<i class="bi bi-gpu-card me-1"></i> ${name} (CUDA)`;
                gpuEl.className = 'chip-active';
            } else if (mps) {
                gpuEl.innerHTML = `<i class="bi bi-gpu-card me-1"></i> Apple Silicon (MPS)`;
                gpuEl.className = 'chip-active';
            } else {
                gpuEl.innerHTML = `<i class="bi bi-gpu-card me-1"></i> CPU Only`;
                gpuEl.className = 'chip-cpu-only';
            }
        })
        .catch(err => {
            console.error('Failed to load system info:', err);
            cpuEl.innerHTML = '<i class="bi bi-cpu me-1"></i> Available';
            gpuEl.innerHTML = '<i class="bi bi-gpu-card me-1"></i> CPU Only';
            gpuEl.className = 'chip-cpu-only';
        });
}

document.addEventListener('DOMContentLoaded', function () {
    const infoModalEl = document.getElementById('infoModal');
    if (infoModalEl) {
        infoModalEl.addEventListener('show.bs.modal', fetchSystemInfo);
    }
});

// ==========================================
// Auto-Shutdown Heartbeat & Beacon System
// ==========================================
(function initAutoShutdownBeacon() {
    const tabSessionId = 'tab_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
    const HEARTBEAT_INTERVAL_MS = 2500;

    function sendHeartbeat() {
        fetch('/api/heartbeat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tab_id: tabSessionId }),
            keepalive: true
        }).catch(() => {});
    }

    // Ping iniziale immediato
    sendHeartbeat();

    // Ping periodico
    const intervalId = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_MS);

    // Re-ping al ritorno del focus sulla scheda
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') sendHeartbeat();
    });
    window.addEventListener('focus', sendHeartbeat);

    // 1. Finestra di conferma alla chiusura della scheda o del browser
    window.addEventListener('beforeunload', (e) => {
        e.preventDefault();
        e.returnValue = '';
        return '';
    });

    // 2. Invio del beacon SOLO quando l'utente ha effettivamente confermato l'uscita
    let beaconSent = false;
    function sendShutdownBeacon() {
        if (beaconSent) return;
        beaconSent = true;
        clearInterval(intervalId);
        const payload = JSON.stringify({ tab_id: tabSessionId });

        if (navigator.sendBeacon) {
            const blob = new Blob([payload], { type: 'application/json' });
            navigator.sendBeacon('/api/beacon_shutdown', blob);
        } else {
            fetch('/api/beacon_shutdown', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: payload,
                keepalive: true
            }).catch(() => {});
        }
    }

    window.addEventListener('pagehide', sendShutdownBeacon);
    window.addEventListener('unload', sendShutdownBeacon);
})();

