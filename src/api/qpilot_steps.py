"""
QPilot Steps Mixin for pCloudy MCP Server

Provides an async method to generate QPilot code steps from the QPilot backend.
Intended to be used as a mixin in the modular API architecture.
"""
from config import Config, logger
import httpx

class QPilotStepsMixin:
    async def generate_qpilot_code_steps(self, booking_host: str, payload: dict) -> dict:
        """
        Generate QPilot code steps using the /api/v2/qpilot/generate-code endpoint.
        Args:
            booking_host (str): The booking host to use in the URL.
            payload (dict): The JSON body for the request.
        Returns:
            dict: The API response data for the generated code steps.
        """
        url = f"{booking_host}/api/v2/qpilot/generate-code"
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"QPilot code steps generated: {data.get('message', data)}")
            return data
