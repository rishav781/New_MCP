"""
QPilot Script Mixin for pCloudy MCP Server

Provides an async method to create/get a script for a QPilot test case from the QPilot backend.
Intended to be used as a mixin in the modular API architecture.
"""
from config import Config, logger
import httpx

class QPilotScriptMixin:
    async def create_qpilot_script(self, hostname: str, auth_token: str, booking_host: str, testCaseId: str, testSuiteId: str, scriptType: str) -> dict:
        """
        Create or get a script for a QPilot test case using the /api/v1/qpilot/create-script endpoint.
        Args:
            hostname (str): The hostname to use in the URL.
            auth_token (str): The authentication token to use in the request header.
            booking_host (str): The booking host for the origin header.
            testCaseId (str): The test case ID.
            testSuiteId (str): The test suite ID.
            scriptType (str): The script type (e.g., 'pcloudy_appium-js').
        Returns:
            dict: The API response data for the script creation.
        """
        url = f"{hostname}/api/v1/qpilot/create-script"
        headers = {
            "token": auth_token,
            "origin": booking_host,
            "Content-Type": "application/json"
        }
        payload = {
            "testCaseId": testCaseId,
            "testSuiteId": testSuiteId,
            "scriptType": scriptType
        }
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"QPilot script creation response: {data.get('message', data)}")
            return data
