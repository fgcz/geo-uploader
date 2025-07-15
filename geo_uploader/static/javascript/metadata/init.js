/**
 * Initialize all metadata tables and event listeners
 * This function should be called when the page loads
 */
function initializeMetadata(){

    const saveBtns = document.querySelectorAll('.save_metadata_btn');
    saveBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            saveMetadata()
        });
    });

    // Initialize study table if data exists
    if (typeof study_data !== 'undefined' && study_data){
        initializeStudyTable(study_data, can_edit);
    }

    // Initialize samples table if data exists
    if (typeof samples_data !== 'undefined' && samples_data) {
        const dropdowns = {
            '*molecule': dropdown_molecule || [],
            '*instrument model': dropdown_instrument || [],
            '*library strategy': dropdown_library || []
        };
        initializeSamplesTable(samples_data, can_edit, dropdowns);
    }

    // Initialize protocol table if data exists
    if (typeof protocol_data !== 'undefined' && protocol_data) {
        initializeProtocolTable(protocol_data, can_edit);
    }

    // Initialize paired-end table if data exists
    if (typeof pairedend_data !== 'undefined' && pairedend_data && pairedend_data.length > 0) {
        initializePairedendTable(pairedend_data);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeMetadata();
});