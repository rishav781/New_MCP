"""
Qpilot Credits API Mixin for pCloudy MCP Server

Implements the QPilot credits endpoint as a modular async mixin.
"""

import httpx
from config import logger, Config

class QpilotCreditsMixin:
    async def get_qpilot_credits(self):
        """
        Get QPilot credits left for the user.
        Returns:
            Dict with credits info or error
        """
        hostname = Config.QPILOT_BASE_HOSTNAME
        url = f"https://{hostname}/api/v1/qpilot/get-qpilot-credits-left"
        headers = {
            "token": self.auth_token,
            "Origin": f"https://{hostname}"
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching QPilot credits: {str(e)}")
            return {"error": str(e)}
