from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Optional
import jwt
import os
from dotenv import load_dotenv

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
                        "/courses/*"
                    ],
                    "actions": ["GET", "POST", "PUT"]
                }
            },
            "student_access": {
                "effect": "allow",
                "priority": 60,
                "conditions": {
                    "roles": ["Student"],
                    "resources": [
                        "/academic/own/*",
                        "/courses/enrolled/*"
                    ],
                    "actions": ["GET"]
                }
            },
            "warden_access": {
                "effect": "allow",
                "priority": 70,
                "conditions": {
                    "roles": ["Warden"],
                    "resources": [
                        "/hostel/*",
                        "/students/hostel/*"
                    ],
                    "actions": ["GET", "POST", "PUT"]
                }
            }
        }

    def evaluate_policy(self, request: PolicyRequest) -> PolicyDecision:
        """
        Evaluate access request against policies
        """
        # Sort policies by priority
        sorted_policies = sorted(
            self.policies.items(),
            key=lambda x: x[1].get("priority", 0),
            reverse=True
        )

        for policy_name, policy in sorted_policies:
            if self._match_policy(policy, request):
                return PolicyDecision(
                    decision=(policy["effect"] == "allow"),
                    reason=f"Policy {policy_name} matched",
                    obligations=policy.get("obligations")
                )

        return PolicyDecision(
            decision=False,
            reason="No matching policy found"
        )

    def _match_policy(self, policy: Dict, request: PolicyRequest) -> bool:
        """
        Check if request matches policy conditions
        """
        conditions = policy.get("conditions", {})
        
        # Check roles
        if "roles" in conditions:
            if not any(role in request.subject.roles for role in conditions["roles"]):
                return False

        # Check resources
        if "resources" in conditions:
            if not any(self._match_pattern(request.resource, pattern) 
                      for pattern in conditions["resources"]):
                return False

        # Check actions
        if "actions" in conditions:
            if request.action.upper() not in [action.upper() for action in conditions["actions"]]:
                return False

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

if __name__ == "__main__":
    import uvicorn
    print("Starting PDP service on port 5002...")
    uvicorn.run(app, host="0.0.0.0", port=5002)
