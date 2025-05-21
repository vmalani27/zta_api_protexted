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
        self.keycloak_host = os.getenv("KEYCLOAK_HOST", "http://localhost:8080")
        self.realm = os.getenv("REALM", "zta")
        self.client_id = os.getenv("CLIENT_ID", "pep-backend")
        self.jwks_url = f"{self.keycloak_host}/realms/{self.realm}/protocol/openid-connect/certs"
        self.jwks_client = PyJWKClient(self.jwks_url)
        self.resource_service_url = os.getenv("RESOURCE_SERVICE_URL", "http://localhost:5001")

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

pep_middleware = PEPMiddleware()

@app.middleware("http")
async def pep_middleware_handler(request: Request, call_next):
    # Skip PEP for health check endpoint
    if request.url.path == "/health":
        return await call_next(request)

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
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000) 