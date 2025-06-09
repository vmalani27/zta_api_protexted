#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Running PDP Test Cases..."
echo "------------------------"

# Function to run test and print result
run_test() {
    echo -e "\nTest: $1"
    echo "Request: $2"
    echo "Network: $3"
    response=$(curl -s -X POST http://localhost:5002/evaluate \
        -H "Content-Type: application/json" \
        -d "$4")
    
    if [[ $response == *"\"decision\":true"* ]]; then
        echo -e "${GREEN}Result: Access Granted${NC}"
    else
        echo -e "${RED}Result: Access Denied${NC}"
    fi
    echo "Response: $response"
    echo "------------------------"
}

# Test Case 1: Student accessing own academic records via ZT segment (Should Succeed)
run_test "Student accessing own academic records via ZT segment" \
    "GET /academic/own/records" \
    "eth1 (ZT segment)" \
    '{
        "subject": {
            "roles": ["Student"],
            "username": "student1",
            "email": "student1@example.com"
        },
        "resource": "/academic/own/records",
        "action": "GET",
        "environment": {
            "network": "zt_segment",
            "timestamp": "2024-01-01T00:00:00Z",
            "interface": "eth1",
            "ip": "192.168.200.10"
        }
    }'

# Test Case 2: Student accessing own academic records via intranet (Should Fail)
run_test "Student accessing own academic records via intranet" \
    "GET /academic/own/records" \
    "eth2 (intranet)" \
    '{
        "subject": {
            "roles": ["Student"],
            "username": "student1",
            "email": "student1@example.com"
        },
        "resource": "/academic/own/records",
        "action": "GET",
        "environment": {
            "network": "intranet",
            "timestamp": "2024-01-01T00:00:00Z",
            "interface": "eth2",
            "ip": "192.168.100.10"
        }
    }'

# Test Case 3: Student accessing own academic records via internet (Should Fail)
run_test "Student accessing own academic records via internet" \
    "GET /academic/own/records" \
    "eth0 (internet)" \
    '{
        "subject": {
            "roles": ["Student"],
            "username": "student1",
            "email": "student1@example.com"
        },
        "resource": "/academic/own/records",
        "action": "GET",
        "environment": {
            "network": "internet",
            "timestamp": "2024-01-01T00:00:00Z",
            "interface": "eth0",
            "ip": "10.0.0.10"
        }
    }'

# Test Case 4: Teacher accessing student records via ZT segment (Should Succeed)
run_test "Teacher accessing student records via ZT segment" \
    "GET /students/records" \
    "eth1 (ZT segment)" \
    '{
        "subject": {
            "roles": ["Teacher"],
            "username": "teacher1",
            "email": "teacher1@example.com"
        },
        "resource": "/students/records",
        "action": "GET",
        "environment": {
            "network": "zt_segment",
            "timestamp": "2024-01-01T00:00:00Z",
            "interface": "eth1",
            "ip": "192.168.200.11"
        }
    }'

# Test Case 5: Teacher accessing student records via intranet (Should Fail)
run_test "Teacher accessing student records via intranet" \
    "GET /students/records" \
    "eth2 (intranet)" \
    '{
        "subject": {
            "roles": ["Teacher"],
            "username": "teacher1",
            "email": "teacher1@example.com"
        },
        "resource": "/students/records",
        "action": "GET",
        "environment": {
            "network": "intranet",
            "timestamp": "2024-01-01T00:00:00Z",
            "interface": "eth2",
            "ip": "192.168.100.11"
        }
    }'

# Test Case 6: Warden accessing hostel records via ZT segment (Should Succeed)
run_test "Warden accessing hostel records via ZT segment" \
    "GET /hostel/records" \
    "eth1 (ZT segment)" \
    '{
        "subject": {
            "roles": ["Warden"],
            "username": "warden1",
            "email": "warden1@example.com"
        },
        "resource": "/hostel/records",
        "action": "GET",
        "environment": {
            "network": "zt_segment",
            "timestamp": "2024-01-01T00:00:00Z",
            "interface": "eth1",
            "ip": "192.168.200.12"
        }
    }'

# Test Case 7: Warden accessing hostel records via intranet (Should Fail)
run_test "Warden accessing hostel records via intranet" \
    "GET /hostel/records" \
    "eth2 (intranet)" \
    '{
        "subject": {
            "roles": ["Warden"],
            "username": "warden1",
            "email": "warden1@example.com"
        },
        "resource": "/hostel/records",
        "action": "GET",
        "environment": {
            "network": "intranet",
            "timestamp": "2024-01-01T00:00:00Z",
            "interface": "eth2",
            "ip": "192.168.100.12"
        }
    }'

# Test Case 8: Admin accessing any resource via ZT segment (Should Succeed)
run_test "Admin accessing any resource via ZT segment" \
    "GET /any/resource" \
    "eth1 (ZT segment)" \
    '{
        "subject": {
            "roles": ["admin"],
            "username": "admin_user",
            "email": "admin@example.com"
        },
        "resource": "/any/resource",
        "action": "GET",
        "environment": {
            "network": "zt_segment",
            "timestamp": "2024-01-01T00:00:00Z",
            "interface": "eth1",
            "ip": "192.168.200.13"
        }
    }'

# Test Case 9: Admin accessing any resource via intranet (Should Fail)
run_test "Admin accessing any resource via intranet" \
    "GET /any/resource" \
    "eth2 (intranet)" \
    '{
        "subject": {
            "roles": ["admin"],
            "username": "admin_user",
            "email": "admin@example.com"
        },
        "resource": "/any/resource",
        "action": "GET",
        "environment": {
            "network": "intranet",
            "timestamp": "2024-01-01T00:00:00Z",
            "interface": "eth2",
            "ip": "192.168.100.13"
        }
    }'

echo -e "\nAll tests completed!" 