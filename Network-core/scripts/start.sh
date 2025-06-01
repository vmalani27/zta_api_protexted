#!/bin/sh
set -e

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Enable IP forwarding
if echo 1 > /proc/sys/net/ipv4/ip_forward 2>/dev/null; then
    log "IP forwarding enabled."
else
    log "Failed to enable IP forwarding!"
fi

# Ensure nftables.conf has LF endings (fix Windows CRLF if present)
tr -d '\r' < /etc/nftables/nftables.conf > /tmp/nftables.conf && mv /tmp/nftables.conf /etc/nftables/nftables.conf

# Load nftables rules
if nft -f /etc/nftables/nftables.conf; then
    log "nftables rules loaded."
else
    log "Failed to load nftables rules!"
    exit 1
fi

# Start FreeRADIUS
log "Starting FreeRADIUS..."
freeradius -X

# Create log directory if it doesn't exist
mkdir -p /var/log/freeradius

# Start FreeRADIUS
echo "Starting FreeRADIUS..."
freeradius -X &
RADIUS_PID=$!

# Wait for FreeRADIUS to start
sleep 2
if ! kill -0 $RADIUS_PID 2>/dev/null; then
    echo "FreeRADIUS failed to start"
    exit 1
fi

echo "Network-core container started successfully"
echo "RADIUS authentication port: 1812"
echo "RADIUS accounting port: 1813"

# Keep container running and monitor processes
while true; do
    if ! kill -0 $RADIUS_PID 2>/dev/null; then
        echo "FreeRADIUS process died, restarting..."
        freeradius -X &
        RADIUS_PID=$!
    fi
    sleep 5
done 