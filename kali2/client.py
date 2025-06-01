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
import secrets
import hashlib
import datetime
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
from collections import defaultdict
import getpass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI()

# Session management
sessions = defaultdict(dict)  # Store sessions by client IP
NONCE_EXPIRY = 300  # 5 minutes in seconds

class ComplianceRequest(BaseModel):
    username: str
    password: str
    nonce: Optional[str] = None

class AuthRequest(BaseModel):
    username: str
    password: str

class Client:
    def __init__(self):
        # Keycloak configuration
        self.keycloak_host = os.getenv("KEYCLOAK_HOST", "192.168.200.2")
        self.keycloak_port = os.getenv("KEYCLOAK_PORT", "8080")
        self.keycloak_url = f"http://{self.keycloak_host}:{self.keycloak_port}"
        self.realm = os.getenv("REALM", "zta")
        self.client_id = os.getenv("CLIENT_ID", "pep-backend")
        self.client_secret = os.getenv("CLIENT_SECRET", "1234567890")
        
        # PEP service configuration
        self.pep_host = os.getenv("PEP_HOST", "192.168.200.2")
        self.pep_port = os.getenv("PEP_PORT", "5000")
        self.pep_endpoint = f"http://{self.pep_host}:{self.pep_port}"
        
        # Network configuration
        self.zt_segment = os.getenv("ZT_SEGMENT", "zt_segment")
        self.allowed_networks = os.getenv("ALLOWED_NETWORKS", "intranet,zt_segment").split(",")
        
        # Timeout configuration
        self.request_timeout = float(os.getenv("REQUEST_TIMEOUT", "5.0"))  # 5 seconds timeout
        
        # Initialize JWKS client
        self.jwks_client = PyJWKClient(f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs")
        
        logger.info(f"Client initialized with Keycloak URL: {self.keycloak_url}")
        logger.info(f"PEP endpoint: {self.pep_endpoint}")
        logger.info(f"ZT segment: {self.zt_segment}")

    def generate_nonce(self) -> str:
        """Generate a new nonce"""
        
        return secrets.token_urlsafe(32)

    def validate_nonce(self, nonce: str, client_ip: str) -> bool:
        """Validate a nonce for a client"""
        if client_ip not in sessions:
            return False
            
        session = sessions[client_ip]
        if 'nonce' not in session or 'timestamp' not in session:
            return False
            
        # Check if nonce matches and hasn't expired
        if session['nonce'] != nonce:
            return False
            
        if time.time() - session['timestamp'] > NONCE_EXPIRY:
            return False
            
        return True

    def authenticate(self, username: str, password: str, nonce: Optional[str] = None, client_ip: Optional[str] = None) -> Tuple[bool, str]:
        """Authenticate with Keycloak"""
        try:
            # Validate nonce if provided
            # if nonce and client_ip:
            #     if not self.validate_nonce(nonce, client_ip):
            #         logger.error("Invalid or expired nonce")
            #         return False, "Invalid or expired nonce"

            
            # Get token directly using password grant
            token_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"
            logger.info(f"Attempting authentication with URL: {token_url}")
            
            token_data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": username,
                "password": password
            }
            
            response = requests.post(token_url, data=token_data)
            logger.info(f"Keycloak response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Failed to get tokens: {response.text}")
                return False, "Authentication failed"
                
            tokens = response.json()
            access_token = tokens["access_token"]
            
            # Decode token to get user info
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            user_roles = decoded.get("realm_access", {}).get("roles", [])
            
            logger.info(f"Authentication successful for user: {username}")
            logger.info(f"User roles: {user_roles}")
            return True, access_token
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False, str(e)

# Create global client instance
client = Client()

@app.get("/get-nonce")
async def get_nonce(request: Request):
    """Get a new nonce for session management"""
    client_ip = request.client.host
    nonce = client.generate_nonce()
    
    # Store nonce with timestamp
    sessions[client_ip] = {
        'nonce': nonce,
        'timestamp': time.time()
    }
    
    return {"nonce": nonce}

# @app.post("/compliance-check")
# async def compliance_check(request: ComplianceRequest, req: Request):
#     """Handle compliance check request"""
#     try:
#         client_ip = req.client.host
        
#         # Authenticate with Keycloak
#         success, result = client.authenticate(
#             request.username, 
#             request.password,
#             request.nonce,
#             client_ip
#         )
        
#         if success:
#             # Clear the used nonce
#             if client_ip in sessions:
#                 del sessions[client_ip]
                
#             return {
#                 "status": "success",
#                 "token": result
#             }
#         else:
#             raise HTTPException(status_code=401, detail=result)
            
#     except Exception as e:
#         logger.error(f"Error in compliance check: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
    


@app.post("/authenticate")
async def authenticate(request: AuthRequest):
    try:
        # Authenticate with Keycloak
        success, result = client.authenticate(
            request.username,
            request.password
        )
        
        if success:
            return {
                "status": "success",
                "token": result
            }
        else:
            raise HTTPException(status_code=401, detail=result)
            
    except Exception as e:
        logger.error(f"Error in authentication: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    # Get host and port from environment or use defaults
    host = os.getenv("CLIENT_HOST", "0.0.0.0")
    port = int(os.getenv("CLIENT_PORT", "5000"))
    
    # Start FastAPI server
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    uvicorn.run(app, host=host, port=port)

    

if __name__ == "__main__":
    main() 