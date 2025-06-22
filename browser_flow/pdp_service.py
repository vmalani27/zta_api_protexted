#!/usr/bin/env python3
import requests
import logging
from typing import Optional, Dict, Any, Tuple
import os
from dotenv import load_dotenv
import json
import jwt
from jwt import PyJWKClient
import time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI()

class PDPRequest(BaseModel):
    token: str
    resource: str
    action: str

class PDP:
    def __init__(self):
        # Keycloak configuration
        self.keycloak_host = os.getenv("KEYCLOAK_HOST", "localhost")
        self.keycloak_port = os.getenv("KEYCLOAK_PORT", "8080")
        self.keycloak_url = f"http://{self.keycloak_host}:{self.keycloak_port}"
        self.realm = os.getenv("REALM", "zta")
        self.client_id = os.getenv("CLIENT_ID", "pep-backend")
        self.client_secret = os.getenv("CLIENT_SECRET", "DXtmD2csJMM21EcTbOXWoFqNRF5yvGS2")
        
        # Service endpoints
        self.pep_host = os.getenv("PEP_HOST", "localhost")
        self.pep_port = os.getenv("PEP_PORT", "5003")
        self.pep_endpoint = f"http://{self.pep_host}:{self.pep_port}"
        
        # Timeout configuration
        self.request_timeout = float(os.getenv("REQUEST_TIMEOUT", "5.0"))
        
        # Initialize JWKS client
        self.jwks_client = PyJWKClient(f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs")
        
        logger.info(f"PDP initialized with Keycloak URL: {self.keycloak_url}")

    def validate_token(self, token: str) -> Tuple[bool, Dict]:
        """Validate the JWT token."""
        try:
        # Extract header
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get('kid')

        # Fetch public key
            key = self.jwks_client.get_signing_key(key_id).key

            unverified_claims = jwt.decode(token, options={"verify_signature": False})
            print("aud claim:", unverified_claims.get("aud"))

        # Decode with validation
            decoded = jwt.decode(
    token,
    key,
    algorithms=["RS256"],
    options={"verify_aud": False},  # disables audience check
    issuer=f"{self.keycloak_url}/realms/{self.realm}"
)
            logger.info(f"Decoded token: {json.dumps(decoded, indent=2)}")

            return True, decoded

        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return False, {"error": str(e)}

    
    def evaluate_policy(self, token_data: Dict, resource: str, action: str) -> Tuple[bool, str]:
        """Evaluate the access policy based on roles"""
        try:
            roles = token_data.get("realm_access", {}).get("roles", [])
            username = token_data.get("preferred_username", "")
        
            logger.info(f"Evaluating access for user: {username} with roles: {roles}")
            logger.info(f"Requested resource: {resource}, action: {action}")

            # Role-to-permission map
            role_permissions = {
                "admin": {
                    "users": ["create", "read", "update", "delete"],
                    "students": ["create", "read", "update", "delete"],
                    "teachers": ["create", "read", "update", "delete"],
                    "hostels": ["create", "read", "update", "delete"],
                    "wardens": ["create", "read", "update", "delete"],
                    "profile": ["read", "update"]
                },
                "teacher": {
                    "students": ["read", "update"],
                    "teachers": ["read"],
                    "profile": ["read"]
                },
                "warden": {
                    "students": ["read"],
                    "hostels": ["read", "update"],
                    "wardens": ["read"],
                    "profile": ["read"]
                },
                "student": {
                    "profile": ["read"]
                }
            }

            # Convert roles to lowercase for case-insensitive comparison
            roles = [role.lower() for role in roles]
            logger.info(f"Normalized roles: {roles}")

            # Evaluate access based on any matching role
            for role in roles:
                role_config = role_permissions.get(role, {})
                allowed_actions = role_config.get(resource, [])
                if action in allowed_actions:
                    return True, f"{role} access granted to {resource} for {action}"

            return False, f"Access denied to {action} {resource}"

        except Exception as e:
            logger.error(f"Policy evaluation error: {str(e)}")
            return False, str(e)


# Create global PDP instance
pdp = PDP()

@app.post("/check")
async def check_permission(request: PDPRequest):
    try:
        # First validate the token
        valid, token_data = pdp.validate_token(request.token)
        print("token validated!")
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Evaluate the policy
        print("continuing with permission verification")
        allowed, message = pdp.evaluate_policy(
            token_data,
            request.resource,
            request.action
        )
        
        if allowed:
            return {
                "status": "success",
                "allowed": True,
                "message": message
            }
        else:
            raise HTTPException(status_code=403, detail=message)
            
    except Exception as e:
        logger.error(f"Error in permission check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    # Get host and port from environment or use defaults
    host = os.getenv("PDP_HOST", "0.0.0.0")
    port = int(os.getenv("PDP_PORT", "5002"))
    
    # Start FastAPI server
    logger.info(f"Starting PDP server on {host}:{port}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
