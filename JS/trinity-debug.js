// Project Trinity Debug Control System

// Trinity Global State
let trinityDebugMode = true;
let trinityStatusContainer = null;
let trinityVersion = '1.0.0';
let trinitySessionId = null;

// Trinity Debug Control Functions
function toggleTrinityDebug() {
    trinityDebugMode = !trinityDebugMode;
    const body = document.body;
    
    if (trinityDebugMode) {
        body.classList.remove('simple-mode');
        body.classList.add('debug-mode');
        document.getElementById('trinity-debug-status').textContent = 'Debug: ON';
        updateTrinityStatus('🔧 Debug mode enabled - showing detailed output', 'info');
        localStorage.setItem('trinity_debug_mode', 'true');
    } else {
        body.classList.remove('debug-mode');
        body.classList.add('simple-mode');
        document.getElementById('trinity-debug-status').textContent = 'Debug: OFF';
        updateTrinityStatus('⚡ Debug mode disabled - showing simplified output', 'warning');
        localStorage.setItem('trinity_debug_mode', 'false');
    }
    
    // Trigger debug mode change event
    const event = new CustomEvent('trinityDebugModeChanged', {
        detail: { debugMode: trinityDebugMode }
    });
    document.dispatchEvent(event);
    
    console.log('Trinity debug mode updated:', trinityDebugMode);
}

function updateTrinityStatus(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const statusDiv = document.createElement('div');
    statusDiv.className = `trinity-status ${type}`;
    
    // Add icon based on type
    let icon = '';
    switch(type) {
        case 'success': icon = '✅'; break;
        case 'error': icon = '❌'; break;
        case 'warning': icon = '⚠️'; break;
        case 'info': icon = 'ℹ️'; break;
        default: icon = '📋'; break;
    }
    
    statusDiv.innerHTML = `<strong>[${timestamp}]</strong> ${icon} ${message}`;
    
    if (!trinityStatusContainer) {
        trinityStatusContainer = document.getElementById('trinity-status-container');
    }
    
    if (trinityStatusContainer) {
        trinityStatusContainer.appendChild(statusDiv);
        trinityStatusContainer.scrollTop = trinityStatusContainer.scrollHeight;
        
        // Auto-remove old entries if too many (keep last 50)
        const entries = trinityStatusContainer.children;
        if (entries.length > 50) {
            trinityStatusContainer.removeChild(entries[0]);
        }
        
        // Add fade-in animation
        statusDiv.style.opacity = '0';
        statusDiv.style.transform = 'translateX(-10px)';
        setTimeout(() => {
            statusDiv.style.transition = 'all 0.3s ease';
            statusDiv.style.opacity = '1';
            statusDiv.style.transform = 'translateX(0)';
        }, 10);
    }
}

function clearTrinityStatus() {
    if (trinityStatusContainer) {
        trinityStatusContainer.innerHTML = '';
        updateTrinityStatus('Status log cleared', 'info');
    }
}

function exportTrinityLogs() {
    if (!trinityStatusContainer) return;
    
    const logs = Array.from(trinityStatusContainer.children).map(child => 
        child.textContent
    ).join('\n');
    
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trinity-debug-logs-${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    updateTrinityStatus('Debug logs exported successfully', 'success');
}

// Initialize Trinity UI System
function initializeTrinityUI() {
    // Call original test UI initialization if it exists
    if (typeof initializeTestUI === 'function') {
        initializeTestUI();
        updateTrinityStatus('Base preflight UI initialized', 'success');
    }
    
    // Generate session ID
    trinitySessionId = 'TR_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    
    // Add Trinity debug control panel
    const debugControl = document.createElement('div');
    debugControl.className = 'trinity-debug-control';
    debugControl.innerHTML = `
        <div class="trinity-brand">🔹 PROJECT TRINITY 🔹</div>
        <div style="margin-bottom: 8px;">
            <span style="font-size: 10px; opacity: 0.7;">Session: ${trinitySessionId}</span>
        </div>
        <div style="margin-bottom: 8px;">
            <span id="trinity-debug-status" class="trinity-debug-label">Debug: ON</span>
            <input type="checkbox" id="trinity-debug-toggle" class="trinity-debug-toggle" 
                   checked onchange="toggleTrinityDebug()">
            <label for="trinity-debug-toggle" class="trinity-debug-label">Detailed</label>
        </div>
        <div style="font-size: 10px;">
            <button onclick="clearTrinityStatus()" style="margin-right: 5px; background: #333; color: #00ff41; border: 1px solid #00ff41; border-radius: 3px; padding: 2px 6px; cursor: pointer;">Clear</button>
            <button onclick="exportTrinityLogs()" style="background: #333; color: #00ff41; border: 1px solid #00ff41; border-radius: 3px; padding: 2px 6px; cursor: pointer;">Export</button>
        </div>
    `;
    document.body.appendChild(debugControl);
    
    // Add Trinity version badge to header
    const header = document.querySelector('.anxlight-header');
    if (header) {
        const versionBadge = document.createElement('div');
        versionBadge.className = 'trinity-version-badge';
        versionBadge.textContent = `v${trinityVersion}`;
        header.style.position = 'relative';
        header.appendChild(versionBadge);
        
        // Add matrix background effect
        const matrixBg = document.createElement('div');
        matrixBg.className = 'trinity-matrix-bg';
        header.appendChild(matrixBg);
    }
    
    // Add Trinity status container  
    const statusContainer = document.createElement('div');
    statusContainer.id = 'trinity-status-container';
    statusContainer.className = 'debug-info trinity-status-container';
    
    const testContainer = document.querySelector('.test-container');
    if (testContainer) {
        // Add status container header
        const statusHeader = document.createElement('div');
        statusHeader.innerHTML = '<strong>🔧 Trinity Debug Console</strong>';
        statusHeader.style.cssText = 'color: #00ff41; margin-bottom: 10px; font-family: "Courier New", monospace;';
        statusContainer.appendChild(statusHeader);
        
        testContainer.appendChild(statusContainer);
        trinityStatusContainer = statusContainer;
    }
    
    // Load debug mode from localStorage if available
    const savedDebugMode = localStorage.getItem('trinity_debug_mode');
    if (savedDebugMode === 'false') {
        document.getElementById('trinity-debug-toggle').checked = false;
        toggleTrinityDebug();
    }
    
    // Add Trinity-specific keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+Shift+T: Toggle debug mode
        if (e.ctrlKey && e.shiftKey && e.key === 'T') {
            e.preventDefault();
            document.getElementById('trinity-debug-toggle').click();
        }
        
        // Ctrl+Shift+C: Clear logs
        if (e.ctrlKey && e.shiftKey && e.key === 'C') {
            e.preventDefault();
            clearTrinityStatus();
        }
        
        // Ctrl+Shift+E: Export logs
        if (e.ctrlKey && e.shiftKey && e.key === 'E') {
            e.preventDefault();
            exportTrinityLogs();
        }
    });
    
    updateTrinityStatus('Trinity UI system initialized successfully', 'success');
    updateTrinityStatus('Keyboard shortcuts: Ctrl+Shift+T (toggle), Ctrl+Shift+C (clear), Ctrl+Shift+E (export)', 'info');
}

// Enhanced Progress Tracking
function updateTrinityProgress(completed, total, operation = '') {
    const percentage = Math.round((completed / total) * 100);
    const progressFill = document.getElementById('progress-fill');
    
    if (progressFill) {
        progressFill.style.width = percentage + '%';
        progressFill.textContent = percentage + '%';
        
        // Add Trinity-style glow effect
        if (percentage === 100) {
            progressFill.style.boxShadow = '0 0 20px rgba(0, 255, 65, 0.6)';
        }
    }
    
    if (operation) {
        updateTrinityStatus(`Progress: ${percentage}% - ${operation}`, 'info');
    }
    
    // Update window title with progress
    if (percentage < 100) {
        document.title = `Trinity [${percentage}%] - Setup in Progress`;
    } else {
        document.title = 'Trinity - Setup Complete';
    }
}

// Test Result Integration
function updateTrinityTestResult(testName, status, details = '') {
    // Call original test card update if available
    if (typeof updateTestCard === 'function') {
        updateTestCard(testName, status, details);
    }
    
    // Add to Trinity status log
    let message = `Test: ${testName} - ${status.toUpperCase()}`;
    if (details) {
        message += ` (${details})`;
    }
    
    let logType = 'info';
    if (status === 'success') logType = 'success';
    else if (status === 'error' || status === 'failed') logType = 'error';
    else if (status === 'warning') logType = 'warning';
    
    updateTrinityStatus(message, logType);
}

// Enhanced Console Integration
const originalConsoleLog = console.log;
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

console.log = function(...args) {
    originalConsoleLog.apply(console, args);
    if (trinityDebugMode) {
        const message = args.join(' ');
        updateTrinityStatus(`[LOG] ${message}`, 'info');
    }
};

console.error = function(...args) {
    originalConsoleError.apply(console, args);
    const message = args.join(' ');
    updateTrinityStatus(`[ERROR] ${message}`, 'error');
};

console.warn = function(...args) {
    originalConsoleWarn.apply(console, args);
    const message = args.join(' ');
    updateTrinityStatus(`[WARN] ${message}`, 'warning');
};

// Trinity Performance Monitoring
const trinityPerformance = {
    startTime: Date.now(),
    milestones: [],
    
    mark: function(name) {
        const time = Date.now() - this.startTime;
        this.milestones.push({ name, time });
        updateTrinityStatus(`⏱️ Milestone: ${name} (${time}ms)`, 'info');
    },
    
    report: function() {
        const total = Date.now() - this.startTime;
        updateTrinityStatus(`📊 Total execution time: ${total}ms`, 'success');
        
        if (trinityDebugMode) {
            this.milestones.forEach(milestone => {
                updateTrinityStatus(`  └─ ${milestone.name}: ${milestone.time}ms`, 'info');
            });
        }
    }
};

// Auto-initialization when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        if (typeof initializeTrinityUI === 'function') {
            // Trinity system should be initialized by the main script
        }
    }, 100);
});

// Trinity Error Handling
window.addEventListener('error', function(e) {
    updateTrinityStatus(`💥 JavaScript Error: ${e.message} (${e.filename}:${e.lineno})`, 'error');
});

window.addEventListener('unhandledrejection', function(e) {
    updateTrinityStatus(`💥 Unhandled Promise Rejection: ${e.reason}`, 'error');
});

// Export Trinity functions for external use
window.Trinity = {
    updateStatus: updateTrinityStatus,
    updateProgress: updateTrinityProgress,
    updateTestResult: updateTrinityTestResult,
    toggleDebug: toggleTrinityDebug,
    clearStatus: clearTrinityStatus,
    exportLogs: exportTrinityLogs,
    performance: trinityPerformance,
    version: trinityVersion,
    sessionId: trinitySessionId
};