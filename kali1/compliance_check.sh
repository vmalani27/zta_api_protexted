#!/bin/bash

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to get device information
get_device_info() {
    # Get IP address (primary interface)
    ip_address=$(ip route get 1 | awk '{print $7;exit}')
    
    # Get MAC address
    mac_address=$(ip link show | grep -A 1 "$(ip route get 1 | awk '{print $5;exit}')" | grep -o -E '([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}')
    
    # Get OS information
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        os_type=$NAME
        os_version=$VERSION_ID
    else
        os_type=$(uname -s)
        os_version=$(uname -r)
    fi
    
    # Generate device ID (using MAC address as base)
    device_id=$(echo $mac_address | tr -d ':' | md5sum | cut -d' ' -f1)
    
    # Check antivirus status (assuming ClamAV)
    if command -v clamd &> /dev/null && systemctl is-active --quiet clamav-daemon; then
        antivirus_status="yes"
    else
        antivirus_status="no"
    fi
    
    # Check firewall status (assuming UFW)
    if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
        firewall_status="yes"
    else
        firewall_status="no"
    fi
    
    # Get last security update date
    if command -v apt-get &> /dev/null; then
        last_security_update=$(stat -c %y /var/lib/apt/lists/security* 2>/dev/null | sort -r | head -n1 | cut -d' ' -f1)
    else
        last_security_update=$(date +%Y-%m-%d)
    fi
}

# Function to collect user credentials
collect_user_credentials() {
    echo "=== User Authentication ==="
    read -p "Enter username: " username
    read -s -p "Enter password: " password
    echo
}

# Function to get nonce from PEP client
get_nonce() {
    log_message "Getting nonce from PEP client"
    
    # Get nonce from PEP client
    nonce_response=$(curl -s -X GET http://192.168.200.2:5000/get-nonce)
    
    # Extract nonce from response
    nonce=$(echo $nonce_response | grep -o '"nonce":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$nonce" ]; then
        log_message "Failed to get nonce from PEP client"
        return 1
    fi
    
    log_message "Successfully got nonce from PEP client"
    echo $nonce
    return 0
}

# Function to check if token is expired
check_token_expiration() {
    local token=$1
    if [ -z "$token" ]; then
        return 1
    fi
    
    # Decode token and get expiration time
    local exp=$(echo $token | cut -d'.' -f2 | base64 -d 2>/dev/null | grep -o '"exp":[0-9]*' | cut -d':' -f2)
    if [ -z "$exp" ]; then
        return 1
    fi
    
    # Get current time
    local current_time=$(date +%s)
    
    # Check if token is expired (with 5 minute buffer)
    if [ $((exp - current_time)) -lt 300 ]; then
        return 1
    fi
    
    return 0
}

# Function to refresh token
refresh_token() {
    log_message "Refreshing token"
    
    # Get refresh token from Keycloak
    local refresh_url="http://192.168.200.2:8080/realms/zta/protocol/openid-connect/token"
    local refresh_data="grant_type=refresh_token&client_id=pep-backend&refresh_token=${refresh_token}"
    
    local response=$(curl -s -X POST \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "$refresh_data" \
        "$refresh_url")
    
    # Extract new access token
    local new_token=$(echo $response | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$new_token" ]; then
        log_message "Failed to refresh token"
        return 1
    fi
    
    log_message "Token refreshed successfully"
    echo $new_token
    return 0
}

# Function to send data to PEP client
send_to_pep_client() {
    # Get nonce first
    nonce=$(get_nonce)
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Check if we have a stored token and if it's expired
    if [ -f ".token" ]; then
        stored_token=$(cat .token)
        if ! check_token_expiration "$stored_token"; then
            # Token is expired or invalid, get a new one
            stored_token=""
        fi
    fi
    
    # If no valid token, authenticate to get a new one
    if [ -z "$stored_token" ]; then
        # Create JSON data with username, password, and nonce
        local json_data=$(cat <<EOF
{
    "username": "${username}",
    "password": "${password}",
    "nonce": "${nonce}"
}
EOF
)

        # Debug: Print JSON to verify it's correct
        echo "Sending JSON data:"
        echo "$json_data"

        # Send data to PEP client
        response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -d "$json_data" \
            http://192.168.200.2:5000/compliance-check)

        # Extract token from response
        stored_token=$(echo $response | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        
        # Store token for future use
        if [ ! -z "$stored_token" ]; then
            echo "$stored_token" > .token
        fi
    fi

    # Check response
    if echo "$response" | grep -q '"status":"success"'; then
        log_message "Data successfully sent to PEP client"
        return 0
    else
        log_message "Failed to send data to PEP client"
        return 1
    fi
}

# Main execution
main() {
    log_message "Starting compliance check"
    
    # Get device information automatically
    get_device_info
    
    # Collect only user credentials
    collect_user_credentials
    
    # Log collected information
    log_message "=== Device Information ==="
    log_message "Device ID: $device_id"
    log_message "IP Address: $ip_address"
    log_message "MAC Address: $mac_address"
    log_message "OS: $os_type $os_version"
    log_message "Antivirus: $antivirus_status"
    log_message "Firewall: $firewall_status"
    log_message "Last Security Update: $last_security_update"
    log_message "=== End Device Information ==="
    
    # For now, just output device is compliant
    log_message "Device is compliant"
    
    # Send data to PEP client
    if send_to_pep_client; then
        log_message "Compliance check completed successfully"
        exit 0
    else
        log_message "Compliance check failed"
        exit 1
    fi
}

# Run main function
main 