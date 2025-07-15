let hot_study;

/**
 * Initialize study metadata table
 * @param {Array} studyData - The study data array
 * @param {boolean} canEdit - Whether the user can edit the data
 */
function initializeStudyTable(studyData, canEdit){
    // Comments Data
    const contributor_comment = {
        value: 'Correctly formatted names\n' +
            '(Firstname, Initial optional , Surname):\n' +
            '    Jane, Doe\n' +
            '    Yixin, Wang\n' +
            '    So-Young, Kim\n' +
            '    Adeola, Sa\'id\n' +
            '    M, Garçon Dumonde\n' +
            '    Mo, G, van der Waal\n' +
            '    R, J, Sánchez-Aquino\n' +
            '    Charles, E, Determan Jr\n' +
            '    John Paul, Getty III \n\n' +
            'Each contributor on a separate line. \nAdd as many contributor lines as needed.',
        readOnly: true,
        style: {width: 200, height: 120}
    };
    const supplementary_comment = {
        value: 'If you submit a processed data file corresponding to *multiple* Samples, include the processed file name here.  \n' +
            '\n' +
            'EXAMPLE:  FPKMs_all_Samples.txt\n' +
            '\n' +
            'The processed file should have sample column names that are unique and can be matched to unique descriptors in SAMPLES.  For example:\n' +
            '\n' +
            'Sample column names can match "library name" column.  \n' +
            '  -OR-\n' +
            'Sample column names can be listed in "description" column. \n' +
            '\n' +
            'An exception would be single-cell submissions.\n',
        readOnly: true,
        style: {width: 200, height: 150}
    }
    const study_comments = [
        {
            row: 0,
            col: 0,
            comment: {
                value: 'Provide a title for this Study. Generally, we recommend the title of an associated manuscript/publication. \n\n' +
                    'The title can be updated later, as needed. \n\n' +
                    'Unique title (maximum of 255 characters) that describes the overall study.',
                readOnly: true,
                style: {width: 200, height: 150}
            }
        },
        {
            row: 1,
            col: 0,
            comment: {
                value: 'Thorough description of the goals and objectives of this study.  A working abstract from the associated manuscript may be suitable.  Include as much text as necessary.',
                readOnly: true,
                style: {width: 200, height: 120}
            }
        },
        {
            row: 2,
            col: 0,
            comment: {
                value: 'Description of the type of SAMPLES included in the submission. \n\n' +
                    'For example:  The experimental conditions and variables under investigation, if replicates are included, are there control and/or reference Samples, etc.\n\n' +
                    'Do not include PROTOCOLS',
                readOnly: true,
                style: {width: 200, height: 150}
            }
        }
    ];

    studyData.forEach((row, rowIndex) => {
        row.forEach((cellValue, colIndex) => {
            if (cellValue === "contributor") {
                // If the cell value is "Contributor", add a comment for that cell
                study_comments.push({row: rowIndex, col: colIndex, comment: contributor_comment});
            }
            if (cellValue === "supplementary file") {
                // If the cell value is "Contributor", add a comment for that cell
                study_comments.push({row: rowIndex, col: colIndex, comment: supplementary_comment});
            }
        });
    });

    // Handsontable Setup
    // Handsontable Setup
    const study_container = document.getElementById('study_handsontable');
    const study_colWidths = Array(studyData[0].length).fill(300);

    hot_study = new Handsontable(study_container, {
        licenseKey: "non-commercial-and-evaluation",
        data: studyData,
        height: 350,
        colWidths: study_colWidths,
        colHeaders: true,
        contextMenu: true,
        autoWrapRow: true,
        autoWrapCol: true,
        allowInsertColumn: false,
        allowRemoveColumn: false,
        allowInsertRow: false,
        allowRemoveRow: false,
        comments: true,
        cell: study_comments,
        cells(row, column) {
            if (!canEdit) {
                return {
                    readOnly: true,
                    className: (column === 0) ? 'bg-info text-dark' : 'text-white bg-secondary'
                };
            } else if (column === 0) {
                return {
                    readOnly: true,
                    className: 'bg-info text-white'
                };
            }
        },
    });

}

/**
 * Resize study form (add/remove contributors or supplementary files)
 * @param {string} actionValue - The action to perform
 */
function resizeStudyForm(actionValue) {
    showSpinner('Resizing metadata...');

    // Call saveData first
    saveMetadata(false)
        .then(() => {
            // If save is successful, proceed with resizing
            // Prepare the data to send, including the action
            const metadataResizeStudyFetchForm = new FormData();
            const csrfTokenResizeStudy = document.querySelector('#metadata-study-resize-form input[name="csrf_token"]').value;
            metadataResizeStudyFetchForm.append('action', actionValue);
            metadataResizeStudyFetchForm.append('csrf_token', csrfTokenResizeStudy);

            // Get the resize URL from the page context
            const resizeUrl = document.querySelector('[data-resize-study-url]')?.dataset.resizeStudyUrl ||
                             window.metadataResizeStudyUrl ||
                             `/metadata/resize_study/${window.sessionId}`;
            // Make the fetch request for resizing
            return fetch(resizeUrl, {
                method: 'POST',
                body: metadataResizeStudyFetchForm,
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
