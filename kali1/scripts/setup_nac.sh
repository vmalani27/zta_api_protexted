#!/bin/bash

# NAC Server Setup Script
# This script automates the setup of the Network Access Control server

# Exit on error
set -e

# Log file
LOG_FILE="/var/log/nac/setup.log"

# Logging function
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Create necessary directories
create_directories() {
    log_message "Creating necessary directories..."
    sudo mkdir -p /var/log/nac
    sudo mkdir -p /etc/freeradius/3.0/certs
    sudo chown -R freerad:freerad /var/log/nac
}

# Install required packages
install_packages() {
    log_message "Installing required packages..."
    sudo apt-get update
    sudo apt-get install -y freeradius freeradius-mysql iptables-persistent
}

# # Configure network interfaces to match the ZT architecture
# configure_network() {
#     log_message "Configuring network interfaces..."
#     sudo tee /etc/network/interfaces.d/eth0 << EOF
# # Internet (external)
# auto eth0
# iface eth0 inet dhcp
# EOF
#     sudo tee /etc/network/interfaces.d/eth1 << EOF
# # ZT Segment (trusted)
# auto eth1
# iface eth1 inet static
#     address 192.168.200.1
#     netmask 255.255.255.0
# EOF
#     sudo tee /etc/network/interfaces.d/eth2 << EOF
# # Intranet (internal legacy)
# auto eth2
# iface eth2 inet static
#     address 192.168.100.1
#     netmask 255.255.255.0
# EOF
# }

# Configure FreeRADIUS
configure_freeradius() {
    log_message "Configuring FreeRADIUS..."
    
    # Backup original configuration
    sudo cp -r /etc/freeradius/3.0 /etc/freeradius/3.0.backup
    
    # Configure radiusd.conf
    sudo tee /etc/freeradius/3.0/radiusd.conf << EOF
prefix = /usr
exec_prefix = /usr
sysconfdir = /etc
localstatedir = /var
sbindir = \${exec_prefix}/sbin
logdir = /var/log/freeradius
raddbdir = /etc/freeradius/3.0
radacctdir = \${logdir}/radacct

log {
    destination = files
    file = \${logdir}/radius.log
    syslog_facility = daemon
    stripped_names = yes
    auth = yes
    auth_badpass = yes
    auth_goodpass = yes
}
EOF

    # Configure clients
    sudo tee /etc/freeradius/3.0/clients.conf << EOF
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
EOF

    # Configure users
    sudo tee /etc/freeradius/3.0/users << EOF
DEFAULT Auth-Type := Accept
    Reply-Message := "Welcome to the network"

testing Cleartext-Password := "password"
    Reply-Message := "Hello, %{User-Name}"
EOF
}

# Configure nftables (optional, skip if you have a custom ruleset)
# configure_nftables() {
#     log_message "Configuring nftables..."
#     sudo tee /etc/nftables.conf << EOF
#     ... (example rules here) ...
#     EOF
#     sudo nft -f /etc/nftables.conf
# }

# Setup compliance check script
setup_compliance_check() {
    log_message "Setting up compliance check script..."
    sudo cp compliance_check.sh /usr/local/bin/
    sudo chmod +x /usr/local/bin/compliance_check.sh
}

# Main setup function
main() {
    log_message "Starting NAC server setup..."
    
    create_directories
    install_packages
    configure_freeradius
    setup_compliance_check
    
    log_message "NAC server setup completed successfully"
    
    # Restart services
    sudo systemctl restart freeradius
    sudo systemctl enable freeradius
    
    log_message "Services restarted"
}

# Run main function
main 