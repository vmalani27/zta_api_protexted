#!/bin/bash

# Define VLANs
# VLAN 10: Quarantine (default for unauthenticated devices)
# VLAN 20: Zero Trust Segment (for authenticated and compliant devices)

table inet dfw {
    # VLAN interface definitions
    set quarantine_vlan {
        type inet_service
        flags constant
        elements = { 10 }
    }
    
    set zt_vlan {
        type inet_service
        flags constant
        elements = { 20 }
    }

    chain forward {
        type filter hook forward priority filter; policy drop;

        # Allow RADIUS traffic between VLANs
        iifname "eth1.10" oifname "eth1.10" ip saddr 192.168.200.0/24 ip daddr 192.168.200.1 udp dport {1812, 1813} accept
        iifname "eth1.20" oifname "eth1.20" ip saddr 192.168.200.0/24 ip daddr 192.168.200.1 udp dport {1812, 1813} accept

        # Allow RADIUS replies
        iifname "eth1.10" oifname "eth1.10" ip saddr 192.168.200.1 ip daddr 192.168.200.0/24 udp sport 1812 accept
        iifname "eth1.20" oifname "eth1.20" ip saddr 192.168.200.1 ip daddr 192.168.200.0/24 udp sport 1812 accept

        # Allow Zero Trust segment to access intranet (only after authentication)
        iifname "eth1.20" oifname "eth2" ip saddr 192.168.200.0/24 ip daddr 192.168.100.0/24 tcp dport {80, 443} accept

        # Allow established connections
        ct state established,related accept

        # Log everything else
        log prefix "DFW_BLOCK: " flags all drop
    }

    chain input {
        type filter hook input priority filter; policy drop;

        # Allow RADIUS requests on both VLANs
        iifname "eth1.10" ip saddr 192.168.200.0/24 udp dport {1812, 1813} accept
        iifname "eth1.20" ip saddr 192.168.200.0/24 udp dport {1812, 1813} accept

        # Allow localhost
        iifname "lo" accept

        # Allow RADIUS replies
        iifname "eth1.10" ip saddr 192.168.200.1 udp sport 1812 accept
        iifname "eth1.20" ip saddr 192.168.200.1 udp sport 1812 accept

        # Allow established/related connections
        ct state established,related accept

        # Log and drop everything else
        log prefix "INPUT_BLOCK: " flags all drop
    }
}

# Apply the rules
nft -f /etc/nftables.conf
