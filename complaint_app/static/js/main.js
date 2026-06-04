// Main JavaScript File for Complaint Registration Application

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-fade flash alerts
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            // Smooth bootstrap fade out
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 2. Client-side File Upload Preview & Feedback
    const fileWrapper = document.getElementById('drag-drop-zone');
    const fileInput = document.getElementById('file-upload-input');
    const fileInfo = document.getElementById('file-upload-info');
    
    if (fileWrapper && fileInput) {
        fileWrapper.addEventListener('click', () => fileInput.click());
        
        fileInput.addEventListener('change', function () {
            if (this.files && this.files.length > 0) {
                const file = this.files[0];
                fileInfo.innerHTML = `<strong>Selected file:</strong> ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
                fileWrapper.style.borderColor = 'var(--accent-color)';
                fileWrapper.style.background = 'rgba(6, 182, 212, 0.08)';
            } else {
                fileInfo.textContent = 'PNG, JPG, PDF, DOC, TXT (Max 16MB)';
                fileWrapper.style.borderColor = 'rgba(255, 255, 255, 0.15)';
                fileWrapper.style.background = 'rgba(255, 255, 255, 0.02)';
            }
        });

        // Drag and drop events
        ['dragenter', 'dragover'].forEach(eventName => {
            fileWrapper.addEventListener(eventName, (e) => {
                e.preventDefault();
                fileWrapper.style.borderColor = 'var(--primary-color)';
                fileWrapper.style.background = 'rgba(79, 70, 229, 0.08)';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            fileWrapper.addEventListener(eventName, (e) => {
                e.preventDefault();
                if (eventName === 'drop' && e.dataTransfer.files.length > 0) {
                    fileInput.files = e.dataTransfer.files;
                    // Trigger change event manually
                    const event = new Event('change');
                    fileInput.dispatchEvent(event);
                } else if (eventName === 'dragleave') {
                    fileWrapper.style.borderColor = 'rgba(255, 255, 255, 0.15)';
                    fileWrapper.style.background = 'rgba(255, 255, 255, 0.02)';
                }
            }, false);
        });
    }

    // 3. Password Strength Indicator (on Registration Page)
    const registerPasswordInput = document.getElementById('register-password');
    const strengthBar = document.getElementById('strength-bar');
    
    if (registerPasswordInput && strengthBar) {
        registerPasswordInput.addEventListener('input', function () {
            const val = this.value;
            let score = 0;
            
            if (val.length >= 8) score++;
            if (/[A-Z]/.test(val)) score++;
            if (/[a-z]/.test(val)) score++;
            if (/[0-9]/.test(val)) score++;
            if (/[^A-Za-z0-9]/.test(val)) score++;
            
            // Set styles based on score
            let color = 'rgba(255,255,255,0.1)';
            let width = '0%';
            
            if (val.length > 0) {
                if (score <= 2) {
                    color = '#ef4444'; // Red
                    width = '33%';
                } else if (score <= 4) {
                    color = '#eab308'; // Yellow
                    width = '66%';
                } else {
                    color = '#10b981'; // Green
                    width = '100%';
                }
            }
            
            strengthBar.style.backgroundColor = color;
            strengthBar.style.width = width;
        });
    }

    // 4. Form Validation Helper
    const formsToValidate = document.querySelectorAll('.needs-validation-custom');
    formsToValidate.forEach(form => {
        form.addEventListener('submit', function (event) {
            let isValid = true;
            
            // Check matching password
            const password = form.querySelector('.password-match');
            const confirm = form.querySelector('.password-confirm');
            
            if (password && confirm) {
                if (password.value !== confirm.value) {
                    isValid = false;
                    confirm.setCustomValidity('Passwords do not match.');
                    // Display visual error
                    const feedback = confirm.nextElementSibling;
                    if (feedback && feedback.classList.contains('invalid-feedback')) {
                        feedback.textContent = 'Passwords do not match.';
                        feedback.style.display = 'block';
                    }
                } else {
                    confirm.setCustomValidity('');
                    const feedback = confirm.nextElementSibling;
                    if (feedback && feedback.classList.contains('invalid-feedback')) {
                        feedback.style.display = 'none';
                    }
                }
            }
            
            if (!form.checkValidity() || !isValid) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });

    // 5. Submit Complaint Category Select Cards Interaction
    const categoryCards = document.querySelectorAll('.category-card');
    const categoryDropdown = document.getElementById('category-dropdown');
    
    if (categoryCards.length > 0 && categoryDropdown) {
        categoryCards.forEach(card => {
            card.addEventListener('click', function () {
                const category = this.getAttribute('data-category');
                
                // Select category in hidden select dropdown
                categoryDropdown.value = category;
                
                // Add active outline to card
                categoryCards.forEach(c => {
                    c.style.borderColor = 'var(--border-glass)';
                    c.style.boxShadow = '0 8px 32px 0 rgba(0, 0, 0, 0.3)';
                });
                this.style.borderColor = 'var(--accent-color)';
                this.style.boxShadow = '0 0 15px var(--accent-glow)';
                
                // Scroll down to title/description form
                document.getElementById('complaint-form-details').scrollIntoView({ behavior: 'smooth' });
            });
        });
        
        // Synchronize dropdown change back to card outline
        categoryDropdown.addEventListener('change', function () {
            const val = this.value;
            categoryCards.forEach(card => {
                if (card.getAttribute('data-category') === val) {
                    card.style.borderColor = 'var(--accent-color)';
                    card.style.boxShadow = '0 0 15px var(--accent-glow)';
                } else {
                    card.style.borderColor = 'var(--border-glass)';
                    card.style.boxShadow = '0 8px 32px 0 rgba(0, 0, 0, 0.3)';
                }
            });
        });
    }
});

// 6. Admin Dashboard Charts Setup (called dynamically if elements present)
function initializeAdminCharts(categoriesData, statusData) {
    // Categories Chart (Donut)
    const catCanvas = document.getElementById('adminCategoriesChart');
    if (catCanvas) {
        const catLabels = Object.keys(categoriesData);
        const catValues = Object.values(categoriesData);
        
        new Chart(catCanvas, {
            type: 'doughnut',
            data: {
                labels: catLabels,
                datasets: [{
                    data: catValues,
                    backgroundColor: [
                        '#818cf8', // light indigo
                        '#a78bfa', // light purple
                        '#22d3ee', // light cyan
                        '#fb7185', // light rose
                        '#fbbf24'  // light amber
                    ],
                    borderColor: 'rgba(15, 23, 42, 0.8)',
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#94a3b8',
                            font: { family: 'Inter', size: 12 }
                        }
                    }
                }
            }
        });
    }

    // Status Chart (Bar)
    const statusCanvas = document.getElementById('adminStatusChart');
    if (statusCanvas) {
        const statusLabels = Object.keys(statusData);
        const statusValues = Object.values(statusData);
        
        new Chart(statusCanvas, {
            type: 'bar',
            data: {
                labels: statusLabels,
                datasets: [{
                    label: 'Complaints count',
                    data: statusValues,
                    backgroundColor: 'rgba(6, 182, 212, 0.4)',
                    borderColor: '#06b6d4',
                    borderWidth: 2,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#94a3b8' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { display: false }
                    }
                }
            }
        });
    }
}
