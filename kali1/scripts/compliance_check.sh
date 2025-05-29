#!/bin/bash

LOG_FILE="/var/log/nac/compliance.log"
ATTEMPTS_FILE="/var/log/nac/device_attempts.log"
mkdir -p /var/log/nac
touch "$LOG_FILE" "$ATTEMPTS_FILE"
chown freerad:freerad "$LOG_FILE" "$ATTEMPTS_FILE"

# Get device identifier (MAC address)
DEVICE_MAC=$(ip link show | grep -E '^[0-9]+: ' | grep -v 'lo:' | head -n 1 | awk '{print $2}')
DEVICE_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d/ -f1)

echo "$(date) - Compliance check STARTED for device $DEVICE_MAC ($DEVICE_IP)" >> "$LOG_FILE"

# Initialize scores
TOTAL_SCORE=0
MAX_SCORE=100

# Function to check attempts
check_attempts() {
    local attempts=$(grep -c "^$DEVICE_MAC:" "$ATTEMPTS_FILE")
    if [ "$attempts" -ge 3 ]; then
        echo "$(date) - Device $DEVICE_MAC has exceeded maximum attempts. Access permanently revoked." >> "$LOG_FILE"
        echo 'Reply-Message := "Access permanently revoked. Contact system administrator."'
        exit 1
    fi
    echo "$DEVICE_MAC:$(date)" >> "$ATTEMPTS_FILE"
}

# Function to add score with logging
add_score() {
    local points=$1
    local reason=$2
    TOTAL_SCORE=$((TOTAL_SCORE + points))
    echo "$(date) - $reason: +$points points (Total: $TOTAL_SCORE)" >> "$LOG_FILE"
}

# 1. Check for pending updates (20 points)
if command -v apt >/dev/null 2>&1; then
    echo "$(date) - Checking for pending updates..." >> "$LOG_FILE"
    updates=$(apt list --upgradeable 2>/dev/null | grep -v "Listing..." | wc -l)
    
    if [ "$updates" -eq 0 ]; then
        add_score 20 "System is up to date"
    elif [ "$updates" -le 10 ]; then
        add_score 15 "System has minor updates pending ($updates updates)"
        echo "Please run: sudo apt update && sudo apt upgrade"
    elif [ "$updates" -le 50 ]; then
        add_score 10 "System has moderate updates pending ($updates updates)"
        echo "Please run: sudo apt update && sudo apt upgrade"
    elif [ "$updates" -le 100 ]; then
        add_score 5 "System has significant updates pending ($updates updates)"
        echo "Please run: sudo apt update && sudo apt upgrade"
    elif [ "$updates" -le 500 ]; then
        add_score 0 "System has critical updates pending ($updates updates)"
        echo "Please run: sudo apt update && sudo apt upgrade immediately"
    else
        echo "$(date) - CRITICAL: System has excessive updates pending ($updates updates)" >> "$LOG_FILE"
        echo "System has too many pending updates. Access denied until updates are applied."
        echo "Please run: sudo apt update && sudo apt upgrade"
        exit 1  # Exit with failure for excessive updates
    fi
else
    echo "$(date) - APT not found, skipping update check" >> "$LOG_FILE"
fi

# 2. Check ClamAV (20 points)
if systemctl is-active --quiet clamav-freshclam && systemctl is-active --quiet clamav-daemon; then
    echo "Both ClamAV services are running."
else
    echo "One or both ClamAV services are NOT running."
fi


# 3. Check firewall configuration (15 points)
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    add_score 15 "Firewall is active"
else
    echo "$(date) - Firewall is not active" >> "$LOG_FILE"
    echo "Please enable firewall: sudo ufw enable"
fi

# 4. Check security services (15 points)
SECURITY_SERVICES=("sshd" "fail2ban")
SECURITY_SCORE=0
for service in "${SECURITY_SERVICES[@]}"; do
    if systemctl is-active --quiet "$service"; then
        SECURITY_SCORE=$((SECURITY_SCORE + 7))
    else
        echo "$(date) - $service is not running" >> "$LOG_FILE"
        echo "Please start $service: sudo systemctl start $service"
    fi
done
add_score $SECURITY_SCORE "Security services"

# 5. Check user privileges (15 points)
if [ "$(id -u)" -ne 0 ]; then
    add_score 15 "Non-root user"
else
    echo "$(date) - Running as root user" >> "$LOG_FILE"
    echo "Please use a non-root user account"
fi

# 6. Check network security (15 points)
if ip link show | grep -q "state UP"; then
    add_score 15 "Network interface is up"
else
    echo "$(date) - Network interface is down" >> "$LOG_FILE"
    echo "Please check network connectivity"
fi

# Calculate threat level and determine access
echo "$(date) - Final score: $TOTAL_SCORE/$MAX_SCORE" >> "$LOG_FILE"

if [ $TOTAL_SCORE -ge 80 ]; then
    echo "$(date) - Device is COMPLIANT (Low threat)" >> "$LOG_FILE"
    echo 'Reply-Message := "Device is compliant. Access granted."'
    exit 0
elif [ $TOTAL_SCORE -ge 50 ]; then
    check_attempts
    echo "$(date) - Device is PARTIALLY COMPLIANT (Medium threat)" >> "$LOG_FILE"
    echo "Remaining attempts: $((3 - $(grep -c "^$DEVICE_MAC:" "$ATTEMPTS_FILE")))"
    echo 'Reply-Message := "Device needs remediation. Please fix the issues above."'
    exit 1
else
    check_attempts
    echo "$(date) - Device is NON-COMPLIANT (High threat)" >> "$LOG_FILE"
    echo "Remaining attempts: $((3 - $(grep -c "^$DEVICE_MAC:" "$ATTEMPTS_FILE")))"
    echo 'Reply-Message := "Device failed compliance check. Please fix the issues above."'
    exit 1
fi
