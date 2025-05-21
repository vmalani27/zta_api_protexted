#!/usr/bin/env python3
import requests
import jwt
from jwt import PyJWKClient
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ZTAClient:
    def __init__(self):
        # Keycloak configuration (running locally on Kali2)
        self.keycloak_host = os.getenv("KEYCLOAK_HOST", "http://localhost:8080")
        self.realm = os.getenv("REALM", "zta")
        self.client_id = os.getenv("CLIENT_ID", "pep-backend")
        self.client_secret = os.getenv("CLIENT_SECRET", "ifTLdQIpnHOscFeMpiY5jiiO58RvjYxu")
        
        # PEP service configuration (running locally on Kali2)
        self.pep_host = os.getenv("PEP_HOST", "localhost")
        self.pep_port = os.getenv("PEP_PORT", "5000")
        self.pep_endpoint = f"http://{self.pep_host}:{self.pep_port}"
        
        # Resource service configuration (on Kali4)
        self.resource_host = os.getenv("RESOURCE_HOST", "192.168.200.4")
        self.resource_port = os.getenv("RESOURCE_PORT", "5001")
        
        # Token management
        self.access_token = None
        self.token_expiry = 0
        self.jwks_client = None

    def initialize_jwks(self):
        """Initialize JWKS client for token validation"""
        jwks_url = f"{self.keycloak_host}/realms/{self.realm}/protocol/openid-connect/certs"
        self.jwks_client = PyJWKClient(jwks_url)
        logger.info("JWKS client initialized")

    def get_token(self) -> str:
        """Get a valid access token, refreshing if necessary"""
        current_time = time.time()
        
        # Return existing token if still valid
        if self.access_token and current_time < self.token_expiry:
            return self.access_token

        # Get new token
        token_url = f"{self.keycloak_host}/realms/{self.realm}/protocol/openid-connect/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            resp = requests.post(token_url, data=data)
            resp.raise_for_status()
            token_data = resp.json()
            
            self.access_token = token_data["access_token"]
            # Set expiry time (subtract 30 seconds for safety margin)
            self.token_expiry = current_time + token_data["expires_in"] - 30
            
            logger.info("Successfully obtained new access token")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to obtain access token: {str(e)}")
            raise

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate and decode the JWT token"""
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id
            )
            logger.info("Token validated successfully")
            return decoded
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise

    def make_authenticated_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Make an authenticated request to the PEP service"""
        token = self.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.pep_endpoint}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def test_connection(self):
        """Test the connection to both PEP and resource services"""
        try:
            # Test PEP service
            pep_response = self.make_authenticated_request("/health")
            logger.info(f"PEP Service Status: {pep_response}")
            
            # Test protected resource
            resource_response = self.make_authenticated_request("/protected-resource")
            logger.info(f"Protected Resource Response: {resource_response}")
            
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

def main():
    try:
        # Initialize client
        client = ZTAClient()
        client.initialize_jwks()
        
        # Get and validate token
        token = client.get_token()
        token_data = client.validate_token(token)
        logger.info("Token data:")
        for key, value in token_data.items():
            logger.info(f"  {key}: {value}")
        
        # Test connection
        if client.test_connection():
            logger.info("All connection tests passed successfully!")
        else:
            logger.error("Connection tests failed")
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main() 