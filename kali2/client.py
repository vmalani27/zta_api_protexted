#!/usr/bin/env python3
import requests
import jwt
from jwt import PyJWKClient
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any, Optional, Tuple, List
import time
import getpass
import json

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
        self.refresh_token = None
        self.token_expiry = 0
        self.jwks_client = None
        self.username = None
        self.user_info = None
        self.user_roles = []

    def initialize_jwks(self):
        """Initialize JWKS client for token validation"""
        jwks_url = f"{self.keycloak_host}/realms/{self.realm}/protocol/openid-connect/certs"
        self.jwks_client = PyJWKClient(jwks_url)
        logger.info("JWKS client initialized")

    def verify_keycloak_connection(self) -> bool:
        """Verify that Keycloak is accessible and properly configured"""
        try:
            # Check if Keycloak is reachable
            health_url = f"{self.keycloak_host}/health"
            resp = requests.get(health_url)
            resp.raise_for_status()
            
            # Check if realm exists
            realm_url = f"{self.keycloak_host}/realms/{self.realm}"
            resp = requests.get(realm_url)
            resp.raise_for_status()
            
            logger.info("Keycloak connection verified successfully")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Keycloak connection failed: {str(e)}")
            return False

    def get_user_roles(self, token_data: Dict[str, Any]) -> List[str]:
        """Extract and return user roles from token data"""
        roles = []
        if 'realm_access' in token_data and 'roles' in token_data['realm_access']:
            roles = token_data['realm_access']['roles']
        return roles

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate user with username and password against Keycloak
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # First verify Keycloak connection
            if not self.verify_keycloak_connection():
                return False, "Cannot connect to Keycloak server"

            # Get token from Keycloak
            token_url = f"{self.keycloak_host}/realms/{self.realm}/protocol/openid-connect/token"
            data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": username,
                "password": password
            }
            
            resp = requests.post(token_url, data=data)
            
            # Handle specific error cases
            if resp.status_code == 401:
                return False, "Invalid username or password"
            elif resp.status_code == 403:
                return False, "Access denied. User may be disabled or locked"
            elif resp.status_code == 400:
                error_data = resp.json()
                return False, f"Authentication failed: {error_data.get('error_description', 'Unknown error')}"
            
            resp.raise_for_status()
            token_data = resp.json()
            
            # Store tokens
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token")
            self.token_expiry = time.time() + token_data["expires_in"] - 30
            self.username = username
            
            # Decode and store user roles
            decoded_token = jwt.decode(
                self.access_token,
                options={"verify_signature": False}  # We'll verify later
            )
            self.user_roles = self.get_user_roles(decoded_token)
            
            logger.info(f"Successfully logged in as {username}")
            logger.info(f"User roles: {self.user_roles}")
            
            return True, "Login successful"
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Login failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.user_roles

    def get_user_info(self) -> Dict[str, Any]:
        """Get user information from Keycloak"""
        if not self.access_token:
            raise Exception("No access token available")
            
        try:
            userinfo_url = f"{self.keycloak_host}/realms/{self.realm}/protocol/openid-connect/userinfo"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            resp = requests.get(userinfo_url, headers=headers)
            resp.raise_for_status()
            
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get user info: {str(e)}")
            return {}

    def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            return False
            
        try:
            token_url = f"{self.keycloak_host}/realms/{self.realm}/protocol/openid-connect/token"
            data = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token
            }
            
            resp = requests.post(token_url, data=data)
            resp.raise_for_status()
            token_data = resp.json()
            
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token")
            self.token_expiry = time.time() + token_data["expires_in"] - 30
            
            # Update user roles after refresh
            decoded_token = jwt.decode(
                self.access_token,
                options={"verify_signature": False}  # We'll verify later
            )
            self.user_roles = self.get_user_roles(decoded_token)
            
            logger.info("Successfully refreshed access token")
            logger.info(f"Updated user roles: {self.user_roles}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return False

    def get_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary"""
        current_time = time.time()
        
        # Return existing token if still valid
        if self.access_token and current_time < self.token_expiry:
            return self.access_token
            
        # Try to refresh the token
        if self.refresh_token and self.refresh_access_token():
            return self.access_token
            
        # If refresh failed, user needs to login again
        logger.error("No valid token available. Please login again.")
        return None

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
        if not token:
            raise Exception("No valid token available. Please login first.")
            
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
        
        # Get user credentials
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        
        # Login user
        success, message = client.login(username, password)
        if not success:
            logger.error(f"Login failed: {message}")
            return
            
        # Get and validate token
        token = client.get_token()
        token_data = client.validate_token(token)
        
        # Display user information
        logger.info("\nUser Information:")
        logger.info(f"Username: {client.username}")
        logger.info(f"Roles: {', '.join(client.user_roles)}")
        
        # Check for specific roles
        if client.has_role('admin'):
            logger.info("User has admin privileges")
        if client.has_role('Teacher'):
            logger.info("User has teacher privileges")
        if client.has_role('Student'):
            logger.info("User has student privileges")
        if client.has_role('Warden'):
            logger.info("User has warden privileges")
        
        # Test connection
        if client.test_connection():
            logger.info("\nAll connection tests passed successfully!")
        else:
            logger.error("\nConnection tests failed")
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main() 