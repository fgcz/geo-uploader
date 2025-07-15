let hot_sample;
let organism_column;
let molecule_column;

/**
 * Initialize samples metadata table
 * @param {Array} samplesData - The samples data array
 * @param {boolean} canEdit - Whether the user can edit the data
 * @param {Object} dropdowns - Dropdown options for various fields
 */
function initializeSamplesTable(samplesData, canEdit, dropdowns){
    // todo hard coded
    const readOnlyColumnsMap = {
        '*library name': true,
        '*single or paired-end': true,
        // '*processed data file': true, (old template)
        'processed data file': true,
        '*raw file': true,
        'raw file': true,
        // Add other column names as needed
    };

    let samples_colWidths = Array(samplesData[0].length).fill(100);
    samples_colWidths[10] = 120

    const sample_container = document.getElementById('sample_handsontable')
    const additions_content = '\n\nAdd characteristics such as:  \ntissue\ncell line\ncell type\nstrain\ngenotype\ngenetic modification\ndevelopmental stage\nsex\ntreatment\ntime\ndisease state\ntumor stage\nChIP antibody\netc.\n\n' +
        '* genotype, cell line, cell type, strain, developmental stage must have plain ascii values'

    const samples_comments = [
        { row: 0, col: 0, comment: { value: 'In each row, provide a unique name for the library.  \n' +
                    'Do not include sensitive information. \n' +
                    'Use only plain ASCII text for the names.\n\n' +
                    'Each row represents a GEO Sample record (GSMxxxxxxx).\n\n' +
                    'The unique  name will be displayed in the "Description" field of the GSM. \n',
                readOnly: true, style: {width: 200, height: 120}}},
        { row: 0, col: 1, comment: { value: 'Unique title that describes the Sample. \n' +
                    '\n' +
                    'We suggest the convention: \n' +
                    '[biomaterial] [condition(s)] [replicate number]\n\n' +
                    'Use biol/tech rep numbers (when \n' +
                    'applicable) to unique the titles. \n' +
                    'For example:\n' +
                    'Muscle, exercised, 60min, biol rep1\n' +
                    'Muscle, exercised, 60min, biol rep2\n'
                , readOnly: true, style: { width: 200, height: 120} } },
        { row: 0, col: 2, comment: { value: 'A Sequence Read Archive (SRA)-specific field that describes the sequencing technique for each library. \n\n' +
                    'Enter one of the strategies from the drop-down list \n' +
                    '(click arrowhead on cell immediately  below).\n\n' +
                    'Click on arrowhead.  To view complete list, use scrollbar or up/down arrows on keyboard (increasing window size or zoom level may improve scroll bar function).\n', readOnly: true, style: {width: 200, height: 120} }},
        { row: 0, col: 3, comment: { value:
                    'Provide a valid scientific name at species level (or lower rank, such as subspecies).  \n\n' +
                    'EXAMPLE:  Mus musculus\n\n' +
                    'Homo sapiens\n' +
                    'Arabidopsis thaliana\n' +
                    'Escherichia coli K-12\n' +
                    'Caenorhabditis elegans\n\n' +

                    'The name must return a SINGLE entry in the Taxonomy database:\n' +
                    'https://www.ncbi.nlm.nih.gov/taxonomy/\n\n' +
                    'Add another "organism" column(s), if needed.\n\n'
                , readOnly: true, style: { width: 200, height: 120},} },
        { row: 0, col: 4, comment: { value: `List the tissue from which this sample was derived. For example:\nLiver\nBreast cancer\nColorectal cancer\nLiver tumor\nWhole organism\nMycelium` + additions_content, readOnly: true, style: { width: 200, height: 120, backgroundColor: 'yellow' },} },
        { row: 0, col: 5, comment: { value: 'List the cell line used, if applicable. For example:\nHeLa\nHEK293\nA549' + additions_content, readOnly: true, style: { width: 200, height: 120, backgroundColor: 'yellow' },} },
        { row: 0, col: 6, comment: { value: 'List the cell type. Examples include:\n' +
                    'PBMCs\n' +
                    'Adipocytes\n' +
                    'neural progenitor cells (NPCs)' + additions_content, readOnly: true, style: { width: 200, height: 120},} },
        { row: 0, col: 7, comment: { value: 'List the genotype (if applicable). If not0 applicable change "genotype" to something else. For example: strain, sex, cultivar, breed, age, developmental stage, etc' + additions_content, readOnly: true, style: { width: 200, height: 120, backgroundColor: 'yellow' },} },
        { row: 0, col: 8, comment: { value: 'List the treatment(s) applied to the sample. If no treatments were applied enter \'none\'. \n' +
                    '**NOTE: You can insert additional columns before \'molecule\' and add more sample descriptions - clinical data, for example**' + additions_content, readOnly: true, style: { width: 200, height: 120, backgroundColor: 'yellow' },} },
        { row: 0, col: 9, comment: { value: 'Scan date, or a similar proxy, from the raw files.', readOnly: true, style: { width: 200, height: 60 }}},
        { row: 0, col: 10, comment: { value: 'Type of molecule that was extracted from the biological material.\n\n' +
                    'Include one of the molecules from the drop-down list\n' +
                    '(click arrowhead on cell immediately below).\n', readOnly: true, style: { width: 200, height: 120 }}},
        { row: 0, col: 12, comment: { value: 'Instrument model used to sequence the library.\n\n' +
                    'Include one of the models from the drop-down list \n' +
                    '(click arrowhead on cell immediately  below).\n', readOnly: true, style: { width: 200, height: 120 }}},
        { row: 0, col: 13, comment: { value: 'Additional information not provided in the other fields, or broad descriptions that cannot be easily dissected into other fields. [optional]  \n\n' +
                    'If you submit a single processed data file for all Samples (for example, FPKMs_allSamples.txt), list the file\'s column names here. But do NOT list here, if the file\'s column names match the "library name" column'
                , readOnly: true, style: { width: 200, height: 120},} },
    ]

    hot_sample = new Handsontable(sample_container, {
        licenseKey: "non-commercial-and-evaluation",

        data: samplesData,
        height: samplesData.length * 41 + 120,
        colWidths: samples_colWidths,
        colHeaders: samplesData[0],
        // colHeaders: true,
        // colHeaders: false,
        allowInsertColumn: true,
        allowRemoveColumn: true,
        autoWrapRow: true,
        autoWrapCol: true,
        manualColumnResize: true, // Enable column resizing

        allowInsertRow: false,
        allowRemoveRow: false,

        comments: true,
        cell: samples_comments,

        // Add tooltip configuration
        customBorders: true,

        // Add cell tooltip on hover
        afterOnCellMouseOver: function(event, coords, TD) {
            if (coords.row >= 0 && coords.col >= 0) { // Check if hovering over a valid cell
                const cellValue = this.getDataAtCell(coords.row, coords.col);
                if (cellValue) {
                    TD.title = cellValue; // Set the HTML title attribute for native tooltip
                }
            }
        },

        cells(row, column) {
            let cellProperties = {};
            const headerValue = hot_sample.getColHeader(column);

            // Set read-only properties based on column names and permissions
            if (row === 0) {
                if (!canEdit) {
                    cellProperties.readOnly = true;
                    cellProperties.className = 'bg-info text-dark';
                } else {
                    cellProperties.readOnly = false; // Allow editing for this row
                    cellProperties.className = 'bg-info text-white';
                }
                if( column > organism_column && column < molecule_column ){
                    cellProperties.className = 'bg-success text-dark';
                }
            } else if (!canEdit || readOnlyColumnsMap[headerValue]) {
                cellProperties.readOnly = true;
                cellProperties.className = 'text-white bg-secondary';
            }

            if (dropdowns[headerValue] && row != 0) {
                cellProperties.type = 'dropdown';
                cellProperties.source = dropdowns[headerValue]; // Set the source based on the header
            }

            return cellProperties;
        },

        // contextMenu: true,
        // beforeChange
        // afterBeginEdition
        // afterChange
        contextMenu: {
            items: {
                "row_above": {},
                "row_below": {},
                "col_left": {
                    name: "Insert Column Left",
                    disabled: function() {
                        var selection = hot_sample.getSelected();
                        if (selection && selection.length > 0) {
                            var getCol = selection[0][1]; // Get the selected column index
                            if(getCol > organism_column + 1 && getCol <= molecule_column) return false;
                        }
                        return true; // Disable if no selection
                    },
                    callback: function () {
                        var selection = hot_sample.getSelected();
                        var getCol = selection[0][1] // startrow, startcol, endrow, endcol

                        insertColumn(getCol-1)
                    }
                },
                "col_right": {
                    name: "Insert Column Right",
                    disabled: function() {
                        var selection = hot_sample.getSelected();
                        if (selection && selection.length > 0) {
                            var getCol = selection[0][1]; // Get the selected column index
                            if(getCol > organism_column && getCol < molecule_column) return false;
                        }
                        return true;
                    },
                    callback: function () {
                        var selection = hot_sample.getSelected();
                        var getCol = selection[0][1] // startrow, startcol, endrow, endcol

                        insertColumn(getCol);
                    }
                },
                "remove_column": {
                    name: "Remove Column",
                    disabled: function() {
                        var selection = hot_sample.getSelected();
                        if (selection && selection.length == 1) {
                            if(selection[0][1] != selection[0][3]) return true;

                            var getCol = selection[0][1]; // Get the selected column index
                            if(getCol > organism_column + 1 && getCol < molecule_column) return false;
                        }
                        return true;
                    },
                    callback: function () {
                        var selection = hot_sample.getSelected();
                        removeColumns(selection[0][1])
                    }
                },
                '---------': Handsontable.plugins.ContextMenu.SEPARATOR,
                'cut': {},
                'copy': {},
                'undo': {},
                'redo': {},
            }
        }
    });

    organism_column = samplesData[0].indexOf("*organism"); // Execute only once if not defined
    molecule_column = samplesData[0].indexOf("*molecule"); // Execute only once if not defined
}

/**
 * Remove column from samples table
 * @param {number} colIndex - Index of column to remove
 */

function removeColumns(colIndex){
    samplesData.forEach((row) => row.splice(colIndex, 1))

    // Adjust or remove comments after deleting the column
    for (let i = samples_comments.length - 1; i >= 0; i--) {
        if (samples_comments[i].col === colIndex) {
            samples_comments.splice(i, 1); // Remove comment at the deleted column
        } else if (samples_comments[i].col > colIndex) {
            samples_comments[i].col -= 1; // Shift column index for comments after the deleted column
        }
    }

    molecule_column -= 1;
    hot_sample.loadData(samplesData)
    hot_sample.updateSettings({ cell: samples_comments }); // Reapply cell comments
    hot_sample.render(); // Re-render the table to apply changes
}


/**
 * Insert column in samples table
 * @param {number} colIndex - Index where to insert the column
 */
function insertColumn(colIndex) {
    samplesData.forEach((row, index) => {
        if (index === 0) {
            row.splice(colIndex + 1, 0, "Complete..."); // Insert "Complete title" at the specified column index for the first row
        } else {
            row.splice(colIndex + 1, 0, ""); // Insert an empty string for all subsequent rows
        }
    });

    samples_comments.forEach(comment => {
        if (comment.col > colIndex) {
            comment.col += 1; // Shift column index for comments
        }
    });

    molecule_column += 1;
    hot_sample.loadData(samplesData)
    hot_sample.updateSettings({ cell: samples_comments }); // Reapply cell comments
    hot_sample.render(); // Re-render the table to apply changes
};


