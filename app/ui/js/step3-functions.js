/**
 * Step 3 Functions - R Code Generation & Management
 * Extracted from real_ui.html for better organization
 */

// R Code Loading and Generation
function loadRCodeGeneration() {
    console.log('💻 Loading R code generation...');

    // Display template summary using same method as Step 2
    const template = window.currentTemplate;
    const templateSummaryElement = document.getElementById('step3-template-summary');

    if (template) {
        // Check if template contains HTML (like Step 2)
        if (template.includes('<table') || template.includes('<div')) {
            // Display as rendered HTML (same as Step 2)
            templateSummaryElement.innerHTML = template;
        } else {
            // Display as text if it's not HTML
            templateSummaryElement.textContent = template.substring(0, 500) + (template.length > 500 ? '...' : '');
        }
    }

    // Generate R code using LLM
    generateHighQualityRCode();
}

function generateHighQualityRCode() {
    console.log('💻 Generating high-quality R code with LLM...');

    const analysisResults = window.lastAnalysisResult;
    const template = window.currentTemplate;

    if (!template) {
        alert('No template available for R code generation.');
        return;
    }

    // Check if dataset exploration has been done
    if (!window.currentDatasetInfo || !window.currentDatasetInfo.dataset_info) {
        const proceed = confirm('⚠️ Dataset exploration not completed. This may result in R code that uses incorrect variable names.\n\nClick "🔍 Explore Dataset" first for better results.\n\nProceed anyway?');
        if (!proceed) {
            return;
        }
        console.log('⚠️ Proceeding without dataset exploration - R code may use generic variable names');
    } else {
        console.log('✅ Dataset exploration found - using actual variable names');
    }

    // Generate execution ID for session isolation
    if (!window.currentExecutionId) {
        const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+/, '');
        const randomId = Math.random().toString(36).substring(2, 10);
        window.currentExecutionId = `${timestamp}_${randomId}`;
        console.log(`📁 Generated execution ID for Step 3: ${window.currentExecutionId}`);
    }

    // Show generation status
    document.getElementById('rcode-generation-status').style.display = 'block';
    document.getElementById('rcode-display').style.display = 'none';

    // Call backend to generate high-quality R code with session context
    fetch('/generate_quality_rcode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            template_content: template,
            template_structure: window.currentTemplateStructure || {},
            domain: analysisResults?.domain_detected,
            dataset: analysisResults?.adam_dataset,
            query: analysisResults?.query,
            dataset_info: window.currentDatasetInfo || {},
            analysis_results: analysisResults || {},
            // Session management for robust file handling
            execution_id: window.currentExecutionId,
            session_directory: `outputs/execution_${window.currentExecutionId}`,
            session_isolation: true
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Hide generation status and show R code
            document.getElementById('rcode-generation-status').style.display = 'none';
            document.getElementById('rcode-display').style.display = 'block';

            // Display the generated R code
            document.getElementById('rcode-content').textContent = data.r_code;

            // Store the R code for later use
            window.currentRCode = data.r_code;

            console.log('✅ High-quality R code generated successfully');
        } else {
            document.getElementById('rcode-generation-status').innerHTML = `
                <h4 style="color: #721c24; margin: 0;">❌ R Code Generation Failed</h4>
                <p style="color: #721c24; margin: 5px 0 0 0;">Error: ${data.error}</p>
            `;
        }
    })
    .catch(error => {
        console.error('❌ R code generation error:', error);
        document.getElementById('rcode-generation-status').innerHTML = `
            <h4 style="color: #721c24; margin: 0;">❌ R Code Generation Failed</h4>
            <p style="color: #721c24; margin: 5px 0 0 0;">Network error: ${error.message}</p>
        `;
    });
}

function regenerateRCode() {
    generateHighQualityRCode();
}

function editRCode() {
    const currentRCode = window.currentRCode || '';
    document.getElementById('rcode-editor').value = currentRCode;
    document.getElementById('rcode-editor-section').style.display = 'block';
    document.getElementById('rcode-display').style.display = 'none';
}

function saveRCodeEdits() {
    const editedRCode = document.getElementById('rcode-editor').value;
    window.currentRCode = editedRCode;

    document.getElementById('rcode-content').textContent = editedRCode;
    document.getElementById('rcode-editor-section').style.display = 'none';
    document.getElementById('rcode-display').style.display = 'block';

    alert('✅ R code changes saved successfully!');
}

function cancelRCodeEdit() {
    document.getElementById('rcode-editor-section').style.display = 'none';
    document.getElementById('rcode-display').style.display = 'block';
}

function validateRCode() {
    const rCode = window.currentRCode;
    if (!rCode) {
        alert('No R code to validate.');
        return;
    }

    fetch('/validate_rcode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            r_code: rCode
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.valid) {
            alert('✅ R code validation passed!');
        } else {
            alert('❌ R code validation failed: ' + data.error);
        }
    })
    .catch(error => {
        alert('❌ Error validating R code: ' + error);
    });
}

function finalizeRCode() {
    const rCode = window.currentRCode;
    if (!rCode) {
        alert('No R code to execute. Please generate R code first.');
        return;
    }

    if (confirm('🚀 Execute this R code and view results?\\n\\nThis will move you to Step 4 where the code will be executed.')) {
        goToStep4();
    }
}

// Navigation Functions
function goToStep3() {
    console.log('🚀 Moving to Step 3 - R Code Generation...');

    // Hide Step 2 and show Step 3
    const step2Container = document.getElementById('step2-container');
    const step3Container = document.getElementById('step3-container');

    if (step2Container) {
        step2Container.style.display = 'none';
        console.log('✅ Step 2 container hidden');
    }

    if (step3Container) {
        step3Container.style.display = 'block';
        console.log('✅ Step 3 container shown');

        // Update progress indicator
        updateProgressIndicator(3);
    } else {
        console.error('❌ Step 3 container not found');
    }

    // Load R code generation interface
    console.log('💻 Loading R code generation...');
    loadRCodeGeneration();
}

function goBackToStep2() {
    // Show Step 2 and hide Step 3
    document.getElementById('step2-container').style.display = 'block';
    document.getElementById('step3-container').style.display = 'none';

    // Update progress indicator
    updateProgressIndicator(2);
}

// Navigation Functions
function goToStep4() {
    console.log('🚀 Moving to Step 4...');
    
    document.getElementById('step3-container').style.display = 'none';
    document.getElementById('step4-container').style.display = 'block';
    
    // Update progress indicator
    updateProgressIndicator(4);
    
    loadCodeExecution();
}

function goBackToStep3() {
    document.getElementById('step4-container').style.display = 'none';
    document.getElementById('step3-container').style.display = 'block';
    
    // Update progress indicator
    updateProgressIndicator(3);
}
