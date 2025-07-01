"""
QPilot Steps Mixin for pCloudy MCP Server

Provides async methods to manage QPilot steps.
Intended to be used as a mixin in the modular API architecture.
"""
from config import Config, logger
import httpx
from utils import encode_auth, parse_response

class QPilotStepsMixin:
    async def execute_qpilot_code_steps(self,payload: dict) -> dict:
        """
        Generate QPilot code steps using the /api/v2/qpilot/generate-code endpoint.
        Args:
            booking_host (str): The booking host to use in the URL.
            payload (dict): The JSON body for the request.
        Returns:
            dict: The API response data for the generated code steps.
        """
        url = "https://device.pcloudy.com/api/v2/qpilot/generate-code"
        headers = {
            "Cookie": "PYPCLOUDY="+Config.auth_token,
        }
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = parse_response(response)
            logger.info(f"QPilot code steps generated: {data}")
            return data
