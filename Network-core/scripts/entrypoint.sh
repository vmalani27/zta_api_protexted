#!/bin/bash

# Error handling
set -e
trap 'echo "Error on line $LINENO"' ERR

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log "Error: $1 is not installed"
        exit 1
    fi
}

# Function to validate configuration files
validate_config() {
    local file=$1
    if [ ! -f "$file" ]; then
        log "Error: Configuration file $file not found"
        exit 1
    fi
}

# Check required commands
check_command nft
check_command freeradius
check_command radtest

# Create necessary directories
mkdir -p /var/log/freeradius /var/log/nftables

# Validate configuration files
validate_config /etc/nftables.conf
validate_config /etc/freeradius/3.0/radiusd.conf
validate_config /etc/freeradius/3.0/clients.conf

# Enable IP forwarding
log "Enabling IP forwarding..."
echo 1 > /proc/sys/net/ipv4/ip_forward

# Load nftables rules
log "Loading nftables rules..."
nft -f /etc/nftables.conf || {
    log "Failed to load nftables rules"
    exit 1
}

# Start FreeRADIUS
log "Starting FreeRADIUS..."
freeradius -X &
RADIUS_PID=$!

# Wait for FreeRADIUS to start
sleep 2
if ! kill -0 $RADIUS_PID 2>/dev/null; then
    log "FreeRADIUS failed to start"
    exit 1
fi

# Test RADIUS authentication
log "Testing RADIUS authentication..."
if ! radtest testuser testpass localhost 0 testing123; then
    log "RADIUS authentication test failed"
    exit 1
fi

log "Network-core container started successfully"
log "RADIUS authentication port: 1812"
log "RADIUS accounting port: 1813"

# Monitor processes and logs
while true; do
    # Check FreeRADIUS process
    if ! kill -0 $RADIUS_PID 2>/dev/null; then
        log "FreeRADIUS process died, restarting..."
        freeradius -X &
        RADIUS_PID=$!
    fi
    
    # Rotate logs if needed
    if [ -f /var/log/freeradius/radius.log ] && [ $(stat -c %s /var/log/freeradius/radius.log) -gt 10485760 ]; then
        log "Rotating FreeRADIUS logs..."
        mv /var/log/freeradius/radius.log /var/log/freeradius/radius.log.old
        touch /var/log/freeradius/radius.log
    fi
    
    sleep 5
done 