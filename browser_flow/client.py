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
from fastapi import FastAPI, HTTPException, Request, Response, status, Cookie
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from collections import defaultdict
import socket
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add a middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {request.headers}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

sessions = defaultdict(dict)
NONCE_EXPIRY = 300  # 5 minutes

# --- Mapping from operations to resource/action ---
OPERATION_MAP = {
    # Admin operations
    "adminCreateUser": {"resource": "users", "action": "create"},
    "adminReadUser": {"resource": "users", "action": "read"},
    "adminUpdateUser": {"resource": "users", "action": "update"},
    "adminDeleteUser": {"resource": "users", "action": "delete"},
    
    "adminCreateStudent": {"resource": "students", "action": "create"},
    "adminReadStudent": {"resource": "students", "action": "read"},
    "adminUpdateStudent": {"resource": "students", "action": "update"},
    "adminDeleteStudent": {"resource": "students", "action": "delete"},
    
    "adminCreateTeacher": {"resource": "teachers", "action": "create"},
    "adminReadTeacher": {"resource": "teachers", "action": "read"},
    "adminUpdateTeacher": {"resource": "teachers", "action": "update"},
    "adminDeleteTeacher": {"resource": "teachers", "action": "delete"},
    
    "adminCreateHostel": {"resource": "hostels", "action": "create"},
    "adminReadHostel": {"resource": "hostels", "action": "read"},
    "adminUpdateHostel": {"resource": "hostels", "action": "update"},
    "adminDeleteHostel": {"resource": "hostels", "action": "delete"},
    
    "adminCreateWarden": {"resource": "wardens", "action": "create"},
    "adminReadWarden": {"resource": "wardens", "action": "read"},
    "adminUpdateWarden": {"resource": "wardens", "action": "update"},
    "adminDeleteWarden": {"resource": "wardens", "action": "delete"},
    
    "adminReadProfile": {"resource": "profile", "action": "read"},
    "adminUpdateProfile": {"resource": "profile", "action": "update"},
    
    # Teacher operations
    "teacherReadStudent": {"resource": "students", "action": "read"},
    "teacherUpdateStudent": {"resource": "students", "action": "update"},
    "teacherReadProfile": {"resource": "profile", "action": "read"},
    
    # Warden operations
    "wardenReadStudent": {"resource": "students", "action": "read"},
    "wardenReadHostel": {"resource": "hostels", "action": "read"},
    "wardenUpdateHostel": {"resource": "hostels", "action": "update"},
    "wardenReadWarden": {"resource": "wardens", "action": "read"},
    "wardenReadProfile": {"resource": "profile", "action": "read"},
    
    # Student operations
    "studentReadProfile": {"resource": "profile", "action": "read"}
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

# --- Session Management ---
SESSIONS = defaultdict(dict)
SESSION_COOKIE_NAME = "zta_session_id"

# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/success.html", response_class=HTMLResponse)
async def success_page():
    with open("static/success.html", "r") as f:
        return f.read()

@app.get("/get-nonce")
async def get_nonce(request: Request):
    client_ip = request.client.host
    nonce = client.generate_nonce()
    sessions[client_ip] = {'nonce': nonce, 'timestamp': time.time()}
    return {"nonce": nonce}

@app.get("/login")
async def login(request: Request):
    # Generate a state and store it in session
    session_id = request.cookies.get(SESSION_COOKIE_NAME) or secrets.token_urlsafe(16)
    state = secrets.token_urlsafe(16)
    SESSIONS[session_id]["state"] = state
    # Use the host from the request instead of hardcoded localhost
    host = request.headers.get("host", "localhost:5000")
    redirect_uri = f"http://{host}/callback"
    params = {
        "client_id": client.client_id,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": redirect_uri,
        "state": state,
    }
    auth_url = f"{client.keycloak_url}/realms/{client.realm}/protocol/openid-connect/auth?{urlencode(params)}"
    logger.info(f"Redirecting to: {auth_url}")
    response = RedirectResponse(auth_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(SESSION_COOKIE_NAME, session_id, httponly=True)
    return response

@app.get("/callback")
async def callback(request: Request, code: str = None, state: str = None):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id or session_id not in SESSIONS:
        return JSONResponse({"error": "Session not found"}, status_code=400)
    if not code or not state:
        return JSONResponse({"error": "Missing code or state"}, status_code=400)
    if SESSIONS[session_id].get("state") != state:
        return JSONResponse({"error": "Invalid state"}, status_code=400)
    # Use the host from the request instead of hardcoded localhost
    host = request.headers.get("host", "localhost:5000")
    redirect_uri = f"http://{host}/callback"
    token_url = f"{client.keycloak_url}/realms/{client.realm}/protocol/openid-connect/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client.client_id,
        "client_secret": client.client_secret,
    }
    token_resp = requests.post(token_url, data=data, timeout=client.request_timeout)
    if token_resp.status_code != 200:
        return JSONResponse({"error": "Token exchange failed", "details": token_resp.text}, status_code=400)
    token_data = token_resp.json()
    access_token = token_data["access_token"]
    SESSIONS[session_id]["resource_authenticated"] = True
    SESSIONS[session_id]["token"] = access_token
    # Decode JWT to extract roles
    try:
        signing_key = client.jwks_client.get_signing_key_from_jwt(access_token)
        decoded = jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=client.client_id,
            options={"verify_exp": True}
        )
        roles = decoded.get("realm_access", {}).get("roles", [])
        SESSIONS[session_id]["roles"] = roles
        logger.info(f"User roles: {roles}")
    except Exception as e:
        logger.error(f"Failed to decode JWT or extract roles: {e}")
        SESSIONS[session_id]["roles"] = []
    # Redirect to success page
    return RedirectResponse("/success.html", status_code=status.HTTP_302_FOUND)

@app.get("/session-status")
async def session_status(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id and SESSIONS[session_id].get("resource_authenticated"):
        return {
            "resource_authenticated": True,
            "roles": SESSIONS[session_id].get("roles", []),
            "session_id": session_id
        }
    return {"resource_authenticated": False}

@app.post("/api/test-pep")
async def test_pep_endpoint(request: Request):
    """Test PEP service with current session token"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id or session_id not in SESSIONS:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = SESSIONS[session_id].get("token")
    if not token:
        raise HTTPException(status_code=401, detail="No token found")
    
    # Test PEP with a sample resource/action
    resource = "students"
    action = "read"
    
    logger.info(f"Testing PEP service for resource={resource}, action={action}")
    allowed, message = client.check_pep(token, resource, action)
    
    return {
        "service": "PEP",
        "resource": resource,
        "action": action,
        "allowed": allowed,
        "message": message,
        "port_knock_performed": True
    }

@app.post("/api/test-pdp")
async def test_pdp_endpoint(request: Request):
    """Test PDP service with current session token"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id or session_id not in SESSIONS:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = SESSIONS[session_id].get("token")
    if not token:
        raise HTTPException(status_code=401, detail="No token found")
    
    # Test PDP with a sample resource/action
    resource = "students"
    action = "read"
    
    logger.info(f"Testing PDP service for resource={resource}, action={action}")
    allowed, message = client.check_pdp(token, resource, action)
    
    return {
        "service": "PDP",
        "resource": resource,
        "action": action,
        "allowed": allowed,
        "message": message,
        "port_knock_performed": True
    }

@app.post("/api/access-resource")
async def access_resource(request: Request):
    """Make a protected resource request through full ZTA flow"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id or session_id not in SESSIONS:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = SESSIONS[session_id].get("token")
    if not token:
        raise HTTPException(status_code=401, detail="No token found")
    
    # Get request body
    body = await request.json()
    operation = body.get("operation", "studentReadProfile")
    
    # Map operation to resource/action
    if operation not in OPERATION_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown operation: {operation}")
    
    mapping = OPERATION_MAP[operation]
    resource = mapping["resource"]
    action = mapping["action"]
    
    logger.info(f"Processing resource access: operation={operation}, resource={resource}, action={action}")
    
    # Step 1: Check PEP (includes port knocking)
    logger.info("Step 1: Checking PEP...")
    pep_allowed, pep_message = client.check_pep(token, resource, action)
    
    if not pep_allowed:
        return {
            "success": False,
            "step": "PEP",
            "message": pep_message,
            "operation": operation,
            "resource": resource,
            "action": action
        }
    
    # Step 2: Check PDP (includes port knocking)
    logger.info("Step 2: Checking PDP...")
    pdp_allowed, pdp_message = client.check_pdp(token, resource, action)
    
    if not pdp_allowed:
        return {
            "success": False,
            "step": "PDP",
            "message": pdp_message,
            "operation": operation,
            "resource": resource,
            "action": action
        }
    
    # Step 3: Access granted
    logger.info("All checks passed - access granted")
    return {
        "success": True,
        "message": "Access granted through full ZTA flow",
        "operation": operation,
        "resource": resource,
        "action": action,
        "steps_completed": ["Port Knocking", "PEP Check", "PDP Check"],
        "pep_message": pep_message,
        "pdp_message": pdp_message
    }

@app.get("/api/operations")
async def get_operations():
    """Get list of available operations for testing"""
    return {
        "operations": list(OPERATION_MAP.keys()),
        "mappings": OPERATION_MAP
    }

@app.get("/test-keycloak")
async def test_keycloak():
    try:
        # Test direct connection to Keycloak
        test_url = f"http://{os.getenv('KEYCLOAK_HOST')}:{os.getenv('KEYCLOAK_PORT')}/realms/{os.getenv('REALM')}/.well-known/openid-configuration"
        logger.info(f"Testing Keycloak connection at: {test_url}")
        
        response = requests.get(test_url, timeout=30)
        response.raise_for_status()
        
        return {
            "status": "success",
            "message": "Successfully connected to Keycloak",
            "url": test_url,
            "response": response.json()
        }
    except Exception as e:
        logger.error(f"Keycloak test failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "url": test_url
        }

# --- Main Entry Point ---
def main():
    host = "0.0.0.0"
    port = int(os.getenv("CLIENT_PORT", "5000"))
    logger.info(f"Starting server at {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
