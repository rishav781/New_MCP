"""
Qpilot Credits API Mixin for pCloudy MCP Server

Implements the QPilot credits endpoint as a modular async mixin.
"""

import httpx
from config import logger, Config

class QpilotCreditsMixin:
    async def get_qpilot_credits(self):
        """
        Get the number of QPilot credits left for the authenticated user.

        Returns:
            dict: API response containing the number of credits left or error details.
        """
        # Ensure token is valid before making the request
        await self.check_token_validity()
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v1/qpilot/get-qpilot-credits-left"
        headers = {"token": self.auth_token, "Origin": Config.get_origin()}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                # Normalize the return value
                return data
        except Exception as e:
            logger.error(f"Error fetching QPilot credits: {str(e)}")
            return {"error": str(e)}
