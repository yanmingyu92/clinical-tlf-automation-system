// ===== MAIN APPLICATION SCRIPT =====
// Clinical TLF Automation - Main JavaScript Module
// Extracted from real_ui.html for better organization

// ===== MODULAR JAVASCRIPT ARCHITECTURE =====
// Most functions have been moved to separate JS files:
// - js/utilities.js: Common helper functions
// - js/navigation-functions.js: Navigation and progress management
// - js/step1-functions.js: Dataset analysis functions
// - js/step2-functions.js: Template generation functions
// - js/step3-functions.js: R code generation functions
// - js/step4-functions.js: Code execution and AI assistant functions

// Global variables (declared once for entire application)
var isExecuting = false;
var interactiveSession = false;

// Status check function
function checkStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            const statusText = document.getElementById('status-text');
            const statusDot = document.getElementById('status-dot');

            if (data.status === 'ready') {
                statusText.textContent = '✅ Real AI backend ready';
                statusText.style.color = '#28a745';
                statusDot.classList.add('ready');

                // Update global variables for main script
                if (typeof window.backendStatus !== 'undefined') {
                    window.backendStatus = 'ready';
                    window.realComponents = data.components;
                }

                // Update component status
                const componentDiv = document.getElementById('component-status');
                if (componentDiv) {
                    componentDiv.innerHTML = `
                        <strong>✅ Real AI Components Status:</strong><br>
                        • MultiLLMClient: ${data.components.llm_client ? '✅ Loaded' : '❌ Failed'}<br>
                        • RAG System: ${data.components.rag_system ? '✅ Loaded' : '❌ Failed'}<br>
                        • Dataset Explorer: ${data.components.llm_client ? '✅ Available' : '❌ Failed'}<br>
                        • Debug Agent: ${data.components.llm_client ? '✅ Available' : '❌ Failed'}<br>
                        <strong>🎯 Ready for real AI analysis!</strong>
                    `;
                    componentDiv.style.background = '#d4edda';
                    componentDiv.style.border = '1px solid #28a745';
                }
            } else if (data.status === 'initializing') {
                statusText.textContent = '🔄 Initializing real AI components...';
                statusText.style.color = '#ffc107';
                statusDot.classList.remove('ready');
            } else {
                statusText.textContent = '❌ Backend connection error';
                statusText.style.color = '#dc3545';
                statusDot.classList.remove('ready');
            }
        })
        .catch(error => {
            console.error('Status check failed:', error);
            const statusText = document.getElementById('status-text');
            statusText.textContent = '❌ Connection error';
            statusText.style.color = '#dc3545';
            document.getElementById('status-dot').classList.remove('ready');
        });
}

// LLM Provider Management Functions
function loadLLMProviders() {
    fetch('/get_llm_providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const select = document.getElementById('llm-provider');
            const status = document.getElementById('llm-status');

            // Clear existing options
            select.innerHTML = '';

            // Add available providers
            data.available_providers.forEach(provider => {
                const option = document.createElement('option');
                option.value = provider;
                option.textContent = provider === 'deepseek' ? 'DeepSeek (Fast & Reliable)' :
                                   provider === 'claude' ? 'Claude (Advanced Reasoning)' : provider;
                if (provider === data.current_provider) {
                    option.selected = true;
                }
                select.appendChild(option);
            });

            status.textContent = `Current: ${data.current_provider} | Available: ${data.available_providers.join(', ')}`;
        } else {
            document.getElementById('llm-status').textContent = 'Error loading providers';
        }
    })
    .catch(error => {
        console.error('Failed to load LLM providers:', error);
        document.getElementById('llm-status').textContent = 'Failed to load providers';
    });
}

function changeLLMProvider() {
    const select = document.getElementById('llm-provider');
    const provider = select.value;

    fetch('/set_llm_provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: provider })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('llm-status').textContent = `✅ Changed to ${provider}`;
            console.log(`LLM provider changed to: ${provider}`);

            // CRITICAL FIX: Update Step 4 provider indicator when user changes provider
            if (typeof updateStep4ProviderIndicator === 'function') {
                updateStep4ProviderIndicator(provider);
            }
        } else {
            document.getElementById('llm-status').textContent = `❌ Failed to change provider`;
            console.error('Failed to change LLM provider:', data.error);
        }
    })
    .catch(error => {
        console.error('Error changing LLM provider:', error);
        document.getElementById('llm-status').textContent = `❌ Error changing provider`;
    });
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Run status check immediately and then every 30 seconds
    checkStatus();
    setInterval(checkStatus, 30000);

    // Debug and fix button states
    setTimeout(function() {
        const analyzeBtn = document.getElementById('analyze-btn');
        if (analyzeBtn) {
            console.log('🔧 Analyze button state:', {
                disabled: analyzeBtn.disabled,
                textContent: analyzeBtn.textContent,
                style: analyzeBtn.style.cssText
            });

            // Force enable the button if it's disabled
            if (analyzeBtn.disabled) {
                console.log('🔧 Forcing button to be enabled...');
                analyzeBtn.disabled = false;
                analyzeBtn.textContent = '🔬 Analyze Query with Real AI';
                analyzeBtn.style.background = '';
            }
        }
    }, 2000);

    // Load LLM providers when page loads
    setTimeout(loadLLMProviders, 3000);
});
