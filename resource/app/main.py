from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to PEP service IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Role to website mapping
ROLE_WEBSITES = {
    "admin": "https://gmail.com",
    "student": "https://google.com",
    "teacher": "https://youtube.com",
    "warden": "https://facebook.com"
}

@app.get("/")
async def root():
    return {"message": "Protected Resource Service"}

@app.get("/api/v1/{resource}")
async def get_resource(
    resource: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        # Get headers from request
        session_id = request.headers.get("X-Session-ID")
        action = request.headers.get("X-Action")
        user = request.headers.get("X-User")
        roles = request.headers.get("X-Roles", "").split(",")
        
        logger.info(f"Request from user {user} with roles {roles} for {action} on {resource}")
        
        # Get the first role (in a real app, you might want to check all roles)
        role = roles[0].lower() if roles else None
        
        if not role or role not in ROLE_WEBSITES:
            raise HTTPException(status_code=403, detail=f"Invalid role: {role}")
        
        # Get the website URL for the role
        website_url = ROLE_WEBSITES[role]
        
        # Log the access
        logger.info(f"User {user} with role {role} accessing {website_url}")
        
        # Return response in the format expected by PEP
        return {
            "status": "success",
            "session_id": session_id,
            "data": {
                "redirect_url": website_url,
                "role": role,
                "user": user,
                "resource": resource,
                "action": action
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 