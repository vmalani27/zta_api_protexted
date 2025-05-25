from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .core.config import settings
import requests

app = FastAPI(title="Protected Resource Service")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

async def verify_pep_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token with PEP service"""
    try:
        response = requests.get(
            f"http://{settings.PEP_HOST}:{settings.PEP_PORT}/verify-token",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        return response.json()
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PEP service unavailable"
        )

@app.get("/")
async def protected_resource(token_data: dict = Depends(verify_pep_token)):
    """
    Protected resource endpoint that requires valid JWT token and enforces policies
    """
    return {
        "message": "Access granted to protected resource",
        "user_info": {
            "sub": token_data.get("sub"),
            "roles": token_data.get("realm_access", {}).get("roles", [])
        }
    } 