#!/bin/bash

# Exit on error
set -e

# Function to check if running as root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root"
        exit 1
    fi
}

# Function to get Kali number
get_kali_number() {
    if [[ -n "$1" ]]; then
        echo "$1"
    else
        hostname | grep -o '[0-9]\+'
    fi
}

# Function to disable nftables
disable_nftables() {
    echo "Disabling nftables..."
    
    # Stop the nftables service
    systemctl stop nftables
    echo "✅ Stopped nftables service"

    # Disable nftables from starting at boot
    systemctl disable nftables
    echo "✅ Disabled nftables from starting at boot"

    # Flush all rules
    nft flush ruleset
    echo "✅ Flushed all rules"

    # Delete all tables
    nft delete table inet filter 2>/dev/null || true
    nft delete table ip nat 2>/dev/null || true
    nft delete table ip6 filter 2>/dev/null || true
    echo "✅ Deleted all tables"

    # Save the empty ruleset
    nft list ruleset > /etc/nftables.conf
    echo "✅ Saved empty ruleset"

    # Verify nftables is stopped and disabled
    echo "Verifying nftables status..."
    systemctl status nftables
}

# Function to configure network
configure_network() {
    local kali_num=$(get_kali_number 2)  # Force Kali2
    echo "Configuring network for Kali${kali_num}..."
    
    # Configure eth1 (ZT Segment)
    cat > /etc/network/interfaces.d/eth1 << EOF
# ZT Segment
auto eth1
iface eth1 inet static
    address 192.168.200.$((kali_num + 10))
    netmask 255.255.255.0
EOF

    # Configure eth2 (Intranet)
    cat > /etc/network/interfaces.d/eth2 << EOF
# Intranet (internal legacy)
auto eth2
iface eth2 inet static
    address 192.168.100.${kali_num}
    netmask 255.255.255.0
EOF

    # Restart networking
    echo "Restarting networking service..."
    systemctl restart networking
    echo "✅ Network configuration completed"
    echo "ZT Segment (eth1): 192.168.200.$((kali_num + 10))"
    echo "Intranet (eth2): 192.168.100.${kali_num}"
}

# Main execution
check_root
disable_nftables
configure_network

echo "✅ Network setup completed for Kali2" 