import os
import logging
import requests
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pep_service")

app = FastAPI()
security = HTTPBearer()

# Configuration from environment variables
PROTECTED_RESOURCE_URL = os.getenv("RESOURCE_HOST", "protected-resource")
PROTECTED_RESOURCE_PORT = os.getenv("RESOURCE_PORT", "8000")

# Session management
sessions: Dict[str, Dict] = {}
SESSION_EXPIRY = timedelta(minutes=30)

# Role-based access control
ROLE_PERMISSIONS = {
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

class CheckRequest(BaseModel):
    resource: str
    action: str
    data: Optional[dict] = None

def get_user_roles(token: str) -> List[str]:
    """Get user roles from token"""
    # For testing, return a list of roles
    # In production, this would decode the JWT token
    return ["admin"]  # Default to admin for testing

def check_role_permission(role: str, resource: str, action: str) -> bool:
    """Check if role has permission to access resource"""
    role_config = ROLE_PERMISSIONS.get(role.lower(), {})
    allowed_actions = role_config.get(resource, [])
    return action in allowed_actions

@app.post("/check")
async def check_access_post(request: CheckRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        roles = get_user_roles(token)
        
        # Check if any role has permission
        has_permission = False
        for role in roles:
            if check_role_permission(role, request.resource, request.action):
                has_permission = True
                break
        
        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail=f"No permission to {request.action} {request.resource}"
            )
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Store session data
        sessions[session_id] = {
            "token": token,
            "roles": roles,
            "expires": datetime.now() + SESSION_EXPIRY
        }
        
        # Forward to protected resource
        protected_url = f"http://{PROTECTED_RESOURCE_URL}:{PROTECTED_RESOURCE_PORT}/api/v1/{request.resource}"
        logger.info(f"Making request to: {protected_url}")
        
        # Extract username from token (for testing, use "admin")
        username = "admin"  # In production, decode from JWT
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Session-ID": session_id,
            "X-Action": request.action,
            "X-User": username,
            "X-Roles": ",".join(roles)
        }
        
        logger.info(f"With headers: {headers}")
        
        # Forward the request to the protected resource
        protected_response = requests.get(
            protected_url,
            headers=headers
        )
        
        if protected_response.status_code != 200:
            raise HTTPException(
                status_code=protected_response.status_code,
                detail=f"Protected resource error: {protected_response.text}"
            )
        
        # Get response data
        response_data = protected_response.json()
        
        # If we have a redirect URL in the response, return it directly
        if "data" in response_data and "redirect_url" in response_data["data"]:
            return {
                "status": "success",
                "session_id": session_id,
                "redirect_url": response_data["data"]["redirect_url"],
                "role": response_data["data"]["role"],
                "user": response_data["data"]["user"]
            }
        
        # Otherwise return the full response
        return {
            "status": "success",
            "session_id": session_id,
            "data": response_data.get("data", {})
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Access check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Access check error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/authenticate")
async def authenticate(request: Request):
    try:
        data = await request.json()
        token = data.get("token")
        
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")
        
        # Get roles based on token
        roles = get_user_roles(token)
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Store session data
        sessions[session_id] = {
            "token": token,
            "roles": roles,
            "expires": datetime.now() + SESSION_EXPIRY
        }
        
        return {
            "status": "success",
            "session_id": session_id,
            "roles": roles
        }
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
    
