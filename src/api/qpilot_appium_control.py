"""
QPilot Appium Control Mixin for pCloudy MCP Server

Provides an async method to control Appium (start/stop) for QPilot sessions from the QPilot backend.
Intended to be used as a mixin in the modular API architecture.
"""
from config import Config, logger
import httpx

class QPilotAppiumControlMixin:
    async def control_qpilot_appium(self, booking_host: str, auth_token: str, rid: str, action: str, os: str, appName: str) -> dict:
        """
        Control Appium for a QPilot session (start/stop) using the /api/v2/qpilot/appium/control endpoint.
        Args:
            booking_host (str): The booking host to use in the URL.
            auth_token (str): The authentication token to use in the request header.
            rid (str): The QPilot RID.
            action (str): The action to perform (e.g., 'start').
            os (str): The platform (e.g., 'android', 'ios').
            appName (str): The app name.
        Returns:
            dict: The API response data for the Appium control action.
        """
        url = f"{booking_host}/api/v2/qpilot/appium/control"
        headers = {"token": auth_token, "Content-Type": "application/json"}
        payload = {
            "rid": rid,
            "action": action,
            "os": os,
            "appName": appName
        }
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"QPilot Appium control response: {data.get('message', data)}")
            return data
