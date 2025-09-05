/**
 * Step 4 Functions - Code Execution & Interactive AI Assistant
 * Extracted from real_ui.html for better organization
 */

console.log('🔍 STEP 4 FUNCTIONS: File is being loaded...');
console.log('🔍 STEP 4 FUNCTIONS: Starting to define functions...');

// Global variables for persistent SSE mode
window.persistentModeActive = false;
window.persistentSessionId = null;
window.persistentConnection = null;
window.lastHeartbeatTime = null;

/**
 * Send message through existing persistent SSE connection
 * This avoids creating new HTTP requests for follow-up messages
 */
function sendMessageThroughPersistentConnection(message) {
    console.log('🔄 PERSISTENT SSE: *** ENTERING PERSISTENT CONNECTION HANDLER ***');
    console.log('🔄 PERSISTENT SSE: Message:', message);
    console.log('🔄 PERSISTENT SSE: Session ID:', window.persistentSessionId);
    console.log('🔄 PERSISTENT SSE: Current execution state:', window.isExecuting);

    // Check if we're already executing
    if (window.isExecuting) {
        console.error('🔄 PERSISTENT SSE: Already executing, aborting follow-up request');
        addInteractiveMessage('⚠️ Please wait for current execution to complete', 'system');
        return;
    }

    // For now, we need to implement a different approach since SSE is unidirectional
    // We'll create a new request but reuse the session ID
    console.log('🔄 PERSISTENT SSE: Creating new request with persistent session ID');

    // Update UI to show processing
    console.log('🔄 PERSISTENT SSE: Updating UI for follow-up request...');
    updateExecutionStatus(true);
    addInteractiveMessage(message, 'user');
    addInteractiveMessage('💭 Analyzing your request...', 'assistant');

    // Create new request but with persistent session ID
    console.log('🔄 PERSISTENT SSE: Calling sendInteractiveMessageWithPersistentSession...');
    sendInteractiveMessageWithPersistentSession(message, window.persistentSessionId);
}

/**
 * Send message with persistent session ID (reuse existing session)
 */
async function sendInteractiveMessageWithPersistentSession(message, sessionId) {
    console.log('🔄 PERSISTENT SSE: Sending message with persistent session');
    console.log('🔄 PERSISTENT SSE: Message:', message);
    console.log('🔄 PERSISTENT SSE: Reusing session ID:', sessionId);

    try {
        // Reset persistent mode flags for this new request
        window.sessionReadyReceived = false;

        // Get current R code
        const currentCode = getCurrentCode();
        console.log('🔄 PERSISTENT SSE: Current R code length:', currentCode.length);

        // Prepare request body with persistent session ID
        const requestBody = {
            message: message,
            context: {
                execution_id: sessionId,  // Reuse the persistent session ID
                step: 'step4_interactive',
                r_code: currentCode,
                dataset_info: null,
                template_info: null
            }
        };

        console.log('🔄 PERSISTENT SSE: Request body prepared');
        console.log('🔄 PERSISTENT SSE: Execution ID (reused):', sessionId);

        // Create new HTTP request (but reuse session on backend)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            console.error('🔄 PERSISTENT SSE: Request timeout after 2 minutes');
            controller.abort();
        }, 120000);

        console.log('🔄 PERSISTENT SSE: About to send fetch request...');
        console.log('🔄 PERSISTENT SSE: URL: /api/step4/interactive/chat');
        console.log('🔄 PERSISTENT SSE: Method: POST');
        console.log('🔄 PERSISTENT SSE: Request body:', JSON.stringify(requestBody, null, 2));

        const response = await fetch('/api/step4/interactive/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        console.log('🔄 PERSISTENT SSE: Fetch response received');
        console.log('🔄 PERSISTENT SSE: Response status:', response.status);
        console.log('🔄 PERSISTENT SSE: Response ok:', response.ok);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        console.log('🔄 PERSISTENT SSE: Response OK, processing stream...');

        // Process the response stream (same as regular requests)
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const event = JSON.parse(line.slice(6));

                        // DIAGNOSTIC: Log all events to see if persistent_mode is received
                        console.log('🔄 PERSISTENT SSE: Event received:', event.type);
                        if (event.type === 'persistent_mode') {
                            console.log('🔄 PERSISTENT SSE: *** PERSISTENT_MODE EVENT DETECTED ***');
                            console.log('🔄 PERSISTENT SSE: Event data:', event);
                        }

                        handleStreamEventJS(event);
                    } catch (e) {
                        console.error('🔄 PERSISTENT SSE: Error parsing event:', e);
                    }
                }
            }
        }

        console.log('🔄 PERSISTENT SSE: Stream processing completed');

    } catch (error) {
        console.error('🔄 PERSISTENT SSE: *** ERROR IN PERSISTENT REQUEST ***');
        console.error('🔄 PERSISTENT SSE: Error type:', error.constructor.name);
        console.error('🔄 PERSISTENT SSE: Error message:', error.message);
        console.error('🔄 PERSISTENT SSE: Error stack:', error.stack);
        console.error('🔄 PERSISTENT SSE: Session ID:', sessionId);
        console.error('🔄 PERSISTENT SSE: Request body was:', JSON.stringify(requestBody, null, 2));

        addInteractiveMessage(`❌ **Persistent Request Failed** - ${error.message}`, 'system');
        addInteractiveMessage(`🔍 **Debug Info**: Session ID: ${sessionId}, Error: ${error.constructor.name}`, 'system');
        updateExecutionStatus(false);
    }
}

// BASIC TEST FUNCTION - Check if JavaScript is working
function testStep4Basic() {
    console.log('🧪 BASIC TEST: Step 4 JavaScript is working');
    alert('🧪 Step 4 JavaScript is working!');

    // Test if we can find the editor element
    const editor = document.getElementById('step4-rcode-editor');
    console.log('🧪 BASIC TEST: Editor element found:', !!editor);

    if (editor) {
        editor.value = '# TEST R CODE\nprint("Hello from Step 4!")';
        console.log('🧪 BASIC TEST: Test R code loaded into editor');
    }

    return true;
}

// Make test function globally available
window.testStep4Basic = testStep4Basic;

// SIMPLE TEST FUNCTION - Test if we can send a message
function testSimpleMessage() {
    console.log('🧪 SIMPLE TEST: Testing message sending...');

    try {
        // Test if we can call the function
        sendInteractiveMessageWithText('test message');
        console.log('🧪 SIMPLE TEST: sendInteractiveMessageWithText called successfully');
    } catch (error) {
        console.error('🧪 SIMPLE TEST: Error calling sendInteractiveMessageWithText:', error);
        alert(`Test Error: ${error.message}`);
    }
}

// Make test function globally available
window.testSimpleMessage = testSimpleMessage;

// MINIMAL WORKING SOLUTION - Just get R code into editor
function minimalRCodeTest() {
    console.log('🧪 MINIMAL TEST: Loading sample R code into editor...');

    const sampleRCode = `# Kaplan-Meier Survival Plot
library(survival)
library(survminer)

# Sample survival data
data(lung)

# Create survival object
surv_obj <- Surv(lung$time, lung$status)

# Fit Kaplan-Meier model
km_fit <- survfit(surv_obj ~ lung$sex, data = lung)

# Create Kaplan-Meier plot
ggsurvplot(km_fit,
           data = lung,
           pval = TRUE,
           conf.int = TRUE,
           risk.table = TRUE,
           title = "Kaplan-Meier Survival Curves by Sex")

# Print summary
print(summary(km_fit))`;

    // Try to load into editor
    try {
        const editor = document.getElementById('step4-rcode-editor');
        if (editor) {
            editor.value = sampleRCode;
            console.log('🧪 MINIMAL TEST: R code loaded successfully');

            // Update status
            updateCodeStatusIndicator('🧪 Test Code', '#007bff');

            // Add to chat
            addInteractiveMessage('🧪 **Test R Code Loaded** - Sample Kaplan-Meier plot code loaded into editor', 'system');

            alert('✅ Minimal test successful! R code loaded into editor.');
        } else {
            console.error('🧪 MINIMAL TEST: Editor element not found');
            alert('❌ Editor element not found');
        }
    } catch (error) {
        console.error('🧪 MINIMAL TEST: Error:', error);
        alert(`❌ Error: ${error.message}`);
    }
}

// Make minimal test globally available
window.minimalRCodeTest = minimalRCodeTest;

// MINIMAL BACKEND TEST - Test if backend responds at all
async function minimalBackendTest() {
    console.log('🧪 MINIMAL BACKEND TEST: Testing backend connectivity...');

    try {
        // Simple test request
        const response = await fetch('/api/step4/interactive/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: 'give me simple R code for hello world',
                context: {}
            })
        });

        console.log('🧪 BACKEND TEST: Response status:', response.status);
        console.log('🧪 BACKEND TEST: Response ok:', response.ok);

        if (response.ok) {
            // Try to read as text first
            const text = await response.text();
            console.log('🧪 BACKEND TEST: Response text:', text.substring(0, 200));

            addInteractiveMessage('🧪 **Backend Test** - Got response from backend!', 'system');
            alert('✅ Backend is responding!');
        } else {
            console.error('🧪 BACKEND TEST: Bad response status:', response.status);
            alert(`❌ Backend error: ${response.status}`);
        }

    } catch (error) {
        console.error('🧪 BACKEND TEST: Error:', error);
        alert(`❌ Backend connection error: ${error.message}`);
    }
}

// Make backend test globally available
window.minimalBackendTest = minimalBackendTest;

// COMPREHENSIVE TEST - Test everything step by step
async function comprehensiveTest() {
    console.log('🧪 COMPREHENSIVE TEST: Starting full system test...');

    let results = [];

    // Test 1: JavaScript Loading
    try {
        console.log('🧪 TEST 1: JavaScript functions...');
        if (typeof sendInteractiveMessage === 'function') {
            results.push('✅ JavaScript functions loaded');
        } else {
            results.push('❌ JavaScript functions missing');
        }
    } catch (e) {
        results.push(`❌ JavaScript error: ${e.message}`);
    }

    // Test 2: UI Elements
    try {
        console.log('🧪 TEST 2: UI elements...');
        const editor = document.getElementById('step4-rcode-editor');
        const chatInput = document.getElementById('ai-chat-input');
        const sendBtn = document.getElementById('send-message-btn');

        if (editor && chatInput && sendBtn) {
            results.push('✅ All UI elements found');
        } else {
            results.push(`❌ Missing UI elements: editor=${!!editor}, input=${!!chatInput}, button=${!!sendBtn}`);
        }
    } catch (e) {
        results.push(`❌ UI element error: ${e.message}`);
    }

    // Test 3: Backend connectivity
    try {
        console.log('🧪 TEST 3: Backend connectivity...');
        const response = await fetch('/api/step4/interactive/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: 'test', context: {} })
        });

        if (response.ok) {
            results.push('✅ Backend responding');
        } else {
            results.push(`❌ Backend error: ${response.status}`);
        }
    } catch (e) {
        results.push(`❌ Backend connection error: ${e.message}`);
    }

    // Display results
    const resultText = results.join('\n');
    console.log('🧪 COMPREHENSIVE TEST RESULTS:\n' + resultText);
    alert('🧪 Test Results:\n\n' + resultText);

    // Add to chat
    addInteractiveMessage(`🧪 **Comprehensive Test Results**\n\n${resultText}`, 'system');
}

// Make comprehensive test globally available
window.comprehensiveTest = comprehensiveTest;

// MANUAL RESET FUNCTION - For debugging execution state issues
function manualReset() {
    console.log('🔧 MANUAL RESET: Resetting execution state...');
    console.log('🔧 MANUAL RESET: Before - window.isExecuting:', window.isExecuting);

    // Force reset execution state
    window.isExecuting = false;
    updateExecutionStatus(false);
    updateExecutionProgress(100, 'Ready');

    console.log('🔧 MANUAL RESET: After - window.isExecuting:', window.isExecuting);
    console.log('🔧 MANUAL RESET: Button disabled:', document.getElementById('send-message-btn')?.disabled);
    console.log('🔧 MANUAL RESET: Input disabled:', document.getElementById('ai-chat-input')?.disabled);

    addInteractiveMessage('🔧 **Manual Reset Complete** - Ready for new queries', 'system');

    // Also add a visual indicator
    const chatInput = document.getElementById('ai-chat-input');
    if (chatInput) {
        chatInput.placeholder = '✅ Reset complete - Type your message...';
        setTimeout(() => {
            chatInput.placeholder = 'Type your message...';
        }, 3000);
    }

    alert('✅ Manual reset complete! Try sending a message now.');
}

// Make manual reset globally available
window.manualReset = manualReset;

// FUNCTION VERIFICATION TEST
function verifyFunctions() {
    console.log('🧪 VERIFICATION: Testing JavaScript functions...');

    const tests = {
        'sendInteractiveMessage': typeof window.sendInteractiveMessage,
        'sendInteractiveMessageWithText': typeof window.sendInteractiveMessageWithText,
        'streamInteractiveResponse': typeof window.streamInteractiveResponse,
        'sendQuickMessage': typeof window.sendQuickMessage
    };

    console.log('🧪 VERIFICATION: Function types:', tests);

    // Test if our function is the right one
    if (window.streamInteractiveResponse) {
        const funcStr = window.streamInteractiveResponse.toString();
        if (funcStr.includes('FRONTEND: streamInteractiveResponse called')) {
            console.log('✅ VERIFICATION: JavaScript streamInteractiveResponse is active');
            addInteractiveMessage('✅ **Function Verification Passed** - JavaScript functions are active', 'system');
        } else {
            console.error('❌ VERIFICATION: Wrong streamInteractiveResponse function is active');
            addInteractiveMessage('❌ **Function Verification Failed** - Wrong function is active', 'system');
        }
    } else {
        console.error('❌ VERIFICATION: streamInteractiveResponse not found');
        addInteractiveMessage('❌ **Function Verification Failed** - Function not found', 'system');
    }

    return tests;
}

// Make verification globally available
window.verifyFunctions = verifyFunctions;

// Global variables
let currentExecutionMode = 'local_interpreter'; // Default execution mode

// Interactive chat global variables
let currentAiResponseDiv = null;
let currentAiContent = '';

// Step 4 Initialization Functions
function loadCodeExecution() {
    console.log('🚀 STEP 4: loadCodeExecution called');
    console.log('🔍 STEP 4: window.currentRCode exists:', !!window.currentRCode);
    console.log('🔍 STEP 4: window.currentRCode length:', window.currentRCode?.length || 0);

    // Set up editor change listeners first
    setTimeout(() => {
        setupEditorChangeListener();
    }, 100);

    // Auto-load R code from Step 3 if available
    if (window.currentRCode && window.currentRCode.trim()) {
        console.log('📝 Auto-loading R code from Step 3...');
        console.log('📝 R code preview:', window.currentRCode.substring(0, 100));
        loadRCodeIntoEditor(window.currentRCode, 'step3');
        updateCodeStatusIndicator('✅ Loaded from Step 3', '#28a745');

        // CRITICAL FIX: Add a verification message to chat
        addInteractiveMessage(`✅ **R Code Loaded from Step 3** (${window.currentRCode.length} characters)\nCode is ready for analysis and debugging.`, 'system');
    } else {
        console.log('⚠️ No R code from Step 3, showing manual input mode');
        console.log('⚠️ window.currentRCode value:', window.currentRCode);
        showManualInputMode();

        // Add helpful message to chat
        addInteractiveMessage(`⚠️ **No R Code Available**\nPlease complete Step 3 first or enter R code manually in the editor above.`, 'system');
    }

    // Initialize interactive session
    initializeInteractiveSession();
}

function loadStep4Interface() {
    console.log('🚀 STEP 4: loadStep4Interface called');
    loadCodeExecution();
}

function loadRCodeOnPageLoad() {
    console.log('🚀 STEP 4: loadRCodeOnPageLoad called');

    // Only auto-load if we're currently on Step 4
    const step4Container = document.getElementById('step4-container');
    if (step4Container && step4Container.style.display !== 'none') {
        loadCodeExecution();
    }
}

// R Code Editor Management
function loadRCodeIntoEditor(rCode, source = 'manual') {
    console.log(`📝 FRONTEND: loadRCodeIntoEditor called`);
    console.log(`📝 FRONTEND: Source: ${source}`);
    console.log(`📝 FRONTEND: R code length: ${rCode ? rCode.length : 'null/undefined'}`);
    console.log(`📝 FRONTEND: R code content (first 200 chars): ${rCode ? rCode.substring(0, 200) : 'null/undefined'}`);

    if (!rCode) {
        console.error(`📝 FRONTEND: No R code provided to loadRCodeIntoEditor`);
        return;
    }

    const editor = document.getElementById('step4-rcode-editor');
    console.log(`📝 FRONTEND: Editor element found: ${!!editor}`);
    console.log(`📝 FRONTEND: Editor element:`, editor);

    if (editor) {
        console.log(`📝 FRONTEND: Setting editor value...`);
        editor.value = rCode;
        console.log(`📝 FRONTEND: Editor value set. Current length: ${editor.value.length}`);
        console.log(`📝 FRONTEND: Editor value preview: ${editor.value.substring(0, 100)}`);

        // CRITICAL FIX: Immediately update global variable to ensure AI can access the code
        window.currentRCode = rCode;
        console.log(`📝 FRONTEND: Updated window.currentRCode (${rCode.length} chars)`);

        // Trigger change event to update any listeners
        editor.dispatchEvent(new Event('change'));

        // Update the display to show code is loaded
        const statusDiv = document.getElementById('code-status-indicator');
        console.log(`📝 FRONTEND: Status div found: ${!!statusDiv}`);

        if (statusDiv) {
            let sourceText = 'manual input';
            if (source === 'step3') sourceText = 'Step 3';
            else if (source === 'ai_generated') sourceText = 'AI Assistant';

            statusDiv.innerHTML = `✅ ${sourceText} (${rCode.length} chars)`;
            statusDiv.style.display = 'block';
            statusDiv.style.background = '#28a745';
            console.log(`📝 FRONTEND: Status div updated with source: ${sourceText}`);
        } else {
            console.warn(`📝 FRONTEND: Status div not found: code-status-indicator`);
        }
    } else {
        console.error(`📝 FRONTEND: Editor element not found: step4-rcode-editor`);
        console.error(`📝 FRONTEND: Available elements with 'step4' in id:`,
            Array.from(document.querySelectorAll('[id*="step4"]')).map(el => el.id));
    }
}

function showManualInputMode() {
    console.log('📝 Showing manual input mode');
    
    const statusDiv = document.getElementById('step4-code-status');
    if (statusDiv) {
        statusDiv.innerHTML = `
            <div class="code-status-manual">
                💡 No R code from previous steps. Enter your R code manually or 
                <button onclick="loadFromStep3()" class="btn-link">load from Step 3</button>
            </div>
        `;
    }
}

function loadFromStep3() {
    console.log('🔄 Attempting to load R code from Step 3...');
    
    if (window.currentRCode) {
        loadRCodeIntoEditor(window.currentRCode, 'step3');
    } else {
        alert('❌ No R code available from Step 3. Please complete Step 3 first or enter code manually.');
    }
}

function clearRCodeEditor() {
    console.log('🗑️ Clearing R code editor');
    
    const editor = document.getElementById('step4-rcode-editor');
    if (editor) {
        editor.value = '';
        showManualInputMode();
    }
}

// Interactive AI Assistant Functions
// Note: initializeInteractiveSession() is defined in real_ui.html

function sendInteractiveMessage() {
    const input = document.getElementById('ai-chat-input');
    const message = input.value.trim();

    if (message) {
        sendInteractiveMessageWithText(message);
        input.value = '';
    }
}

function sendQuickMessage(message) {
    sendInteractiveMessageWithText(message);
}

// DIAGNOSTIC FUNCTION: Debug code transfer to AI
function debugCodeTransfer() {
    console.log('🔧 DEBUG: Checking code transfer to AI...');

    const editor = document.getElementById('step4-rcode-editor');
    const currentCode = getCurrentCode();

    console.log('🔧 DEBUG: Editor element:', !!editor);
    console.log('🔧 DEBUG: Editor value length:', editor?.value?.length || 0);
    console.log('🔧 DEBUG: Editor value preview:', editor?.value?.substring(0, 100) || 'EMPTY');
    console.log('🔧 DEBUG: window.currentRCode length:', window.currentRCode?.length || 0);
    console.log('🔧 DEBUG: getCurrentCode() length:', currentCode.length);
    console.log('🔧 DEBUG: getCurrentCode() preview:', currentCode.substring(0, 100) || 'EMPTY');

    // Create detailed diagnostic message
    let diagnosticInfo = `🔧 **DIAGNOSTIC REPORT**\n`;
    diagnosticInfo += `- Editor found: ${!!editor}\n`;
    diagnosticInfo += `- Editor has content: ${!!(editor?.value?.trim())}\n`;
    diagnosticInfo += `- Editor content length: ${editor?.value?.length || 0}\n`;
    diagnosticInfo += `- Global currentRCode length: ${window.currentRCode?.length || 0}\n`;
    diagnosticInfo += `- getCurrentCode() length: ${currentCode.length}\n`;

    if (currentCode.length > 0) {
        diagnosticInfo += `- Code preview: "${currentCode.substring(0, 100)}..."\n`;

        // FIXED: Include the actual code in the test message
        const debugMessage = `🔧 **CODE TRANSFER TEST** - Can you see this R code?

Here is the R code that should be loaded in the editor:

\`\`\`r
${currentCode}
\`\`\`

Please confirm:
1. Can you see the complete R code above?
2. How many lines does it contain?
3. What does this code do?

This is a test to verify the code transfer mechanism is working properly.`;

        addInteractiveMessage(diagnosticInfo, 'system');
        addInteractiveMessage(`🔧 **Sending test message with actual code to AI...**`, 'system');

        sendInteractiveMessageWithText(debugMessage);
    } else {
        diagnosticInfo += `- ❌ NO CODE FOUND! This is the problem.\n`;
        diagnosticInfo += `- Try loading R code from Step 3 first.\n`;

        addInteractiveMessage(diagnosticInfo, 'system');

        // Try to load sample code for testing
        const sampleCode = `# Sample R code for testing
library(dplyr)
data <- mtcars
summary(data)`;

        if (editor) {
            editor.value = sampleCode;
            window.currentRCode = sampleCode;
            addInteractiveMessage(`🔧 **Loaded sample R code for testing**`, 'system');

            // Now test again
            setTimeout(() => {
                const testMessage = `Debug request: I just loaded sample R code. Can you see it now?`;
                sendInteractiveMessageWithText(testMessage);
            }, 1000);
        }
    }
}

// Make debug function globally available
window.debugCodeTransfer = debugCodeTransfer;

// ENHANCED DEBUG FUNCTION: Debug current R code with force refresh
function debugCurrentCode() {
    console.log('🔧 DEBUG: Enhanced debug current R code...');

    // Force refresh the current code state
    const editor = document.getElementById('step4-rcode-editor');
    if (editor && editor.value && editor.value.trim()) {
        // Force sync global variable with editor
        window.currentRCode = editor.value.trim();
        console.log('🔧 DEBUG: Force synced window.currentRCode with editor');
    }

    const currentCode = getCurrentCode();

    if (currentCode && currentCode.trim()) {
        const debugMessage = `Please debug and analyze this R code. Look for any errors, suggest improvements, and explain what it does:

\`\`\`r
${currentCode}
\`\`\`

Please provide:
1. Code analysis and explanation
2. Any syntax or logical errors found
3. Suggestions for improvement
4. Expected output description`;

        addInteractiveMessage(`🔧 **Debugging Current R Code** (${currentCode.length} characters)\nSending code to AI for analysis...`, 'system');
        sendInteractiveMessageWithText(debugMessage);
    } else {
        addInteractiveMessage(`❌ **No R Code to Debug**\nPlease load R code from Step 3 or enter code manually in the editor above.`, 'system');

        // Try to load from Step 3 if available
        if (window.currentRCode && window.currentRCode.trim()) {
            console.log('🔧 DEBUG: Found code in global variable, loading to editor...');
            if (editor) {
                editor.value = window.currentRCode;
                addInteractiveMessage(`✅ **Loaded R code from Step 3** - Try debugging again.`, 'system');
            }
        }
    }
}

// Make enhanced debug function globally available
window.debugCurrentCode = debugCurrentCode;

// EMERGENCY FIX: Force code sync before any AI interaction
function forceCodeSync() {
    console.log('🚨 EMERGENCY: Force syncing R code...');

    const editor = document.getElementById('step4-rcode-editor');
    if (editor && editor.value && editor.value.trim()) {
        window.currentRCode = editor.value.trim();
        console.log('🚨 EMERGENCY: Synced editor to global variable:', window.currentRCode.length, 'chars');
        return editor.value.trim();
    } else if (window.currentRCode && window.currentRCode.trim()) {
        if (editor) {
            editor.value = window.currentRCode;
            console.log('🚨 EMERGENCY: Synced global variable to editor:', window.currentRCode.length, 'chars');
        }
        return window.currentRCode;
    } else {
        console.log('🚨 EMERGENCY: No R code found anywhere!');
        return '';
    }
}

// Make emergency function globally available
window.forceCodeSync = forceCodeSync;

function sendInteractiveMessageWithText(message) {
    // REFERENCE PROJECT STYLE: No forced initialization - LLM decides what to do

    console.log('🔍 FRONTEND: sendInteractiveMessageWithText called with:', message);
    console.log('🔍 FRONTEND: Current window.isExecuting state:', window.isExecuting);
    console.log('🔍 FRONTEND: Current UI state - button disabled:', document.getElementById('send-message-btn')?.disabled);
    console.log('🔍 FRONTEND: Current UI state - input disabled:', document.getElementById('ai-chat-input')?.disabled);

    // DEBUG: Check current code state
    const currentCode = getCurrentCode();
    console.log('🔍 FRONTEND: Current code length:', currentCode.length);
    console.log('🔍 FRONTEND: Current code preview:', currentCode.substring(0, 100));
    console.log('🔍 FRONTEND: window.currentRCode exists:', !!window.currentRCode);
    console.log('🔍 FRONTEND: Editor element exists:', !!document.getElementById('step4-rcode-editor'));
    console.log('🔍 FRONTEND: Editor has content:', !!document.getElementById('step4-rcode-editor')?.value);

    // PERSISTENT SSE: Check if we should use existing persistent connection
    if (window.persistentModeActive && window.persistentSessionId) {
        console.log('🔄 FRONTEND: *** PERSISTENT MODE DETECTED ***');
        console.log('🔄 FRONTEND: Using persistent session for follow-up request');
        console.log('🔄 FRONTEND: Persistent session ID:', window.persistentSessionId);
        console.log('🔄 FRONTEND: Message:', message);
        console.log('🔄 FRONTEND: Calling sendMessageThroughPersistentConnection...');

        // Use persistent connection instead of new HTTP request
        sendMessageThroughPersistentConnection(message);
        return;
    } else {
        console.log('🔄 FRONTEND: Persistent mode check:');
        console.log('🔄 FRONTEND: persistentModeActive:', window.persistentModeActive);
        console.log('🔄 FRONTEND: persistentSessionId:', window.persistentSessionId);
        console.log('🔄 FRONTEND: Will use regular request flow');
    }

    // Check if already executing (this might be blocking subsequent requests)
    if (window.isExecuting) {
        console.error('🚨 FRONTEND: EXECUTION BLOCKED - Already executing!');
        console.error('🚨 FRONTEND: Current window.isExecuting state:', window.isExecuting);
        console.error('🚨 FRONTEND: Send button state:', document.getElementById('send-message-btn')?.disabled);
        console.error('🚨 FRONTEND: Chat input state:', document.getElementById('ai-chat-input')?.disabled);
        console.error('🚨 FRONTEND: Session ready received:', window.sessionReadyReceived);
        console.error('🚨 FRONTEND: Current execution ID:', window.currentExecutionId);
        console.error('🚨 FRONTEND: This is blocking follow-up requests!');

        // DIAGNOSTIC: Force reset if stuck for debugging
        console.error('🚨 FRONTEND: DIAGNOSTIC - Forcing reset of execution state');
        window.isExecuting = false;
        updateExecutionStatus(false);
        console.error('🚨 FRONTEND: DIAGNOSTIC - Execution state force reset, trying request again');

        // Don't return - let the request proceed after reset
        // addInteractiveMessage('⚠️ Please wait for current execution to complete', 'system');
        // return;
    }

    // Test basic functionality first
    try {
        // Add user message to chat
        console.log('🔍 FRONTEND: Adding user message to chat...');
        addInteractiveMessage(`👤 You\n${message}`, 'user');
        console.log('🔍 FRONTEND: User message added successfully');

        // Update UI state
        console.log('🔍 FRONTEND: Updating UI state...');
        updateExecutionStatus(true);
        updateExecutionProgress(5, 'Processing request...');
        console.log('🔍 FRONTEND: UI state updated successfully');

        // Stream the response
        console.log('🔍 FRONTEND: Starting stream response...');
        streamInteractiveResponse(message);
        console.log('🔍 FRONTEND: Stream response initiated');

    } catch (error) {
        console.error('🔍 FRONTEND: Error in sendInteractiveMessageWithText:', error);
        alert(`Frontend Error: ${error.message}`);
    }
}

// Function to update R code from editor changes
function updateRCodeFromEditor() {
    const editor = document.getElementById('step4-rcode-editor');
    if (editor && editor.value.trim()) {
        // Store current code globally
        if (typeof window !== 'undefined') {
            window.currentRCode = editor.value.trim();
            console.log(`📝 Updated global R code from editor (${editor.value.trim().length} chars)`);
        }

        // Update status indicator
        const statusIndicator = document.getElementById('code-status-indicator');
        if (statusIndicator) {
            statusIndicator.style.display = 'block';
        }
    }
}

// Auto-update R code when editor content changes
function setupEditorChangeListener() {
    const editor = document.getElementById('step4-rcode-editor');
    if (editor) {
        // Remove existing listeners to prevent duplicates
        editor.removeEventListener('input', updateRCodeFromEditor);
        editor.removeEventListener('change', updateRCodeFromEditor);

        // Add fresh listeners
        editor.addEventListener('input', updateRCodeFromEditor);
        editor.addEventListener('change', updateRCodeFromEditor);
        console.log('✅ Editor change listeners set up');

        // CRITICAL FIX: Immediately sync current editor content with global variable
        if (editor.value && editor.value.trim()) {
            window.currentRCode = editor.value.trim();
            console.log(`✅ Synced existing editor content with global variable (${editor.value.trim().length} chars)`);
        }
    } else {
        console.warn('⚠️ Editor element not found when setting up change listeners');
    }
}

// NDJSON Stream Reader (based on Azure DeepSeek example)
async function* readNDJSONStream(stream) {
    console.log('🔍 NDJSON reader starting...');
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let chunkCount = 0;

    try {
        while (true) {
            const { done, value } = await reader.read();
            chunkCount++;
            console.log(`🔍 NDJSON chunk ${chunkCount}: done=${done}, bytes=${value?.length || 0}`);

            if (done) {
                console.log('🔍 NDJSON stream done');
                break;
            }

            const chunk = decoder.decode(value, { stream: true });
            console.log(`🔍 NDJSON decoded chunk ${chunkCount}:`, JSON.stringify(chunk.substring(0, 100)));

            buffer += chunk;
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            console.log(`🔍 NDJSON processing ${lines.length} lines from chunk ${chunkCount}`);

            for (const line of lines) {
                if (line.trim()) {
                    console.log('🔍 NDJSON parsing line:', JSON.stringify(line.substring(0, 100)));
                    try {
                        const parsed = JSON.parse(line);
                        console.log('🔍 NDJSON parsed successfully:', parsed.type);
                        yield parsed;
                    } catch (e) {
                        console.warn('❌ Failed to parse JSON line:', line, 'Error:', e.message);
                    }
                }
            }
        }
    } finally {
        console.log('🔍 NDJSON reader cleanup');
        reader.releaseLock();
    }
}

// Generate unique execution ID for session isolation
function generateUniqueExecutionId() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '').slice(0, 15);
    const random = Math.random().toString(36).substring(2, 8);
    return `${timestamp}_${random}`;
}

async function streamInteractiveResponse(message) {
    console.log('🔍 FRONTEND: streamInteractiveResponse called with message:', message);
    console.log('🔍 FRONTEND: Current window.isExecuting state:', window.isExecuting);

    // Ensure we have a unique execution ID for this session
    console.log(`🔍 FRONTEND: Current execution ID before check: ${window.currentExecutionId}`);
    console.log(`🔍 FRONTEND: Current session ID: ${window.currentSessionId}`);

    if (!window.currentExecutionId) {
        window.currentExecutionId = generateUniqueExecutionId();
        console.log(`📁 FRONTEND: Generated new execution ID: ${window.currentExecutionId}`);
    } else {
        console.log(`🔄 FRONTEND: Using existing execution ID: ${window.currentExecutionId}`);
    }

    try {
        // Check if we're already executing (this might be the issue)
        if (window.isExecuting) {
            console.error('🚨 FRONTEND: EXECUTION BLOCKED - Already executing in sendInteractiveMessageWithText!');
            console.error('🚨 FRONTEND: Current window.isExecuting state:', window.isExecuting);
            console.error('🚨 FRONTEND: Send button state:', document.getElementById('send-message-btn')?.disabled);
            console.error('🚨 FRONTEND: Chat input state:', document.getElementById('ai-chat-input')?.disabled);
            console.error('🚨 FRONTEND: Session ready received:', window.sessionReadyReceived);

            // DIAGNOSTIC: Force reset if stuck for debugging
            console.error('🚨 FRONTEND: DIAGNOSTIC - Forcing reset of execution state in sendInteractiveMessageWithText');
            window.isExecuting = false;
            updateExecutionStatus(false);
            console.error('🚨 FRONTEND: DIAGNOSTIC - Execution state force reset, trying request again');

            // Don't return - let the request proceed after reset
            // addInteractiveMessage('⚠️ Please wait for current execution to complete', 'system');
            // return;
        }

        // Set executing state - FIXED: Use updateExecutionStatus to keep flag and UI in sync
        console.log('🔍 FRONTEND: Setting execution state to true');

        // SAFETY: Auto-reset execution state after 3 minutes to prevent permanent stuck state
        window.currentSafetyTimeoutId = setTimeout(() => {
            if (window.isExecuting) {
                console.warn('🚨 SAFETY: Auto-resetting stuck execution state after 3 minutes');
                window.isExecuting = false;
                updateExecutionStatus(false);
                updateExecutionProgress(0, 'Reset - Ready');
                addInteractiveMessage('🚨 **Safety Reset**: Execution state was reset after 3 minutes. You can try again.', 'system');
            }
        }, 180000); // 3 minute safety timeout

        // Reset global AI response variables for new conversation
        console.log('🔍 FRONTEND: Resetting global variables...');
        currentAiResponseDiv = null;
        currentAiContent = '';
        window.sessionReadyReceived = false; // Reset session ready flag

        // Add thinking indicator that will be replaced when content arrives
        console.log('🔍 FRONTEND: Adding thinking indicator...');
        addInteractiveMessage('🤖 AI Assistant<br>💭 Analyzing your request...', 'ai');

        // Update execution log
        console.log('🔍 FRONTEND: Updating execution log...');
        addExecutionLogEntry(`🤖 Processing: ${message.substring(0, 50)}...`, '#6f42c1');

        console.log('🔍 FRONTEND: Making fetch request to /api/step4/interactive/chat...');

        // CRITICAL DEBUG: Get current code and log it
        const currentCode = getCurrentCode();
        console.log('🔍 FRONTEND: Current code from getCurrentCode():', currentCode.length, 'chars');
        console.log('🔍 FRONTEND: Current code preview:', currentCode.substring(0, 100));

        // ENHANCED DEBUG: Check all possible sources of R code
        const editor = document.getElementById('step4-rcode-editor');
        console.log('🔍 FRONTEND: Editor element exists:', !!editor);
        console.log('🔍 FRONTEND: Editor value length:', editor?.value?.length || 0);
        console.log('🔍 FRONTEND: Editor value preview:', editor?.value?.substring(0, 100) || 'EMPTY');
        console.log('🔍 FRONTEND: window.currentRCode length:', window.currentRCode?.length || 0);
        console.log('🔍 FRONTEND: window.currentRCode preview:', window.currentRCode?.substring(0, 100) || 'EMPTY');

        // CRITICAL FIX: If getCurrentCode() returns empty but editor has content, force sync
        if (!currentCode && editor?.value?.trim()) {
            console.log('🔍 FRONTEND: CRITICAL FIX - getCurrentCode() empty but editor has content, forcing sync...');
            window.currentRCode = editor.value.trim();
            const fixedCode = getCurrentCode();
            console.log('🔍 FRONTEND: After force sync, getCurrentCode() length:', fixedCode.length);
        }

        // EMERGENCY FIX: Force code sync before sending to AI
        const emergencyCode = forceCodeSync();
        console.log('🚨 FRONTEND: Emergency code sync result:', emergencyCode.length, 'chars');

        // CRITICAL FIX: Get the most current code after any fixes
        const finalCurrentCode = emergencyCode || getCurrentCode();

        // SIMPLEST FIX: Just copy what works from debugCodeTransfer
        let enhancedMessage = message;

        // Add code directly to message like debugCodeTransfer does
        if (finalCurrentCode && finalCurrentCode.trim()) {
            enhancedMessage += `\n\nCurrent R code in editor:\n\`\`\`r\n${finalCurrentCode}\n\`\`\``;
            console.log('🔍 FRONTEND: Added code to message text (simple approach)');
        }

        const requestBody = {
            message: enhancedMessage,
            context: {
                dataset_path: window.currentDatasetPath || '',
                current_code: finalCurrentCode,
                execution_history: window.executionHistory || [],
                step: 'step4_interactive',
                // Enhanced context for better AI understanding
                dataset_info: window.datasetExplorationResult || null,
                template_info: window.currentTemplate || null,
                code_version_history: window.codeVersionHistory || [],
                last_execution_result: window.lastExecutionData || null,
                // Session management for robust file handling - use consistent session directory
                execution_id: window.currentExecutionId,
                session_directory: `outputs/execution_${window.currentExecutionId}`,
                session_isolation: true
            }
        };
        console.log('🔍 FRONTEND: Request body context.current_code length:', requestBody.context.current_code.length);
        console.log('🔍 FRONTEND: Full request body:', requestBody);

        // Add timeout to prevent hanging - increased to 2 minutes for complex R code execution
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            console.error('🔍 FRONTEND: Fetch request timeout after 2 minutes');
            controller.abort();
        }, 120000); // 2 minute timeout to match backend

        const response = await fetch('/api/step4/interactive/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
            signal: controller.signal
        });

        clearTimeout(timeoutId); // Clear timeout if request succeeds

        console.log('🔍 FRONTEND: Fetch response received:', response);
        console.log('🔍 FRONTEND: Response status:', response.status);
        console.log('🔍 FRONTEND: Response ok:', response.ok);

        console.log('✅ Response status:', response.status);
        console.log('✅ Response content-type:', response.headers.get('content-type'));

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Handle Server-Sent Events stream
        console.log('🔍 FRONTEND: Creating SSE stream reader...');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        console.log('🔍 FRONTEND: Starting SSE stream reading loop...');
        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                console.log('🔍 FRONTEND: SSE stream completed');
                break;
            }

            console.log('🔍 FRONTEND: Received SSE chunk, size:', value.length);

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;

            // Process complete SSE events
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const eventData = line.substring(6); // Remove 'data: ' prefix
                    if (eventData.trim()) {
                        try {
                            const event = JSON.parse(eventData);
                            const contentPreview = event.content && typeof event.content === 'string' ? event.content.substring(0, 30) : '(no content)';
                            console.log('🔍 FRONTEND: SSE event received:', event.type, contentPreview);
                            console.log('🔍 FRONTEND: Full event object:', event);

                            // DIAGNOSTIC: Special logging for persistent_mode events
                            if (event.type === 'persistent_mode') {
                                console.log('🔄 FRONTEND: *** PERSISTENT_MODE EVENT DETECTED IN MAIN SSE ***');
                                console.log('🔄 FRONTEND: Event data:', event);
                                console.log('🔄 FRONTEND: Session ID:', event.session_id);
                                console.log('🔄 FRONTEND: Status:', event.status);
                            }

                            // Special logging for end events
                            if (event.type === 'end') {
                                console.log('🔍 FRONTEND: END EVENT DETECTED! About to call handleStreamEventJS');
                            }

                            // Special logging for function_result events
                            if (event.type === 'function_result') {
                                console.log('🔍 FRONTEND: FUNCTION_RESULT EVENT DETECTED!');
                                console.log('🔍 FRONTEND: Event keys:', Object.keys(event));
                                console.log('🔍 FRONTEND: Has r_code:', !!event.r_code);
                                if (event.r_code) {
                                    console.log('🔍 FRONTEND: R code preview:', event.r_code.substring(0, 200));
                                }
                            }

                            handleStreamEventJS(event);

                            // Special logging after handling end events
                            if (event.type === 'end') {
                                console.log('🔍 FRONTEND: END EVENT HANDLED! UI should be reset now');
                            }
                        } catch (e) {
                            console.warn('❌ FRONTEND: Failed to parse SSE event:', typeof eventData === 'string' ? eventData.substring(0, 100) : eventData);
                            console.warn('❌ FRONTEND: Parse error:', e.message);
                            // Don't break the stream for parsing errors
                        }
                    }
                } else if (line.trim() && !line.startsWith(':')) {
                    // Handle non-SSE lines (might be direct JSON)
                    try {
                        const event = JSON.parse(line);
                        console.log('🔍 Direct JSON event received:', event.type);
                        handleStreamEventJS(event);
                    } catch (e) {
                        // Ignore non-JSON lines
                    }
                }
            }
        }

        // Stream reading completed - Check if session_ready was received
        console.log('🔍 FRONTEND: Stream reading completed');
        console.log('🔍 FRONTEND: Current execution state - window.isExecuting:', window.isExecuting);
        console.log('🔍 FRONTEND: Session ready received:', window.sessionReadyReceived);

        // CRITICAL FIX: Only reset if session_ready was NOT received (non-persistent mode)
        if (!window.sessionReadyReceived) {
            console.log('🔍 FRONTEND: Non-persistent mode - resetting UI');
            updateExecutionStatus(false);  // This also sets window.isExecuting = false
            updateExecutionProgress(100, 'Ready');

            const sendBtn = document.getElementById('send-message-btn');
            const chatInput = document.getElementById('ai-chat-input');
            if (sendBtn) {
                sendBtn.disabled = false;
                sendBtn.textContent = '🚀 Send';
            }
            if (chatInput) {
                chatInput.disabled = false;
            }
        } else {
            console.log('🔍 FRONTEND: Persistent mode - UI already reset by session_ready event');
        }

        // Clear safety timeout since execution completed normally
        if (window.currentSafetyTimeoutId) {
            clearTimeout(window.currentSafetyTimeoutId);
            window.currentSafetyTimeoutId = null;
            console.log('🔍 FRONTEND: Safety timeout cleared - execution completed normally');
        }

        // CRITICAL FIX: Don't reset session ready flag here - it should persist for next request
        // window.sessionReadyReceived = false;  // ← REMOVED: This was breaking session continuity
        console.log('🔍 FRONTEND: Stream processing completed, session ready flag preserved for next query');

    } catch (error) {
        console.error('❌ SSE stream error:', error);
        console.error('❌ Error name:', error.name);
        console.error('❌ Error message:', error.message);
        console.error('❌ Error stack:', error.stack);

        // Check specific error types
        if (error.name === 'AbortError') {
            console.error('❌ Request was aborted (timeout or manual abort)');
            addInteractiveMessage('❌ **Request Timeout** - The server took too long to respond. Please try again.', 'system');
        } else if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
            console.error('❌ Network/connection error - backend may be down');
            addInteractiveMessage('❌ **Connection Failed** - Cannot reach the backend server. Please check if the server is running.', 'system');
        } else {
            console.error('❌ Other fetch error:', error.message);
            addInteractiveMessage(`❌ **Request Error** - ${error.message}`, 'system');
        }

        // Don't try fallback - it can cause conflicts with state management
        console.log('🔄 Skipping fallback request to avoid state conflicts');
        addInteractiveMessage(`❌ Error: ${error.message}`, 'system');

        // Always re-enable UI after error so user can try again
        console.log('🔍 FRONTEND: Stream error occurred, resetting execution state');
        updateExecutionStatus(false);  // This also sets window.isExecuting = false

        // CRITICAL FIX: Force UI reset after error to ensure next query can be sent
        const sendBtn = document.getElementById('send-message-btn');
        const chatInput = document.getElementById('ai-chat-input');
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.textContent = '🚀 Send';
        }
        if (chatInput) {
            chatInput.disabled = false;
        }
        console.log('🔍 FRONTEND: Stream error reset complete');
    }
}

function handleStreamEventJS(event) {
            const eventType = event.type;
            const content = event.content || '';

            console.log('🔍 Stream event:', eventType, 'Content:', content);
            console.log('🔍 Full event object:', event);

            switch (eventType) {
                case 'system':
                    // Add system messages and update execution log
                    if (content && content.trim() && !content.includes('Iteration') && !content.includes('Analyzing')) {
                        addInteractiveMessage(`⚙️ ${content}`, 'system');
                        addExecutionLogEntry(`⚙️ ${content}`, '#17a2b8');
                    }
                    break;

                case 'content':
                    // Ignore individual content chunks - we'll use complete_content instead
                    console.log('🔍 FRONTEND: Ignoring content chunk, waiting for complete_content...');
                    break;

                case 'complete_content':
                    // Display the complete content directly (much simpler!)
                    console.log('🔍 FRONTEND: Received complete content:', content.length, 'characters');

                    // Remove thinking message if it exists
                    const chatArea = document.getElementById('ai-chat-area');
                    if (chatArea) {
                        const thinkingMessages = chatArea.querySelectorAll('.ai-message');
                        thinkingMessages.forEach(msg => {
                            if (msg.textContent.includes('💭 Analyzing your request')) {
                                msg.remove();
                            }
                        });
                    }

                    // Display the complete AI response in one message
                    addInteractiveMessage(`🤖 AI Assistant<br>${content.replace(/\n/g, '<br>')}`, 'ai');
                    console.log('✅ FRONTEND: Displayed complete content in UI');

                    // NOTE: Don't reset execution state here - wait for 'end' event
                    break;

                case 'function_start':
                    addInteractiveMessage(`🔧 Executing: ${event.function_name}`, 'system');
                    addExecutionLogEntry(`🔧 Starting: ${event.function_name}`, '#ffc107');
                    updateExecutionProgress(25, 'Executing function...');

                    // Store function call info for later extraction
                    if (event.function_name === 'execute_r_code') {
                        window.lastFunctionCall = {
                            name: event.function_name,
                            arguments: event.arguments || null,
                            timestamp: new Date().toISOString()
                        };
                        console.log('🔍 Stored function call for R code extraction:', window.lastFunctionCall);
                    }
                    break;

                case 'code_preview':
                case 'code_final':
                    // Handle R code display from AI function calls
                    if (event.code) {
                        console.log('🔍 Received R code from AI:', event.code.substring(0, 100));

                        // Load the code into the editor immediately
                        loadRCodeIntoEditor(event.code, 'ai_generated');
                        addCodeVersion(event.code, 'AI Generated', 'Code generated by AI assistant', 1);
                        window.currentRCode = event.code;

                        addInteractiveMessage(`📝 R code loaded into editor (${event.code.length} chars)`, 'system');
                        addExecutionLogEntry(`📝 R code loaded into editor`, '#6f42c1');
                    }
                    break;

                case 'function_result':
                    console.log('🔍 FRONTEND: Function result event received:', event);
                    console.log('🔍 FRONTEND: Event keys:', Object.keys(event));
                    console.log('🔍 FRONTEND: Function name:', event.function_name);
                    console.log('🔍 FRONTEND: Has r_code field:', !!event.r_code);

                    addInteractiveMessage(`✅ Function completed: ${event.function_name}`, 'system');
                    addExecutionLogEntry(`✅ Completed: ${event.function_name}`, '#28a745');
                    updateExecutionProgress(75, 'Processing results...');

                    // Load R code into editor if available
                    if (event.function_name === 'execute_r_code') {
                        console.log('🔍 FRONTEND: Processing execute_r_code function result');

                        if (event.r_code) {
                            console.log('🔍 FRONTEND: Found R code, loading into editor:', event.r_code.substring(0, 100));

                            // CRITICAL FIX: Force editor update
                            const editor = document.getElementById('step4-rcode-editor');
                            if (editor) {
                                editor.value = event.r_code;
                                console.log('🔍 FRONTEND: Editor value updated directly');
                            }

                            // Also use the existing function
                            loadRCodeIntoEditor(event.r_code, 'ai_generated');
                            addCodeVersion(event.r_code, 'AI Generated', 'Code generated by AI assistant', 1);
                            window.currentRCode = event.r_code;

                            addInteractiveMessage(`📝 R code loaded into editor (${event.r_code.length} chars)`, 'system');
                            addExecutionLogEntry(`📝 R code loaded into editor`, '#6f42c1');
                        } else {
                            console.warn('🔍 FRONTEND: No r_code field in function result event');
                            console.warn('🔍 FRONTEND: Available fields:', Object.keys(event));
                            addExecutionLogEntry(`⚠️ No R code found in function result`, '#ffc107');
                        }
                    } else {
                        console.log('🔍 FRONTEND: Not an execute_r_code function, skipping R code extraction');
                    }

                    // CRITICAL FIX: Always display results for execute_r_code
                    if (event.function_name === 'execute_r_code') {
                        console.log('🔍 FRONTEND: Displaying R execution results');
                        displayStep4Results(event);
                    }

                    // Handle generated files from function execution
                    if (event.files_generated && event.files_generated.length > 0) {
                        // CRITICAL FIX: Get session ID from multiple sources with priority

                        // Priority 1: Direct session_id from event
                        if (event.session_id) {
                            window.currentExecutionId = event.session_id;
                            console.log(`🔍 FRONTEND: Set session ID from event: ${window.currentExecutionId}`);
                        }
                        // Priority 2: Extract from output directory
                        else if (event.output_directory) {
                            const match = event.output_directory.match(/execution_([^\/\\]+)/);
                            if (match) {
                                window.currentExecutionId = match[1];
                                console.log(`🔍 FRONTEND: Set session ID from output directory: ${window.currentExecutionId}`);
                            }
                        }
                        // Priority 3: Use existing execution data
                        else if (window.lastExecutionData?.execution_id) {
                            window.currentExecutionId = window.lastExecutionData.execution_id;
                            console.log(`🔍 FRONTEND: Set session ID from execution data: ${window.currentExecutionId}`);
                        }

                        // Ensure we have a session ID before proceeding
                        if (!window.currentExecutionId) {
                            console.error(`❌ FRONTEND: No session ID available for file loading!`);
                            console.error(`❌ Event data:`, event);
                        }
                        addInteractiveMessage(`📁 Generated ${event.files_generated.length} file(s): ${event.files_generated.join(', ')}`, 'system');
                        addExecutionLogEntry(`📁 Generated ${event.files_generated.length} files`, '#28a745');

                        // Store files for UI display
                        window.lastExecutionData = window.lastExecutionData || {};
                        window.lastExecutionData.files_generated = event.files_generated;
                        window.lastExecutionData.output_directory = event.output_directory;

                        // REMOVED: displayGeneratedFilesInline(event) - duplicate call, already handled by displayStep4Results
                        // Only call displayGeneratedFilesInline if this is NOT an execute_r_code event
                        if (event.function_name !== 'execute_r_code') {
                            displayGeneratedFilesInline(event);
                        }

                        // Show results section
                        const resultsSection = document.getElementById('step4-results');
                        if (resultsSection) {
                            resultsSection.style.display = 'block';
                        }
                    }


                    break;

                case 'complete':
                    // Don't show verbose completion messages
                    if (content && content.trim() &&
                        !content.includes('Task completed successfully') &&
                        !content.includes('completed in') &&
                        !content.includes('Response complete')) {
                        addInteractiveMessage(`✅ ${content}`, 'system');
                    }
                    // Update progress but don't disable UI yet - wait for 'end' event
                    updateExecutionProgress(100, 'Complete');
                    addExecutionLogEntry('✅ Task completed successfully', '#28a745');
                    break;

                case 'session_ready':
                    // ChatGPT Code Interpreter style: Session is ready for next input
                    console.log('🔄 FRONTEND: *** SESSION_READY EVENT *** - ChatGPT Code Interpreter style');
                    console.log('🔄 FRONTEND: Session ID:', event.session_id);
                    console.log('🔄 FRONTEND: Conversation length:', event.conversation_length);

                    // CRITICAL FIX: Set flag to prevent stream completion from resetting UI
                    window.sessionReadyReceived = true;

                    // FALLBACK: Auto-activate persistent mode for Step 4 Interactive sessions
                    if (!window.persistentModeActive && event.session_id) {
                        console.log('🔄 FRONTEND: *** AUTO-ACTIVATING PERSISTENT MODE (FALLBACK) ***');
                        console.log('🔄 FRONTEND: Session ID:', event.session_id);

                        window.persistentModeActive = true;
                        window.persistentSessionId = event.session_id;

                        console.log('✅ FRONTEND: Persistent mode auto-activated successfully');
                        console.log('✅ FRONTEND: persistentModeActive:', window.persistentModeActive);
                        console.log('✅ FRONTEND: persistentSessionId:', window.persistentSessionId);
                    }

                    // Show session ready message
                    addInteractiveMessage(`🔄 Session ready for next input (${event.conversation_length} messages in conversation)`, 'system');
                    addExecutionLogEntry('🔄 Session ready for next input', '#17a2b8');

                    // CRITICAL FIX: Reset ALL UI components for next input
                    resetExecutionUI();
                    updateExecutionProgress(0, 'Ready for next input');

                    // CRITICAL FIX: Reset chat interface execution state
                    updateExecutionStatus(false);  // Re-enable chat input and send button (also sets window.isExecuting = false)

                    console.log('🔄 FRONTEND: CRITICAL FIX - Chat interface reset for next input');
                    console.log('🔄 FRONTEND: window.isExecuting:', window.isExecuting);
                    console.log('🔄 FRONTEND: Send button disabled:', document.getElementById('send-message-btn')?.disabled);
                    console.log('🔄 FRONTEND: Chat input disabled:', document.getElementById('ai-chat-input')?.disabled);

                    // ENHANCED DIAGNOSTIC: Show clear ready state
                    console.log('🎉 FRONTEND: *** READY FOR FOLLOW-UP REQUESTS ***');
                    console.log('🎉 FRONTEND: You can now send another message!');
                    console.log('🎉 FRONTEND: Session ID for reuse:', window.currentExecutionId);

                    // VISUAL INDICATOR: Add prominent ready message
                    addInteractiveMessage('🎉 **READY FOR NEXT MESSAGE** 🎉\n\n✅ Session is active and ready\n✅ Variables are preserved\n✅ You can send follow-up requests now!', 'system');

                    // FOCUS CHAT INPUT: Make it obvious user can type
                    setTimeout(() => {
                        const chatInput = document.getElementById('ai-chat-input');
                        if (chatInput) {
                            chatInput.focus();
                            chatInput.placeholder = '💬 Ready for your next message...';
                            console.log('🎯 FRONTEND: Chat input focused and ready for user');
                        }
                    }, 500);

                    // Store session info for continuity - CRITICAL FIX: Update both variables
                    window.currentSessionId = event.session_id;
                    window.currentExecutionId = event.session_id;  // ← CRITICAL: Use same session for follow-up requests
                    window.conversationLength = event.conversation_length;

                    console.log(`🔄 FRONTEND: Session continuity - currentExecutionId updated to: ${window.currentExecutionId}`);

                    console.log('✅ FRONTEND: Session ready - ALL UI reset for next input');
                    break;

                case 'persistent_mode':
                    console.log('🔄 FRONTEND: *** PERSISTENT MODE ACTIVATED ***');
                    console.log('🔄 FRONTEND: Session ID:', event.session_id);
                    console.log('🔄 FRONTEND: Status:', event.status);

                    // Mark persistent mode as active
                    window.persistentModeActive = true;
                    window.persistentSessionId = event.session_id;

                    addInteractiveMessage('🔄 **Persistent Session Active**: Connection will remain open for immediate follow-up requests', 'system');
                    addExecutionLogEntry('🔄 Persistent SSE mode activated - connection kept alive', '#28a745');

                    // Update UI to show persistent mode
                    const statusIndicator = document.getElementById('connection-status');
                    if (statusIndicator) {
                        statusIndicator.textContent = '🔄 Persistent Connection Active';
                        statusIndicator.style.color = '#28a745';
                    }
                    break;

                case 'heartbeat':
                    console.log('🔄 FRONTEND: Heartbeat received - persistent connection alive');
                    // Update last heartbeat time for connection monitoring
                    window.lastHeartbeatTime = Date.now();
                    // Don't show heartbeat messages to user, just log them
                    break;

                case 'end':
                    // Stream ended - just log it, UI already reset by stream completion
                    console.log('🔍 FRONTEND: *** END EVENT RECEIVED *** - UI already reset by stream completion');
                    console.log('🔍 FRONTEND: Current execution state - window.isExecuting:', window.isExecuting);
                    console.log('🔍 FRONTEND: Current send button state:', document.getElementById('send-message-btn')?.disabled);
                    break;

                case 'error':
                    addInteractiveMessage(`❌ Error: ${content}`, 'system');
                    addExecutionLogEntry(`❌ Error: ${content}`, '#dc3545');

                    // Reset UI on error so user can try again
                    console.log('🔍 FRONTEND: Error occurred, resetting execution state');
                    window.isExecuting = false;
                    updateExecutionStatus(false);
                    updateExecutionProgress(0, 'Error');

                    // Clear safety timeout on error
                    if (window.currentSafetyTimeoutId) {
                        clearTimeout(window.currentSafetyTimeoutId);
                        window.currentSafetyTimeoutId = null;
                        console.log('🔍 FRONTEND: Safety timeout cleared due to error');
                    }

                    console.log('🔍 FRONTEND: Error reset complete, ready for retry');
                    break;

                default:
                    console.log('Unknown event type:', eventType);
            }
        }

// UI Helper Functions
function updateSessionStatus(status, color) {
    const statusElement = document.getElementById('session-status');
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.style.color = color;
    }
}

function displayGeneratedFilesInline(data) {
    // Display generated files with inline content (improved design)
    const filesList = document.getElementById('step4-files-list');
    if (!filesList || !data.files_generated || data.files_generated.length === 0) {
        filesList.innerHTML = `
            <div style="text-align: center; color: #6c757d; padding: 30px;">
                <div style="font-size: 48px; margin-bottom: 15px;">📄</div>
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">No Files Generated</div>
                <div style="font-size: 14px;">Execute R code to generate clinical tables and data files</div>
            </div>
        `;
        return;
    }

    let filesHtml = '';

    data.files_generated.forEach((file, index) => {
        const fileName = typeof file === 'string' ? file : file.name;
        const fileExt = fileName.split('.').pop().toLowerCase();

        // Determine file type, icon, and color
        let fileIcon = '📄';
        let fileColor = '#6c757d';
        let fileType = 'Document';

        if (['html', 'htm'].includes(fileExt)) {
            fileIcon = '🌐';
            fileColor = '#ff9800';
            fileType = 'Clinical Table';
        } else if (['csv', 'txt', 'dat'].includes(fileExt)) {
            fileIcon = '📊';
            fileColor = '#4caf50';
            fileType = 'Data File';
        } else if (['png', 'jpg', 'jpeg', 'gif', 'pdf'].includes(fileExt)) {
            fileIcon = '🖼️';
            fileColor = '#9c27b0';
            fileType = 'Plot/Chart';
        } else if (['r', 'R', 'log'].includes(fileExt)) {
            fileIcon = '📝';
            fileColor = '#17a2b8';
            fileType = 'Script/Log';
        }

        filesHtml += `
            <div style="margin-bottom: 16px; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: all 0.2s;">
                <!-- File Header -->
                <div style="background: linear-gradient(135deg, ${fileColor} 0%, ${fileColor}dd 100%); color: white; padding: 14px 16px; display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 20px;">${fileIcon}</span>
                    <div style="flex: 1;">
                        <div style="font-weight: bold; font-size: 14px; margin-bottom: 2px;">${fileName}</div>
                        <div style="font-size: 12px; opacity: 0.9;">${fileType} • ${fileExt.toUpperCase()} • File ${index + 1} of ${data.files_generated.length}</div>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="toggleFileContent('file-content-${index}')"
                                style="background: rgba(255,255,255,0.2); color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all 0.2s; font-weight: bold;">
                            👁️ View
                        </button>
                        <button onclick="downloadSingleFile('${fileName}')"
                                style="background: rgba(255,255,255,0.2); color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all 0.2s; font-weight: bold;">
                            💾 Save
                        </button>
                    </div>
                </div>

                <!-- File Content -->
                <div id="file-content-${index}" style="display: none; padding: 0; max-height: 600px; overflow: hidden; border-top: 1px solid rgba(0,0,0,0.1);">
                    <div class="loading-content" style="text-align: center; color: #6c757d; padding: 40px;">
                        <div style="font-size: 24px; margin-bottom: 12px;">⏳</div>
                        <div style="font-size: 14px; font-weight: bold;">Loading content...</div>
                        <div style="font-size: 12px; margin-top: 4px; opacity: 0.7;">Please wait while we fetch the file content</div>
                    </div>
                </div>
            </div>
        `;
    });

    filesList.innerHTML = filesHtml;

    // Load file contents asynchronously
    console.log(`🔍 Loading ${data.files_generated.length} files with session ID: ${window.currentExecutionId}`);
    data.files_generated.forEach((file, index) => {
        const fileName = typeof file === 'string' ? file : file.name;
        console.log(`🔍 Loading file ${index + 1}/${data.files_generated.length}: ${fileName}`);
        loadFileContentInline(fileName, index);
    });
}

// REMOVED: updateFileTabDisplay() - redundant function not used by UI

function updateExecutionStatus(executing) {
    console.log(`🔍 updateExecutionStatus called with: ${executing}`);
    console.log(`🔍 Stack trace:`, new Error().stack);

    // CRITICAL FIX: Update the global execution flag
    window.isExecuting = executing;
    console.log(`🔍 CRITICAL FIX: window.isExecuting updated to: ${window.isExecuting}`);

    // Update the send button
    const button = document.getElementById('send-message-btn');
    if (button) {
        button.disabled = executing;
        button.textContent = executing ? '🔄 Processing...' : '🚀 Send';
        console.log(`🔍 Button updated - disabled: ${button.disabled}, text: ${button.textContent}`);
    }

    // Also update input field
    const input = document.getElementById('ai-chat-input');
    if (input) {
        input.disabled = executing;
        console.log(`🔍 Input updated - disabled: ${input.disabled}`);
    }
}

function addInteractiveMessage(content, type) {
    const chatContainer = document.getElementById('interactive-chat');
    if (!chatContainer) return null;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = content.replace(/\n/g, '<br>');
    
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return messageDiv;
}

// REMOVED: Simple resetExecutionUI() - keeping the more complete implementation

// Session Management
function interruptExecution() {
    console.log('🛑 Interrupting execution...');
    
    fetch('/api/step4/interactive/interrupt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addInteractiveMessage('🛑 Execution interrupted', 'system');
        }
    })
    .catch(error => {
        console.error('Interrupt error:', error);
    });
}

function restartSession() {
    console.log('🔄 Restarting session...');
    
    fetch('/api/step4/interactive/restart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.interactiveSession = true;
            updateSessionStatus('✅ Restarted', '#28a745');
            addInteractiveMessage('🔄 Session restarted', 'system');
        }
    })
    .catch(error => {
        console.error('Restart error:', error);
    });
}

// ===== EXECUTION SYSTEM FUNCTIONS =====

function executeRCodeStep4() {
    console.log('🚀 Starting REFERENCE PROJECT style execution...');

    if (window.isExecuting) {
        alert('⚠️ Please wait for current execution to complete');
        return;
    }

    // Get R code from editor (supports both Step 3 and manual input)
    const editor = document.getElementById('step4-rcode-editor');
    let rCode = '';

    if (editor && editor.value.trim()) {
        rCode = editor.value.trim();
    } else if (window.currentRCode) {
        rCode = window.currentRCode;
        if (editor) editor.value = rCode;
    } else {
        alert('❌ No R code to execute. Please enter R code or load from Step 3.');
        return;
    }

    // Store the code for execution
    window.currentRCode = rCode;

    // Update UI to show execution started
    const executeBtn = document.getElementById('execute-step4-btn');
    if (executeBtn) {
        executeBtn.textContent = '⏳ Executing...';
        executeBtn.disabled = true;
    }

    // Show execution status
    const statusDiv = document.getElementById('step4-execution-status');
    if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.textContent = '⏳ Executing R code...';
    }

    // CORRECT APPROACH: Try direct execution first, like reference project
    // Only involve LLM if there are errors
    executeRCodeDirectFirst(rCode);
}

function executeRCodeDirectFirst(rCode) {
    console.log('🚀 Executing R code directly first...');

    // Use persistent execution ID for session continuity (like Interactive AI Assistant)
    if (!window.currentExecutionId) {
        // Only create new ID if none exists
        const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+/, '');
        const randomId = Math.random().toString(36).substring(2, 10);
        window.currentExecutionId = `${timestamp}_${randomId}`;
        console.log(`📁 Created new persistent session ID: ${window.currentExecutionId}`);
    } else {
        console.log(`📁 Reusing persistent session ID: ${window.currentExecutionId}`);
    }

    const executionId = window.currentExecutionId;

    // FIRST: Load the R code into the editor so user can see what's being executed
    loadRCodeIntoEditor(rCode, 'execution');
    addCodeVersion(rCode, 'Direct Execution', 'Code executed directly', 1);
    window.currentRCode = rCode;

    addExecutionLogEntry('🚀 Starting R code execution...', '#007bff');
    addExecutionLogEntry(`📝 Code loaded into editor (${rCode.length} chars)`, '#6f42c1');
    addExecutionLogEntry(`📁 Session ID: ${executionId}`, '#17a2b8');
    updateExecutionProgress(10, 'Preparing...');

    // Clear previous files display with session info
    const filesList = document.getElementById('step4-files-list');
    if (filesList) {
        filesList.innerHTML = `
            <div style="text-align: center; color: #6c757d; padding: 20px;">
                <div style="font-size: 24px; margin-bottom: 10px;">⏳</div>
                <div>Executing R code...</div>
                <div style="font-size: 12px; margin-top: 5px;">Session: ${executionId}</div>
            </div>
        `;
    }

    // Get dataset info from Step 1 for context
    const datasetInfo = getDatasetInfoFromStep1();

    fetch('/execute_rcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            r_code: rCode,
            execution_id: executionId,
            dataset_info: datasetInfo,
            work_dir: `./outputs/execution_${executionId}`,  // Unique session directory
            session_isolation: true  // Enable session isolation
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('📊 R execution result:', data);

        if (data.success) {
            addExecutionLogEntry('✅ R code executed successfully', '#28a745');
            updateExecutionProgress(100, 'Complete');

            // Display results
            displayStep4Results(data);

            // Update execution stats
            updateExecutionStats(data.execution_time || 0, data.files_generated?.length || 0);
        } else {
            addExecutionLogEntry(`❌ Execution failed: ${data.error}`, '#dc3545');
            updateExecutionProgress(0, 'Failed');

            // Store error details for Interactive AI Assistant context
            window.lastExecutionData = {
                success: false,
                error: data.error,
                output: data.output || '',
                timestamp: new Date().toISOString(),
                execution_id: data.execution_id || window.currentExecutionId
            };

            // Show error in chat
            addInteractiveMessage(`❌ **Execution Error**: ${data.error}`, 'system');
        }
    })
    .catch(error => {
        console.error('❌ R execution error:', error);
        addExecutionLogEntry(`❌ Connection error: ${error.message}`, '#dc3545');
        updateExecutionProgress(0, 'Error');
        addInteractiveMessage(`❌ **Connection Error**: ${error.message}`, 'system');
    })
    .finally(() => {
        resetExecutionUI();
    });
}

function resetExecutionUI() {
    window.isExecuting = false;

    const executeBtn = document.getElementById('execute-step4-btn');
    if (executeBtn) {
        executeBtn.textContent = '🚀 Execute R Code with AI Debugging';
        executeBtn.disabled = false;
    }

    const statusDiv = document.getElementById('step4-execution-status');
    if (statusDiv) {
        statusDiv.style.display = 'none';
    }
}

// ===== RESULTS DISPLAY FUNCTIONS =====

// ===== EXECUTION LOG & PROGRESS FUNCTIONS =====

function clearExecutionLog() {
    console.log('🗑️ Clearing execution log');

    const logElement = document.getElementById('execution-log-display');
    if (logElement) {
        logElement.innerHTML = `
            <div style="color: #569cd6;">🤖 R Code Execution System v2.0</div>
            <div style="color: #6a9955;">Ready for AI-powered R code execution with iterative debugging...</div>
            <div style="color: #4ec9b0;">Mode: <span id="execution-current-mode">AI-Powered Execution</span></div>
            <div style="margin: 10px 0; color: #d7ba7d;">
                <span style="color: #569cd6;">></span> <span id="execution-cursor" style="animation: blink 1s infinite;">_</span>
            </div>
        `;
    }

    // Reset progress
    updateExecutionProgress(0, 'Ready');
}

function addExecutionLogEntry(message, color = '#d4d4d4', timestamp = true) {
    console.log('📝 Adding execution log entry:', message);

    const logElement = document.getElementById('execution-log-display');
    if (!logElement) return;

    const time = timestamp ? new Date().toLocaleTimeString() : '';
    const logLine = document.createElement('div');
    logLine.style.color = color;
    logLine.style.marginBottom = '2px';
    logLine.textContent = `${time ? `[${time}] ` : ''}${message}`;

    logElement.appendChild(logLine);
    logElement.scrollTop = logElement.scrollHeight;
}

function updateExecutionProgress(percentage, statusText) {
    console.log('📊 Updating execution progress:', percentage, statusText);

    const progressBar = document.getElementById('execution-progress-bar');
    const progressText = document.getElementById('execution-progress-text');
    const statusIndicator = document.getElementById('execution-status-indicator');

    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
    }

    if (progressText) {
        progressText.textContent = `${percentage}%`;
    }

    if (statusIndicator) {
        statusIndicator.textContent = statusText;

        // Update color based on status
        if (percentage === 100) {
            statusIndicator.style.background = '#28a745';
        } else if (percentage > 0) {
            statusIndicator.style.background = '#ffc107';
        } else {
            statusIndicator.style.background = '#6c757d';
        }
    }
}

function addCodeVersion(code, source, description = '', iterations = 0) {
    // Initialize code version history if not exists
    if (!window.codeVersionHistory) {
        window.codeVersionHistory = [];
    }

    const version = {
        code: code,
        source: source,
        description: description,
        iterations: iterations,
        timestamp: new Date().toLocaleString()
    };

    window.codeVersionHistory.push(version);
    console.log(`📚 Added code version: ${source} (${window.codeVersionHistory.length} total versions)`);
}

// ===== MISSING UI FUNCTION IMPLEMENTATIONS =====

function switchCodeView(viewType) {
    console.log(`🔄 Switching to code view: ${viewType}`);

    // Hide all views
    const views = ['editor', 'original', 'final', 'changes'];
    views.forEach(view => {
        const element = document.getElementById(`view-${view}`);
        const tab = document.getElementById(`tab-${view}`);

        if (element) element.style.display = 'none';
        if (tab) {
            tab.style.background = '#6c757d';
            tab.style.color = 'white';
        }
    });

    // Show selected view
    const selectedView = document.getElementById(`view-${viewType}`);
    const selectedTab = document.getElementById(`tab-${viewType}`);

    if (selectedView) selectedView.style.display = 'block';
    if (selectedTab) {
        selectedTab.style.background = '#007bff';
        selectedTab.style.color = 'white';
    }
}

function validateRCodeInEditor() {
    console.log('✅ Validating R code in editor...');

    const editor = document.getElementById('step4-rcode-editor');
    if (!editor || !editor.value.trim()) {
        alert('❌ No R code to validate. Please enter some R code first.');
        return;
    }

    const rCode = editor.value.trim();

    fetch('/validate_rcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ r_code: rCode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addInteractiveMessage('✅ **R Code Validation Passed** - Your code looks good!', 'system');
            updateCodeStatusIndicator('✅ Valid', '#28a745');
        } else {
            addInteractiveMessage(`❌ **R Code Validation Failed**: ${data.error}`, 'system');
            updateCodeStatusIndicator('❌ Invalid', '#dc3545');
        }
    })
    .catch(error => {
        console.error('Validation error:', error);
        addInteractiveMessage(`❌ **Validation Error**: ${error.message}`, 'system');
    });
}

// REMOVED: Duplicate showCodeVersionHistory() function - using the modal version below

function clearRCodeEditor() {
    console.log('🗑️ Clearing R code editor...');

    const editor = document.getElementById('step4-rcode-editor');
    if (editor) {
        editor.value = '';
        updateCodeStatusIndicator('🗑️ Cleared', '#6c757d');
        addInteractiveMessage('🗑️ **R code editor cleared**', 'system');
    }
}

function updateRCodeFromEditor() {
    const editor = document.getElementById('step4-rcode-editor');
    if (editor && editor.value.trim()) {
        // Store current code globally
        window.currentRCode = editor.value.trim();

        // Update status indicator
        updateCodeStatusIndicator('✏️ Modified', '#ffc107');
    }
}

function updateCodeStatusIndicator(text, color) {
    const indicator = document.getElementById('code-status-indicator');
    if (indicator) {
        indicator.textContent = text;
        indicator.style.background = color;
        indicator.style.display = 'block';
    }
}

function loadCodeVersion(index) {
    if (window.codeVersionHistory && window.codeVersionHistory[index]) {
        const version = window.codeVersionHistory[index];
        loadRCodeIntoEditor(version.code, version.source);
        addInteractiveMessage(`📚 **Loaded code version ${index + 1}** from ${version.source}`, 'system');
    }
}

// ===== NAVIGATION FUNCTIONS =====

function goBackToStep3() {
    console.log('🔙 Going back to Step 3...');

    document.getElementById('step4-container').style.display = 'none';
    document.getElementById('step3-container').style.display = 'block';

    // Update progress indicator if it exists
    if (typeof updateProgressIndicator === 'function') {
        updateProgressIndicator(3);
    }
}

function exportExecutionLog() {
    console.log('📥 Exporting execution log');

    const logElement = document.getElementById('execution-log-display');
    if (!logElement) {
        alert('No execution log to export');
        return;
    }

    const logText = logElement.textContent;
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `execution_log_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    addInteractiveMessage('📥 **Execution log exported** - Downloaded as text file for your records.', 'system');
}

function updateExecutionStats(time, files) {
    console.log('📈 Updating execution stats:', time, files);

    const timeDisplay = document.getElementById('execution-time-display');
    const filesCount = document.getElementById('execution-files-count');

    if (timeDisplay) timeDisplay.textContent = `${time.toFixed(1)}s`;
    if (filesCount) filesCount.textContent = files;
}

function displayStep4Results(data) {
    console.log('📊 Displaying Step 4 results:', data);

    // Store execution ID if provided
    if (data.execution_id) {
        window.currentExecutionId = data.execution_id;
        console.log(`📁 Updated execution ID: ${data.execution_id}`);
    }

    // Show the results section
    const resultsSection = document.getElementById('step4-results');
    if (resultsSection) {
        resultsSection.style.display = 'block';
    }

    // Display clinical output (console output) - handle both direct execution and interactive chat formats
    const clinicalOutput = document.getElementById('step4-clinical-output');
    if (clinicalOutput) {
        // CRITICAL: Use 'output' field for raw R console output (UI display)
        // 'content' field contains LLM summary (no real data)
        const consoleOutput = data.output || '';

        if (consoleOutput && consoleOutput.trim()) {
            clinicalOutput.innerHTML = formatConsoleOutput(consoleOutput);
        } else {
            // Show message when no output is available
            clinicalOutput.innerHTML = `
                <div style="text-align: center; color: #6c757d; padding: 20px;">
                    <div style="font-size: 18px; margin-bottom: 8px;">📋</div>
                    <div>Execute R code to see console output here</div>
                    <div style="font-size: 12px; margin-top: 5px;">R execution results and messages will be displayed</div>
                </div>
            `;
        }
    }

    // Display generated files with inline content (session-aware)
    if (data.files_generated && data.files_generated.length > 0) {
        displayGeneratedFilesInline(data);
    } else {
        // Show no files message
        const filesList = document.getElementById('step4-files-list');
        if (filesList) {
            filesList.innerHTML = `
                <div style="text-align: center; color: #6c757d; padding: 30px;">
                    <div style="font-size: 48px; margin-bottom: 15px;">📄</div>
                    <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">No Files Generated</div>
                    <div style="font-size: 14px;">R code executed successfully but no output files were created</div>
                    ${data.execution_id ? `<div style="font-size: 12px; margin-top: 8px; opacity: 0.7;">Session: ${data.execution_id}</div>` : ''}
                </div>
            `;
        }
    }

    // Store results globally
    window.lastExecutionData = data;
}

// Utility Functions
function getDatasetInfoFromStep1() {
    // Get dataset information from Step 1 analysis results
    if (window.analysisResults && window.analysisResults.dataset_info) {
        return window.analysisResults.dataset_info;
    }
    return null;
}

function getCurrentCode() {
    console.log('🔍 getCurrentCode called');

    // Get current R code from the editor first (most up-to-date)
    const editor = document.getElementById('step4-rcode-editor');
    if (editor && editor.value && editor.value.trim()) {
        const editorCode = editor.value.trim();
        console.log(`🔍 getCurrentCode: Found code in editor (${editorCode.length} chars)`);
        console.log(`🔍 getCurrentCode: Editor code preview: ${editorCode.substring(0, 100)}...`);

        // CRITICAL FIX: Ensure global variable is always in sync with editor
        window.currentRCode = editorCode;
        console.log(`🔍 getCurrentCode: Synced window.currentRCode with editor content`);

        return editorCode;
    }

    // Fallback to global variable
    const globalCode = window.currentRCode || '';
    console.log(`🔍 getCurrentCode: Using global variable (${globalCode.length} chars)`);
    if (globalCode) {
        console.log(`🔍 getCurrentCode: Global code preview: ${globalCode.substring(0, 100)}...`);

        // If we have global code but editor is empty, load it into editor
        if (editor && !editor.value.trim()) {
            console.log(`🔍 getCurrentCode: Loading global code into empty editor`);
            editor.value = globalCode;
        }
    } else {
        console.warn('🔍 getCurrentCode: No code found in editor or global variable');
    }

    return globalCode;
}

// ===== FILE MANAGEMENT FUNCTIONS =====

function toggleFileContent(contentId) {
    const contentDiv = document.getElementById(contentId);
    if (!contentDiv) return;

    const isVisible = contentDiv.style.display !== 'none';
    contentDiv.style.display = isVisible ? 'none' : 'block';

    // Update button text
    const button = document.querySelector(`button[onclick*="${contentId}"]`);
    if (button) {
        button.innerHTML = isVisible ? '👁️ View' : '👁️ View';
    }
}

function openImageModal(imageSrc, fileName) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        cursor: pointer;
    `;

    // Create image container
    const imageContainer = document.createElement('div');
    imageContainer.style.cssText = `
        max-width: 95%;
        max-height: 95%;
        position: relative;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        overflow: hidden;
    `;

    // Create header
    const header = document.createElement('div');
    header.style.cssText = `
        background: #343a40;
        color: white;
        padding: 12px 16px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
    `;
    header.innerHTML = `
        <span>🖼️ ${fileName}</span>
        <button onclick="this.closest('.modal').remove()" style="background: none; border: none; color: white; font-size: 20px; cursor: pointer; padding: 0; width: 24px; height: 24px;">×</button>
    `;

    // Create image
    const img = document.createElement('img');
    img.src = imageSrc;
    img.style.cssText = `
        max-width: 100%;
        max-height: 80vh;
        display: block;
        margin: 0 auto;
    `;

    // Assemble modal
    imageContainer.appendChild(header);
    imageContainer.appendChild(img);
    modal.appendChild(imageContainer);
    modal.className = 'modal';

    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });

    // Close on Escape key
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);

    document.body.appendChild(modal);
}

function loadFileContentInline(fileName, index) {
    const contentDiv = document.getElementById(`file-content-${index}`);
    if (!contentDiv) {
        console.error(`❌ Content div not found for file ${fileName} (index: ${index})`);
        return;
    }

    // CRITICAL FIX: Get session ID from multiple sources
    const sessionId = window.currentExecutionId ||
                     window.lastExecutionData?.execution_id ||
                     'default';

    console.log(`🔍 Loading file: ${fileName} with session ID: ${sessionId}`);
    console.log(`🔍 Available session data:`, {
        currentExecutionId: window.currentExecutionId,
        lastExecutionData: window.lastExecutionData
    });

    // Use session-aware file loading
    const fileUrl = `/get_file_content?file=${encodeURIComponent(fileName)}&session_id=${encodeURIComponent(sessionId)}`;

    console.log(`📡 Fetching file from: ${fileUrl}`);

    fetch(fileUrl)
        .then(response => {
            console.log(`📡 File fetch response: ${response.status} for ${fileName}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.text();
        })
        .then(content => {
            console.log(`✅ Successfully loaded ${fileName} (${content.length} chars)`);
            displayFileContentInline(fileName, content, contentDiv, fileName);
        })
        .catch(error => {
            console.error(`❌ Failed to load file ${fileName}:`, error);
            // FALLBACK: Try direct file path approach
            tryDirectFileLoad(fileName, index, contentDiv, sessionId);
        });
}

function tryDirectFileLoad(fileName, index, contentDiv, sessionId) {
    console.log(`🔄 Trying direct file load fallback for: ${fileName}`);

    // Try direct path strategies as fallback
    const pathStrategies = [
        `outputs/execution_${sessionId}/${fileName}`,
        `outputs/${fileName}`,
        fileName
    ];

    let pathIndex = 0;

    function tryNextPath() {
        if (pathIndex >= pathStrategies.length) {
            console.log(`📄 All fallback paths failed for ${fileName}`);
            displayFileContentFallback(fileName, contentDiv);
            return;
        }

        const currentPath = pathStrategies[pathIndex];
        console.log(`📄 Trying fallback path: ${currentPath}`);

        fetch(`/get_file_content?file=${encodeURIComponent(currentPath)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.text();
            })
            .then(content => {
                console.log(`✅ Fallback success: ${fileName} from ${currentPath}`);
                displayFileContentInline(fileName, content, contentDiv, currentPath);
            })
            .catch(error => {
                console.log(`❌ Fallback path ${currentPath} failed: ${error.message}`);
                pathIndex++;
                tryNextPath();
            });
    }

    tryNextPath();
}

function displayFileContentInline(fileName, content, contentDiv, filePath = null) {
    const fileExt = fileName.split('.').pop().toLowerCase();
    let displayHtml = '';

    if (['html', 'htm'].includes(fileExt)) {
        // Display HTML content directly (clinical tables) with enhanced styling
        displayHtml = `
            <div style="background: white;">
                <div style="background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); color: white; padding: 12px 16px; font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                    <span>🌐</span>
                    <span>Clinical Table Content</span>
                    <div style="margin-left: auto; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 12px; font-size: 11px;">
                        HTML
                    </div>
                </div>
                <div style="padding: 20px; background: white; max-height: 500px; overflow: auto; border-bottom: 1px solid #dee2e6;">
                    ${content}
                </div>
                <div style="background: #f8f9fa; padding: 8px 16px; font-size: 11px; color: #6c757d; border-top: 1px solid #dee2e6;">
                    💡 This clinical table is ready for use in reports and presentations
                </div>
            </div>
        `;
    } else if (['csv', 'txt', 'dat', 'log'].includes(fileExt)) {
        // Enhanced CSV/text content display
        const lines = content.split('\n').filter(line => line.trim());
        const totalLines = lines.length;
        const displayLines = lines.slice(0, 50); // Show more lines
        const isCSV = fileExt === 'csv' && content.includes(',');

        if (isCSV) {
            displayHtml = formatEnhancedCSVContent(displayLines, totalLines);
        } else {
            displayHtml = `
                <div style="background: white;">
                    <div style="background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%); color: white; padding: 12px 16px; font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                        <span>📊</span>
                        <span>Data Content</span>
                        <div style="margin-left: auto; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 12px; font-size: 11px;">
                            ${totalLines} lines
                        </div>
                    </div>
                    <pre style="margin: 0; padding: 20px; background: white; font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.5; max-height: 400px; overflow: auto; border-bottom: 1px solid #dee2e6;">${displayLines.join('\n')}</pre>
                    ${totalLines > 50 ? `<div style="background: #f8f9fa; padding: 8px 16px; font-size: 11px; color: #6c757d; border-top: 1px solid #dee2e6;">📄 Showing first 50 of ${totalLines} lines</div>` : ''}
                </div>
            `;
        }
    } else if (['png', 'jpg', 'jpeg', 'gif', 'svg'].includes(fileExt)) {
        // Display images inline (reference project style)
        const imageUrl = filePath ? `/get_file_content?file=${encodeURIComponent(filePath)}` : `/get_file_content?file=${encodeURIComponent(fileName)}`;
        displayHtml = `
            <div style="background: white;">
                <div style="background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%); color: white; padding: 12px 16px; font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                    <span>🖼️</span>
                    <span>Plot/Chart Image</span>
                    <div style="margin-left: auto; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 12px; font-size: 11px;">
                        ${fileExt.toUpperCase()}
                    </div>
                </div>
                <div style="padding: 20px; background: white; text-align: center; border-bottom: 1px solid #dee2e6; overflow: auto;">
                    <div style="display: inline-block; max-width: 100%; position: relative;">
                        <img src="${imageUrl}"
                             style="max-width: 100%; height: auto; min-height: 200px; max-height: 800px; border: 1px solid #dee2e6; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); cursor: pointer; transition: all 0.3s ease;"
                             onload="this.style.opacity='1'; console.log('Image loaded:', this.naturalWidth + 'x' + this.naturalHeight);"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block'"
                             onclick="openImageModal(this.src, '${fileName}')"
                             title="Click to view full size"
                             style="opacity: 0;">
                        <div style="display: none; color: #dc3545; padding: 20px;">
                            <div style="font-size: 24px; margin-bottom: 10px;">❌</div>
                            <div>Failed to load image: ${fileName}</div>
                            <div style="font-size: 12px; margin-top: 8px;">Check if the file exists and is a valid image format</div>
                        </div>
                    </div>
                </div>
                <div style="background: #f8f9fa; padding: 8px 16px; font-size: 11px; color: #6c757d; border-top: 1px solid #dee2e6;">
                    📊 Generated plot/chart from R analysis
                </div>
            </div>
        `;
    } else if (['pdf'].includes(fileExt)) {
        // Display PDF with embedded viewer
        const pdfUrl = filePath ? `/get_file_content?file=${encodeURIComponent(filePath)}` : `/get_file_content?file=${encodeURIComponent(fileName)}`;
        displayHtml = `
            <div style="background: white;">
                <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 12px 16px; font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                    <span>📋</span>
                    <span>PDF Document</span>
                    <div style="margin-left: auto; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 12px; font-size: 11px;">
                        PDF
                    </div>
                </div>
                <div style="padding: 20px; background: white; text-align: center; border-bottom: 1px solid #dee2e6;">
                    <iframe src="${pdfUrl}" style="width: 100%; height: 500px; border: 1px solid #dee2e6; border-radius: 4px;"
                            onload="this.style.opacity='1'"
                            style="opacity: 0; transition: opacity 0.3s;">
                    </iframe>
                    <div style="margin-top: 10px;">
                        <a href="${pdfUrl}" target="_blank" style="background: #dc3545; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-size: 12px;">
                            📄 Open in New Tab
                        </a>
                    </div>
                </div>
                <div style="background: #f8f9fa; padding: 8px 16px; font-size: 11px; color: #6c757d; border-top: 1px solid #dee2e6;">
                    📋 Clinical report document
                </div>
            </div>
        `;
    } else if (['r', 'R'].includes(fileExt)) {
        // Display R code with syntax highlighting
        displayHtml = `
            <div style="background: white;">
                <div style="background: linear-gradient(135deg, #17a2b8 0%, #138496 100%); color: white; padding: 12px 16px; font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                    <span>📝</span>
                    <span>R Script</span>
                    <div style="margin-left: auto; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 12px; font-size: 11px;">
                        R CODE
                    </div>
                </div>
                <pre style="margin: 0; padding: 20px; background: #f8f9fa; font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.5; max-height: 500px; overflow: auto; border-bottom: 1px solid #dee2e6; color: #495057;">${content}</pre>
                <div style="background: #f8f9fa; padding: 8px 16px; font-size: 11px; color: #6c757d; border-top: 1px solid #dee2e6;">
                    💻 R script used for analysis
                </div>
            </div>
        `;
    } else {
        // Enhanced display for other file types
        displayHtml = `
            <div style="background: white; text-align: center; padding: 40px;">
                <div style="font-size: 48px; margin-bottom: 16px;">📄</div>
                <div style="font-size: 16px; font-weight: bold; color: #495057; margin-bottom: 8px;">${fileName}</div>
                <div style="font-size: 14px; color: #6c757d; margin-bottom: 16px;">${fileExt.toUpperCase()} File</div>
                <div style="background: #e3f2fd; color: #1976d2; padding: 12px 20px; border-radius: 6px; display: inline-block; font-size: 13px;">
                    💡 Preview not available for this file type
                </div>
                ${filePath ? `<div style="margin-top: 16px;"><a href="/get_file_content?file=${encodeURIComponent(filePath)}" target="_blank" style="background: #007bff; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-size: 12px;">📄 Download File</a></div>` : ''}
            </div>
        `;
    }

    contentDiv.innerHTML = displayHtml;
}

function displayFileContentFallback(fileName, contentDiv) {
    contentDiv.innerHTML = `
        <div style="text-align: center; color: #6c757d; padding: 20px;">
            <div style="font-size: 24px; margin-bottom: 10px;">📄</div>
            <div>File: <strong>${fileName}</strong></div>
            <div style="font-size: 12px; margin-top: 5px;">✅ File generated successfully</div>
            <div style="font-size: 12px; color: #28a745;">Content preview not available - file exists in output directory</div>
        </div>
    `;
}

function formatCSVContent(lines) {
    if (lines.length === 0) return '<div>No content</div>';

    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    const rows = lines.slice(1).filter(line => line.trim());

    let tableHtml = `
        <div style="border: 1px solid #dee2e6; border-radius: 4px; overflow: hidden;">
            <div style="background: #f8f9fa; padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: bold; color: #495057;">
                📊 Data Table (First ${Math.min(rows.length, 19)} rows)
            </div>
            <div style="overflow-x: auto; max-height: 300px;">
                <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <thead>
                        <tr style="background: #f8f9fa;">
    `;

    headers.forEach(header => {
        tableHtml += `<th style="padding: 8px; border: 1px solid #dee2e6; text-align: left; font-weight: bold;">${header}</th>`;
    });

    tableHtml += '</tr></thead><tbody>';

    rows.slice(0, 19).forEach((row, index) => {
        const cells = row.split(',').map(c => c.trim().replace(/"/g, ''));
        tableHtml += `<tr style="background: ${index % 2 === 0 ? 'white' : '#f9f9f9'};">`;
        cells.forEach(cell => {
            tableHtml += `<td style="padding: 6px 8px; border: 1px solid #dee2e6;">${cell}</td>`;
        });
        tableHtml += '</tr>';
    });

    tableHtml += '</tbody></table></div></div>';

    if (rows.length > 19) {
        tableHtml += `<div style="text-align: center; padding: 8px; color: #6c757d; font-size: 12px;">... and ${rows.length - 19} more rows</div>`;
    }

    return tableHtml;
}

function formatEnhancedCSVContent(lines, totalLines) {
    if (lines.length === 0) return '<div>No content</div>';

    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    const rows = lines.slice(1).filter(line => line.trim());
    const displayRows = Math.min(rows.length, 49); // Show up to 49 rows

    let tableHtml = `
        <div style="background: white;">
            <div style="background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%); color: white; padding: 12px 16px; font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                <span>📊</span>
                <span>Data Table</span>
                <div style="margin-left: auto; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 12px; font-size: 11px;">
                    ${headers.length} columns • ${totalLines - 1} rows
                </div>
            </div>
            <div style="overflow-x: auto; max-height: 450px; border-bottom: 1px solid #dee2e6;">
                <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <thead style="position: sticky; top: 0; z-index: 10;">
                        <tr style="background: #f8f9fa;">
    `;

    headers.forEach((header, index) => {
        tableHtml += `<th style="padding: 10px 12px; border: 1px solid #dee2e6; text-align: left; font-weight: bold; background: #f8f9fa; position: sticky; top: 0;">${header}</th>`;
    });

    tableHtml += '</tr></thead><tbody>';

    rows.slice(0, displayRows).forEach((row, index) => {
        const cells = row.split(',').map(c => c.trim().replace(/"/g, ''));
        const rowBg = index % 2 === 0 ? 'white' : '#f9f9f9';
        tableHtml += `<tr style="background: ${rowBg}; transition: background-color 0.2s;" onmouseover="this.style.background='#e3f2fd'" onmouseout="this.style.background='${rowBg}'">`;

        cells.forEach((cell, cellIndex) => {
            // Detect numeric values for right alignment
            const isNumeric = !isNaN(parseFloat(cell)) && isFinite(cell);
            const alignment = isNumeric ? 'right' : 'left';
            tableHtml += `<td style="padding: 8px 12px; border: 1px solid #dee2e6; text-align: ${alignment};">${cell}</td>`;
        });
        tableHtml += '</tr>';
    });

    tableHtml += '</tbody></table></div>';

    if (totalLines - 1 > displayRows) {
        tableHtml += `<div style="background: #f8f9fa; padding: 12px 16px; font-size: 12px; color: #6c757d; border-top: 1px solid #dee2e6; text-align: center;">
            📄 Showing first ${displayRows} of ${totalLines - 1} data rows
        </div>`;
    }

    tableHtml += '</div>';

    return tableHtml;
}

// ===== ENHANCED UI HELPER FUNCTIONS =====

function expandAllFiles() {
    console.log('📖 Expanding all file contents...');
    const fileContents = document.querySelectorAll('[id^="file-content-"]');
    fileContents.forEach(content => {
        content.style.display = 'block';
    });

    // Update all toggle buttons
    const toggleButtons = document.querySelectorAll('button[onclick*="toggleFileContent"]');
    toggleButtons.forEach(button => {
        button.innerHTML = '🙈 Hide';
    });
}

function collapseAllFiles() {
    console.log('📕 Collapsing all file contents...');
    const fileContents = document.querySelectorAll('[id^="file-content-"]');
    fileContents.forEach(content => {
        content.style.display = 'none';
    });

    // Update all toggle buttons
    const toggleButtons = document.querySelectorAll('button[onclick*="toggleFileContent"]');
    toggleButtons.forEach(button => {
        button.innerHTML = '👁️ View';
    });
}

function downloadSingleFile(fileName) {
    console.log(`💾 Downloading single file: ${fileName}`);

    // Create download link
    const link = document.createElement('a');
    link.href = `/get_file_content?file=${encodeURIComponent(`outputs/step4/${fileName}`)}&download=true`;
    link.download = fileName;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Show feedback
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 10000;
        background: #28a745; color: white; padding: 12px 20px;
        border-radius: 6px; font-size: 14px; font-weight: bold;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = `💾 Downloading ${fileName}...`;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}



function displayExecutionResults(data) {
    console.log('📊 Displaying execution results:', data);

    // Show the existing results display
    const resultsDisplay = document.getElementById('results-display');
    if (!resultsDisplay) return;

    resultsDisplay.style.display = 'block';

    // Enhanced results display with Local Code Interpreter style
    displayExecutionResults(data);

    // Update console output with detailed logs
    updateConsoleOutput(data);

    // Display generated clinical tables
    displayClinicalTables(data);

    // Store results for export
    window.lastExecutionData = data;
}

// REMOVED: displayEnhancedExecutionResults() - redundant with displayStep4Results()

function formatConsoleOutput(output) {
    if (!output) return '';

    return output
        .replace(/✅/g, '<span style="color: #27ae60;">✅</span>')
        .replace(/❌/g, '<span style="color: #e74c3c;">❌</span>')
        .replace(/⚠️/g, '<span style="color: #f39c12;">⚠️</span>')
        .replace(/📊/g, '<span style="color: #3498db;">📊</span>')
        .replace(/📁/g, '<span style="color: #9b59b6;">📁</span>')
        .replace(/Loading required packages/g, '<span style="color: #3498db;">Loading required packages</span>')
        .replace(/Loaded package:/g, '<span style="color: #27ae60;">Loaded package:</span>')
        .replace(/Working directory set/g, '<span style="color: #2ecc71;">Working directory set</span>')
        .replace(/Output directory created/g, '<span style="color: #27ae60;">Output directory created</span>')
        .replace(/Saved.*:/g, '<span style="color: #27ae60;">$&</span>');
}

// REMOVED: displayGeneratedFiles() - targets non-existent UI element 'files-list', functionality moved to displayGeneratedFilesInline()

function showTablePreview(fileName, content) {
    // Create a modal or expand the results area to show the table
    const generatedTable = document.getElementById('generated-table');
    if (!generatedTable) return;

    const previewHTML = `
        <div style="margin-bottom: 20px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <h5 style="color: #495057; margin: 0;">📋 ${fileName}</h5>
                <button onclick="closeTablePreview()" style="background: #6c757d; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 12px;">
                    ✕ Close Preview
                </button>
            </div>
            <div style="background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; overflow-x: auto; max-height: 600px; overflow-y: auto;">
                ${content}
            </div>
        </div>
    `;

    generatedTable.innerHTML = previewHTML;
    addTerminalLine(`✅ Table preview loaded: ${fileName}`, '#28a745');
}

function closeTablePreview() {
    // Restore the original results display
    if (window.lastExecutionData) {
        displayClinicalTables(window.lastExecutionData);
    }
}

// REMOVED: Duplicate downloadFile() - keeping the first implementation

function toggleTableVisibility(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const isVisible = table.style.display !== 'none';
    table.style.display = isVisible ? 'none' : 'block';

    // Update button text - find the button that was clicked
    const buttons = document.querySelectorAll(`button[onclick*="${tableId}"]`);
    if (buttons.length > 0) {
        buttons[0].textContent = isVisible ? '👁️ Show' : '👁️ Hide';
    }
}

// Additional enhanced functions
function validateBeforeExecution() {
    const rCode = window.currentRCode;
    if (!rCode) {
        alert('No R code available for validation.');
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
            alert('✅ R code validation passed! Ready for execution.');
        } else {
            alert('❌ R code validation failed: ' + data.error + '\\n\\nPlease fix the code before execution.');
        }
    })
    .catch(error => {
        alert('❌ Error validating R code: ' + error);
    });
}

function validateRCodeInEditor() {
    console.log('✅ Validating R code in editor');

    const editor = document.getElementById('step4-rcode-editor');
    if (!editor) return;

    const code = editor.value.trim();
    if (!code) {
        alert('No R code to validate. Please enter R code in the editor.');
        return;
    }

    // Show validation in progress
    const validationMsg = document.createElement('div');
    validationMsg.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 10000; text-align: center;';
    validationMsg.innerHTML = '🔍 <strong>Validating R code...</strong><br><small>AI is analyzing your code</small>';
    document.body.appendChild(validationMsg);

    // Use LLM backend for intelligent R code validation
    fetch('/validate_r_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            r_code: code,
            context: 'clinical_analysis',
            dataset_info: window.currentDatasetInfo || {}
        })
    })
    .then(response => response.json())
    .then(data => {
        document.body.removeChild(validationMsg);

        if (data.success) {
            const validation = data.validation;
            let message = `📊 AI Code Validation Results:\n\n`;
            message += `Score: ${validation.score}% confidence\n\n`;

            if (validation.score >= 70) {
                message += `✅ Code looks good and ready for execution!\n\n`;
            } else {
                message += `⚠️ Code may need improvements:\n`;
                validation.issues.forEach(issue => message += `• ${issue}\n`);
                message += `\n`;
            }

            if (validation.suggestions && validation.suggestions.length > 0) {
                message += `AI Suggestions:\n`;
                validation.suggestions.forEach(suggestion => message += `${suggestion}\n`);
            }

            alert(message);
        } else {
            alert('❌ Validation failed: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        document.body.removeChild(validationMsg);
        console.error('Validation error:', error);
        alert('❌ Unable to validate code. Please check your connection and try again.');
    });
}

// REMOVED: Duplicate displayStep4Results() - keeping the first implementation

function switchCodeView(viewName) {
    console.log(`🔄 Switching to code view: ${viewName}`);

    // Update tab buttons
    ['editor', 'original', 'final', 'changes'].forEach(tab => {
        const button = document.getElementById(`tab-${tab}`);
        if (button) {
            button.style.background = tab === viewName ? '#007bff' : '#6c757d';
        }
    });

    // Show/hide content views
    ['editor', 'original', 'final', 'changes'].forEach(view => {
        const viewDiv = document.getElementById(`view-${view}`);
        if (viewDiv) {
            viewDiv.style.display = view === viewName ? 'block' : 'none';
        }
    });
}

// Code version history management
if (!window.codeVersionHistory) {
    window.codeVersionHistory = [];
}

// ===== OVERRIDE HTML FUNCTIONS WITH JS VERSIONS =====
// Ensure JavaScript file functions take precedence over HTML inline functions

// Make functions globally available with unique names to avoid conflicts
window.sendInteractiveMessage_JS = sendInteractiveMessage;
window.sendQuickMessage_JS = sendQuickMessage;
window.sendInteractiveMessageWithText_JS = sendInteractiveMessageWithText;
window.streamInteractiveResponse_JS = streamInteractiveResponse;

// Update Step 4 provider indicator
function updateStep4ProviderIndicator(provider) {
    const indicator = document.getElementById('step4-provider-indicator');
    if (indicator) {
        const providerName = provider === 'deepseek' ? 'DeepSeek' :
                           provider === 'claude' ? 'Claude' : provider;
        indicator.textContent = `Provider: ${providerName}`;
        indicator.style.background = provider === 'claude' ? '#e8f4fd' : '#f0f9ff';
        indicator.style.color = provider === 'claude' ? '#0066cc' : '#0080ff';
    }
}

// Also override the HTML versions
window.sendInteractiveMessage = sendInteractiveMessage;
window.sendQuickMessage = sendQuickMessage;
window.sendInteractiveMessageWithText = sendInteractiveMessageWithText;
window.streamInteractiveResponse = streamInteractiveResponse;

// Make them available globally
if (typeof globalThis !== 'undefined') {
    globalThis.sendInteractiveMessage = sendInteractiveMessage;
    globalThis.sendQuickMessage = sendQuickMessage;
    globalThis.sendInteractiveMessageWithText = sendInteractiveMessageWithText;
    globalThis.streamInteractiveResponse = streamInteractiveResponse;
}

console.log('🔍 STEP 4 FUNCTIONS: Overriding HTML functions with JS versions');
console.log('🔍 STEP 4 FUNCTIONS: sendInteractiveMessage type:', typeof window.sendInteractiveMessage);
console.log('🔍 STEP 4 FUNCTIONS: streamInteractiveResponse type:', typeof window.streamInteractiveResponse);
console.log('🔍 STEP 4 FUNCTIONS: Functions available globally:', {
    sendInteractiveMessage: typeof sendInteractiveMessage,
    streamInteractiveResponse: typeof streamInteractiveResponse
});

// ===== FILE LOADING COMPLETE =====
console.log('🔍 STEP 4 FUNCTIONS: File loading completed successfully!');
console.log('🔍 STEP 4 FUNCTIONS: Available test functions:', {
    testStep4Basic: typeof window.testStep4Basic,
    testSimpleMessage: typeof window.testSimpleMessage,
    minimalRCodeTest: typeof window.minimalRCodeTest,
    minimalBackendTest: typeof window.minimalBackendTest,
    comprehensiveTest: typeof window.comprehensiveTest
});

console.log('✅ STEP 4 FUNCTIONS: All functions loaded and HTML functions overridden!');

// ===== AGGRESSIVE OVERRIDE ON DOM READY =====
// Ensure our functions override HTML functions even if HTML loads later
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 DOM READY: Re-overriding HTML functions with JS versions...');

    // Force override again
    window.sendInteractiveMessage = sendInteractiveMessage;
    window.sendQuickMessage = sendQuickMessage;
    window.sendInteractiveMessageWithText = sendInteractiveMessageWithText;
    window.streamInteractiveResponse = streamInteractiveResponse;

    console.log('🔧 DOM READY: Functions re-overridden');
    console.log('🔧 DOM READY: streamInteractiveResponse type:', typeof window.streamInteractiveResponse);
});

// ===== FINAL OVERRIDE AFTER PAGE LOAD =====
window.addEventListener('load', function() {
    console.log('🔧 PAGE LOAD: Final override of HTML functions...');

    // Final override
    window.sendInteractiveMessage = sendInteractiveMessage;
    window.sendQuickMessage = sendQuickMessage;
    window.sendInteractiveMessageWithText = sendInteractiveMessageWithText;
    window.streamInteractiveResponse = streamInteractiveResponse;

    console.log('🔧 PAGE LOAD: Final override complete');
    console.log('🔧 PAGE LOAD: streamInteractiveResponse type:', typeof window.streamInteractiveResponse);

    // Test that our function is actually being used
    const testFunc = window.streamInteractiveResponse;
    if (testFunc && testFunc.toString().includes('FRONTEND: streamInteractiveResponse called')) {
        console.log('✅ PAGE LOAD: JavaScript function is active');
    } else {
        console.error('❌ PAGE LOAD: HTML function is still active!');
    }
});

function showCodeVersionHistory() {
    console.log('📚 Showing code version history');

    if (window.codeVersionHistory.length === 0) {
        alert('📚 No code version history available yet. Execute R code with AI debugging to start tracking versions.');
        return;
    }

    let historyHtml = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 12px; padding: 20px; max-width: 80%; max-height: 80%; overflow-y: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
                    <h3 style="color: #495057; margin: 0;">📚 Code Version History</h3>
                    <button onclick="closeCodeHistory()" style="background: #dc3545; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer;">✕ Close</button>
                </div>

                <div style="margin-bottom: 15px; color: #6c757d; font-size: 14px;">
                    📊 Total versions: ${window.codeVersionHistory.length} | Click on any version to restore it to the editor
                </div>
    `;

    window.codeVersionHistory.forEach((version, index) => {
        const isLatest = index === window.codeVersionHistory.length - 1;
        historyHtml += `
            <div onclick="restoreCodeVersion(${index})" style="border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 10px; cursor: pointer; transition: all 0.2s; ${isLatest ? 'border-color: #28a745; background: #f8fff9;' : ''}"
                 onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='${isLatest ? '#f8fff9' : 'white'}'">

                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="font-weight: 600; color: #495057;">
                        📝 Version ${index + 1} ${isLatest ? '(Current)' : ''}
                    </div>
                    <div style="font-size: 12px; color: #6c757d;">
                        ${version.timestamp}
                    </div>
                </div>

                <div style="margin-bottom: 8px;">
                    <span style="background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-right: 8px;">
                        ${version.source}
                    </span>
                    ${version.iterations ? `<span style="background: #fff3e0; color: #f57c00; padding: 2px 6px; border-radius: 3px; font-size: 11px;">${version.iterations} iterations</span>` : ''}
                </div>

                <div style="background: #f8f9fa; border-radius: 4px; padding: 10px; font-family: 'Courier New', monospace; font-size: 11px; max-height: 100px; overflow-y: auto;">
                    ${version.code.substring(0, 200)}${version.code.length > 200 ? '...' : ''}
                </div>

                ${version.description ? `<div style="margin-top: 8px; font-size: 12px; color: #6c757d; font-style: italic;">${version.description}</div>` : ''}
            </div>
        `;
    });

    historyHtml += `
            </div>
        </div>
    `;

    // Add to page
    const historyModal = document.createElement('div');
    historyModal.id = 'code-history-modal';
    historyModal.innerHTML = historyHtml;
    document.body.appendChild(historyModal);
}

function closeCodeHistory() {
    console.log('✕ Closing code version history modal');
    const modal = document.getElementById('code-history-modal');
    if (modal) {
        modal.remove();
    }
}

function restoreCodeVersion(index) {
    console.log(`📚 Restoring code version ${index + 1}`);

    if (!window.codeVersionHistory || !window.codeVersionHistory[index]) {
        console.error('❌ Code version not found:', index);
        return;
    }

    const version = window.codeVersionHistory[index];

    // Load the code into the editor
    const editor = document.getElementById('step4-rcode-editor');
    if (editor) {
        editor.value = version.code;
        window.currentRCode = version.code;

        // Update status indicator
        updateCodeStatusIndicator('📚 Restored', '#6f42c1');

        // Add message to chat
        addInteractiveMessage(`📚 **Restored code version ${index + 1}** from ${version.source} (${version.timestamp})`, 'system');
        addExecutionLogEntry(`📚 Restored version ${index + 1}: ${version.source}`, '#6f42c1');

        console.log(`✅ Code version ${index + 1} restored successfully`);
    } else {
        console.error('❌ R code editor not found');
    }

    // Close the modal
    closeCodeHistory();
}


