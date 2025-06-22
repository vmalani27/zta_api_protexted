<?php
// Logging access to this page
$log_file = __DIR__ . '/access_log.txt';
$log_entry = date('Y-m-d H:i:s') . " | URI: " . $_SERVER['REQUEST_URI'] . " | Query: " . http_build_query($_GET) . "\n";
file_put_contents($log_file, $log_entry, FILE_APPEND);

session_start();

// Check if network authentication is successful
if (!isset($_SESSION['network_authenticated']) || !$_SESSION['network_authenticated']) {
    header('Location: index.php');
    exit;
}

// Check if resource authentication is successful
$resource_authenticated = isset($_SESSION['resource_authenticated']) && $_SESSION['resource_authenticated'];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authentication Status</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .success-box {
            text-align: center;
            padding: 20px;
            margin-bottom: 20px;
        }
        .success-icon {
            color: var(--success-color);
            font-size: 48px;
            margin-bottom: 20px;
        }
        .resource-form {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
        .logout-btn {
            margin-top: 20px;
            background-color: var(--error-color);
        }
        .logout-btn:hover {
            background-color: #c0392b;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9em;
            margin-left: 10px;
        }
        .status-success {
            background-color: var(--success-color);
            color: white;
        }
        .status-pending {
            background-color: #f1c40f;
            color: black;
        }
        #alert-container {
            margin: 10px 0;
        }
        .status-indicator {
            margin: 20px 0;
            padding: 15px;
            border-radius: 5px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
        }
        .status-indicator.online {
            background-color: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }
        .status-indicator.offline {
            background-color: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }
        .status-indicator.checking {
            background-color: #fff3cd;
            border-color: #ffeeba;
            color: #856404;
        }
        .status-details {
            margin-top: 10px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card mt-5">
                    <div class="card-header">
                        <h3 class="text-center">Resource Authentication</h3>
                    </div>
                    <div class="card-body">
                        <!-- Add Keycloak status indicator -->
                        <div id="keycloak-status" class="status-indicator checking">
                            <div class="d-flex justify-content-between align-items-center">
                                <span>Keycloak Status: <span id="status-text">Checking...</span></span>
                                <button class="btn btn-sm btn-outline-secondary" onclick="checkKeycloakStatus()">
                                    Refresh Status
                                </button>
                            </div>
                            <div id="status-details" class="status-details"></div>
                        </div>

                        <!-- Alert container -->
                        <div id="alert-container"></div>

                        <!-- Network Authentication Status -->
                        <div class="login-box success-box">
                            <i class="fas fa-check-circle success-icon"></i>
                            <h2>Network Authentication Successful</h2>
                            <p>Welcome, <?php echo htmlspecialchars($_SESSION['username']); ?>!</p>
                            <p>Network Status: <span class="status-badge status-success">Connected</span></p>
                        </div>

                        <!-- Resource Authentication Form -->
                        <?php if (!$resource_authenticated): ?>
                        <div class="login-box">
                            <h2>Resource Authentication</h2>
                            <div id="alert-container"></div>
                            <!-- Intent Selection Modal/Page -->
                            <form id="intentForm" action="proxy.php/login" method="GET">
                                <label for="operation">Select Operation:</label>
                                <select name="operation" id="operation" required>
                                    <option value="">Select Operation</option>
                                    <optgroup label="Admin Operations">
                                        <option value="adminCreateUser">Create User</option>
                                        <option value="adminReadUser">View Users</option>
                                        <option value="adminUpdateUser">Update User</option>
                                        <option value="adminDeleteUser">Delete User</option>
                                        <option value="adminCreateStudent">Create Student</option>
                                        <option value="adminReadStudent">View Students</option>
                                        <option value="adminUpdateStudent">Update Student</option>
                                        <option value="adminDeleteStudent">Delete Student</option>
                                        <option value="adminCreateTeacher">Create Teacher</option>
                                        <option value="adminReadTeacher">View Teachers</option>
                                        <option value="adminUpdateTeacher">Update Teacher</option>
                                        <option value="adminDeleteTeacher">Delete Teacher</option>
                                        <option value="adminCreateHostel">Create Hostel</option>
                                        <option value="adminReadHostel">View Hostels</option>
                                        <option value="adminUpdateHostel">Update Hostel</option>
                                        <option value="adminDeleteHostel">Delete Hostel</option>
                                        <option value="adminCreateWarden">Create Warden</option>
                                        <option value="adminReadWarden">View Wardens</option>
                                        <option value="adminUpdateWarden">Update Warden</option>
                                        <option value="adminDeleteWarden">Delete Warden</option>
                                    </optgroup>
                                    <optgroup label="Teacher Operations">
                                        <option value="teacherReadStudent">View Students</option>
                                        <option value="teacherUpdateStudent">Update Student</option>
                                    </optgroup>
                                    <optgroup label="Warden Operations">
                                        <option value="wardenReadStudent">View Students</option>
                                        <option value="wardenReadHostel">View Hostels</option>
                                        <option value="wardenUpdateHostel">Update Hostel</option>
                                        <option value="wardenReadWarden">View Wardens</option>
                                    </optgroup>
                                    <optgroup label="Student Operations">
                                        <option value="studentReadProfile">View Profile</option>
                                    </optgroup>
                                </select>
                                <button type="submit" class="login-btn" id="intentLoginButton">Continue with Keycloak Login</button>
                            </form>
                        </div>
                        <?php else: ?>
                        <div class="login-box success-box">
                            <i class="fas fa-check-circle success-icon"></i>
                            <h2>Resource Authentication Successful</h2>
                            <p>Resource Status: <span class="status-badge status-success">Authenticated</span></p>
                            <p>Operation: <?php echo htmlspecialchars($_SESSION['operation']); ?></p>
                            <form action="logout.php" method="POST">
                                <button type="submit" class="login-btn logout-btn">Logout</button>
                            </form>
                        </div>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="js/resource-auth.js"></script>
    <script>
        // Function to check Keycloak status
        async function checkKeycloakStatus() {
            const statusDiv = document.getElementById('keycloak-status');
            const statusText = document.getElementById('status-text');
            const statusDetails = document.getElementById('status-details');
            
            try {
                statusDiv.className = 'status-indicator checking';
                statusText.textContent = 'Checking...';
                statusDetails.textContent = '';

                // Use proxy.php for all requests
                const response = await fetch('proxy.php/test-keycloak');
                const data = await response.json();

                if (data.status === 'success') {
                    statusDiv.className = 'status-indicator online';
                    statusText.textContent = 'Online';
                    statusDetails.textContent = `Connected to ${data.url}`;
                } else {
                    statusDiv.className = 'status-indicator offline';
                    statusText.textContent = 'Offline';
                    statusDetails.textContent = `Error: ${data.message}`;
                }
            } catch (error) {
                statusDiv.className = 'status-indicator offline';
                statusText.textContent = 'Offline';
                statusDetails.textContent = `Error: ${error.message}`;
                console.error('Keycloak status check failed:', error);
            }
        }

        // Check status when page loads
        document.addEventListener('DOMContentLoaded', function() {
            checkKeycloakStatus();
        });
    </script>
</body>
</html>
