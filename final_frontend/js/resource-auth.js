document.addEventListener('DOMContentLoaded', function() {
    const resourceLoginForm = document.getElementById('resourceLoginForm');
    const alertContainer = document.getElementById('alert-container');
    const loginButton = document.getElementById('resourceLoginButton');

    function showAlert(message, type = 'error') {
        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                ${message}
            </div>
        `;
    }

    async function authenticateResource(username, password, operation) {
        try {
            console.log('Authenticating with:', { username, operation });
            const response = await fetch('proxy.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    username,
                    password,
                    operation
                })
            });

            console.log('Response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
                throw new Error(`Authentication failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Authentication successful:', data);
            return data;
        } catch (error) {
            console.error('Authentication error:', error);
            showAlert(`Authentication failed: ${error.message}`);
            throw error;
        }
    }

    resourceLoginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('resourceUsername').value;
        const password = document.getElementById('resourcePassword').value;
        const operation = document.getElementById('operation').value;

        if (!username || !password || !operation) {
            showAlert('Please fill in all fields');
            return;
        }

        try {
            // Disable the login button and show loading state
            loginButton.disabled = true;
            loginButton.textContent = 'Authenticating...';
            alertContainer.innerHTML = '';

            // Authenticate
            const authResult = await authenticateResource(username, password, operation);

            // Handle successful authentication
            if (authResult.status === 'success') {
                showAlert('Authentication successful!', 'success');
                
                // Store authentication data in session via PHP
                const response = await fetch('store_resource_auth.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        token: authResult.token,
                        operation: operation,
                        resource: authResult.resource,
                        action: authResult.action
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to store authentication data');
                }

                // Reload the page to show success state
                window.location.href = '/success.php';
            } else {
                throw new Error(authResult.message || 'Authentication failed');
            }
        } catch (error) {
            console.error('Login process failed:', error);
            showAlert(error.message);
        } finally {
            // Re-enable the login button
            loginButton.disabled = false;
            loginButton.textContent = 'Authenticate Resource';
        }
    });
}); 