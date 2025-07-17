// Global data store
let samplesData = {};
let unassignedFiles = [];
let allFiles = [];

function initializeData() {
    samplesData = JSON.parse(JSON.stringify(initialData.samples));
    allFiles = [...initialData.all_files];

    // Extract unassigned files from samples data
    extractUnassignedFiles();

    renderSamples();
    renderUnassignedFiles();
}

function extractUnassignedFiles() {
    unassignedFiles = [];

    // Collect all unassigned files from all samples
    Object.keys(samplesData).forEach(sampleName => {
        if (samplesData[sampleName].unassigned) {
            unassignedFiles.push(...samplesData[sampleName].unassigned);
            // Remove unassigned from sample data since we'll track it separately
            delete samplesData[sampleName].unassigned;
        }
    });

    // Remove duplicate files
    unassignedFiles = [...new Set(unassignedFiles)];
}

function renderSamples() {
    const samplesContainer = document.getElementById('samples-list');
    const sampleFilesContainer = document.getElementById('sample-files-container');

    // Clear containers
    samplesContainer.innerHTML = '';
    sampleFilesContainer.innerHTML = '';

    // Create sample names overview
    renderSampleNamesList();

    // Render sample file containers
    Object.keys(samplesData).forEach(sampleName => {
        renderSampleContainer(sampleName);
    });
}

function renderUnassignedFiles() {
    const unassignedContainer = document.getElementById('unassigned-files-container');
    const unassignedCount = document.getElementById('unassigned-count');
    const placeholder = document.getElementById('dock-placeholder');

    // Update counter
    unassignedCount.textContent = unassignedFiles.length;

    // Remove existing file elements but keep placeholder
    const existingFiles = unassignedContainer.querySelectorAll('.file-item');
    existingFiles.forEach(file => file.remove());

    if (unassignedFiles.length === 0) {
        // Show placeholder
        placeholder.style.display = 'flex';
        unassignedContainer.classList.remove('has-files');
    } else {
        // Hide placeholder and show files
        placeholder.style.display = 'none';
        unassignedContainer.classList.add('has-files');

        unassignedFiles.forEach(filename => {
            const fileElement = createUnassignedFileElement(filename);
            unassignedContainer.appendChild(fileElement);
        });
    }
}

function createUnassignedFileElement(filename) {
    const fileDiv = document.createElement('div');
    fileDiv.className = 'file-item unassigned-file-item';
    fileDiv.draggable = true;
    fileDiv.dataset.filename = filename;

    // Determine file icon based on extension
    let icon = 'bi-file';
    if (filename.toLowerCase().includes('.fastq') || filename.toLowerCase().includes('.fq')) {
        icon = 'bi-file-earmark-text';
    } else if (filename.toLowerCase().includes('.txt') || filename.toLowerCase().includes('.csv')) {
        icon = 'bi-file-earmark-spreadsheet';
    }

    fileDiv.innerHTML = `
        <span class="file-content">
            <i class="${icon}"></i> ${filename}
        </span>
    `;

    setupDragEvents(fileDiv);
    return fileDiv;
}
function renderSampleNamesList() {
    const samplesContainer = document.getElementById('samples-list');

    // Create container for sample names
    const namesContainer = document.createElement('div');
    namesContainer.className = 'sample-names-container';

    if (Object.keys(samplesData).length === 0) {
        namesContainer.innerHTML = '<p class="text-muted mb-0">No samples yet. Add samples to organize files.</p>';
    } else {
        namesContainer.innerHTML = '<h6 class="mb-2">Current Samples:</h6>';

        Object.keys(samplesData).forEach(sampleName => {
            const nameItem = document.createElement('div');
            nameItem.className = 'sample-name-item';

            const rawCount = samplesData[sampleName].raw ? samplesData[sampleName].raw.length : 0;
            const processedCount = samplesData[sampleName].processed ? samplesData[sampleName].processed.length : 0;

            nameItem.innerHTML = `
                <div class="sample-name-content">
                    <strong>${sampleName}</strong>
                    <div class="files-stats">
                        Raw: ${rawCount} | Processed: ${processedCount}
                    </div>
                </div>
                <span class="remove-sample-name" onclick="removeSample('${sampleName}')" title="Remove Sample">
                    <i class="bi bi-x-lg"></i>
                </span>
            `;

            namesContainer.appendChild(nameItem);
        });
    }

    samplesContainer.appendChild(namesContainer);
}

function renderSampleContainer(sampleName) {
    const sampleFilesContainer = document.getElementById('sample-files-container');

    // Create main sample container
    const sampleDiv = document.createElement('div');
    sampleDiv.className = 'sample-container';
    sampleDiv.dataset.sample = sampleName;

    // Create sample header
    const headerDiv = document.createElement('div');
    headerDiv.className = 'sample-header';

    const rawCount = samplesData[sampleName].raw ? samplesData[sampleName].raw.length : 0;
    const processedCount = samplesData[sampleName].processed ? samplesData[sampleName].processed.length : 0;

    headerDiv.innerHTML = `
        <h5><i class="bi bi-folder"></i> ${sampleName}</h5>
        <div>
            <span class="badge bg-primary me-2">Raw: ${rawCount}</span>
            <span class="badge bg-success me-2">Processed: ${processedCount}</span>
            <span class="remove-sample" onclick="removeSample('${sampleName}')" title="Remove Sample">
                <i class="bi bi-x-lg"></i>
            </span>
        </div>
    `;

    // Create files row container
    const filesRowDiv = document.createElement('div');
    filesRowDiv.className = 'sample-files-row';

    // Create raw files section
    const rawSectionDiv = document.createElement('div');
    rawSectionDiv.className = 'sample-files-section raw-section';
    rawSectionDiv.dataset.sample = sampleName;
    rawSectionDiv.dataset.type = 'raw';

    rawSectionDiv.innerHTML = '<h6><i class="bi bi-file-earmark-text"></i> Raw Reads</h6>';

    if (!samplesData[sampleName].raw || samplesData[sampleName].raw.length === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'empty-section';
        emptyDiv.innerHTML = 'Drop raw files here';
        rawSectionDiv.appendChild(emptyDiv);
    } else {
        samplesData[sampleName].raw.forEach(filename => {
            const fileElement = createFileElement(filename);
            rawSectionDiv.appendChild(fileElement);
        });
    }

    // Create processed files section
    const processedSectionDiv = document.createElement('div');
    processedSectionDiv.className = 'sample-files-section processed-section';
    processedSectionDiv.dataset.sample = sampleName;
    processedSectionDiv.dataset.type = 'processed';

    processedSectionDiv.innerHTML = '<h6><i class="bi bi-gear"></i> Processed Reads</h6>';

    if (!samplesData[sampleName].processed || samplesData[sampleName].processed.length === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'empty-section';
        emptyDiv.innerHTML = 'Drop processed files here';
        processedSectionDiv.appendChild(emptyDiv);
    } else {
        samplesData[sampleName].processed.forEach(filename => {
            const fileElement = createFileElement(filename);
            processedSectionDiv.appendChild(fileElement);
        });
    }

    // Setup drop zones
    setupDropZone(rawSectionDiv);
    setupDropZone(processedSectionDiv);

    // Assemble the container
    filesRowDiv.appendChild(rawSectionDiv);
    filesRowDiv.appendChild(processedSectionDiv);

    sampleDiv.appendChild(headerDiv);
    sampleDiv.appendChild(filesRowDiv);

    sampleFilesContainer.appendChild(sampleDiv);
}

function createFileElement(filename) {
    const fileDiv = document.createElement('div');
    fileDiv.className = 'file-item';
    fileDiv.draggable = true;
    fileDiv.dataset.filename = filename;

    // Determine file icon based on extension
    let icon = 'bi-file';
    if (filename.toLowerCase().includes('.fastq') || filename.toLowerCase().includes('.fq')) {
        icon = 'bi-file-earmark-text';
    } else if (filename.toLowerCase().includes('.txt') || filename.toLowerCase().includes('.csv')) {
        icon = 'bi-file-earmark-spreadsheet';
    }

    fileDiv.innerHTML = `
        <span class="file-content">
            <i class="${icon}"></i> ${filename}
        </span>
        <span class="file-actions">
            <i class="bi bi-arrow-left move-to-unassigned-btn" onclick="moveFileToUnassigned('${filename}')" title="Move to unassigned"></i>
        </span>
    `;

    setupDragEvents(fileDiv);
    return fileDiv;
}

function setupDragEvents(element) {
    element.addEventListener('dragstart', function(e) {
        // Don't start dragging if clicking on action buttons
        if (e.target.classList.contains('move-to-unassigned-btn')) {
            e.preventDefault();
            return;
        }
        e.dataTransfer.setData('text/plain', this.dataset.filename);
        this.classList.add('dragging');
    });

    element.addEventListener('dragend', function(e) {
        this.classList.remove('dragging');
    });

    // Add double-click to move to unassigned (only for assigned files)
    if (!element.classList.contains('unassigned-file-item')) {
        element.addEventListener('dblclick', function(e) {
            // Don't trigger if clicking on action buttons
            if (e.target.classList.contains('move-to-unassigned-btn')) {
                return;
            }

            const filename = this.dataset.filename;
            moveFileToUnassigned(filename);
        });
    }
}

function setupDropZone(element) {
    element.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('drag-over');
    });

    element.addEventListener('dragleave', function(e) {
        if (!this.contains(e.relatedTarget)) {
            this.classList.remove('drag-over');
        }
    });

    element.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');

        const filename = e.dataTransfer.getData('text/plain');
        const sampleName = this.dataset.sample;
        const fileType = this.dataset.type;

        moveFileToSample(filename, sampleName, fileType);
    });
}

function setupUnassignedDropZone() {
    const unassignedContainer = document.getElementById('unassigned-files-container');

    unassignedContainer.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('drag-over');
    });

    unassignedContainer.addEventListener('dragleave', function(e) {
        if (!this.contains(e.relatedTarget)) {
            this.classList.remove('drag-over');
        }
    });

    unassignedContainer.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');

        const filename = e.dataTransfer.getData('text/plain');
        moveFileToUnassigned(filename);
    });
}

function moveFileToSample(filename, sampleName, fileType) {
    // Remove file from current location (including unassigned)
    removeFileFromAllLocations(filename);

    // Add to new location
    if (!samplesData[sampleName]) {
        samplesData[sampleName] = { raw: [], processed: [] };
    }

    // Initialize arrays if they don't exist
    if (!samplesData[sampleName][fileType]) {
        samplesData[sampleName][fileType] = [];
    }

    samplesData[sampleName][fileType].push(filename);
    renderSamples();
    renderUnassignedFiles();
}

function moveFileToUnassigned(filename) {
    // Remove file from current location
    removeFileFromAllLocations(filename);

    // Add to unassigned
    if (!unassignedFiles.includes(filename)) {
        unassignedFiles.push(filename);
    }

    renderSamples();
    renderUnassignedFiles();
}

// Remove the removeFile function entirely since we no longer delete files

function removeFileFromAllLocations(filename) {
    // Remove from all samples
    Object.keys(samplesData).forEach(sampleName => {
        if (samplesData[sampleName].raw) {
            samplesData[sampleName].raw = samplesData[sampleName].raw.filter(f => f !== filename);
        }
        if (samplesData[sampleName].processed) {
            samplesData[sampleName].processed = samplesData[sampleName].processed.filter(f => f !== filename);
        }

        // Don't remove empty samples - keep them for user convenience
    });

    // Remove from unassigned files
    unassignedFiles = unassignedFiles.filter(f => f !== filename);
}

function addNewSample() {
    const sampleName = prompt('Enter new sample name:');
    if (sampleName && sampleName.trim()) {
        const trimmedName = sampleName.trim();
        if (!samplesData[trimmedName]) {
            samplesData[trimmedName] = { raw: [], processed: [] };
            renderSamples();
        } else {
            alert('Sample already exists!');
        }
    }
}

function removeSample(sampleName) {
    // if (confirm(`Remove sample "${sampleName}"? All files will be moved to unassigned.`)) {
    // Move all files to unassigned before removing sample
    if (samplesData[sampleName].raw) {
        unassignedFiles.push(...samplesData[sampleName].raw);
    }
    if (samplesData[sampleName].processed) {
        unassignedFiles.push(...samplesData[sampleName].processed);
    }

    // Remove duplicates from unassigned files
    unassignedFiles = [...new Set(unassignedFiles)];

    delete samplesData[sampleName];
    renderSamples();
    renderUnassignedFiles();

}

function saveConfiguration() {
    // Create a deep copy of samplesData with full paths
    const samplesDataWithFullPaths = {};

    Object.keys(samplesData).forEach(sampleName => {
        samplesDataWithFullPaths[sampleName] = {
            raw: (samplesData[sampleName].raw || []).map(filename => `${initialData.folder_path}/${filename}`),
            processed: (samplesData[sampleName].processed || []).map(filename => `${initialData.folder_path}/${filename}`)
        };
    });

    showSpinner('Creating your upload session. Please be patient as it takes a bit...')

    fetch('/sessions/create/folder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(samplesDataWithFullPaths)
    }).then((response) => {
        hideSpinner();
        if (response.ok) {
            // Redirect manually after successful response
            window.location.href = '/dashboard';  // or use the full URL
        }
    })
    .catch(error => {
        hideSpinner();
        alert('Error creating an upload session ' + error);
    });
}

// function resetToDefaults() {
//     if (confirm('Reset to initial auto-grouping?')) {
//         samplesData = JSON.parse(JSON.stringify(initialData.samples));
//         extractUnassignedFiles();
//         renderSamples();
//         renderUnassignedFiles();
//     }
// }

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeData();
    setupUnassignedDropZone();
});