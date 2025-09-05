/**
 * Navigation & Progress Functions
 * Extracted from real_ui.html for better organization
 */

// Step Navigation Functions
function goToStepDirect(stepNumber) {
    console.log(`🚀 Navigating directly to Step ${stepNumber}`);
    
    // Hide all steps
    for (let i = 1; i <= 4; i++) {
        const stepContainer = document.getElementById(`step${i}-container`);
        if (stepContainer) {
            stepContainer.style.display = 'none';
        }
    }
    
    // Show selected step
    const targetStep = document.getElementById(`step${stepNumber}-container`);
    if (targetStep) {
        targetStep.style.display = 'block';
        
        // Load step-specific content
        switch (stepNumber) {
            case 1:
                // Step 1 is always ready
                break;
            case 2:
                loadTemplateGeneration();
                break;
            case 3:
                loadRCodeGeneration();
                break;
            case 4:
                loadCodeExecution();
                break;
        }
        
        // Update progress indicator
        updateProgressIndicator(stepNumber);
    }
}

function updateProgressIndicator(currentStep) {
    console.log(`📊 Updating progress indicator for step ${currentStep}`);
    
    // Get all progress step elements
    const progressSteps = document.querySelectorAll('.progress-step');
    
    // Remove active class from all steps and update their appearance
    progressSteps.forEach((step, index) => {
        const stepNumber = index + 1;
        step.classList.remove('active', 'completed', 'pending');
        
        if (stepNumber < currentStep) {
            // Completed steps - show as completed (green)
            step.classList.add('completed');
        } else if (stepNumber === currentStep) {
            // Current step - make it active (blue)
            step.classList.add('active');
        } else {
            // Future steps - show as pending (gray)
            step.classList.add('pending');
        }
    });
}

// Project Management Functions
function startNewProject() {
    console.log('🆕 Starting new project...');
    
    if (confirm('Are you sure you want to start a new project? This will clear all current progress.')) {
        // Clear all stored data
        window.analysisResults = null;
        window.currentTemplate = null;
        window.currentRCode = null;
        window.datasetExploration = null;
        window.datasetInfo = null;
        window.interactiveSession = false;
        
        // Clear all form inputs
        const queryInput = document.getElementById('query');
        const datasetInput = document.getElementById('dataset-path');
        if (queryInput) queryInput.value = '';
        if (datasetInput) datasetInput.value = '';
        
        // Clear all result displays
        const resultsDiv = document.getElementById('results');
        if (resultsDiv) {
            resultsDiv.innerHTML = '';
            resultsDiv.classList.remove('show');
        }
        
        // Hide all steps except Step 1
        for (let i = 2; i <= 4; i++) {
            const stepContainer = document.getElementById(`step${i}-container`);
            if (stepContainer) {
                stepContainer.style.display = 'none';
            }
        }
        
        // Show Step 1
        const step1Container = document.getElementById('step1-container');
        if (step1Container) {
            step1Container.style.display = 'block';
        }
        
        // Reset progress indicator
        updateProgressIndicator(1);
        
        console.log('✅ New project started');
    }
}

// LLM Provider Management Functions
function loadLLMProviders() {
    console.log('🔧 Loading LLM providers...');
    
    fetch('/api/llm/providers')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('llm-provider-select');
            if (select && data.providers) {
                select.innerHTML = '';
                
                data.providers.forEach(provider => {
                    const option = document.createElement('option');
                    option.value = provider.name;
                    option.textContent = `${provider.display_name} ${provider.status === 'available' ? '✅' : '❌'}`;
                    option.disabled = provider.status !== 'available';
                    
                    if (provider.name === data.current_provider) {
                        option.selected = true;
                    }
                    
                    select.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Failed to load LLM providers:', error);
        });
}

function changeLLMProvider() {
    const select = document.getElementById('llm-provider-select');
    const newProvider = select.value;
    
    console.log(`🔄 Changing LLM provider to: ${newProvider}`);
    
    fetch('/api/llm/change_provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: newProvider })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`✅ LLM provider changed to: ${newProvider}`);
            // Reload providers to update status
            setTimeout(loadLLMProviders, 1000);
        } else {
            console.error(`❌ Failed to change provider: ${data.error}`);
            alert(`Failed to change provider: ${data.error}`);
            // Reload providers to reset selection
            loadLLMProviders();
        }
    })
    .catch(error => {
        console.error('Provider change error:', error);
        alert(`Provider change error: ${error.message}`);
        loadLLMProviders();
    });
}

// Status Check Functions
function checkStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            updateStatusIndicator(data.status);
            updateComponentStatus(data.components_status);
        })
        .catch(error => {
            console.error('Status check failed:', error);
            updateStatusIndicator('Error');
            updateComponentStatus('Error');
        });
}

// File Download Functions
function downloadFile(fileName) {
    console.log(`💾 Downloading file: ${fileName}`);
    
    const link = document.createElement('a');
    link.href = `/download/${fileName}`;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function downloadAllFiles() {
    console.log('💾 Downloading all files...');
    
    fetch('/download_all')
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('Download failed');
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'clinical_analysis_results.zip';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Download all files error:', error);
            alert(`Download failed: ${error.message}`);
        });
}

// Export Functions
async function exportResults() {
    console.log('📤 Exporting results...');
    
    try {
        const exportData = {
            query: document.getElementById('query')?.value || '',
            dataset_path: document.getElementById('dataset-path')?.value || '',
            analysis_results: window.analysisResults || null,
            template: window.currentTemplate || null,
            rcode: window.currentRCode || null,
            dataset_exploration: window.datasetExploration || null,
            timestamp: new Date().toISOString()
        };
        
        const response = await fetch('/export_project', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(exportData)
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'clinical_project_export.json';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            console.log('✅ Project exported successfully');
        } else {
            throw new Error('Export failed');
        }
    } catch (error) {
        console.error('Export error:', error);
        alert(`Export failed: ${error.message}`);
    }
}

function saveProject() {
    console.log('💾 Saving project...');
    
    const projectData = {
        query: document.getElementById('query')?.value || '',
        dataset_path: document.getElementById('dataset-path')?.value || '',
        analysis_results: window.analysisResults || null,
        template: window.currentTemplate || null,
        rcode: window.currentRCode || null,
        dataset_exploration: window.datasetExploration || null,
        timestamp: new Date().toISOString()
    };
    
    localStorage.setItem('clinical_project', JSON.stringify(projectData));
    alert('✅ Project saved to browser storage');
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize functions when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Page loaded, initializing navigation functions...');
    
    // Load LLM providers
    loadLLMProviders();
    
    // Check initial status
    checkStatus();
    
    // Set up periodic status checks
    setInterval(checkStatus, 30000); // Check every 30 seconds
    
    // Initialize progress indicator
    updateProgressIndicator(1);
    
    console.log('✅ Navigation functions initialized');
});
