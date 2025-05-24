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
import httpx
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PEPAgent:
    def __init__(self):
        # Keycloak configuration
        self.keycloak_host = os.getenv("KEYCLOAK_HOST", "http://localhost:8080")
        self.realm = os.getenv("REALM", "zta")
        self.client_id = os.getenv("CLIENT_ID", "pep-backend")
        self.client_secret = os.getenv("CLIENT_SECRET", "")
        
        # PEP service configuration
        self.pep_host = os.getenv("PEP_HOST", "localhost")
        self.pep_port = os.getenv("PEP_PORT", "5000")
        self.pep_endpoint = f"http://{self.pep_host}:{self.pep_port}"

        # Resource service configuration
        self.resource_host = os.getenv("RESOURCE_HOST", "192.168.200.4")
        self.resource_port = os.getenv("RESOURCE_PORT", "5001")

        # OIDC configuration
        self.discovery_url = f"{self.keycloak_host}/realms/{self.realm}/.well-known/openid-configuration"
        self.discovery_data = self.get_discovery_document()

        # Token management
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = 0
        self.jwks_client = None
        self.username = None
        self.user_roles = []

        # PEP connection status
        self.pep_connected = False
        logger.info("PEP Agent initialized")

    def connect_to_pep(self) -> bool:
        """Establish connection with PEP server"""
        try:
            response = requests.get(f"{self.pep_endpoint}/health")
            response.raise_for_status()
            self.pep_connected = True
            logger.info(f"Connected to PEP server at {self.pep_endpoint}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PEP server: {str(e)}")
            self.pep_connected = False
            return False

    def capture_login_request(self, username: str, password: str) -> Tuple[bool, str]:
        """Capture and process login request"""
        logger.info(f"Capturing login request for user: {username}")
        
        # First verify PEP connection
        if not self.pep_connected and not self.connect_to_pep():
            return False, "Cannot connect to PEP server"

        # Then attempt Keycloak authentication
        try:
            token_url = self.discovery_data.get("token_endpoint")
            data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": username,
                "password": password
            }
            
            logger.info("Sending authentication request to Keycloak")
            resp = requests.post(token_url, data=data)

            if resp.status_code in (400, 401, 403):
                error = resp.json().get("error_description", "Authentication failed")
                logger.error(f"Authentication failed: {error}")
                return False, error

            resp.raise_for_status()
            token_data = resp.json()

            # Store tokens
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token")
            self.token_expiry = time.time() + token_data["expires_in"] - 30
            self.username = username

            # Decode and store roles
            decoded = jwt.decode(self.access_token, options={"verify_signature": False})
            self.user_roles = self.get_user_roles(decoded)

            logger.info(f"Login successful for {username}")
            logger.info(f"User roles: {self.user_roles}")
            
            # Verify PEP connection with new token
            if not self.verify_pep_connection():
                return False, "Failed to establish PEP connection with new token"
                
            return True, "Login successful"
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False, str(e)

    def verify_pep_connection(self) -> bool:
        """Verify PEP connection with current token"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{self.pep_endpoint}/health", headers=headers)
            response.raise_for_status()
            logger.info("PEP connection verified with current token")
            return True
        except Exception as e:
            logger.error(f"PEP connection verification failed: {str(e)}")
            return False

    def get_discovery_document(self) -> Dict[str, Any]:
        try:
            resp = requests.get(self.discovery_url)
            resp.raise_for_status()
            data = resp.json()
            logger.info("Keycloak discovery document fetched")
            return data
        except Exception as e:
            logger.error(f"Failed to fetch discovery document: {str(e)}")
            raise

    def initialize_jwks(self):
        """Initialize JWKS client using discovery document"""
        jwks_url = self.discovery_data.get("jwks_uri")
        if not jwks_url:
            raise Exception("JWKS URI not found in discovery document")
        self.jwks_client = PyJWKClient(jwks_url)
        logger.info("JWKS client initialized")

    def verify_keycloak_connection(self) -> bool:
        """Check if the realm and discovery doc are available"""
        try:
            _ = self.get_discovery_document()
            return True
        except Exception as e:
            logger.error(f"Keycloak connection verification failed: {e}")
            return False

    def get_user_roles(self, token_data: Dict[str, Any]) -> List[str]:
        return token_data.get('realm_access', {}).get('roles', [])

    def has_role(self, role: str) -> bool:
        return role in self.user_roles

    def get_user_info(self) -> Dict[str, Any]:
        if not self.access_token:
            raise Exception("No access token available")
        try:
            userinfo_url = self.discovery_data.get("userinfo_endpoint")
            headers = {"Authorization": f"Bearer {self.access_token}"}
            resp = requests.get(userinfo_url, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get user info: {str(e)}")
            return {}

    def refresh_access_token(self) -> bool:
        if not self.refresh_token:
            return False
        try:
            token_url = self.discovery_data.get("token_endpoint")
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

            decoded = jwt.decode(self.access_token, options={"verify_signature": False})
            self.user_roles = self.get_user_roles(decoded)

            logger.info("Access token refreshed")
            return True
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return False

    def get_token(self) -> Optional[str]:
        if self.access_token and time.time() < self.token_expiry:
            return self.access_token
        if self.refresh_token and self.refresh_access_token():
            return self.access_token
        logger.warning("No valid token. Please log in again.")
        return None

    def validate_token(self, token: str) -> Dict[str, Any]:
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id
            )
            logger.info("Token successfully validated")
            return decoded
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise

    def make_authenticated_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        token = self.get_token()
        if not token:
            raise Exception("No valid token. Please login.")
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
            logger.error(f"Request to {url} failed: {e}")
            raise

    def test_connection(self) -> bool:
        try:
            pep_response = self.make_authenticated_request("/health")
            logger.info(f"PEP Service: {pep_response}")
            resource_response = self.make_authenticated_request("/protected-resource")
            logger.info(f"Protected Resource: {resource_response}")
            return True
        except Exception as e:
            logger.error(f"Test connection failed: {e}")
            return False

class ZTAClient:
    def __init__(self, pep_url: str, keycloak_url: str):
        self.pep_url = pep_url
        self.keycloak_url = keycloak_url
        self.session_key: Optional[str] = None
        self.session_expires_at: Optional[int] = None
        self.http_client = httpx.Client()

    def handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the PEP service"""
        try:
            error_data = response.json()
            error_msg = error_data.get('detail', 'Unknown error')
            
            if response.status_code == 401:
                if "No valid authorization header" in error_msg:
                    logger.error("Authentication required. Please authenticate first.")
                elif "Token has expired" in error_msg:
                    logger.error("Session expired. Please re-authenticate.")
                else:
                    logger.error(f"Authentication error: {error_msg}")
            elif response.status_code == 403:
                if "Not in allowed network" in error_msg:
                    logger.error("Access denied: You are not in the allowed network.")
                else:
                    logger.error(f"Access denied: {error_msg}")
            elif response.status_code == 503:
                logger.error(f"Service unavailable: {error_msg}")
            else:
                logger.error(f"Error: {error_msg}")
        except json.JSONDecodeError:
            logger.error(f"Error: {response.text}")

    async def get_nonce(self, subject: Dict) -> Optional[str]:
        """Request a nonce from the PEP service"""
        try:
            response = await self.http_client.post(
                f"{self.pep_url}/auth/nonce",
                json={
                    "subject": subject,
                    "timestamp": str(time.time())
                }
            )
            
            if response.status_code == 200:
                nonce_data = response.json()
                return nonce_data.get('nonce')
            else:
                self.handle_error_response(response)
                return None
                
        except Exception as e:
            logger.error(f"Error requesting nonce: {str(e)}")
            return None

    async def get_session_key(self, subject: Dict, nonce: str, nonce_response: str) -> bool:
        """Request session keys after nonce validation"""
        try:
            response = await self.http_client.post(
                f"{self.pep_url}/auth/session",
                json={
                    "subject": subject,
                    "nonce": nonce,
                    "nonce_response": nonce_response,
                    "timestamp": str(time.time())
                }
            )
            
            if response.status_code == 200:
                session_data = response.json()
                self.session_key = session_data.get('session_key')
                self.session_expires_at = session_data.get('expires_at')
                return True
            else:
                self.handle_error_response(response)
                return False
                
        except Exception as e:
            logger.error(f"Error getting session key: {str(e)}")
            return False

    async def validate_session(self) -> bool:
        """Validate if the current session is still valid"""
        if not self.session_key:
            return False
            
        try:
            response = await self.http_client.get(
                f"{self.pep_url}/validate-session/{self.session_key}"
            )
            
            if response.status_code == 200:
                return True
            else:
                self.handle_error_response(response)
                return False
                
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return False

    async def make_authenticated_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make an authenticated request to a protected resource"""
        if not self.session_key:
            logger.error("No session key available. Please authenticate first.")
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.session_key}"}
            response = await self.http_client.request(
                method=method,
                url=f"{self.pep_url}/{endpoint}",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.handle_error_response(response)
                return None
                
        except Exception as e:
            logger.error(f"Error making authenticated request: {str(e)}")
            return None

def main():
    try:
        # Initialize PEP agent
        agent = PEPAgent()
        agent.initialize_jwks()  # Initialize JWKS client first
        
        # Get user credentials
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        
        # Capture and process login request
        success, message = agent.capture_login_request(username, password)
        if not success:
            logger.error(f"Login failed: {message}")
            return
            
        # Get and validate token
        token = agent.get_token()
        if not token:
            logger.error("No valid token available")
            return
            
        try:
            token_data = agent.validate_token(token)
            
            # Display welcome message based on primary role
            if agent.has_role('admin'):
                print("\nWelcome, Administrator!")
            elif agent.has_role('Teacher'):
                print("\nWelcome, Teacher!")
            elif agent.has_role('Student'):
                print("\nWelcome, Student!")
            elif agent.has_role('Warden'):
                print("\nWelcome, Warden!")
            else:
                print("\nWelcome!")
            
            # Test PEP connection
            if agent.verify_pep_connection():
                print("Connected to PEP server successfully!")
            else:
                print("Warning: PEP connection verification failed")
                
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
