<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Authentication</title>
    <link rel="stylesheet" href="css/style.css">
    <!-- Add Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <div class="login-box">
            <div class="logo">
                <img src="img/logo.png" alt="Logo" class="logo-img">
            </div>
            <h2>Network Authentication</h2>
            <form id="loginForm" action="auth.php" method="POST">
                <div class="input-group">
                    <i class="fas fa-user"></i>
                    <input type="text" name="username" id="username" placeholder="Username" required>
                </div>
                <div class="input-group">
                    <i class="fas fa-lock"></i>
                    <input type="password" name="password" id="password" placeholder="Password" required>
                </div>
                <div class="remember-forgot">
                    <label>
                        <input type="checkbox" name="remember"> Remember me
                    </label>
                    <a href="#" class="forgot-link">Forgot Password?</a>
                </div>
                <button type="submit" class="login-btn">Login</button>
                <div id="error-message" class="error-message"></div>
            </form>
        </div>
    </div>
    <script src="js/script.js"></script>
</body>
</html>