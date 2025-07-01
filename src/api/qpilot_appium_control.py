"""
QPilot Appium Control Mixin for pCloudy MCP Server

Provides async methods to control appium sessions for QPilot.
Intended to be used as a mixin in the modular API architecture.
"""
from config import Config, logger
import httpx
from utils import encode_auth, parse_response

class QPilotAppiumControlMixin:
    async def control_qpilot_appium(self,rid: str, action: str, os: str, appName: str) -> dict:
        """
        Control Appium for a QPilot session (start/stop) using the /api/v2/qpilot/appium/control endpoint.
        Args:
            booking_host (str): The booking host to use in the URL.
            rid (str): The QPilot RID.
            action (str): The action to perform (e.g., 'start').
            os (str): The platform (e.g., 'android', 'ios').
            appName (str): The app name.
        Returns:
            dict: The API response data for the Appium control action.
        """
        url = "https://device.pcloudy.com/api/v2/qpilot/appium/control"
        headers = {"token": Config.auth_token}
        payload = {
            "rid": rid,
            "action": action,
            "os": os,
            "appName": appName
        }
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = parse_response(response)
            logger.info(f"QPilot Appium control response: {data}")
            return data
