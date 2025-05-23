#!/bin/bash

# Device Compliance Check Script
# This script checks various security aspects of a device before allowing network access

LOG_FILE="/var/log/nac/compliance.log"
COMPLIANCE_THRESHOLD=80  # Minimum compliance score required

# Logging function
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Check OS version and updates
check_os_updates() {
    if [ -f /etc/debian_version ]; then
        updates=$(apt-get -s upgrade | grep -c "^Inst")
        if [ "$updates" -gt 0 ]; then
            log_message "WARNING: $updates updates available"
            return 1
        fi
    elif [ -f /etc/redhat-release ]; then
        updates=$(yum check-update | grep -c "^[a-zA-Z]")
        if [ "$updates" -gt 0 ]; then
            log_message "WARNING: $updates updates available"
            return 1
        fi
    fi
    return 0
}

# Check firewall status
check_firewall() {
    if command -v ufw &> /dev/null; then
        if ! ufw status | grep -q "Status: active"; then
            log_message "WARNING: UFW firewall is not active"
            return 1
        fi
    elif command -v firewall-cmd &> /dev/null; then
        if ! firewall-cmd --state | grep -q "running"; then
            log_message "WARNING: Firewalld is not running"
            return 1
        fi
    else
        log_message "WARNING: No firewall detected"
        return 1
    fi
    return 0
}

# Check antivirus status
check_antivirus() {
    if command -v clamd &> /dev/null; then
        if ! systemctl is-active --quiet clamav-daemon; then
            log_message "WARNING: ClamAV daemon is not running"
            return 1
        fi
    else
        log_message "WARNING: No antivirus detected"
        return 1
    fi
    return 0
}

# Check disk encryption
check_disk_encryption() {
    if command -v cryptsetup &> /dev/null; then
        if ! cryptsetup status | grep -q "active"; then
            log_message "WARNING: Disk encryption not active"
            return 1
        fi
    else
        log_message "WARNING: No disk encryption detected"
        return 1
    fi
    return 0
}

# Check screen lock
check_screen_lock() {
    if command -v gsettings &> /dev/null; then
        if ! gsettings get org.gnome.desktop.screensaver lock-enabled | grep -q "true"; then
            log_message "WARNING: Screen lock is not enabled"
            return 1
        fi
    fi
    return 0
}

# Main compliance check
main() {
    local score=0
    local total_checks=5

    log_message "Starting compliance check for device"

    # Run all checks
    check_os_updates && ((score++))
    check_firewall && ((score++))
    check_antivirus && ((score++))
    check_disk_encryption && ((score++))
    check_screen_lock && ((score++))

    # Calculate compliance percentage
    local compliance_percentage=$((score * 100 / total_checks))
    
    log_message "Compliance score: $compliance_percentage%"

    # Return status based on threshold
    if [ "$compliance_percentage" -ge "$COMPLIANCE_THRESHOLD" ]; then
        log_message "Device is compliant"
        exit 0
    else
        log_message "Device is not compliant"
        exit 1
    fi
}

# Run main function
main 