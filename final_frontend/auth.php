<?php
header('Content-Type: application/json');

// Function to call FreeRADIUS
function authenticateWithRadius($username, $password) {
    // This is a placeholder. You'll need to implement the actual FreeRADIUS authentication
    // using the appropriate method (e.g., radclient, PAM, or direct socket communication)
    
    // Example using radclient (you'll need to install it: sudo apt-get install freeradius-utils)
    $command = sprintf(
        'echo "User-Name=%s,User-Password=%s" | radclient -x localhost auth testing123',
        escapeshellarg($username),
        escapeshellarg($password)
    );
    
    exec($command, $output, $return_var);
    
    // Check the output for success
    $output_str = implode("\n", $output);
    return strpos($output_str, 'Access-Accept') !== false;
}

// Get POST data
$username = $_POST['username'] ?? '';
$password = $_POST['password'] ?? '';

// Validate input
if (empty($username) || empty($password)) {
    echo json_encode([
        'success' => false,
        'message' => 'Username and password are required'
    ]);
    exit;
}

// Attempt authentication
if (authenticateWithRadius($username, $password)) {
    // Start session and store user info
    session_start();
    $_SESSION['authenticated'] = true;
    $_SESSION['username'] = $username;
    
    echo json_encode([
        'success' => true,
        'message' => 'Authentication successful',
        'redirect' => 'success.php'
    ]);
} else {
    echo json_encode([
        'success' => false,
        'message' => 'Invalid username or password'
    ]);
}
?>
