/**
 * Step 1 Functions - Dataset Analysis & Query Processing
 * Extracted from real_ui.html for better organization
 */

// Status and Component Management
function updateStatusIndicator(status) {
    const indicator = document.getElementById('status-indicator');
    if (indicator) {
        indicator.textContent = status;
        indicator.className = status === 'Ready' ? 'status-ready' : 'status-loading';
    }
}

function updateComponentStatus(status) {
    const componentStatus = document.getElementById('component-status');
    if (componentStatus) {
        componentStatus.textContent = status;
        componentStatus.className = status === 'Ready' ? 'status-ready' : 'status-loading';
    }
}

// Main Analysis Function
window.analyzeQueryReal = async function analyzeQueryReal() {
    console.log('🔧 analyzeQueryReal function called!');
    
    const query = document.getElementById('query').value.trim();
    const datasetPath = document.getElementById('dataset-path').value.trim();
    
    if (!query) {
        alert('Please enter a query');
        return;
    }
    
    if (!datasetPath) {
        alert('Please enter a dataset path');
        return;
    }
    
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="loading">🔄 Analyzing query and exploring dataset...</div>';
    resultsDiv.classList.add('show');
    
    try {
        const response = await fetch('/analyze_query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                query: query,
                dataset_path: datasetPath
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Store results for Step 2
            window.analysisResults = result;
            
            try {
                displayRealAnalysisResults(result);
                populateDatasetPath(result);
            } catch (displayError) {
                console.error('Display function error:', displayError);
                resultsDiv.innerHTML = `<div class="error">Display error: ${displayError.message}</div>`;
            }
        } else {
            resultsDiv.innerHTML = `<div class="error">❌ Analysis failed: ${result.error}</div>`;
        }
    } catch (error) {
        console.error('Analysis error:', error);
        resultsDiv.innerHTML = `<div class="error">❌ Network error: ${error.message}</div>`;
    }
};

// Dataset Path Population
function populateDatasetPath(result) {
    if (result.dataset_info && result.dataset_info.dataset_path) {
        const pathInput = document.getElementById('dataset-path');
        if (pathInput && !pathInput.value.trim()) {
            pathInput.value = result.dataset_info.dataset_path;
        }
    }
}

// RAG Results HTML Generation
function generateRAGResultsHTML(ragResults) {
    if (!ragResults || !ragResults.length) {
        return '<p><em>No relevant templates found in knowledge base.</em></p>';
    }
    
    let html = '<div class="rag-results">';
    html += '<h4>📚 Relevant Templates Found:</h4>';
    
    ragResults.forEach((result, index) => {
        const score = (result.score * 100).toFixed(1);
        html += `
            <div class="rag-result-item" style="margin-bottom: 15px; padding: 12px; border: 1px solid #e9ecef; border-radius: 6px; background: #f8f9fa;">
                <div style="font-weight: bold; color: #495057; margin-bottom: 5px;">
                    📄 Template ${index + 1} (${score}% match)
                </div>
                <div style="font-size: 13px; color: #6c757d; margin-bottom: 8px;">
                    <strong>Source:</strong> ${result.metadata?.source || 'Unknown'}
                </div>
                <div style="font-size: 12px; line-height: 1.4; color: #495057;">
                    ${result.content.substring(0, 200)}${result.content.length > 200 ? '...' : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

// Analysis Results Display
function displayRealAnalysisResults(result) {
    const resultsDiv = document.getElementById('results');
    
    let html = '<div class="analysis-results">';
    
    // Domain Detection
    if (result.domain) {
        html += `
            <div class="result-section">
                <h3>🎯 Domain Detection</h3>
                <div class="domain-result">
                    <strong>Detected Domain:</strong> <span class="domain-tag">${result.domain}</span>
                </div>
            </div>
        `;
    }
    
    // RAG Results
    if (result.rag_results) {
        html += `
            <div class="result-section">
                <h3>📚 Knowledge Base Search</h3>
                ${generateRAGResultsHTML(result.rag_results)}
            </div>
        `;
    }
    
    // Dataset Information
    if (result.dataset_info) {
        html += `
            <div class="result-section">
                <h3>📊 Dataset Information</h3>
                <div class="dataset-info">
                    <p><strong>Path:</strong> ${result.dataset_info.dataset_path || 'Not specified'}</p>
                    <p><strong>Status:</strong> ${result.dataset_info.exists ? '✅ Found' : '❌ Not found'}</p>
                    ${result.dataset_info.records ? `<p><strong>Records:</strong> ${result.dataset_info.records.toLocaleString()}</p>` : ''}
                    ${result.dataset_info.variables ? `<p><strong>Variables:</strong> ${result.dataset_info.variables}</p>` : ''}
                </div>
            </div>
        `;
    }
    
    // Next Step Button
    html += `
        <div class="result-section">
            <div class="next-step-container">
                <button onclick="goToNextStep()" class="next-step-btn">
                    🚀 Continue to Template Generation →
                </button>
            </div>
        </div>
    `;
    
    html += '</div>';
    resultsDiv.innerHTML = html;
}

// Dataset Exploration
async function exploreDataset() {
    const datasetPath = document.getElementById('dataset-path').value.trim();
    
    if (!datasetPath) {
        alert('Please enter a dataset path first');
        return;
    }
    
    const exploreBtn = document.getElementById('explore-btn');
    const originalText = exploreBtn.textContent;
    exploreBtn.textContent = '🔄 Exploring...';
    exploreBtn.disabled = true;
    
    try {
        const response = await fetch('/explore_dataset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset_path: datasetPath })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Store dataset exploration results for Step 4 R execution
            window.datasetExploration = result;
            displayDatasetExploration(result);
        } else {
            displayDatasetExplorationError(result.error);
        }
    } catch (error) {
        console.error('Dataset exploration error:', error);
        displayDatasetExplorationError(error.message);
    } finally {
        exploreBtn.textContent = originalText;
        exploreBtn.disabled = false;
    }
}

// Dataset Exploration Display
function displayDatasetExploration(result) {
    const explorationDiv = document.getElementById('dataset-exploration');
    
    let html = '<div class="exploration-results">';
    html += '<h4>📊 Dataset Exploration Results</h4>';
    
    if (result.summary) {
        html += `
            <div class="exploration-section">
                <h5>📋 Summary</h5>
                <pre class="exploration-output">${result.summary}</pre>
            </div>
        `;
    }
    
    if (result.structure) {
        html += `
            <div class="exploration-section">
                <h5>🏗️ Structure</h5>
                <pre class="exploration-output">${result.structure}</pre>
            </div>
        `;
    }
    
    if (result.sample_data) {
        html += `
            <div class="exploration-section">
                <h5>🔍 Sample Data</h5>
                <pre class="exploration-output">${result.sample_data}</pre>
            </div>
        `;
    }
    
    html += '</div>';
    
    // Store dataset info for use in later steps
    if (result.dataset_info) {
        window.datasetInfo = result.dataset_info;
    }
    
    explorationDiv.innerHTML = html;
    explorationDiv.style.display = 'block';
}

function displayDatasetExplorationError(error) {
    const explorationDiv = document.getElementById('dataset-exploration');
    explorationDiv.innerHTML = `
        <div class="exploration-error">
            <h4>❌ Exploration Failed</h4>
            <p>${error}</p>
        </div>
    `;
    explorationDiv.style.display = 'block';
}

// Navigation Functions
function goToNextStep() {
    console.log('🚀 Moving to Step 2...');
    
    // Hide Step 1 and show Step 2
    document.getElementById('step1-container').style.display = 'none';
    document.getElementById('step2-container').style.display = 'block';
    
    // Update progress indicator
    updateProgressIndicator(2);
    
    // Load template generation
    loadTemplateGeneration();
}

function goBackToStep1() {
    // Show Step 1 and hide Step 2
    document.getElementById('step1-container').style.display = 'block';
    document.getElementById('step2-container').style.display = 'none';
    
    // Update progress indicator
    updateProgressIndicator(1);
}
