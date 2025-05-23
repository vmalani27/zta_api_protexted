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
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # PDP configuration
        self.pdp_url = os.getenv("PDP_URL", "http://192.168.200.3:5002")
        
        # Network configuration
        self.pep_host = os.getenv("PEP_HOST", "192.168.200.2")  # ZT segment IP of Kali2
        self.pep_port = int(os.getenv("PEP_PORT", "5000"))
        
        # ZT segment configuration
        self.zt_segment = os.getenv("ZT_SEGMENT", "zt_segment")
        self.allowed_networks = os.getenv("ALLOWED_NETWORKS", "intranet,zt_segment").split(",")
        
        # Timeout configuration
        self.resource_timeout = float(os.getenv("RESOURCE_TIMEOUT", "5.0"))  # 5 seconds timeout
        self.pdp_timeout = float(os.getenv("PDP_TIMEOUT", "3.0"))  # 3 seconds timeout

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

    async def consult_pdp(self, token_data: Dict[str, Any], resource: str, action: str) -> bool:
        """
        Consult the Policy Decision Point (PDP) for access control decisions
        """
        try:
            async with httpx.AsyncClient(timeout=self.pdp_timeout) as client:
                response = await client.post(
                    f"{self.pdp_url}/evaluate",
                    json={
                        "subject": {
                            "roles": token_data.get("realm_access", {}).get("roles", []),
                            "username": token_data.get("preferred_username", ""),
                            "email": token_data.get("email", "")
                        },
                        "resource": resource,
                        "action": action,
                        "environment": {
                            "network": self.zt_segment,
                            "timestamp": str(datetime.datetime.utcnow())
                        }
                    }
                )
                if response.status_code == 200:
                    decision = response.json()
                    return decision.get("decision", False)
                logger.error(f"PDP returned status code {response.status_code}")
                return False
        except httpx.TimeoutException:
            logger.error("PDP consultation timed out")
            raise HTTPException(status_code=503, detail="Policy decision service timed out")
        except Exception as e:
            logger.error(f"Error consulting PDP: {str(e)}")
            raise HTTPException(status_code=503, detail="Policy decision service unavailable")

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

    # Consult PDP for policy decision
    if not await pep_middleware.consult_pdp(token_data, resource, action):
        raise HTTPException(
            status_code=403,
            detail="Access denied based on policy decision"
        )

    # Forward the request to the resource service
    async with httpx.AsyncClient(timeout=pep_middleware.resource_timeout) as client:
        try:
            # Forward the request to the resource service
            response = await client.request(
                method=request.method,
                url=f"{pep_middleware.resource_service_url}{request.url.path}",
                headers=dict(request.headers),
                content=await request.body()
            )
            return response
        except httpx.TimeoutException:
            logger.error(f"Resource service timed out after {pep_middleware.resource_timeout} seconds")
            raise HTTPException(
                status_code=503,
                detail=f"Protected resource service timed out after {pep_middleware.resource_timeout} seconds"
            )
        except httpx.ConnectError:
            logger.error("Could not connect to resource service")
            raise HTTPException(
                status_code=503,
                detail="Protected resource service is not running or unreachable"
            )
        except httpx.RequestError as e:
            logger.error(f"Error accessing resource service: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Error accessing protected resource service: {str(e)}"
            )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "pep",
        "host": pep_middleware.pep_host,
        "network": pep_middleware.zt_segment,
        "keycloak": pep_middleware.keycloak_host,
        "pdp": pep_middleware.pdp_url
    }

if __name__ == "__main__":
    import uvicorn
    print(f"Starting PEP service on {pep_middleware.pep_host}:{pep_middleware.pep_port}")
    print(f"Resource service URL: {pep_middleware.resource_service_url}")
    print(f"Keycloak URL: {pep_middleware.keycloak_host}")
    print(f"PDP URL: {pep_middleware.pdp_url}")
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Listen on all interfaces
        port=pep_middleware.pep_port
    ) 