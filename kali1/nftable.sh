#!/usr/bin/nft -f

# Define variables
define ZT_SEGMENT = 192.168.200.0/24
define KALI2_IP = 192.168.200.2
define KALI4_IP = 192.168.200.4
define FREERADIUS_PORT = 1812
define IAM_PEP_PORTS = { 8080, 5000 }  # Keycloak and PEP ports

# Flush existing rules
flush ruleset

# Create the main filter table
table inet filter {
    # Define sets for tracking authenticated devices
    set authenticated_devices {
        type ipv4_addr
        flags dynamic
        timeout 3600s  # 1 hour timeout
    }

    # Define sets for tracking devices in authentication process
    set auth_in_progress {
        type ipv4_addr
        flags dynamic
        timeout 300s  # 5 minutes timeout
    }

    # Base chains
    chain input {
        type filter hook input priority 0;
        policy drop;
    }
    
    chain forward {
        type filter hook forward priority 0;
        policy drop;
    }
    
    chain output {
        type filter hook output priority 0;
        policy drop;
    }

    # Chain for initial authentication
    chain initial_auth {
        # Allow FreeRADIUS authentication
        ip saddr $ZT_SEGMENT tcp dport $FREERADIUS_PORT accept
        
        # Add device to auth_in_progress set
        ip saddr $ZT_SEGMENT add @auth_in_progress { ip saddr }
        
        # Block everything else
        drop
    }

    # Chain for authenticated devices
    chain authenticated {
        # Allow communication with Kali2 (IAM/PEP)
        ip saddr $ZT_SEGMENT ip daddr $KALI2_IP tcp dport $IAM_PEP_PORTS accept
        
        # Block access to Kali4 unless fully authenticated
        ip saddr $ZT_SEGMENT ip daddr $KALI4_IP drop
        
        # Block port scanning
        tcp flags & (syn|fin) == (syn|fin) drop
        tcp flags & (syn|rst) == (syn|rst) drop
        tcp flags & (fin|rst) == (fin|rst) drop
        
        # Block other traffic
        drop
    }

    # Chain for fully authenticated devices
    chain fully_authenticated {
        # Allow access to Kali4 only for fully authenticated devices
        ip saddr $ZT_SEGMENT ip daddr $KALI4_IP tcp dport { 5001 } accept
        
        # Allow established connections
        ct state established,related accept
        
        # Block everything else
        drop
    }
}

# Logging for security events
table inet filter {
    chain input {
        # Log blocked attempts
        ip saddr $ZT_SEGMENT ip daddr $KALI4_IP log prefix "Blocked access to protected resources: " drop
        
        # Log port scanning attempts
        tcp flags & (syn|fin) == (syn|fin) log prefix "Port scan attempt: " drop
    }
}