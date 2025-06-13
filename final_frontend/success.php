<?php
session_start();

// Check if user is authenticated
if (!isset($_SESSION['authenticated']) || !$_SESSION['authenticated']) {
    header('Location: index.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authentication Successful</title>
    <link rel="stylesheet" href="css/style.css">
    <style>
        .success-box {
            text-align: center;
            padding: 20px;
        }
        .success-icon {
            color: var(--success-color);
            font-size: 48px;
            margin-bottom: 20px;
        }
        .logout-btn {
            margin-top: 20px;
            background-color: var(--error-color);
        }
        .logout-btn:hover {
            background-color: #c0392b;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="login-box success-box">
            <i class="fas fa-check-circle success-icon"></i>
            <h2>Authentication Successful</h2>
            <p>Welcome, <?php echo htmlspecialchars($_SESSION['username']); ?>!</p>
            <p>You are now connected to the network.</p>
            <form action="logout.php" method="POST">
                <button type="submit" class="login-btn logout-btn">Logout</button>
            </form>
        </div>
    </div>
</body>
</html>
