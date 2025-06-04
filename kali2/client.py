#!/usr/bin/env python3
import requests
import logging
from typing import Optional, Dict, Tuple
import os
from dotenv import load_dotenv
import jwt
from jwt import PyJWKClient
import time
import secrets
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
from collections import defaultdict
import socket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()
sessions = defaultdict(dict)
NONCE_EXPIRY = 300  # 5 minutes

# --- Mapping from operations to resource/action ---
OPERATION_MAP = {
    "admincreate": {"resource": "users", "action": "create"},
    "adminread": {"resource": "users", "action": "read"},
    "studentview": {"resource": "students", "action": "read"},
    "teacheredit": {"resource": "teachers", "action": "update"},
    "hostelcreate": {"resource": "hostels", "action": "create"},
    
    # Add more as needed
}

# --- Pydantic Models ---
class AuthRequest(BaseModel):
    username: str
    password: str
    operation: str  # maps to resource/action

class ComplianceRequest(BaseModel):
    username: str
    password: str
    nonce: Optional[str] = None

# --- Client Class ---
class Client:
    def __init__(self):
        # Keycloak configuration
        self.keycloak_host = os.getenv("KEYCLOAK_HOST", "localhost")
        self.keycloak_port = os.getenv("KEYCLOAK_PORT", "8080")
        self.keycloak_url = f"http://{self.keycloak_host}:{self.keycloak_port}"
        self.realm = os.getenv("REALM", "zta")
        self.client_id = os.getenv("CLIENT_ID", "pep-backend")
        self.client_secret = os.getenv("CLIENT_SECRET", "secret")

        # Service endpoints
        self.pep_host = os.getenv("PEP_HOST", "localhost")
        self.pep_port = os.getenv("PEP_PORT", "5003")
        self.pep_endpoint = f"http://{self.pep_host}:{self.pep_port}"

        self.pdp_host = os.getenv("PDP_HOST", "localhost")
        self.pdp_port = os.getenv("PDP_PORT", "5002")
        self.pdp_endpoint = f"http://{self.pdp_host}:{self.pdp_port}"

        # Port knocking configuration
        self.knock_sequence = [int(p) for p in os.getenv("KNOCK_SEQUENCE", "7000,8000,9000").split(",")]
        self.knock_timeout = int(os.getenv("KNOCK_TIMEOUT", "1"))  # seconds between knocks

        self.request_timeout = float(os.getenv("REQUEST_TIMEOUT", "5.0"))
        self.jwks_client = PyJWKClient(f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs")

        logger.info(f"Initialized client for realm '{self.realm}' at {self.keycloak_url}")

    def perform_port_knock(self, target_host: str) -> bool:
        """Perform port knocking sequence before making actual request"""
        try:
            logger.info(f"Starting port knock sequence for {target_host}")
            for port in self.knock_sequence:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.knock_timeout)
                try:
                    logger.debug(f"Knocking port {port}")
                    sock.connect((target_host, port))
                except:
                    pass
                finally:
                    sock.close()
                time.sleep(0.1)  # Small delay between knocks
            
            # Wait for ports to open
            time.sleep(1)
            logger.info("Port knock sequence completed")
            return True
        except Exception as e:
            logger.error(f"Port knocking failed: {e}")
            return False

    def generate_nonce(self) -> str:
        return secrets.token_urlsafe(32)

    def validate_nonce(self, nonce: str, client_ip: str) -> bool:
        session = sessions.get(client_ip, {})
        return (
            session.get("nonce") == nonce and
            time.time() - session.get("timestamp", 0) <= NONCE_EXPIRY
        )

    def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
        try:
            token_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"
            response = requests.post(
                token_url,
                data={
                    "grant_type": "password",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "username": username,
                    "password": password
                },
                timeout=self.request_timeout
            )
            if response.status_code != 200:
                return False, response.text

            access_token = response.json()["access_token"]
            return True, access_token

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, str(e)

    def check_pdp(self, token: str, resource: str, action: str) -> Tuple[bool, str]:
        try:
            # Perform port knocking before PDP request
            if not self.perform_port_knock(self.pdp_host):
                return False, "Port knocking failed for PDP"

            response = requests.post(
                f"{self.pdp_endpoint}/check",
                json={"token": token, "resource": resource, "action": action},
                timeout=self.request_timeout
            )
            if response.status_code != 200:
                return False, response.text
            result = response.json()
            return result.get("allowed", False), result.get("message", "No message")
        except Exception as e:
            return False, str(e)

    def check_pep(self, token: str, resource: str, action: str) -> Tuple[bool, str]:
        try:
            # Perform port knocking before PEP request
            if not self.perform_port_knock(self.pep_host):
                return False, "Port knocking failed for PEP"

            response = requests.post(
                f"{self.pep_endpoint}/check",
                headers={"Authorization": f"Bearer {token}"},
                json={"resource": resource, "action": action},
                timeout=self.request_timeout
            )
            if response.status_code != 200:
                return False, response.text
            result = response.json()
            return result.get("allowed", False), result.get("message", "No message")
        except Exception as e:
            return False, str(e)

# --- Global Client Instance ---
client = Client()

# --- API Endpoints ---
@app.get("/get-nonce")
async def get_nonce(request: Request):
    client_ip = request.client.host
    nonce = client.generate_nonce()
    sessions[client_ip] = {'nonce': nonce, 'timestamp': time.time()}
    return {"nonce": nonce}

@app.post("/authenticate")
async def authenticate(request: AuthRequest):
    try:
        logger.info(f"Authenticating {request.username} for operation {request.operation}")
        
        # Step 1: Authenticate with Keycloak
        success, token = client.authenticate(request.username, request.password)
        if not success:
            raise HTTPException(status_code=401, detail=token)

        # Step 2: Map operation to resource/action
        mapping = OPERATION_MAP.get(request.operation)
        if not mapping:
            raise HTTPException(status_code=400, detail="Invalid operation keyword")

        resource = mapping["resource"]
        action = mapping["action"]

        # Step 3: PDP check
        allowed, message = client.check_pdp(token, resource, action)
        if not allowed:
            raise HTTPException(status_code=403, detail=f"PDP denied: {message}")

        # Step 4: PEP check
        allowed, message = client.check_pep(token, resource, action)
        if not allowed:
            raise HTTPException(status_code=403, detail=f"PEP denied: {message}")

        return {
            "status": "success",
            "token": token,
            "resource": resource,
            "action": action,
            "message": message
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Main Entry Point ---
def main():
    host = os.getenv("CLIENT_HOST", "0.0.0.0")
    port = int(os.getenv("CLIENT_PORT", "5000"))
    logger.info(f"Starting server at {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
