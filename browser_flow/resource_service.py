from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    return {"message": "Protected Resource Service", "status": "running"}

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
        
        logger.info(f"Protected Resource: Request from user {user} with roles {roles} for {action} on {resource}")
        
        # Get the first role
        role = roles[0].lower() if roles else None
        
        if not role or role not in ROLE_WEBSITES:
            logger.warning(f"Invalid role: {role}")
            raise HTTPException(status_code=403, detail=f"Invalid role: {role}")
        
        # Get the website URL for the role
        website_url = ROLE_WEBSITES[role]
        
        # Log the access
        logger.info(f"Access granted: User {user} with role {role} -> {website_url}")
        
        # Return response in the format expected by PEP
        return {
            "status": "success",
            "session_id": session_id,
            "data": {
                "redirect_url": website_url,
                "role": role,
                "user": user,
                "resource": resource,
                "action": action,
                "message": f"Access granted to {resource}"
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
