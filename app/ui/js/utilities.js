/**
 * Utility Functions
 * Common helper functions used across the application
 */

// HTML and Text Processing
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatCode(code) {
    if (!code) return '';
    
    // Basic code formatting
    return code
        .replace(/\t/g, '    ') // Convert tabs to spaces
        .replace(/\r\n/g, '\n') // Normalize line endings
        .trim();
}

function formatConsoleOutput(output) {
    if (!output) return '';
    
    // Remove ANSI color codes and format console output
    return output
        .replace(/\x1b\[[0-9;]*m/g, '') // Remove ANSI codes
        .replace(/\r\n/g, '\n')
        .trim();
}

// File and Data Processing
function getFileExtension(fileName) {
    if (!fileName) return '';
    const lastDot = fileName.lastIndexOf('.');
    return lastDot > 0 ? fileName.substring(lastDot + 1).toLowerCase() : '';
}

function getFileMetadata(fileName) {
    const extension = getFileExtension(fileName);
    
    const metadata = {
        name: fileName,
        extension: extension,
        type: 'unknown',
        icon: '📄',
        description: 'File'
    };
    
    // Determine file type and icon
    switch (extension) {
        case 'csv':
            metadata.type = 'data';
            metadata.icon = '📊';
            metadata.description = 'CSV Data File';
            break;
        case 'html':
        case 'htm':
            metadata.type = 'report';
            metadata.icon = '📄';
            metadata.description = 'HTML Report';
            break;
        case 'png':
        case 'jpg':
        case 'jpeg':
        case 'gif':
            metadata.type = 'image';
            metadata.icon = '🖼️';
            metadata.description = 'Image File';
            break;
        case 'pdf':
            metadata.type = 'document';
            metadata.icon = '📋';
            metadata.description = 'PDF Document';
            break;
        case 'r':
            metadata.type = 'code';
            metadata.icon = '📊';
            metadata.description = 'R Script';
            break;
        case 'txt':
        case 'log':
            metadata.type = 'text';
            metadata.icon = '📝';
            metadata.description = 'Text File';
            break;
        default:
            metadata.type = 'unknown';
            metadata.icon = '📄';
            metadata.description = 'File';
    }
    
    return metadata;
}

// Date and Time Utilities
function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    
    try {
        const date = new Date(timestamp);
        return date.toLocaleString();
    } catch (error) {
        return timestamp;
    }
}

function getElapsedTime(startTime) {
    if (!startTime) return '0s';
    
    const elapsed = Date.now() - startTime;
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else {
        return `${seconds}s`;
    }
}

// Data Validation
function validateDatasetPath(path) {
    if (!path || typeof path !== 'string') {
        return { valid: false, error: 'Dataset path is required' };
    }
    
    const trimmedPath = path.trim();
    if (trimmedPath.length === 0) {
        return { valid: false, error: 'Dataset path cannot be empty' };
    }
    
    // Basic path validation
    const validExtensions = ['.csv', '.sas7bdat', '.xpt', '.xlsx', '.txt'];
    const hasValidExtension = validExtensions.some(ext => 
        trimmedPath.toLowerCase().endsWith(ext)
    );
    
    if (!hasValidExtension) {
        return { 
            valid: false, 
            error: `Dataset path should end with one of: ${validExtensions.join(', ')}` 
        };
    }
    
    return { valid: true, path: trimmedPath };
}

function validateQuery(query) {
    if (!query || typeof query !== 'string') {
        return { valid: false, error: 'Query is required' };
    }
    
    const trimmedQuery = query.trim();
    if (trimmedQuery.length === 0) {
        return { valid: false, error: 'Query cannot be empty' };
    }
    
    if (trimmedQuery.length < 10) {
        return { valid: false, error: 'Query should be at least 10 characters long' };
    }
    
    return { valid: true, query: trimmedQuery };
}

function validateRCode(code) {
    if (!code || typeof code !== 'string') {
        return { valid: false, error: 'R code is required' };
    }
    
    const trimmedCode = code.trim();
    if (trimmedCode.length === 0) {
        return { valid: false, error: 'R code cannot be empty' };
    }
    
    // Basic R code validation
    const hasLibraryCall = /library\s*\(/.test(trimmedCode);
    const hasDataRead = /(read\.|read_)/.test(trimmedCode);
    
    if (!hasLibraryCall && !hasDataRead) {
        return { 
            valid: false, 
            error: 'R code should typically include library() calls and data reading functions' 
        };
    }
    
    return { valid: true, code: trimmedCode };
}

// UI Helper Functions
function showLoading(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="loading">🔄 ${message}</div>`;
        element.classList.add('loading-state');
    }
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('loading-state');
    }
}

function showError(elementId, error) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="error">❌ ${error}</div>`;
        element.classList.add('error-state');
    }
}

function clearError(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('error-state');
    }
}

// Local Storage Utilities
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
        return false;
    }
}

function loadFromLocalStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return null;
    }
}

function removeFromLocalStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Failed to remove from localStorage:', error);
        return false;
    }
}

// Network Utilities
function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    return fetch(url, finalOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        });
}

function downloadBlob(blob, fileName) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Markdown Processing
function convertMarkdownTableToHTML(markdownTable) {
    if (!markdownTable || typeof markdownTable !== 'string') {
        return '';
    }
    
    const lines = markdownTable.trim().split('\n');
    if (lines.length < 2) return markdownTable;
    
    let html = '<table class="markdown-table">\n';
    
    // Process header
    const headerCells = lines[0].split('|').map(cell => cell.trim()).filter(cell => cell);
    html += '  <thead>\n    <tr>\n';
    headerCells.forEach(cell => {
        html += `      <th>${escapeHtml(cell)}</th>\n`;
    });
    html += '    </tr>\n  </thead>\n';
    
    // Skip separator line (line 1)
    if (lines.length > 2) {
        html += '  <tbody>\n';
        for (let i = 2; i < lines.length; i++) {
            const cells = lines[i].split('|').map(cell => cell.trim()).filter(cell => cell);
            if (cells.length > 0) {
                html += '    <tr>\n';
                cells.forEach(cell => {
                    html += `      <td>${escapeHtml(cell)}</td>\n`;
                });
                html += '    </tr>\n';
            }
        }
        html += '  </tbody>\n';
    }
    
    html += '</table>';
    return html;
}

// Debug and Logging
function debugLog(message, data = null) {
    if (window.DEBUG_MODE) {
        console.log(`🔍 DEBUG: ${message}`, data);
    }
}

function errorLog(message, error = null) {
    console.error(`❌ ERROR: ${message}`, error);
}

// Global error handler
window.addEventListener('error', function(event) {
    errorLog('Global error caught:', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
    });
});

// Export utilities to global scope for backward compatibility
window.utilities = {
    escapeHtml,
    formatCode,
    formatConsoleOutput,
    getFileExtension,
    getFileMetadata,
    formatTimestamp,
    getElapsedTime,
    validateDatasetPath,
    validateQuery,
    validateRCode,
    showLoading,
    hideLoading,
    showError,
    clearError,
    saveToLocalStorage,
    loadFromLocalStorage,
    removeFromLocalStorage,
    makeRequest,
    downloadBlob,
    convertMarkdownTableToHTML,
    debugLog,
    errorLog
};
