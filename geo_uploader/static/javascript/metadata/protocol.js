let hot_protocol;

/**
 * Initialize protocol metadata table
 * @param {Array} protocolData - The protocol data array
 * @param {boolean} canEdit - Whether the user can edit the data
 */
function initializeProtocolTable(protocolData, canEdit){
    const protocol_container = document.getElementById('protocol_handsontable')
    const protocol_colWidths = Array(protocolData[0].length).fill(300);
    const protocol_rowHeights = Array(protocolData.length).fill(40);


    const data_step_comment = {
        value: 'Provide details of how processed data files were generated. \n' +
            '\n' +
            'Steps may include:\n' +
            'Base-calling software, version, parameters;\n' +
            'Data filtering steps;\n' +
            'Read alignment software, version, parameters;\n' +
            'Additional processing software (e.g., peak-calling, abundance measurement), version, parameters;\n' +
            'etc.\n',
        readOnly: true, style: {width: 200, height: 100}
    }
    const processed_file_comment = {
        value: 'For each processed data file type, provide a description of the format and content.',
        readOnly: true, style: {width: 200, height: 80}
    }
    const genome_build_comment = {
        value: 'NCBI or UCSC genome build number (e.g., GRCh38, hg38, GRCm39, mm39, etc.), or reference sequence used for read alignment. \n',
        readOnly: true, style: {width: 200, height: 120}
    }
    const protocol_comments = [
        {
            row: 0, col: 0, comment: {
                value: '[Optional]  Describe the conditions used to grow or maintain organisms or cells prior to extract preparation.',
                readOnly: true, style: {width: 200, height: 90}
            }
        },
        {
            row: 1, col: 0, comment: {
                value: '[Optional] Describe the treatments applied to the biological material prior to extract preparation.',
                readOnly: true, style: {width: 200, height: 80}
            }
        },
        {
            row: 2, col: 0, comment: {
                value: 'Describe the protocols used to extract and prepare the material to be sequenced. ',
                readOnly: true, style: {width: 200, height: 80}
            }
        },
        {
            row: 3, col: 0, comment: {
                value: 'Describe the library construction protocol.',
                readOnly: true, style: {width: 200, height: 60}
            }
        },
        {
            row: 4, col: 0, comment: {
                value: 'A Sequence Read Archive-specific field that describes the sequencing technique for each library. \n' +
                    '\n' +
                    'Please enter one of the following terms:\n' +
                    '\n' +
                    'RNA-Seq\n' +
                    'scRNA-seq\n' +
                    'miRNA-Seq\n' +
                    'ncRNA-Seq\n' +
                    'ChIP-Seq\n' +
                    'ATAC-seq\n' +
                    'Bisulfite-Seq\n' +
                    'Bisulfite-Seq (reduced representation)\n' +
                    'Spatial Transcriptomics\n' +
                    'CITE-seq\n' +
                    'CUT&Run\n' +
                    'CUT&Tag\n' +
                    'MNase-Seq\n' +
                    'Hi-C\n' +
                    'MBD-Seq\n' +
                    'MRE-Seq\n' +
                    'MeDIP-Seq\n' +
                    'DNase-Hypersensitivity\n' +
                    'Tn-Seq\n' +
                    'FAIRE-seq\n' +
                    'SELEX\n' +
                    'RIP-Seq\n' +
                    'ChIA-PET\n' +
                    '\n' +
                    'BRU-Seq\n' +
                    'CRISPR Screen\n' +
                    'Capture-C\n' +
                    'ChEC-seq\n' +
                    'ChIRP-seq\n' +
                    'DamID-Seq\n' +
                    'EM-seq\n' +
                    'GRO-Seq\n' +
                    'HiChIP\n' +
                    'MeRIP-Seq\n' +
                    'PRO-Seq\n' +
                    'RNA methylation\n' +
                    'Ribo-Seq\n' +
                    'TCR-Seq\n' +
                    'BCR-Seq\n' +
                    'iCLIP\n' +
                    'smallRNA-Seq\n' +
                    'snRNA-Seq\n' +
                    'ssRNA-Seq\n' +
                    'RNA-Seq (CAGE)\n' +
                    'RNA-Seq (RACE)\n' +
                    '16S rRNA-seq\n' +
                    '4C-Seq\n' +
                    '\n' +
                    'OTHER: specify',
                readOnly: true, style: {width: 220, height: 200}
            }
        },
    ]

    protocolData.forEach((row, rowIndex) => {
        row.forEach((cellValue, colIndex) => {
            if (cellValue === "*data processing step" || cellValue === "data processing step") {
                protocol_comments.push({row: rowIndex, col: colIndex, comment: data_step_comment});
            } else if (cellValue === "*processed data files format and content" || cellValue === "processed data files format and content") {
                protocol_comments.push({row: rowIndex, col: colIndex, comment: processed_file_comment});
            } else if (cellValue === "*genome build/assembly") {
                protocol_comments.push({row: rowIndex, col: colIndex, comment: genome_build_comment});
            }

        });
    });

    hot_protocol = new Handsontable(protocol_container, {
        licenseKey: "non-commercial-and-evaluation",
        data: protocolData,
        width: 'auto',
        height: protocolData.length * 41,
        fontsize: 16,
        manualRowResize: true,
        colWidths: protocol_colWidths,
        rowHeights: protocol_rowHeights,
        autoRowSize: true,

        allowInsertColumn: false,
        allowRemoveColumn: false,
        allowInsertRow: false,
        allowRemoveRow: false,

        colHeaders: true,
        contextMenu: true,
        autoWrapRow: true,
        autoWrapCol: true,
        comments: true,
        cell: protocol_comments,
        cells(row, column) {

            if (column === 0) {
                return {
                    className: 'bg-info text-white',
                    // readOnly: true,
                };
            } else {
                if (canEdit) {
                    return {
                        readOnly: false
                    };
                } else {
                    return {
                        readOnly: true,
                        className: 'bg-secondary text-white',
                    };
                }
            }
        },

    });
}

/**
 * Resize protocol form (add/remove steps or formats)
 * @param {string} actionValue - The action to perform
 */
function resizeProtocolForm(actionValue) {
    showSpinner('Resizing metadata...');

    // Call saveData first
    saveMetadata(false)
        .then(() => {
            // If save is successful, proceed with resizing
            // Prepare the data to send, including the action
            const metadataResizeProtocolFetchForm = new FormData();
            const csrfTokenResizeProtocol = document.querySelector('#metadata-study-resize-protocol input[name="csrf_token"]').value;

            metadataResizeProtocolFetchForm.append('action', actionValue);
            metadataResizeProtocolFetchForm.append('csrf_token', csrfTokenResizeProtocol);

            // Get the resize URL from the page context
            const resizeUrl = document.querySelector('[data-resize-protocol-url]')?.dataset.resizeProtocolUrl ||
                             window.metadataResizeProtocolUrl ||
                             `/metadata/resize_protocol/${window.sessionId}`;

            // Make the fetch request for resizing
            return fetch(resizeUrl, {
                method: 'POST',
                body: metadataResizeProtocolFetchForm,
            });
        })
        .then(response => response.json())  // Convert the response to JSON
        .then(data => {
            // Handle the successful response for resizing

            // Check if the response indicates success, then refresh the page
            if (data.status === 'success') {
                window.location.reload();  // Force page refresh
            } else {
                // Handle any errors or messages returned
                hideSpinner();  // Hide spinner in case of error
                console.error('Error:', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            hideSpinner();  // Hide spinner in case of error
        });
}
