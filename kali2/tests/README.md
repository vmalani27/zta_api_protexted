# PDP Test Cases

This directory contains test cases for the Policy Decision Point (PDP) service.

## Test Script

The `test_pdp.sh` script contains various test cases that verify the PDP service's policy enforcement for different user roles and resources, with a focus on network interface access control.

## Prerequisites

1. PDP service must be running on `localhost:5002`
2. Bash shell environment
3. `curl` command-line tool

## Running the Tests

1. Make the script executable:
   ```bash
   chmod +x test_pdp.sh
   ```

2. Run the tests:
   ```bash
   ./test_pdp.sh
   ```

## Test Cases

The script includes the following test cases, testing access through different network interfaces:

1. **Student Access Tests**
   - Accessing own academic records via ZT segment (eth1) (Should Succeed)
   - Accessing own academic records via intranet (eth2) (Should Fail)
   - Accessing own academic records via internet (eth0) (Should Fail)

2. **Teacher Access Tests**
   - Accessing student records via ZT segment (eth1) (Should Succeed)
   - Accessing student records via intranet (eth2) (Should Fail)

3. **Warden Access Tests**
   - Accessing hostel records via ZT segment (eth1) (Should Succeed)
   - Accessing hostel records via intranet (eth2) (Should Fail)

4. **Admin Access Tests**
   - Accessing any resource via ZT segment (eth1) (Should Succeed)
   - Accessing any resource via intranet (eth2) (Should Fail)

## Network Configuration

- **eth0 (Internet)**: 10.0.0.x network
  - Used for external internet access
  - Access to protected resources should be denied
  - Represents untrusted external network

- **eth1 (Zero Trust Segment)**: 192.168.200.x network
  - Used for secure access to protected resources
  - Access to protected resources should be allowed
  - Represents the secure Zero Trust network segment

- **eth2 (Intranet)**: 192.168.100.x network
  - Used for internal network access
  - Access to protected resources should be denied
  - Represents the internal network

## Expected Results

- Green output indicates access granted
- Red output indicates access denied
- Each test shows:
  - The network interface being used
  - The full response from the PDP service
  - The reason for access grant/denial

## Troubleshooting

If tests fail:
1. Ensure the PDP service is running
2. Check the PDP service logs for errors
3. Verify the policy configuration in the PDP service
4. Check network connectivity to the PDP service
5. Verify that the network interface information is being correctly passed in the requests 