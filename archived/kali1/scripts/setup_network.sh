#!/bin/bash

# Exit on error
set -e

# Log file
LOG_FILE="/var/log/network/setup.log"

# Logging function
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Create log directory
sudo mkdir -p /var/log/network
sudo chown -R root:root /var/log/network

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

# Function to setup VLANs with nftables (for Kali1 only)
setup_kali1_vlans() {
    local kali_num=1  # Force Kali1
    
    echo "Setting up VLANs and nftables for Kali${kali_num}..."
    
    # Load VLAN module if not loaded
    modprobe 8021q 2>/dev/null || true

    # Remove existing VLAN interfaces if they exist
    ip link delete eth1.10 2>/dev/null || true
    ip link delete eth1.20 2>/dev/null || true

    # Create VLAN interfaces
    ip link add link eth1 name eth1.10 type vlan id 10
    ip addr add "192.168.200.$((kali_num + 19))/24" dev eth1.10
    ip link set eth1.10 up

    ip link add link eth1 name eth1.20 type vlan id 20
    ip addr add "192.168.200.$((kali_num + 19))/24" dev eth1.20
    ip link set eth1.20 up

    # Enable IP forwarding
    sysctl -w net.ipv4.ip_forward=1

    # Setup nftables (only on Kali1)
    nft flush ruleset
    nft -f - <<EOF
table inet filter {
    chain input {
        type filter hook input priority 0;
        policy drop;

        # Allow established connections
        ct state established,related accept
        ct state invalid drop

        # Allow localhost
        iif "lo" accept

        # Allow essential protocols
        ip protocol icmp accept
        tcp dport { 22, 80, 443 } accept
        udp dport { 67, 68, 53, 1812, 1813 } accept

        # Allow VLAN traffic
        iifname "eth1.10" ip saddr 192.168.200.0/24 accept
        iifname "eth1.20" ip saddr 192.168.200.0/24 accept

        # Log and drop everything else
        log prefix "INPUT_BLOCK: " flags all drop
    }

    chain forward {
        type filter hook forward priority 0;
        policy drop;

        # Allow established connections
        ct state established,related accept
        ct state invalid drop

        # Allow inter-VLAN communication
        iifname "eth1.10" oifname "eth1.20" ip saddr 192.168.200.0/24 ip daddr 192.168.200.0/24 accept
        iifname "eth1.20" oifname "eth1.10" ip saddr 192.168.200.0/24 ip daddr 192.168.200.0/24 accept

        # Allow Zero Trust VLAN to access intranet
        iifname "eth1.20" oifname "eth2" ip saddr 192.168.200.0/24 ip daddr 192.168.100.0/24 tcp dport {80, 443} accept

        # Log and drop everything else
        log prefix "FORWARD_BLOCK: " flags all drop
    }

    chain output {
        type filter hook output priority 0;
        policy accept;
    }
}
EOF

    # Setup policy-based routing
    ip route add 192.168.200.0/24 dev eth1.10 table 10 2>/dev/null || true
    ip rule add iif eth1.10 table 10 priority 100 2>/dev/null || true

    ip route add 192.168.200.0/24 dev eth1.20 table 20 2>/dev/null || true
    ip rule add iif eth1.20 table 20 priority 101 2>/dev/null || true

    # Make configuration persistent
    cat > /etc/network/interfaces.d/vlans << EOF
# VLAN Configuration for Kali${kali_num}
auto eth1.10
iface eth1.10 inet static
    address 192.168.200.$((kali_num + 19))
    netmask 255.255.255.0
    vlan-raw-device eth1
    post-up ip route add 192.168.200.0/24 dev eth1.10 table 10
    post-up ip rule add iif eth1.10 table 10 priority 100

auto eth1.20
iface eth1.20 inet static
    address 192.168.200.$((kali_num + 19))
    netmask 255.255.255.0
    vlan-raw-device eth1
    post-up ip route add 192.168.200.0/24 dev eth1.20 table 20
    post-up ip rule add iif eth1.20 table 20 priority 101
EOF

    # Configure eth2 (Intranet)
    cat > /etc/network/interfaces.d/eth2 << EOF
# Intranet (internal legacy)
auto eth2
iface eth2 inet static
    address 192.168.100.1
    netmask 255.255.255.0
EOF

    # Make IP forwarding persistent
    echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/99-ip-forward.conf
    sysctl -p /etc/sysctl.d/99-ip-forward.conf

    # Enable and start nftables
    systemctl enable nftables
    systemctl restart nftables

    echo "✅ VLAN and nftables setup completed for Kali1"
    echo "Quarantine VLAN (eth1.10): 192.168.200.20"
    echo "Zero Trust VLAN (eth1.20): 192.168.200.20"
    echo "Intranet (eth2): 192.168.100.1"
}

# Main execution
check_root
setup_kali1_vlans

log_message "Network setup completed successfully!"
echo "Network setup completed. Check $LOG_FILE for details." 