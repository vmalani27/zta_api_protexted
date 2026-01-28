// Success page specific JavaScript

// Load user information on page load
document.addEventListener('DOMContentLoaded', function() {
    loadUserInfo();
    checkSessionStatus();
});

// Load user information
async function loadUserInfo() {
    const sessionId = getSessionId();
    const sessionIdElement = document.getElementById('session-id');
    
    if (sessionIdElement) {
        sessionIdElement.textContent = sessionId ? sessionId.substring(0, 16) + '...' : 'N/A';
    }
    
    // Get user info from session status API
    try {
        const response = await fetch('/session-status');
        const data = await response.json();
        
        if (data.resource_authenticated) {
            updateSessionStatus('Active', true);
            
            // Display actual roles from the session
            displayRoles(data.roles || []);
        } else {
            updateSessionStatus('Inactive', false);
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Error loading user info:', error);
        displayRoles(['Error loading roles']);
    }
}

// Update session status
function updateSessionStatus(status, isActive) {
    const statusElement = document.getElementById('session-status');
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = isActive ? 'badge badge-success' : 'badge';
    }
}

// Display user roles
function displayRoles(roles) {
    const rolesContainer = document.getElementById('user-roles');
    if (!rolesContainer) return;
    
    rolesContainer.innerHTML = '';
    
    if (roles && roles.length > 0) {
        roles.forEach(role => {
            const badge = document.createElement('span');
            badge.className = 'role-badge';
            badge.textContent = role;
            rolesContainer.appendChild(badge);
        });
    } else {
        rolesContainer.innerHTML = '<span class="loading">No roles assigned</span>';
    }
}

// Test PEP service
async function testPEP() {
    showTestResults('Testing PEP service...\nPerforming port knocking sequence...');
    
    try {
        const response = await fetch('/api/test-pep', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            showTestResults(`Error: ${error.detail || 'Failed to test PEP'}`);
            return;
        }
        
        const result = await response.json();
        showTestResults(JSON.stringify(result, null, 2));
    } catch (error) {
        showTestResults(`Error: ${error.message}`);
    }
}

// Test PDP service
async function testPDP() {
    showTestResults('Testing PDP service...\nPerforming port knocking sequence...');
    
    try {
        const response = await fetch('/api/test-pdp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            showTestResults(`Error: ${error.detail || 'Failed to test PDP'}`);
            return;
        }
        
        const result = await response.json();
        showTestResults(JSON.stringify(result, null, 2));
    } catch (error) {
        showTestResults(`Error: ${error.message}`);
    }
}

// Test full ZTA flow with resource access
async function testResourceAccess(operation = 'studentReadProfile') {
    showTestResults(`Testing full ZTA flow...\nOperation: ${operation}\nPerforming port knocking and policy checks...`);
    
    try {
        const response = await fetch('/api/access-resource', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ operation })
        });
        
        if (!response.ok) {
            const error = await response.json();
            showTestResults(`Error: ${error.detail || 'Failed to access resource'}`);
            return;
        }
        
        const result = await response.json();
        showTestResults(JSON.stringify(result, null, 2));
    } catch (error) {
        showTestResults(`Error: ${error.message}`);
    }
}

// Show test results
function showTestResults(content) {
    const resultsDiv = document.getElementById('test-results');
    const resultsContent = document.getElementById('results-content');
    
    if (resultsDiv && resultsContent) {
        resultsContent.textContent = content;
        resultsDiv.style.display = 'block';
        
        // Scroll to results
        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Check session status (redefine for success page)
async function checkSessionStatus() {
    try {
        const response = await fetch('/session-status');
        const data = await response.json();
        
        if (!data.resource_authenticated) {
            // Redirect to home if not authenticated
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Error checking session status:', error);
    }
}
