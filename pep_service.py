from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from typing import Dict, Any
import requests
from functools import lru_cache
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

app = FastAPI(title="PEP Service")
security = HTTPBearer()

class PEPMiddleware:
    def __init__(self):
        # Keycloak configuration - running locally on Kali2
        self.keycloak_host = os.getenv("KEYCLOAK_HOST", "http://localhost:8080")
        self.realm = os.getenv("REALM", "zta")
        self.client_id = os.getenv("CLIENT_ID", "pep-backend")
        self.jwks_url = f"{self.keycloak_host}/realms/{self.realm}/protocol/openid-connect/certs"
        self.jwks_client = PyJWKClient(self.jwks_url)
        
        # Resource service configuration - using ZT segment IP of Kali4
        self.resource_service_url = os.getenv("RESOURCE_SERVICE_URL", "http://192.168.200.4:5001")
        
        # Network configuration
        self.pep_host = os.getenv("PEP_HOST", "192.168.200.2")  # ZT segment IP of Kali2
        self.pep_port = int(os.getenv("PEP_PORT", "5000"))
        
        # ZT segment configuration
        self.zt_segment = os.getenv("ZT_SEGMENT", "zt_segment")
        self.allowed_networks = os.getenv("ALLOWED_NETWORKS", "intranet,zt_segment").split(",")

    @lru_cache(maxsize=1)
    def get_signing_key(self, token: str):
        try:
            return self.jwks_client.get_signing_key_from_jwt(token).key
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid token signature")

    def validate_token(self, token: str) -> Dict[str, Any]:
        try:
            signing_key = self.get_signing_key(token)
            decoded = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.client_id
            )
            return decoded
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

    def enforce_policy(self, token_data: Dict[str, Any], resource: str, action: str) -> bool:
        """
        Enforce access control policies based on token claims and resource/action
        """
        roles = token_data.get("realm_access", {}).get("roles", [])
        
        # Example policy: Only allow access if user has 'admin' role
        if action == "read" and "admin" in roles:
            return True
            
        # Example policy: Allow access to public resources
        if resource == "public" and action == "read":
            return True
            
        return False

    def validate_network_access(self, request: Request) -> bool:
        """
        Validate if the request is coming from an allowed network
        """
        client_ip = request.client.host
        # Check if request is coming from ZT segment or intranet
        if client_ip.startswith("192.168.200.") or client_ip.startswith("192.168.100."):
            return True
        return False

pep_middleware = PEPMiddleware()

@app.middleware("http")
async def pep_middleware_handler(request: Request, call_next):
    # Skip PEP for health check endpoint
    if request.url.path == "/health":
        return await call_next(request)

    # Validate network access
    if not pep_middleware.validate_network_access(request):
        raise HTTPException(status_code=403, detail="Access denied: Not in allowed network")

    # Get the authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No valid authorization header")

    # Extract and validate token
    token = auth_header.split(" ")[1]
    token_data = pep_middleware.validate_token(token)

    # Determine resource and action from the request
    resource = request.url.path.strip("/")
    action = request.method.lower()

    # Enforce policy
    if not pep_middleware.enforce_policy(token_data, resource, action):
        raise HTTPException(
            status_code=403,
            detail="Access denied based on policy enforcement"
        )

    # Forward the request to the resource service
    async with httpx.AsyncClient() as client:
        try:
            # Forward the request to the resource service
            response = await client.request(
                method=request.method,
                url=f"{pep_middleware.resource_service_url}{request.url.path}",
                headers=dict(request.headers),
                content=await request.body()
            )
            return response
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Resource service unavailable: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "pep",
        "host": pep_middleware.pep_host,
        "network": pep_middleware.zt_segment,
        "keycloak": self.keycloak_host
    }

if __name__ == "__main__":
    import uvicorn
    print(f"Starting PEP service on {pep_middleware.pep_host}:{pep_middleware.pep_port}")
    print(f"Resource service URL: {pep_middleware.resource_service_url}")
    print(f"Keycloak URL: {pep_middleware.keycloak_host}")
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Listen on all interfaces
        port=pep_middleware.pep_port
    ) 