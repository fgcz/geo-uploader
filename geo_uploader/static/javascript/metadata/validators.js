/**
 * Main validation function that validates all data
 * @returns {Object} Validation results with valid flag and errors array
 */
async function validateData(){
    let validationResults = {
        valid: true,
        errors: []
    }

    // Validate study data
    const studyResults = validateStudyData()
    if (!studyResults.valid){
        validationResults.valid = false;
        validationResults.errors.push(...studyResults.errors)
    }

    // Validate samples data
    const samplesResults = await validateSamplesData()
    if (!samplesResults.valid){
        validationResults.valid = false;
        validationResults.errors.push(...samplesResults.errors)
    }
    return validationResults;
}

async function validateSamplesData(){
    // Get the data from the Handsontable instance
    // const data = hot_sample.getData();
    let validationResults = {
        valid: true,
        errors: []
    };

    // Add any other samples validation logic here if needed

    return validationResults;
}

function validateStudyData() {
    // Get the data from the Handsontable instance
    const data = hot_study.getData();
    let validationResults = {
        valid: true,
        errors: []
    };

    // Loop through the data and validate the second column
    data.forEach(row => {
        const role = row[0]; // First column value (Role)
        const name = row[1]; // Second column value (Name)

        // Check if the role is 'contributor'
        if (role === 'contributor') {
            if (name) {
                if(!validateName(name)){
                    validationResults.valid = false;
                    validationResults.errors.push({
                        type: 'contributor',
                        message: 'Contributor name format is invalid. Please use format: "Firstname, Initial (optional), Surname"',
                    });
                }
            }
        } else if (role === '*title'){
            if(name){
                if(name.length < 50 || name.length > 255){
                    validationResults.valid = false;
                    validationResults.errors.push({
                        type: 'title',
                        message: 'Title must be at least 50 characters long and at most 255 characters',
                    });
                }
            }
        } else if (role === '*summary (abstract)'){
            if(name){
                if(name.length < 50){
                    validationResults.valid = false;
                    validationResults.errors.push({
                        type: 'summary',
                        message: 'Summary (abstract) must be at least 75 characters long',
                    });
                }
            }
        } else if (role === '*experimental design'){
            if(name){
                if(name.length < 75){
                    validationResults.valid = false;
                    validationResults.errors.push({
                        type: 'design',
                        message: 'Experimental design must be at least 75 characters long',
                    });
                }
            }
        }
    });

    return validationResults;
}

/**
 * Validate contributor name format
 * This validation follows the validation of the original spreadsheet.
 * @param {string} input - The name to validate
 * @returns {boolean} True if valid, false otherwise
 */
function validateName(input) {
    // Trim the input
    const trimmedInput = input.trim();

    // Count commas
    const commaCount = (trimmedInput.match(/,/g) || []).length;

    // Check if there are either 1 or 2 commas
    const hasValidCommaCount = commaCount === 1 || commaCount === 2;

    // Find position of first comma
    const firstCommaPosition = trimmedInput.indexOf(',');

    // Check if first comma is not at the beginning or end
    const hasValidFirstCommaPosition =
        firstCommaPosition > 0 && firstCommaPosition < trimmedInput.length - 1;

    // Return true only if all conditions are met
    return hasValidCommaCount && hasValidFirstCommaPosition;
}