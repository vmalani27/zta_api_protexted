#!/bin/bash

# Check antivirus status
if systemctl is-active --quiet clamav-daemon; then
    # If compliant, output score 80
    echo "Compliance-Score := 80"
    exit 0
else
    # If not compliant, output score 30
    echo "Compliance-Score := 30"
    exit 1
fi
