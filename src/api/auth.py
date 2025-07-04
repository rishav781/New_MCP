"""
Authentication Mixin for pCloudy MCP Server

Provides authentication and token management for the PCloudyAPI class.
- authenticate: Authenticates with pCloudy using username and API key.
- check_token_validity: Ensures the token is valid and refreshes if expired.

Intended to be used as a mixin in the modular API architecture.
"""

import time
from utils import encode_auth, parse_response
from config import Config, logger
import httpx

class AuthMixin:
    def __init__(self):
        self.username = None
        self.api_key = None
        self.base_url = None
        self.auth_token = None
        self.token_timestamp = None
        self.client = None

    async def authenticate(self) -> str:
        """
        Authenticate with the pCloudy API and store the token.
        Raises ValueError if credentials are missing or authentication fails.
        """
        try:
            if not self.username or not self.api_key:
                logger.error("PCLOUDY_USERNAME or PCLOUDY_API_KEY environment variable not set.")
                raise ValueError("PCLOUDY_USERNAME or PCLOUDY_API_KEY environment variable not set.")
            logger.info("Authenticating with pCloudy")
            url = f"{self.base_url}/access"
            auth = encode_auth(self.username, self.api_key)
            headers = {"Authorization": f"Basic {auth}"}
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            self.auth_token = result.get("token")
            if not self.auth_token:
                logger.error("Authentication failed: No token received")
                raise ValueError("Authentication failed: No token received")
            self.token_timestamp = time.time()
            logger.info("Authentication successful")
            return self.auth_token
        except httpx.RequestError as e:
            logger.error(f"Authentication request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise

    async def check_token_validity(self) -> str:
        """
        Ensure the authentication token is valid, refreshing if expired.
        Raises ValueError if not authenticated.
        """
        if not self.auth_token:
            logger.error("Not authenticated. Please call authorize tool first.")
            raise ValueError("Not authenticated. Please call authorize tool first.")
        if self.token_timestamp and (time.time() - self.token_timestamp) > Config.TOKEN_REFRESH_THRESHOLD:
            logger.info("Token expired, refreshing...")
            await self.authenticate()
        return self.auth_token