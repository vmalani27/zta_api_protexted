from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import secrets
import logging
from typing import Dict, Optional, List
import os
import requests
from pydantic import BaseModel
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class CheckRequest(BaseModel):
    resource: str
    action: str

class CheckResponse(BaseModel):
    allowed: bool
    message: str
    url: Optional[str] = None
    session_id: Optional[str] = None

class ResourceResponse(BaseModel):
    data: Dict
    message: str

app = FastAPI(title="College Management System")
security = HTTPBearer()

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Session management
sessions: Dict[str, dict] = {}

def get_session(session_id: str) -> Optional[dict]:
    """Get session data if valid"""
    if session_id not in sessions:
        return None
    
    session = sessions[session_id]
    if datetime.now().timestamp() > session["expires_at"]:
        del sessions[session_id]
        return None
    
    return session

@app.post("/session")
async def create_session(request: Request):
    """Create a new session"""
    try:
        # Get headers
        auth_header = request.headers.get("Authorization")
        username = request.headers.get("X-User")
        roles = request.headers.get("X-Roles", "").split(",")
        resource = request.headers.get("X-Resource")
        action = request.headers.get("X-Action")
        
        # Log headers for debugging
        logger.info(f"Received headers:")
        logger.info(f"Authorization: {auth_header}")
        logger.info(f"X-User: {username}")
        logger.info(f"X-Roles: {roles}")
        logger.info(f"X-Resource: {resource}")
        logger.info(f"X-Action: {action}")
        
        # Validate required headers
        if not auth_header:
            raise HTTPException(status_code=400, detail="Missing Authorization header")
        if not username:
            raise HTTPException(status_code=400, detail="Missing X-User header")
        if not roles or roles == [""]:
            raise HTTPException(status_code=400, detail="Missing X-Roles header")
        if not resource:
            raise HTTPException(status_code=400, detail="Missing X-Resource header")
        if not action:
            raise HTTPException(status_code=400, detail="Missing X-Action header")
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)
        
        sessions[session_id] = {
            "session_id": session_id,
            "username": username,
            "roles": roles,
            "resource": resource,
            "action": action,
            "created_at": datetime.now().timestamp(),
            "expires_at": expires_at.timestamp()
        }
        
        logger.info(f"Created session {session_id} for user {username}")
        return {"session_id": session_id, "expires_at": expires_at.timestamp()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/check", response_model=CheckResponse)
async def check_permission(
    request: CheckRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Check if user has permission to access resource
    """
    try:
        # Generate a unique session ID
        session_id = secrets.token_urlsafe(32)
        
        # Create session with user info
        sessions[session_id] = {
            "session_id": session_id,
            "username": credentials.credentials,  # Using token as username for now
            "roles": [],  # Will be populated by PDP
            "resource": request.resource,
            "action": request.action,
            "created_at": datetime.now().timestamp(),
            "expires_at": (datetime.now() + timedelta(hours=1)).timestamp()
        }
        
        # Construct URL based on resource and action
        resource_path = request.resource.lower()
        url = f"/api/v1/{resource_path}?session_id={session_id}"
        
        return {
            "allowed": True,
            "message": "Access granted",
            "url": url,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Permission check error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 