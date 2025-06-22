<?php
// Remove the default Content-Type header (let backend set it)
header_remove('Content-Type');

// Get the request method
$method = $_SERVER['REQUEST_METHOD'];

// Get the request path
$request_uri = $_SERVER['REQUEST_URI'];
$path = parse_url($request_uri, PHP_URL_PATH);

// Debug log
error_log("Original request URI: " . $request_uri);
error_log("Parsed path: " . $path);

// Remove 'proxy.php' from the path and any leading/trailing slashes
$path = trim(str_replace('/proxy.php', '', $path), '/');
if (empty($path)) {
    $path = '/';
}

// Debug log
error_log("Final path: " . $path);

// Get the request body
$input = file_get_contents('php://input');

// Set up cURL to connect to local client service
$client_url = "http://localhost:5000" . ($path === '/' ? '' : '/' . $path);
error_log("Forwarding to client URL: " . $client_url);

$ch = curl_init($client_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10); // Increase timeout to 10 seconds
curl_setopt($ch, CURLOPT_TIMEOUT, 30); // Total timeout of 30 seconds
curl_setopt($ch, CURLOPT_HEADER, true); // <--- Important: include headers in response

// Forward headers (including cookies)
$headers = getallheaders();
$forward_headers = [];
foreach ($headers as $key => $value) {
    // Forward all headers except Host (let cURL set it)
    if (strtolower($key) !== 'host') {
        $forward_headers[] = "$key: $value";
    }
}
curl_setopt($ch, CURLOPT_HTTPHEADER, $forward_headers);

// Forward the request body
if ($method === 'POST' && !empty($input)) {
    curl_setopt($ch, CURLOPT_POSTFIELDS, $input);
}

// Forward cookies from browser to backend
if (isset($_SERVER['HTTP_COOKIE'])) {
    curl_setopt($ch, CURLOPT_COOKIE, $_SERVER['HTTP_COOKIE']);
}

// Execute the request
$response = curl_exec($ch);
$header_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
$header_text = substr($response, 0, $header_size);
$body = substr($response, $header_size);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);

// Debug log
error_log("Client response code: " . $http_code);
error_log("Client response: " . $response);

// Check for errors
if (curl_errno($ch)) {
    error_log("Proxy error: " . curl_error($ch));
    http_response_code(500);
    echo json_encode([
        'error' => 'Proxy error: ' . curl_error($ch),
        'details' => [
            'path' => $path,
            'client_url' => $client_url,
            'curl_info' => curl_getinfo($ch)
        ]
    ]);
    exit;
}

// Forward all response headers (including Set-Cookie and Location)
foreach (explode("\r\n", $header_text) as $header_line) {
    if (stripos($header_line, 'Set-Cookie:') === 0 || stripos($header_line, 'Location:') === 0 || stripos($header_line, 'Content-Type:') === 0) {
        header($header_line, false);
    }
}

// Set the HTTP response code
http_response_code($http_code);

// Output the response body
echo $body;

curl_close($ch);
?> 