# PDP Test Cases

This directory contains test cases for the Policy Decision Point (PDP) service.

## Test Script

The `test_pdp.sh` script contains various test cases that verify the PDP service's policy enforcement for different user roles and resources.

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

The script includes the following test cases:

1. **Student Access Tests**
   - Accessing own academic records (Should Succeed)
   - Accessing all academic records (Should Fail)

2. **Teacher Access Tests**
   - Accessing student records (Should Succeed)
   - Modifying system settings (Should Fail)

3. **Warden Access Tests**
   - Accessing hostel records (Should Succeed)
   - Accessing academic records (Should Fail)

4. **Admin Access Tests**
   - Accessing any resource (Should Succeed)

5. **Multi-role Access Tests**
   - Staff with Teacher and Warden roles accessing hostel records (Should Succeed)

## Expected Results

- Green output indicates access granted
- Red output indicates access denied
- Each test shows the full response from the PDP service

## Troubleshooting

If tests fail:
1. Ensure the PDP service is running
2. Check the PDP service logs for errors
3. Verify the policy configuration in the PDP service
4. Check network connectivity to the PDP service 