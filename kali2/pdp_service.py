from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Optional
import jwt
import os
import secrets
import time
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class Subject(BaseModel):
    roles: List[str]
    username: str
    email: str

class Environment(BaseModel):
    network: str
    timestamp: str

class PolicyRequest(BaseModel):
    subject: Subject
    resource: str
    action: str
    environment: Environment

class PolicyDecision(BaseModel):
    decision: bool
    reason: str
    obligations: Optional[Dict] = None

class NonceRequest(BaseModel):
    subject: Subject
    timestamp: str

class NonceResponse(BaseModel):
    nonce: str
    expires_at: int

class SessionKeyRequest(BaseModel):
    subject: Subject
    nonce: str
    nonce_response: str
    timestamp: str

class SessionKeyResponse(BaseModel):
    session_key: str
    expires_at: int

class PDP:
    def __init__(self):
        # Load policies from configuration
        self.policies = {
            "default": {
                "effect": "deny",
                "priority": 0
            },
            "admin_access": {
                "effect": "allow",
                "priority": 100,
                "conditions": {
                    "roles": ["admin"],
                    "resources": ["*"],
                    "actions": ["*"]
                }
            },
            "teacher_access": {
                "effect": "allow",
                "priority": 80,
                "conditions": {
                    "roles": ["Teacher"],
                    "resources": [
                        "/academic/*",
                        "/students/*",
                        "/courses/*",
                        "/protected-resource"
                    ],
                    "actions": ["GET", "POST", "PUT", "access"]
                }
            },
            "student_access": {
                "effect": "allow",
                "priority": 60,
                "conditions": {
                    "roles": ["Student"],
                    "resources": [
                        "/academic/own/*",
                        "/courses/enrolled/*",
                        "/protected-resource"
                    ],
                    "actions": ["GET", "access"]
                }
            },
            "warden_access": {
                "effect": "allow",
                "priority": 70,
                "conditions": {
                    "roles": ["Warden"],
                    "resources": [
                        "/hostel/*",
                        "/students/hostel/*",
                        "/protected-resource"
                    ],
                    "actions": ["GET", "POST", "PUT", "access"]
                }
            }
        }
        # Add nonce and session storage
        self.nonce_store: Dict[str, Dict] = {}
        self.session_store: Dict[str, Dict] = {}
        self.nonce_expiry = 300  # 5 minutes
        self.session_expiry = 3600  # 1 hour

    def evaluate_policy(self, request: PolicyRequest) -> PolicyDecision:
        """
        Evaluate access request against policies
        """
        logger.info(f"Evaluating policy for request: {request.dict()}")
        
        # Sort policies by priority
        sorted_policies = sorted(
            self.policies.items(),
            key=lambda x: x[1].get("priority", 0),
            reverse=True
        )
        logger.info(f"Sorted policies by priority: {[p[0] for p in sorted_policies]}")

        for policy_name, policy in sorted_policies:
            logger.info(f"Checking policy: {policy_name}")
            if self._match_policy(policy, request):
                logger.info(f"Policy {policy_name} matched")
                return PolicyDecision(
                    decision=(policy["effect"] == "allow"),
                    reason=f"Policy {policy_name} matched",
                    obligations=policy.get("obligations")
                )
            else:
                logger.info(f"Policy {policy_name} did not match")

        logger.info("No matching policy found")
        return PolicyDecision(
            decision=False,
            reason="No matching policy found"
        )

    def _match_policy(self, policy: Dict, request: PolicyRequest) -> bool:
        """
        Check if request matches policy conditions
        """
        conditions = policy.get("conditions", {})
        logger.info(f"Checking conditions: {conditions}")
        
        # Check roles
        if "roles" in conditions:
            logger.info(f"Checking roles. Required: {conditions['roles']}, User has: {request.subject.roles}")
            if not any(role in request.subject.roles for role in conditions["roles"]):
                logger.info("Role check failed")
                return False
            logger.info("Role check passed")

        # Check resources
        if "resources" in conditions:
            logger.info(f"Checking resources. Required: {conditions['resources']}, Requested: {request.resource}")
            if not any(self._match_pattern(request.resource, pattern) 
                      for pattern in conditions["resources"]):
                logger.info("Resource check failed")
                return False
            logger.info("Resource check passed")

        # Check actions
        if "actions" in conditions:
            logger.info(f"Checking actions. Required: {conditions['actions']}, Requested: {request.action}")
            if request.action.upper() not in [action.upper() for action in conditions["actions"]]:
                logger.info("Action check failed")
                return False
            logger.info("Action check passed")

        logger.info("All checks passed")
        return True

    def _match_pattern(self, resource: str, pattern: str) -> bool:
        """
        Match resource against pattern with wildcard support
        """
        if pattern == "*":
            return True
        import re
        pattern = pattern.replace("*", ".*")
        return bool(re.match(f"^{pattern}$", resource))

    def generate_nonce(self, request: NonceRequest) -> NonceResponse:
        """
        Generate a secure nonce for authentication
        """
        nonce = secrets.token_hex(32)
        expires_at = int(time.time()) + self.nonce_expiry
        
        # Store nonce with subject info
        self.nonce_store[nonce] = {
            "subject": request.subject,
            "expires_at": expires_at,
            "timestamp": request.timestamp
        }
        
        return NonceResponse(nonce=nonce, expires_at=expires_at)

    def validate_nonce_response(self, request: SessionKeyRequest) -> bool:
        """
        Validate the client's response to the nonce challenge
        """
        if request.nonce not in self.nonce_store:
            return False
            
        nonce_data = self.nonce_store[request.nonce]
        
        # Check if nonce has expired
        if time.time() > nonce_data["expires_at"]:
            del self.nonce_store[request.nonce]
            return False
            
        # Validate the response (this is a simple example - you should implement proper validation)
        expected_response = self._generate_expected_response(request.nonce, nonce_data["subject"])
        return request.nonce_response == expected_response

    def generate_session_key(self, request: SessionKeyRequest) -> Optional[SessionKeyResponse]:
        """
        Generate session keys if nonce response is valid
        """
        if not self.validate_nonce_response(request):
            return None
            
        # Generate session key
        session_key = secrets.token_hex(32)
        expires_at = int(time.time()) + self.session_expiry
        
        # Store session
        self.session_store[session_key] = {
            "subject": request.subject,
            "expires_at": expires_at,
            "created_at": time.time()
        }
        
        # Clean up used nonce
        del self.nonce_store[request.nonce]
        
        return SessionKeyResponse(session_key=session_key, expires_at=expires_at)

    def _generate_expected_response(self, nonce: str, subject: Subject) -> str:
        """
        Generate the expected response for the nonce challenge
        This is a simple example - implement proper challenge-response mechanism
        """
        # In a real implementation, this would be a proper cryptographic challenge-response
        return f"{nonce}:{subject.username}"

# Initialize FastAPI app
app = FastAPI(title="Policy Decision Point")
pdp = PDP()

@app.post("/evaluate")
async def evaluate_policy(request: PolicyRequest):
    """
    Evaluate access request and return policy decision
    """
    try:
        decision = pdp.evaluate_policy(request)
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "pdp",
        "policies": list(pdp.policies.keys())
    }

@app.post("/nonce")
async def get_nonce(request: NonceRequest):
    """
    Generate a nonce for authentication
    """
    try:
        return pdp.generate_nonce(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session-key")
async def get_session_key(request: SessionKeyRequest):
    """
    Generate session keys after nonce validation
    """
    try:
        response = pdp.generate_session_key(request)
        if not response:
            raise HTTPException(status_code=401, detail="Invalid nonce response")
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting PDP service on port 5002...")
    uvicorn.run(app, host="0.0.0.0", port=5002)
