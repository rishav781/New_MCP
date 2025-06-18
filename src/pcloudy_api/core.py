import httpx
import time
import os
from typing import Dict, Any
from config import Config, logger
from utils import encode_auth, parse_response

class PCloudyAPI:
    def __init__(self, base_url=None):
        self.username = os.environ.get("PCLOUDY_USERNAME")
        self.api_key = os.environ.get("PCLOUDY_API_KEY")
        self.base_url = base_url or Config.PCLOUDY_BASE_URL
        self.auth_token = None
        self.token_timestamp = None
        self.client = httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT)
        self.rid = None
        logger.info("PCloudyAPI initialized")

    async def authenticate(self) -> str:
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
        if not self.auth_token:
            logger.error("Not authenticated. Please call authorize tool first.")
            raise ValueError("Not authenticated. Please call authorize tool first.")
        if self.token_timestamp and (time.time() - self.token_timestamp) > Config.TOKEN_REFRESH_THRESHOLD:
            logger.info("Token expired, refreshing...")
            await self.authenticate()
        return self.auth_token

    async def close(self):
        """Close the HTTP client."""
        try:
            await self.client.aclose()
            logger.info("HTTP client closed")
        except Exception as e:
            logger.error(f"Error closing HTTP client: {str(e)}")