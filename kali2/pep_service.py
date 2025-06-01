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
from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI()

class PEPRequest(BaseModel):
    resource: str
    action: str
    token: str

class PEP:
    def __init__(self):
        # Keycloak configuration
        self.keycloak_host = os.getenv("KEYCLOAK_HOST", "keycloak")
        self.keycloak_port = os.getenv("KEYCLOAK_PORT", "8080")
        self.keycloak_url = f"http://{self.keycloak_host}:{self.keycloak_port}"
        self.realm = os.getenv("REALM", "zta")
        self.client_id = os.getenv("CLIENT_ID", "pep-backend")
        self.client_secret = os.getenv("CLIENT_SECRET", "DXtmD2csJMM21EcTbOXWoFqNRF5yvGS2")
        
        # PDP service configuration
        self.pdp_host = os.getenv("PDP_HOST", "pdp-service")
        self.pdp_port = os.getenv("PDP_PORT", "5002")
        self.pdp_endpoint = f"http://{self.pdp_host}:{self.pdp_port}"
        
        # Timeout configuration
        self.request_timeout = float(os.getenv("REQUEST_TIMEOUT", "5.0"))
        
        # Initialize JWKS client
        self.jwks_client = PyJWKClient(f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs")
        
        logger.info(f"PEP initialized with Keycloak URL: {self.keycloak_url}")
        logger.info(f"PDP endpoint: {self.pdp_endpoint}")

    def validate_token(self, token: str) -> Tuple[bool, Dict]:
        """Validate the JWT token"""
        try:
            # Get the key ID from the token header
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get('kid')
            
            # Get the key from JWKS
            key = self.jwks_client.get_signing_key(key_id).key
            
            # Verify and decode the token
            decoded = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=f"{self.keycloak_url}/realms/{self.realm}"
            )
            
            return True, decoded
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return False, {"error": str(e)}

    def check_permission(self, token: str, resource: str, action: str) -> Tuple[bool, str]:
        """Check permission with PDP"""
        try:
            # First validate the token
            valid, decoded = self.validate_token(token)
            if not valid:
                return False, "Invalid token"
            
            # Prepare the request to PDP
            pdp_request = {
                "token": token,
                "resource": resource,
                "action": action
            }
            
            # Send request to PDP
            response = requests.post(
                f"{self.pdp_endpoint}/check",
                json=pdp_request,
                timeout=self.request_timeout
            )
            
            if response.status_code != 200:
                return False, f"PDP error: {response.text}"
                
            result = response.json()
            return result.get("allowed", False), result.get("message", "No message")
            
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            return False, str(e)

# Create global PEP instance
pep = PEP()

@app.post("/check")
async def check_permission(request: PEPRequest):
    try:
        allowed, message = pep.check_permission(
            request.token,
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
    host = os.getenv("PEP_HOST", "0.0.0.0")
    port = int(os.getenv("PEP_PORT", "5001"))
    
    # Start FastAPI server
    logger.info(f"Starting PEP server on {host}:{port}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main() 