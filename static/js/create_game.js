document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const submitButton = form.querySelector('button[type="submit"]');

    function validateField(field) {
        const value = field.value.trim();
        const fieldName = field.name;
        let errorMessage = '';

        if (fieldName === 'time_limit') {
            if (!value) {
                errorMessage = 'Time limit is required.';
            } else if (isNaN(value) || value < 60 || value > 3600) {
                errorMessage = 'Time limit must be between 60 and 3600 seconds.';
            }
        } else if (fieldName === 'max_players') {
            if (!value) {
                errorMessage = 'Maximum number of players is required.';
            } else if (isNaN(value) || value < 2 || value > 100) {
                errorMessage = 'Number of players must be between 2 and 100.';
            }
        } else if (fieldName === 'pot_size') {
            if (!value) {
                errorMessage = 'Pot size is required.';
            } else if (isNaN(value) || value < 1) {
                errorMessage = 'Pot size must be at least 1.';
            }
        } else if (fieldName === 'entry_value') {
            if (!value) {
                errorMessage = 'Entry value is required.';
            } else if (isNaN(value) || value < 0.01) {
                errorMessage = 'Entry value must be at least 0.01.';
            }
        } else if (fieldName === 'start_time') {
            if (!value) {
                errorMessage = 'Start time is required.';
            } else if (new Date(value) <= new Date()) {
                errorMessage = 'Start time must be in the future.';
            }
        }

        const errorElement = field.nextElementSibling;
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.textContent = errorMessage;
        } else if (errorMessage) {
            const newErrorElement = document.createElement('div');
            newErrorElement.classList.add('error-message');
            newErrorElement.textContent = errorMessage;
            field.parentNode.insertBefore(newErrorElement, field.nextSibling);
        }

        return !errorMessage;
    }

    form.addEventListener('submit', function(e) {
        let isValid = true;
        const fields = form.querySelectorAll('input, select, textarea');
        fields.forEach(field => {
            if (!validateField(field)) {
                isValid = false;
            }
        });

        if (!isValid) {
            e.preventDefault();
        }
    });

    form.addEventListener('input', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
            validateField(e.target);
        }
    });
});
