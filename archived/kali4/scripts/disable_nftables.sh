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

# Function to disable and clear nftables
disable_nftables() {
    echo "Disabling and clearing nftables..."

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

# Main execution
check_root
disable_nftables

echo "✅ Nftables has been permanently disabled and cleared" 