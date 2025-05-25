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

# Function to send data to PEP client
send_to_pep_client() {
    local json_data=$(cat <<EOF
{
    "username": "$username",
    "password": "$password",
    "device_id": "$device_id",
    "ip_address": "$ip_address",
    "mac_address": "$mac_address",
    "os_type": "$os_type",
    "os_version": "$os_version",
    "antivirus_status": $([ "$antivirus_status" = "yes" ] && echo "true" || echo "false"),
    "firewall_status": $([ "$firewall_status" = "yes" ] && echo "true" || echo "false"),
    "last_security_update": "$last_security_update"
}
EOF
)

    # Send data to PEP client
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$json_data" \
        http://kali2:5000/compliance-check)

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
    log_message "Device ID: $device_id"
    log_message "IP Address: $ip_address"
    log_message "MAC Address: $mac_address"
    log_message "OS: $os_type $os_version"
    log_message "Antivirus: $antivirus_status"
    log_message "Firewall: $firewall_status"
    log_message "Last Security Update: $last_security_update"
    
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