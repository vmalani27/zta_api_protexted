from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, List
import requests
import time
import logging
import os
from .core.config import settings

app = FastAPI(title="Policy Enforcement Point Service")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

class AuthRequest(BaseModel):
    username: str
    password: str

class CheckRequest(BaseModel):
    resource: str
    action: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class CheckResponse(BaseModel):
    allowed: bool
    message: str
    url: Optional[str] = None

@app.post("/authenticate", response_model=TokenResponse)
async def authenticate(request: AuthRequest):
    """
    Authenticate user and return JWT token
    """
    try:
        # Call IAM service to authenticate
        response = requests.post(
            f"{settings.IAM_SERVICE_URL}/authenticate",
            json={"username": request.username, "password": request.password}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/check", response_model=CheckResponse)
async def check_permission(
    request: CheckRequest,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """
    Check if user has permission to access resource
    """
    try:
        # Call PDP service to check permission
        response = requests.post(
            f"{settings.PDP_SERVICE_URL}/check",
            json={
                "token": credentials.credentials,
                "resource": request.resource,
                "action": request.action
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if result["allowed"]:
                # Construct URL based on resource and action
                base_url = settings.PROTECTED_RESOURCE_URL
                resource_path = request.resource.lower()
                
                # Add session ID to URL
                session_id = f"session_{int(time.time())}"
                url = f"{base_url}/{resource_path}?session_id={session_id}"
                
                return {
                    "allowed": True,
                    "message": "Access granted",
                    "url": url
                }
            else:
                return {
                    "allowed": False,
                    "message": "Access denied"
                }
        else:
            raise HTTPException(
                status_code=403,
                detail="Permission check failed"
            )
    except Exception as e:
        logger.error(f"Permission check error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 