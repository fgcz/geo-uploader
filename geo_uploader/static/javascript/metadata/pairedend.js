let hot_pairedend;

/**
 * Initialize paired-end metadata table
 * @param {Array} pairedendData - The paired-end data array
 */
function initializePairedendTable(pairedendData){
    var container = document.getElementById('pairedend_handsontable')
    colWidths = Array(pairedendData[0].length).fill(300);

    hot_pairedend = new Handsontable(container, {
        licenseKey: "non-commercial-and-evaluation",
        data: pairedendData,
        width: 'auto',
        // height: data.length * 46,
        colWidths: colWidths,
        colHeaders: true,
        contextMenu: true,
        autoWrapRow: true,
        autoWrapCol: true,
        allowInsertColumn: false,
        allowRemoveColumn: false,
        allowInsertRow: false,
        allowRemoveRow: false,
        cells(row, column) {
            if (row == 0) {
                return {
                    readOnly: true,
                    className: 'bg-info text-white',
                }
            } else {
                return {
                    className: 'text-white bg-secondary',
                    readOnly: true,
                }
            }
        },

    });
}