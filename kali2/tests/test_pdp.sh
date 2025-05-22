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
    response=$(curl -s -X POST http://localhost:5002/evaluate \
        -H "Content-Type: application/json" \
        -d "$3")
    
    if [[ $response == *"\"decision\":true"* ]]; then
        echo -e "${GREEN}Result: Access Granted${NC}"
    else
        echo -e "${RED}Result: Access Denied${NC}"
    fi
    echo "Response: $response"
    echo "------------------------"
}

# Test Case 1: Student accessing own academic records (Should Succeed)
run_test "Student accessing own academic records" \
    "GET /academic/own/records" \
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
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }'

# Test Case 2: Student trying to access all academic records (Should Fail)
run_test "Student accessing all academic records" \
    "GET /academic/all/records" \
    '{
        "subject": {
            "roles": ["Student"],
            "username": "student1",
            "email": "student1@example.com"
        },
        "resource": "/academic/all/records",
        "action": "GET",
        "environment": {
            "network": "zt_segment",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }'

# Test Case 3: Teacher accessing student records (Should Succeed)
run_test "Teacher accessing student records" \
    "GET /students/records" \
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
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }'

# Test Case 4: Teacher trying to modify system settings (Should Fail)
run_test "Teacher modifying system settings" \
    "PUT /system/settings" \
    '{
        "subject": {
            "roles": ["Teacher"],
            "username": "teacher1",
            "email": "teacher1@example.com"
        },
        "resource": "/system/settings",
        "action": "PUT",
        "environment": {
            "network": "zt_segment",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }'

# Test Case 5: Warden accessing hostel records (Should Succeed)
run_test "Warden accessing hostel records" \
    "GET /hostel/records" \
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
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }'

# Test Case 6: Warden trying to access academic records (Should Fail)
run_test "Warden accessing academic records" \
    "GET /academic/records" \
    '{
        "subject": {
            "roles": ["Warden"],
            "username": "warden1",
            "email": "warden1@example.com"
        },
        "resource": "/academic/records",
        "action": "GET",
        "environment": {
            "network": "zt_segment",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }'

# Test Case 7: Admin accessing any resource (Should Succeed)
run_test "Admin accessing any resource" \
    "GET /any/resource" \
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
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }'

# Test Case 8: Staff with Teacher and Warden roles (Should Succeed)
run_test "Staff accessing hostel records" \
    "GET /hostel/records" \
    '{
        "subject": {
            "roles": ["Teacher", "Warden"],
            "username": "staff1",
            "email": "staff1@example.com"
        },
        "resource": "/hostel/records",
        "action": "GET",
        "environment": {
            "network": "zt_segment",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }'

echo -e "\nAll tests completed!" 