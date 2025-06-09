#!/bin/bash

# Stop FreeRADIUS service
sudo systemctl stop freeradius

# Create certificates directory if it doesn't exist
sudo mkdir -p /etc/freeradius/3.0/certs

# Set proper permissions for certificates
sudo chown -R freerad:freerad /etc/freeradius/3.0/certs
sudo chmod 640 /etc/freeradius/3.0/certs/*

# Configure EAP-TLS in sites-enabled/default
sudo tee /etc/freeradius/3.0/sites-enabled/default << 'EOF'
authorize {
    eap
}

authenticate {
    eap
}

EOF

# Configure TLS in mods-enabled/eap
sudo tee /etc/freeradius/3.0/mods-enabled/eap << 'EOF'
eap {
    default_eap_type = tls
    timer_expire = 60
    ignore_unknown_eap_types = no
    cisco_accounting_username_bug = no
    max_sessions = 4096

    tls-config tls-common {
        private_key_file = /etc/freeradius/3.0/certs/server.key
        certificate_file = /etc/freeradius/3.0/certs/server.pem
        ca_file = /etc/freeradius/3.0/certs/ca.pem
        private_key_password = whatever
        verify_depth = 1
        pem_file_type = yes
    }

    tls {
        tls = tls-common
    }
}
EOF

# Restart FreeRADIUS service
sudo systemctl restart freeradius

echo "EAP-TLS configuration completed. Please ensure you have placed the following files in /etc/freeradius/3.0/certs/:"
echo "- server.pem (server certificate)"
echo "- server.key (server private key)"
echo "- ca.pem (CA certificate)"
echo ""
echo "Also verify that the permissions are set correctly:"
echo "sudo chown freerad:freerad /etc/freeradius/3.0/certs/*"
echo "sudo chmod 640 /etc/freeradius/3.0/certs/*" 