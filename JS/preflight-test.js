// AnxLight Pre-Flight Testing UI JavaScript
window.testResults = {};
window.totalTests = 0;
window.completedTests = 0;

function updateTestCard(testName, status, details) {
    const testId = testName.replace(/[^a-zA-Z0-9]/g, '-');
    let card = document.getElementById(`test-${testId}`);
    
    if (!card) {
        // Create new test card
        card = document.createElement('div');
        card.id = `test-${testId}`;
        card.className = 'test-card testing';
        card.innerHTML = `
            <div class="test-title">
                ${testName}
                <span class="test-status"><div class="loading-spinner"></div></span>
            </div>
            <div class="test-details">Testing...</div>
        `;
        document.getElementById('test-grid').appendChild(card);
    }
    
    // Update status
    const statusIcons = {
        'passed': '✅',
        'failed': '❌',
        'warning': '⚠️',
        'testing': '<div class="loading-spinner"></div>'
    };
    
    card.className = `test-card ${status}`;
    card.querySelector('.test-status').innerHTML = statusIcons[status] || '❓';
    card.querySelector('.test-details').innerHTML = details || 'No details';
    
    // Update progress
    if (status !== 'testing') {
        window.completedTests++;
        const progress = Math.round((window.completedTests / window.totalTests) * 100);
        document.getElementById('progress-fill').style.width = progress + '%';
        document.getElementById('progress-fill').innerHTML = progress + '%';
    }
}

function showSummary(passed, warning, failed) {
    const summaryHtml = `
        <div class="summary-box">
            <div class="summary-title">🎯 Testing Complete!</div>
            <div class="summary-stats">
                <div class="stat-item">
                    <div class="stat-number" style="color: #4ade80;">${passed}</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" style="color: #fbbf24;">${warning}</div>
                    <div class="stat-label">Warnings</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" style="color: #f87171;">${failed}</div>
                    <div class="stat-label">Failed</div>
                </div>
            </div>
        </div>
    `;
    document.getElementById('test-results').insertAdjacentHTML('beforeend', summaryHtml);
}

function initializeTestUI() {
    console.log('AnxLight Pre-Flight Test UI Initialized');
}
