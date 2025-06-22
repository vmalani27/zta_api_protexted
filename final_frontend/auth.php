<?php
header('Content-Type: application/json');

// Function to call FreeRADIUS
function authenticateWithRadius($username, $password) {
    // Use radtest for FreeRADIUS authentication
    $command = sprintf(
        'radtest %s %s 127.0.0.1 0 testing123',
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
    $_SESSION['network_authenticated'] = true;  // Set network authentication flag
    $_SESSION['username'] = $username;
    
    echo json_encode([
        'success' => true,
        'message' => 'Network authentication successful',
        'redirect' => 'success.php'
    ]);
} else {
    echo json_encode([
        'success' => false,
        'message' => 'Invalid username or password'
    ]);
}
?>
