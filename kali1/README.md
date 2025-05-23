# Kali1 Network Access Control (NAC) Setup

## Overview
This directory contains the configuration and setup files for implementing Network Access Control (NAC) on Kali1, which serves as the 802.1x authentication server and network access controller.

## Directory Structure
```
kali1/
├── README.md
├── config/
│   ├── radiusd.conf
│   ├── clients.conf
│   └── users
├── scripts/
│   ├── setup_nac.sh
│   └── compliance_check.sh
└── logs/
    └── nac_audit.log
```

## Implementation Steps

### 1. System Preparation
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y freeradius freeradius-mysql iptables-persistent
```

### 2. Network Configuration
```bash
# Configure network interface
sudo nano /etc/network/interfaces

# Add the following configuration
auto eth0
iface eth0 inet static
    address 192.168.200.1
    netmask 255.255.255.0
    network 192.168.200.0
    broadcast 192.168.200.255
```

### 3. FreeRADIUS Setup
```bash
# Stop FreeRADIUS service
sudo systemctl stop freeradius

# Backup original configuration
sudo cp -r /etc/freeradius/3.0 /etc/freeradius/3.0.backup

# Configure radiusd.conf
sudo nano /etc/freeradius/3.0/radiusd.conf
# See config/radiusd.conf for configuration

# Configure clients
sudo nano /etc/freeradius/3.0/clients.conf
# See config/clients.conf for configuration

# Configure users
sudo nano /etc/freeradius/3.0/users
# See config/users for configuration
```

### 4. Network Access Control Rules
```bash
# (Optional) Configure nftables rules
# If you already have a custom nftables ruleset, SKIP this step and ensure your rules match your security policy.
# You may want to manually review or merge the example rules below with your own.

# # Example (do not run if you have your own rules):
# sudo nano /etc/nftables.conf

# # Example rules:
# table inet filter {
#     chain input {
#         # Allow ZT segment
#         ip saddr 192.168.200.0/24 accept
#         # Drop and log all other HTTP/HTTPS
#         tcp dport { 80, 443 } log prefix "Unauthorized HTTP/HTTPS: " drop
#     }
# }
# ```

> **Note:** If you have a custom nftables configuration (such as the one shown in your screenshot), do not overwrite it. Ensure your rules enforce Zero Trust principles and only allow compliant, authenticated devices to communicate as intended.

### 5. Device Compliance Checks
```bash
# Create compliance check script
sudo nano /usr/local/bin/compliance_check.sh
# See scripts/compliance_check.sh for implementation
```

### 6. Integration with Kali2 (IAM)
```bash
# Configure communication with Kali2
sudo nano /etc/freeradius/3.0/sites-enabled/default
# Add proxy configuration for Kali2
```

### 7. Testing
```bash
# Test FreeRADIUS configuration
sudo freeradius -X

# Test authentication
radtest testing password localhost 0 testing123
```

### 8. Monitoring
```bash
# Set up logging
sudo nano /etc/freeradius/3.0/radiusd.conf
# Configure logging to logs/nac_audit.log
```

## Configuration Files

### radiusd.conf
```ini
# Basic configuration
prefix = /usr
exec_prefix = /usr
sysconfdir = /etc
localstatedir = /var
sbindir = ${exec_prefix}/sbin
logdir = /var/log/freeradius
raddbdir = /etc/freeradius/3.0
radacctdir = ${logdir}/radacct

# Logging configuration
log {
    destination = files
    file = ${logdir}/radius.log
    syslog_facility = daemon
    stripped_names = yes
    auth = yes
    auth_badpass = yes
    auth_goodpass = yes
}
```

### clients.conf
```ini
client localhost {
    ipaddr = 127.0.0.1
    secret = testing123
    require_message_authenticator = no
    nastype = other
}

client kali2 {
    ipaddr = 192.168.200.2
    secret = shared_secret
    require_message_authenticator = no
    nastype = other
}
```

### users
```
# Default user configuration
DEFAULT Auth-Type := Accept
    Reply-Message := "Welcome to the network"

# Test user
testing Cleartext-Password := "password"
    Reply-Message := "Hello, %{User-Name}"
```

## Maintenance

### Regular Tasks
1. Monitor logs for unauthorized access attempts
2. Update device compliance checks
3. Review and update user accounts
4. Check system resources and performance

### Troubleshooting
1. Check FreeRADIUS logs: `tail -f /var/log/freeradius/radius.log`
2. Verify network connectivity: `ping 192.168.200.2`
3. Test authentication: `radtest testing password localhost 0 testing123`
4. Check nftables rules: `sudo nft list ruleset`

## Security Considerations
1. Regularly update system and packages
2. Monitor logs for suspicious activity
3. Keep shared secrets secure
4. Regular backup of configurations
5. Implement failover if needed

## Next Steps
1. Implement automated compliance checks
2. Set up monitoring and alerting
3. Configure backup and recovery procedures
4. Document incident response procedures 