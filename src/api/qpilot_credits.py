"""
QPilot Credits Mixin for pCloudy MCP Server

Provides an async method to get QPilot credits left from the QPilot backend.
Intended to be used as a mixin in the modular API architecture.
"""
from config import Config, logger
import httpx

class QPilotCreditsMixin:
    async def get_qpilot_credits_left(self) -> int:
        """
        Fetch the number of QPilot credits left from the QPilot backend.
        Returns:
            int: The number of credits left, or raises an exception on error.
        """
        if not self.auth_token:
            raise ValueError("auth_token is not set. Please authenticate first.")
        url = f"{Config.HOSTNAME}/api/v1/qpilot/get-qpilot-credits-left"
        headers = {
            "token": self.auth_token,
            "origin": Config.Bookinghost
        }
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            credits = data["result"]["data"]["creditsLeft"]
            logger.info(f"QPilot credits left: {credits}")
            return credits
