// Main JavaScript for ZTA Frontend

// Check session status on page load
document.addEventListener('DOMContentLoaded', function() {
    checkSessionStatus();
});

// Login button handler
const loginBtn = document.getElementById('login-btn');
if (loginBtn) {
    loginBtn.addEventListener('click', function() {
        window.location.href = '/login';
    });
}

// Check session status
async function checkSessionStatus() {
    try {
        const response = await fetch('/session-status');
        const data = await response.json();
        
        const statusIndicator = document.getElementById('session-status');
        const statusText = document.getElementById('status-text');
        
        if (data.resource_authenticated) {
            if (statusIndicator) {
                statusIndicator.classList.add('active');
            }
            if (statusText) {
                statusText.textContent = 'Authenticated';
            }
            
            // If on index page and authenticated, could redirect to success
            if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
                // Optional: Auto-redirect to success page
                // window.location.href = '/success.html';
            }
        } else {
            if (statusIndicator) {
                statusIndicator.classList.remove('active');
            }
            if (statusText) {
                statusText.textContent = 'Not Authenticated';
            }
        }
    } catch (error) {
        console.error('Error checking session status:', error);
    }
}

// Logout function
function logout() {
    // Clear session cookie
    document.cookie = 'zta_session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    
    // Redirect to home page
    window.location.href = '/';
}

// Get session ID from cookie
function getSessionId() {
    const name = 'zta_session_id=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return null;
}
