from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# Network configuration with explicit defaults
RESOURCE_HOST: str = os.getenv("RESOURCE_HOST", "192.168.200.4")  # ZT segment IP of Kali4
RESOURCE_PORT: int = int(os.getenv("RESOURCE_PORT", "5001"))
ZT_SEGMENT: str = os.getenv("ZT_SEGMENT", "zt_segment")
PEP_SERVICE_IP: str = os.getenv("PEP_SERVICE_IP", "192.168.200.2")  # ZT segment IP of Kali2

# Create FastAPI app
app = FastAPI(
    title="Protected Resource Service",
    description="Resource service running on Kali4 in ZT segment",
    version="1.0.0"
)

# Set up CORS - only allow requests from PEP service
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{PEP_SERVICE_IP}:5000"],  # Only allow PEP service
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def validate_pep_request(request: Request, call_next):
    """
    Middleware to ensure requests only come from PEP service
    """
    client_ip = request.client.host
    if client_ip != PEP_SERVICE_IP:
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied: Request must come from PEP service ({PEP_SERVICE_IP})"
        )
    return await call_next(request)

@app.get("/")
def root():
    return {
        "message": "Welcome to Protected Resource Service",
        "host": RESOURCE_HOST,
        "network": ZT_SEGMENT,
        "interface": "ZT segment (eth1)",
        "pep_service": PEP_SERVICE_IP
    }

@app.get("/protected-resource")
async def protected_resource():
    """
    Protected resource endpoint
    """
    return {
        "message": "Access granted to protected resource",
        "data": {
            "resource_id": "123",
            "resource_type": "sensitive_data",
            "content": "This is protected content",
            "network": ZT_SEGMENT,
            "interface": "ZT segment (eth1)"
        }
    }

@app.get("/public-resource")
async def public_resource():
    """
    Public resource endpoint
    """
    return {
        "message": "Access granted to public resource",
        "data": {
            "resource_id": "456",
            "resource_type": "public_data",
            "content": "This is public content",
            "network": ZT_SEGMENT,
            "interface": "ZT segment (eth1)"
        }
    }

@app.get("/config")
def get_config():
    """
    Get current service configuration
    """
    return {
        "resource_host": RESOURCE_HOST,
        "resource_port": RESOURCE_PORT,
        "zt_segment": ZT_SEGMENT,
        "pep_service_ip": PEP_SERVICE_IP
    }

if __name__ == "__main__":
    import uvicorn
    print(f"Starting Resource service on {RESOURCE_HOST}:{RESOURCE_PORT}")
    print(f"Only accepting requests from PEP service at {PEP_SERVICE_IP}:5000")
    print(f"Network: ZT segment (eth1)")
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Listen on all interfaces
        port=RESOURCE_PORT
    ) 