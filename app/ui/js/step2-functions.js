/**
 * Step 2 Functions - Template Generation & Management
 * Extracted from real_ui.html for better organization
 */

function loadTemplateGeneration() {
    // Get the analysis results from Step 1
    const analysisResults = window.lastAnalysisResult;

    console.log('🔍 Loading template generation...');
    console.log('🔍 Analysis results:', analysisResults);

    if (analysisResults) {
        console.log('📊 Populating analysis summary...');

        // Populate Step 2 with analysis results
        const domainElement = document.getElementById('step2-domain');
        const datasetElement = document.getElementById('step2-dataset');
        const similarityElement = document.getElementById('step2-similarity');
        const titleElement = document.getElementById('step2-template-title');
        const descElement = document.getElementById('step2-template-desc');

        if (domainElement) {
            domainElement.textContent = analysisResults.domain_detected || 'Unknown';
            console.log('✅ Domain set:', analysisResults.domain_detected);
        } else {
            console.error('❌ step2-domain element not found');
        }

        if (datasetElement) {
            datasetElement.textContent = analysisResults.adam_dataset || 'Unknown';
            console.log('✅ Dataset set:', analysisResults.adam_dataset);
        } else {
            console.error('❌ step2-dataset element not found');
        }

        if (similarityElement) {
            similarityElement.textContent = (analysisResults.best_similarity || 0).toFixed(3);
            console.log('✅ Similarity set:', analysisResults.best_similarity);
        } else {
            console.error('❌ step2-similarity element not found');
        }

        if (analysisResults.top_template) {
            if (titleElement) {
                titleElement.textContent = analysisResults.top_template.title || 'Unknown';
                console.log('✅ Template title set:', analysisResults.top_template.title);
            }
            if (descElement) {
                descElement.textContent = analysisResults.top_template.description || 'No description available';
                console.log('✅ Template description set');
            }
        } else {
            console.log('⚠️ No top_template data available');
        }

        // Generate high-quality template using LLM
        console.log('🎨 Starting template generation...');
        generateHighQualityTemplate(analysisResults);

        console.log('✅ Step 2 populated with analysis results');
    } else {
        console.error('❌ No analysis results found for Step 2');
        console.error('❌ window.lastAnalysisResult is:', window.lastAnalysisResult);
        alert('No analysis results found. Please complete Step 1 first.');
    }
}

function generateHighQualityTemplate(analysisResults) {
    console.log('🎨 Generating high-quality template with LLM...');
    console.log('🎨 Analysis results for template generation:', analysisResults);

    // Show generation status
    const statusElement = document.getElementById('template-generation-status');
    const displayElement = document.getElementById('template-display');

    if (statusElement) {
        statusElement.style.display = 'block';
        console.log('✅ Template generation status shown');
    } else {
        console.error('❌ template-generation-status element not found');
    }

    if (displayElement) {
        displayElement.style.display = 'none';
        console.log('✅ Template display hidden');
    } else {
        console.error('❌ template-display element not found');
    }

    // Call backend to generate high-quality template using real LLM
    fetch('/generate_quality_template', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query: analysisResults.query,
            domain: analysisResults.domain_detected,
            dataset: analysisResults.adam_dataset,
            top_template: analysisResults.top_template,
            similarity: analysisResults.best_similarity,
            rag_matches: analysisResults.rag_matches
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Hide generation status and show template
            document.getElementById('template-generation-status').style.display = 'none';
            document.getElementById('template-display').style.display = 'block';

            // Update analysis summary with RAG data
            if (data.rag_analysis) {
                const ragData = data.rag_analysis;

                // Update similarity info
                const similarityElement = document.getElementById('step2-similarity');
                if (similarityElement && ragData.examples && ragData.examples.length > 0) {
                    const topExample = ragData.examples[0];
                    similarityElement.textContent = `${(topExample.similarity * 100).toFixed(1)}%`;
                }

                // Update template reference info
                const titleElement = document.getElementById('step2-template-title');
                const descElement = document.getElementById('step2-template-desc');

                if (titleElement && ragData.examples && ragData.examples.length > 0) {
                    const topExample = ragData.examples[0];
                    titleElement.textContent = topExample.title || 'No reference template';
                }

                if (descElement && ragData.examples && ragData.examples.length > 0) {
                    const exampleCount = ragData.examples_count || ragData.examples.length;
                    descElement.textContent = `Found ${exampleCount} similar templates for reference`;
                }

                console.log('✅ RAG analysis updated:', ragData);
            }

            // Display the generated template (use innerHTML for HTML content)
            const templateContentElement = document.getElementById('template-content');
            if (data.template_content && data.template_content.trim()) {
                templateContentElement.innerHTML = data.template_content;
            } else {
                // Fallback to structure if HTML is empty
                templateContentElement.textContent = JSON.stringify(data.template_structure, null, 2);
            }

            // Store the template for later use
            window.currentTemplate = data.template_content || JSON.stringify(data.template_structure, null, 2);
            window.currentTemplateStructure = data.template_structure;

            console.log('✅ High-quality template generated successfully');
            console.log('📊 Template data:', data);
        } else {
            document.getElementById('template-generation-status').innerHTML = `
                <h4 style="color: #721c24; margin: 0;">❌ Template Generation Failed</h4>
                <p style="color: #721c24; margin: 5px 0 0 0;">Error: ${data.error}</p>
            `;
        }
    })
    .catch(error => {
        console.error('❌ Template generation error:', error);
        document.getElementById('template-generation-status').innerHTML = `
            <h4 style="color: #721c24; margin: 0;">❌ Template Generation Failed</h4>
            <p style="color: #721c24; margin: 5px 0 0 0;">Network error: ${error.message}</p>
        `;
    });
}

function regenerateTemplate() {
    const analysisResults = window.lastAnalysisResult;
    if (!analysisResults) {
        alert('No analysis results available. Please go back to Step 1.');
        return;
    }

    // Regenerate template using the same function
    generateHighQualityTemplate(analysisResults);
}

function editTemplate() {
    // Show template editor with current content
    const currentTemplate = window.currentTemplate || '';
    document.getElementById('template-editor').value = currentTemplate;
    document.getElementById('template-editor-section').style.display = 'block';
    document.getElementById('template-display').style.display = 'none';
}

function saveTemplateEdits() {
    // Save the edited template
    const editedTemplate = document.getElementById('template-editor').value;
    window.currentTemplate = editedTemplate;

    // Update display and hide editor
    document.getElementById('template-content').textContent = editedTemplate;
    document.getElementById('template-editor-section').style.display = 'none';
    document.getElementById('template-display').style.display = 'block';

    alert('✅ Template changes saved successfully!');
}

function cancelTemplateEdit() {
    // Cancel editing and go back to display
    document.getElementById('template-editor-section').style.display = 'none';
    document.getElementById('template-display').style.display = 'block';
}

function validateTemplate() {
    const template = window.currentTemplate;
    if (!template) {
        alert('No template to validate.');
        return;
    }

    // Simple validation
    if (template.length < 100) {
        alert('⚠️ Template seems too short. Consider adding more content.');
    } else if (!template.includes('|') && !template.includes('Table')) {
        alert('⚠️ Template might be missing table structure or title.');
    } else {
        alert('✅ Template validation passed! Template looks good.');
    }
}

function finalizeTemplate() {
    const template = window.currentTemplate;
    if (!template) {
        alert('No template to finalize. Please generate a template first.');
        return;
    }

    if (confirm('🎯 Finalize this template and proceed to R code generation?\\n\\nThis will move you to Step 3 where R code will be generated based on this template.')) {
        goToStep3();
    }
}

function downloadTemplate() {
    const template = window.currentTemplate;

    if (!template) {
        alert('No template to download. Please generate a template first.');
        return;
    }

    // Create download content
    const content = `# Clinical TLF Template
# Generated by Real AI Backend using LLM
# Generated at: ${new Date().toISOString()}

${template}`;

    // Create and trigger download
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'clinical_tlf_template.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    alert('📥 Template downloaded successfully!');
}

// Navigation Functions
function goToNextStep() {
    console.log('🚀 Moving to Step 2...');
    console.log('🔍 Analysis results available:', !!window.lastAnalysisResult);

    // Hide Step 1 and show Step 2
    const step1Container = document.getElementById('step1-container');
    const step2Container = document.getElementById('step2-container');

    if (step1Container) {
        step1Container.style.display = 'none';
        console.log('✅ Step 1 container hidden');
    } else {
        console.error('❌ Step 1 container not found');
    }

    if (step2Container) {
        step2Container.style.display = 'block';
        console.log('✅ Step 2 container shown');

        // Update progress indicator
        updateProgressIndicator(2);
    } else {
        console.error('❌ Step 2 container not found');
    }

    // Update progress indicator (if exists)
    const step1Indicator = document.getElementById('step1-indicator');
    const step2Indicator = document.getElementById('step2-indicator');

    if (step1Indicator) {
        step1Indicator.classList.remove('active');
        step1Indicator.classList.add('completed');
    }

    if (step2Indicator) {
        step2Indicator.classList.add('active');
    }

    // Load template generation interface
    console.log('🎨 Loading template generation...');
    loadTemplateGeneration();
}

function goBackToStep1() {
    // Show Step 1 and hide Step 2
    document.getElementById('step1-container').style.display = 'block';
    document.getElementById('step2-container').style.display = 'none';

    // Update progress indicator
    updateProgressIndicator(1);
}
