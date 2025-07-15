// Global timeout variables for status messages
let saveTimeoutStudy, fadeTimeoutStudy;
let saveTimeoutSamples, fadeTimeoutSamples;
let saveTimeoutProtocol, fadeTimeoutProtocol;

// Status message elements for each tab
const statusMessageElements = {
    study: document.querySelector('.status-message-study'),
    samples: document.querySelector('.status-message-samples'),
    protocol: document.querySelector('.status-message-protocol')
};

/**
 * Set status message for a specific tab
 * @param {HTMLElement} statusElement - The status message container
 * @param {string} type - Bootstrap alert type (success, danger, warning, info)
 * @param {string} message - The message to display
 */
function setStatusMessage(statusElement, type, message) {
    statusElement.innerHTML = `<div class="alert alert-${type} fade show" role="alert">${message}</div>`;
}

/**
 * Start fade out timer for status messages
 * @param {HTMLElement} statusElement - The status message container
 * @param {number} saveTimeoutVar - Current save timeout variable
 * @param {number} fadeTimeoutVar - Current fade timeout variable
 * @returns {Object} Updated timeout variables
 */
function startFadeOut(statusElement, saveTimeoutVar, fadeTimeoutVar) {
    // Clear previous timeouts
    if (saveTimeoutVar) clearTimeout(saveTimeoutVar);
    if (fadeTimeoutVar) clearTimeout(fadeTimeoutVar);

    // Start the timeout to fade out the message
    saveTimeoutVar = setTimeout(() => {
        const alert = statusElement.querySelector('.alert');
        if (alert) {
            alert.classList.remove('show');

            // Remove the alert from the DOM after fading out
            fadeTimeoutVar = setTimeout(() => {
                statusElement.innerHTML = '';
            }, 500);
        }
    }, 4000);

    // Return updated timeouts
    return {saveTimeoutVar, fadeTimeoutVar};
}

/**
 * Main save metadata function
 * Validates data and saves all tabs
 * @param {boolean} hide - Whether to hide spinner after completion
 * @returns {Promise} Promise that resolves when save is complete
 */
function saveMetadata(hide=true) {
    return new Promise(async (resolve, reject) => {
        // Perform validation
        const validationResults = await validateData();
        if (!validationResults.valid) {
            validationResults.errors.forEach(error => {
                if (error.type === 'contributor') {
                    setStatusMessage(statusMessageElements.study, 'danger', 'Contributor validator failed: ' + error.message);
                    setStatusMessage(statusMessageElements.samples, 'danger', 'Careful! Contributors validator failed at the study tab!');
                    setStatusMessage(statusMessageElements.protocol, 'danger', 'Careful contributors validator failed at the study tab!');
                }
                else if (error.type === 'title') {
                    setStatusMessage(statusMessageElements.study, 'danger', 'Title validator failed: ' + error.message);
                    setStatusMessage(statusMessageElements.samples, 'danger', 'Careful! Title validator failed at the study tab!');
                    setStatusMessage(statusMessageElements.protocol, 'danger', 'Careful! Title validator failed at the study tab!');
                }
                else if (error.type === 'summary') {
                    setStatusMessage(statusMessageElements.study, 'danger', 'Summary validator failed: ' + error.message);
                    setStatusMessage(statusMessageElements.samples, 'danger', 'Careful! Summary validator failed at the study tab!');
                    setStatusMessage(statusMessageElements.protocol, 'danger', 'Careful! Summary validator failed at the study tab!');
                }
                else if (error.type === 'design') {
                    setStatusMessage(statusMessageElements.study, 'danger', 'Design validator failed: ' + error.message);
                    setStatusMessage(statusMessageElements.samples, 'danger', 'Careful! Design validator failed at the study tab!');
                    setStatusMessage(statusMessageElements.protocol, 'danger', 'Careful! Design validator failed at the study tab!');
                }
                else if (error.type === 'organism'){
                    setStatusMessage(statusMessageElements.study, 'danger', 'Careful! Organism validator failed at the samples tab!');
                    setStatusMessage(statusMessageElements.samples, 'danger', 'Organism validator failed: ' + error.message);
                    setStatusMessage(statusMessageElements.protocol, 'danger', 'Careful! Organism validator failed at the samples tab!');
                }
            });

            ({
                saveTimeoutVar: saveTimeoutStudy,
                fadeTimeoutVar: fadeTimeoutStudy
            } = startFadeOut(statusMessageElements.study, saveTimeoutStudy, fadeTimeoutStudy));
            ({
                saveTimeoutVar: saveTimeoutSamples,
                fadeTimeoutVar: saveTimeoutSamples
            } = startFadeOut(statusMessageElements.samples, saveTimeoutSamples, fadeTimeoutSamples));
            ({
                saveTimeoutVar: saveTimeoutProtocol,
                fadeTimeoutVar: fadeTimeoutProtocol
            } = startFadeOut(statusMessageElements.protocol, saveTimeoutProtocol, fadeTimeoutProtocol));

            reject('Validation failed');
            return;
        }
        showSpinner('Saving data...');

        const csrfTokenSaveMetadata = document.querySelector('#metadataSave-csrf-form input[name="csrf_token"]').value;
        // create a form because csrf needs to be in the fetch body
        const metadataSaveFetchForm = new FormData();
        metadataSaveFetchForm.append('csrf_token', csrfTokenSaveMetadata);
        metadataSaveFetchForm.append('study_data', JSON.stringify(hot_study.getData()));
        metadataSaveFetchForm.append('samples_data', JSON.stringify(hot_sample.getData()));
        metadataSaveFetchForm.append('protocol_data', JSON.stringify(hot_protocol.getData()));

        // Get the save URL from the page context
        const saveUrl = document.querySelector('[data-save-url]')?.dataset.saveUrl ||
            window.metadataSaveUrl ||
            `/metadata/save/${window.sessionId}`;

        // Perform fetch request to save data
        fetch(saveUrl, {
            method: 'POST',
            body: metadataSaveFetchForm,
        }).then(response => {
            if (!response.ok) {
                // Show error message
                setStatusMessage(statusMessageElements.study, 'danger', 'Could not save');
                setStatusMessage(statusMessageElements.samples, 'danger', 'Could not save');
                setStatusMessage(statusMessageElements.protocol, 'danger', 'Could not save');

                // Handle timeouts for fading out messages
                ({
                    saveTimeoutVar: saveTimeoutStudy,
                    fadeTimeoutVar: fadeTimeoutStudy
                } = startFadeOut(statusMessageElements.study, saveTimeoutStudy, fadeTimeoutStudy));
                ({
                    saveTimeoutVar: saveTimeoutSamples,
                    fadeTimeoutVar: fadeTimeoutSamples
                } = startFadeOut(statusMessageElements.samples, saveTimeoutSamples, fadeTimeoutSamples));
                ({
                    saveTimeoutVar: saveTimeoutProtocol,
                    fadeTimeoutVar: fadeTimeoutProtocol
                } = startFadeOut(statusMessageElements.protocol, saveTimeoutProtocol, fadeTimeoutProtocol));
                hideSpinner()
            } else {
                // Show success message
                setStatusMessage(statusMessageElements.study, 'success', 'Progress saved!');
                setStatusMessage(statusMessageElements.samples, 'success', 'Progress saved!');
                setStatusMessage(statusMessageElements.protocol, 'success', 'Progress saved!');

                // Handle timeouts for fading out messages
                ({
                    saveTimeoutVar: saveTimeoutStudy,
                    fadeTimeoutVar: fadeTimeoutStudy
                } = startFadeOut(statusMessageElements.study, saveTimeoutStudy, fadeTimeoutStudy));
                ({
                    saveTimeoutVar: saveTimeoutSamples,
                    fadeTimeoutVar: fadeTimeoutSamples
                } = startFadeOut(statusMessageElements.samples, saveTimeoutSamples, fadeTimeoutSamples));
                ({
                    saveTimeoutVar: saveTimeoutProtocol,
                    fadeTimeoutVar: fadeTimeoutProtocol
                } = startFadeOut(statusMessageElements.protocol, saveTimeoutProtocol, fadeTimeoutProtocol));

                if(hide) hideSpinner();
                resolve('Save successful');
            }
        }).catch(error => {
            // Show error message
            setStatusMessage(statusMessageElements.study, 'danger', 'Could not save');
            setStatusMessage(statusMessageElements.samples, 'danger', 'Could not save');
            setStatusMessage(statusMessageElements.protocol, 'danger', 'Could not save');

            // Handle timeouts for fading out messages
            ({
                saveTimeoutVar: saveTimeoutStudy,
                fadeTimeoutVar: fadeTimeoutStudy
            } = startFadeOut(statusMessageElements.study, saveTimeoutStudy, fadeTimeoutStudy));
            ({
                saveTimeoutVar: saveTimeoutSamples,
                fadeTimeoutVar: fadeTimeoutSamples
            } = startFadeOut(statusMessageElements.samples, saveTimeoutSamples, fadeTimeoutSamples));
            ({
                saveTimeoutVar: saveTimeoutProtocol,
                fadeTimeoutVar: fadeTimeoutProtocol
            } = startFadeOut(statusMessageElements.protocol, saveTimeoutProtocol, fadeTimeoutProtocol));
            hideSpinner()
        });
    })
}
