document.addEventListener('DOMContentLoaded', function() {
    // --- UI Enhancement Functions ---
    function initializeFormInteractions() {
        document.querySelectorAll('.form-input').forEach(input => {
            // Add focus animation
            input.addEventListener('focus', () => {
                input.closest('.group').querySelector('.form-label')?.classList.add('text-indigo-500');
                input.closest('.group').querySelector('i')?.classList.add('text-indigo-500');
            });
            
            input.addEventListener('blur', () => {
                input.closest('.group').querySelector('.form-label')?.classList.remove('text-indigo-500');
                input.closest('.group').querySelector('i')?.classList.remove('text-indigo-500');
            });

            // Add typing animation
            input.addEventListener('input', () => {
                input.classList.add('typing');
                clearTimeout(input.typingTimeout);
                input.typingTimeout = setTimeout(() => {
                    input.classList.remove('typing');
                }, 1000);
            });
        });
    }

    function initializeCharacterCounters() {
        document.querySelectorAll('textarea[id^="project"]').forEach(textarea => {
            const projectNum = textarea.id.match(/\d+/)[0];
            const counter = document.getElementById(`desc_${projectNum}_counter`);
            
            function updateCounter() {
                const count = textarea.value.length;
                const maxLength = 500;
                counter.innerHTML = `<span class="font-medium ${count > maxLength ? 'text-red-500' : ''}">${count}</span> / ${maxLength} characters`;
            }

            textarea.addEventListener('input', updateCounter);
            updateCounter(); // Initial count
        });
    }

    function initializeUploadZones() {
        document.querySelectorAll('.upload-zone').forEach(zone => {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, preventDefaults, false);
            });

            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }

            ['dragenter', 'dragover'].forEach(eventName => {
                zone.addEventListener(eventName, () => {
                    zone.classList.add('dragging');
                });
            });

            ['dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, () => {
                    zone.classList.remove('dragging');
                });
            });

            // Add success animation
            zone.addEventListener('drop', () => {
                zone.classList.add('success');
                setTimeout(() => {
                    zone.classList.remove('success');
                }, 3000);
            });
        });
    }

    // --- Element Selectors ---
    const portfolioForm = document.getElementById('portfolio-form');
    const previewFrame = document.getElementById('preview-frame');
    const templateSelector = document.getElementById('template-selector');
    const saveButton = document.getElementById('save-button');
    const saveStatus = document.getElementById('save-status');
    const skillsContainer = document.getElementById('skills-container');
    const addSkillBtn = document.getElementById('add-skill-btn');
    const profilePicUpload = document.getElementById('profile_pic_upload');
    const profilePicPreview = document.getElementById('profile_pic_preview');
    const profilePicHiddenInput = document.getElementById('profile_pic');
    const resumeUpload = document.getElementById('resume_upload');
    const resumeIcon = document.getElementById('resume_icon');
    const resumeHiddenInput = document.getElementById('resume_file');

    let selectedTemplateId = document.querySelector('.template-option.selected')?.dataset.templateId || 1;

    // --- Core Functions ---

    function getFormData() {
        const data = {
            template_id: parseInt(selectedTemplateId, 10)
        };
        // Get all standard inputs
        portfolioForm.querySelectorAll('input, textarea').forEach(input => {
            if(input.type !== 'file') {
                 data[input.id] = input.value;
            }
        });

        // Collect skills from both input fields and static tags
        const skills = [];
        // Collect from static tags
        skillsContainer.querySelectorAll('.skill-tag').forEach(tag => {
            const span = tag.querySelector('span');
            const input = tag.querySelector('input');
            if (span && span.textContent.trim()) {
                skills.push(span.textContent.trim());
            } else if (input && input.value.trim()) {
                skills.push(input.value.trim());
            }
        });
        
        console.log('Collected skills:', skills);
        // Ensure valid JSON
        try {
            data.skills = JSON.stringify(skills || []);
            console.log('Skills data being sent:', data.skills);
        } catch (error) {
            console.error('Error stringifying skills:', error);
            data.skills = '[]';
        }

        return data;
    }

    async function updatePreview() {
        const formData = getFormData();
        try {
            const response = await fetch('/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const html = await response.text();
            previewFrame.srcdoc = html;

        } catch (error) {
            console.error('Error updating preview:', error);
            previewFrame.srcdoc = `<div style="padding: 2rem; font-family: sans-serif; color: red;">Error loading preview.</div>`;
        }
    }

    // --- Skills Management ---

    function createSkillInput(value = '') {
        console.log('Creating skill input with value:', value);
        
        const skillsContainer = document.getElementById('skills-container');
        if (!skillsContainer) {
            console.error('Skills container not found in createSkillInput');
            return;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'skill-tag';
        
        if (value) {
            // Create static tag for existing skill
            wrapper.innerHTML = `
                <span>${value}</span>
                <button type="button" class="remove-btn">
                    <i class="fas fa-times"></i>
                </button>
            `;
            const removeBtn = wrapper.querySelector('.remove-btn');
            removeBtn.onclick = () => {
                console.log('Removing skill:', value);
                wrapper.remove();
                updatePreview();
            };
        } else {
            // Create input for new skill
            console.log('Creating new skill input field');
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'skill-input';
            input.placeholder = 'Add skill...';

            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && input.value.trim()) {
                    const value = input.value.trim();
                    console.log('New skill entered:', value);
                    wrapper.remove();
                    createSkillInput(value); // Create static tag
                    createSkillInput(); // Create new input
                    updatePreview();
                } else if (e.key === 'Escape') {
                    console.log('Canceling skill input');
                    wrapper.remove();
                }
            });

            input.addEventListener('blur', () => {
                if (input.value.trim()) {
                    const value = input.value.trim();
                    console.log('New skill added on blur:', value);
                    wrapper.remove();
                    createSkillInput(value);
                    updatePreview();
                } else {
                    wrapper.remove();
                }
            });

            wrapper.appendChild(input);
            input.focus();
        }
        
        skillsContainer.appendChild(wrapper);
    }

    function initializeSkills(skillsArray) {
        console.log('initializeSkills called with:', skillsArray);
        
        // Get fresh references to elements
        const skillsContainer = document.getElementById('skills-container');
        const addSkillBtn = document.getElementById('add-skill-btn');

        if (!skillsContainer) {
            console.error('Skills container not found');
            return;
        }

        // Clear existing skills
        console.log('Clearing skills container');
        skillsContainer.innerHTML = '';

        try {
            // Parse skills if it's a string
            let skills = skillsArray;
            if (typeof skillsArray === 'string') {
                try {
                    skills = JSON.parse(skillsArray);
                } catch (e) {
                    console.error('Error parsing skills string:', e);
                    skills = [];
                }
            }
            
            // Ensure we have valid skills array
            skills = Array.isArray(skills) ? skills : [];
            console.log('Processing skills array:', skills);
            
            // Add existing skills
            skills.forEach(skill => {
                if (skill && typeof skill === 'string' && skill.trim()) {
                    console.log('Creating skill tag for:', skill.trim());
                    createSkillInput(skill.trim());
                }
            });

            // Add button event listener and empty input for new skills
            if (addSkillBtn) {
                console.log('Setting up add skill button');
                // Remove any existing listeners
                addSkillBtn.replaceWith(addSkillBtn.cloneNode(true));
                const newAddSkillBtn = document.getElementById('add-skill-btn');
                if (newAddSkillBtn) {
                    newAddSkillBtn.addEventListener('click', () => {
                        console.log('Add skill button clicked');
                        // Only create new input if there isn't already an empty one
                        if (!skillsContainer.querySelector('.skill-input')) {
                            createSkillInput();
                        }
                    });
                }
            } else {
                console.error('Add skill button not found');
            }
            
            // Trigger preview update to show skills
            updatePreview();
        } catch (error) {
            console.error('Error initializing skills:', error);
        }
    }

    addSkillBtn.addEventListener('click', () => createSkillInput());


    // --- File Upload Management ---

    async function handleFileUpload(file, targetHiddenInput, previewElement) {
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        
        // Show loading state if applicable
        if(previewElement && previewElement.tagName === 'IMG') {
            previewElement.style.opacity = '0.5';
        }

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if (!response.ok || !result.success) throw new Error(result.message || 'Upload failed');
            
            targetHiddenInput.value = result.filepath;

            if (previewElement) {
                if (previewElement.tagName === 'IMG') {
                    previewElement.src = result.filepath + `?t=${new Date().getTime()}`; // bust cache
                } else if (previewElement.tagName === 'I') {
                    previewElement.classList.remove('text-gray-300');
                    previewElement.classList.add('text-green-500');
                }
            }
            updatePreview(); // Refresh preview with new file path

        } catch (error) {
            console.error('File upload error:', error);
            saveStatus.textContent = `Error: ${error.message}`;
            saveStatus.className = 'text-sm text-center mt-2 h-4 text-red-600';
        } finally {
            if(previewElement && previewElement.tagName === 'IMG') {
                previewElement.style.opacity = '1';
            }
        }
    }

    profilePicUpload.addEventListener('change', (e) => handleFileUpload(e.target.files[0], profilePicHiddenInput, profilePicPreview));
    resumeUpload.addEventListener('change', (e) => handleFileUpload(e.target.files[0], resumeHiddenInput, resumeIcon));

    // --- General Event Listeners ---

    let debounceTimer;
    portfolioForm.addEventListener('input', (e) => {
        if(e.target.type === 'file') return; // file inputs handled separately
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(updatePreview, 300);
    });

    templateSelector.addEventListener('click', (e) => {
        const targetOption = e.target.closest('.template-option');
        if (!targetOption) return;
        
        document.querySelectorAll('.template-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        targetOption.classList.add('selected');

        selectedTemplateId = targetOption.dataset.templateId;
        updatePreview();
    });

    saveButton.addEventListener('click', async () => {
        const formData = getFormData();
        const saveButtonContent = saveButton.innerHTML;
        saveButton.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Saving Changes...</span>`;
        saveButton.disabled = true;
        saveButton.classList.add('saving', 'opacity-75');
        saveStatus.textContent = '';

        try {
            const response = await fetch('/save_portfolio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });
            const result = await response.json();
            if (!result.success) throw new Error(result.message || 'Failed to save.');
            
            saveStatus.innerHTML = `<span class="flex items-center gap-2 justify-center text-green-600">
                <i class="fas fa-check-circle"></i>${result.message}
            </span>`;
            saveStatus.className = 'text-sm text-center mt-2 h-4';
        } catch (error) {
            saveStatus.innerHTML = `<span class="flex items-center gap-2 justify-center text-red-600">
                <i class="fas fa-exclamation-circle"></i>${error.message}
            </span>`;
            saveStatus.className = 'text-sm text-center mt-2 h-4';
        } finally {
            saveButton.innerHTML = saveButtonContent;
            saveButton.disabled = false;
            saveButton.classList.remove('saving', 'opacity-75');
            setTimeout(() => {
                saveStatus.style.opacity = '1';
                saveStatus.style.transition = 'opacity 0.5s ease';
                setTimeout(() => {
                    saveStatus.style.opacity = '0';
                    setTimeout(() => { 
                        saveStatus.textContent = '';
                        saveStatus.style.removeProperty('opacity');
                        saveStatus.style.removeProperty('transition');
                    }, 500);
                }, 3000);
            }, 500);
        }
    });

    // --- Initial Load ---
    initializeSkills(initialSkills);
    updatePreview();
});



