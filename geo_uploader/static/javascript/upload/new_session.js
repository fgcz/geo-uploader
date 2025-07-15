
const new_session_form = document.getElementById('new-session-form');
document.addEventListener('DOMContentLoaded', function () {

    const dropdownInput = document.getElementById('user_dropdown');
    const datalistOptions = Array.from(document.getElementById('user-options').options);
    const hiddenUserIdInput = document.getElementById('selected_user_id');
    new_session_form.addEventListener('submit', function (event) {
        // Clear previous error message before validation
        const errorDiv = document.querySelector('.text-danger');
        if (errorDiv) errorDiv.remove();

        // If "No eligible users available" is selected, treat it as empty (None)
        else if (dropdownInput.value === "No eligible users available") {
            hiddenUserIdInput.value = '';  // Treat as no selection
            showSpinner('Checking FTP connection and verifying samples...');
        } else {
            // Check if the input value matches any option in the datalist
            const isValid = datalistOptions.some(option => option.value === dropdownInput.value);

            if (!isValid && dropdownInput.value !== '') {
                // Prevent form submission if invalid
                event.preventDefault();

                // Display validation error message
                const errorMessage = "Please select a valid bioinformatician from the list or leave the field empty.";
                const errorDiv = document.createElement('div');
                errorDiv.classList.add('text-danger');
                errorDiv.innerHTML = `<p>${errorMessage}</p>`;

                // Insert error message under the user dropdown field
                const userDropdownContainer = dropdownInput.closest('.form-group');
                userDropdownContainer.appendChild(errorDiv);
            } else if (isValid) {
                // Set the hidden field with the corresponding user ID if valid
                const selectedOption = datalistOptions.find(option => option.value === dropdownInput.value);
                hiddenUserIdInput.value = selectedOption.getAttribute('data-id');
                showSpinner('Checking FTP connection and verifying samples...');
            } else if (dropdownInput.value === ''){
                showSpinner('Checking FTP connection and verifying samples...');
            }
        }
    });

});

