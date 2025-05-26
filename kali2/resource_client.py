#!/usr/bin/env python3
import requests
import logging
from typing import Optional, Dict, Any, Tuple
import os
from dotenv import load_dotenv
import json
import jwt
import time
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ResourceClient:
    def __init__(self):
        # PEP service configuration
        self.pep_host = os.getenv("PEP_HOST", "192.168.200.2")
        self.pep_port = os.getenv("PEP_PORT", "5000")
        self.pep_endpoint = f"http://{self.pep_host}:{self.pep_port}"
        
        # PDP service configuration
        self.pdp_host = os.getenv("PDP_HOST", "192.168.200.2")
        self.pdp_port = os.getenv("PDP_PORT", "5002")
        self.pdp_endpoint = f"http://{self.pdp_host}:{self.pdp_port}"
        
        # Resource service configuration
        self.resource_host = os.getenv("RESOURCE_HOST", "192.168.200.4")
        self.resource_port = os.getenv("RESOURCE_PORT", "5001")
        self.resource_endpoint = f"http://{self.resource_host}:{self.resource_port}"
        
        # Token management
        self.access_token = None
        self.username = None
        self.user_roles = []
        
        logger.info("Resource Client initialized")

    def set_token(self, token: str) -> bool:
        """Set token received from compliance check"""
        try:
            # Decode token to get user information
            decoded = jwt.decode(token, options={"verify_signature": False})
            self.access_token = token
            self.username = decoded.get("preferred_username", "")
            self.user_roles = decoded.get("realm_access", {}).get("roles", [])
            
            logger.info(f"Token set for user: {self.username}")
            logger.info(f"User roles: {self.user_roles}")
            return True
        except Exception as e:
            logger.error(f"Error setting token: {str(e)}")
            return False

    def evaluate_policy(self) -> Tuple[bool, str]:
        """Evaluate policy with PDP service"""
        if not self.access_token:
            return False, "No token available"
            
        try:
            request_data = {
                "subject": {
                    "roles": self.user_roles,
                    "username": self.username,
                    "email": ""  # Email not required for policy evaluation
                },
                "resource": "/protected-resource",
                "action": "access",
                "environment": {
                    "network": "zt_segment",
                    "timestamp": str(datetime.datetime.utcnow())
                }
            }
            logger.info(f"Sending policy evaluation request to PDP with data: {request_data}")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = requests.post(
                f"{self.pdp_endpoint}/evaluate",
                json=request_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"PDP response: {result}")
                if result.get("decision") == True:
                    logger.info("Policy evaluation successful: Access allowed")
                    return True, "Access allowed"
                else:
                    logger.warning(f"Policy evaluation failed: {result.get('reason', 'Access denied')}")
                    return False, result.get("reason", "Access denied")
            else:
                logger.error(f"Policy evaluation failed with status {response.status_code}: {response.text}")
                return False, "Policy evaluation failed"
                
        except Exception as e:
            logger.error(f"Error during policy evaluation: {str(e)}")
            return False, str(e)

    def get_protected_resource(self) -> Optional[Dict[str, Any]]:
        """Access the protected resource"""
        if not self.access_token:
            logger.error("No access token available")
            return None
            
        try:
            # First evaluate policy with PDP
            policy_success, policy_message = self.evaluate_policy()
            if not policy_success:
                logger.error(f"Policy evaluation failed: {policy_message}")
                return None
            
            # If policy evaluation succeeds, access the resource
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.pep_endpoint}/protected-resource",
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("Successfully accessed protected resource")
                return response.json()
            else:
                logger.error(f"Failed to access protected resource: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error accessing protected resource: {str(e)}")
            return None

def main():
    # Create client instance
    client = ResourceClient()
    
    # Get token from compliance check
    token = input("Enter token from compliance check: ")
    
    # Set token
    if client.set_token(token):
        # Access protected resource
        resource_data = client.get_protected_resource()
        if resource_data:
            print("\nProtected Resource Data:")
            print(json.dumps(resource_data, indent=2))
    else:
        print("Failed to set token. Please check the token.")

if __name__ == "__main__":
    main() 