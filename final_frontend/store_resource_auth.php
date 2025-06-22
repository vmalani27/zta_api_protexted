<?php
session_start();
header('Content-Type: application/json');

// Check if network authentication is successful
if (!isset($_SESSION['network_authenticated']) || !$_SESSION['network_authenticated']) {
    http_response_code(401);
    echo json_encode(['error' => 'Network authentication required']);
    exit;
}

// Get JSON data from request
$json = file_get_contents('php://input');
$data = json_decode($json, true);

if (!$data || !isset($data['token']) || !isset($data['operation'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid request data']);
    exit;
}

// Store resource authentication data in session
$_SESSION['resource_authenticated'] = true;
$_SESSION['resource_token'] = $data['token'];
$_SESSION['operation'] = $data['operation'];
$_SESSION['resource'] = $data['resource'] ?? null;
$_SESSION['action'] = $data['action'] ?? null;

echo json_encode(['status' => 'success']);
?> 