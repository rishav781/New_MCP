"""
QPilot Code/Script Management API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotCodeScriptMixin:
    async def generate_code(self, rid: str = None, description: str = None, testId: str = None, suiteId: str = None, appPackage: str = None, appName: str = None, appActivity: str = None, steps: str = None, projectId: str = None, testdata: dict = None):
        # Interconnect with previous API values if available
        # If rid is not provided, try to get it from self.rid or from a DeviceMixin booking
        if not rid:
            rid = getattr(self, 'rid', None)
            if not rid and hasattr(self, 'last_device_booking') and isinstance(self.last_device_booking, dict):
                rid = self.last_device_booking.get('rid')
        appName = appName or getattr(self, 'appName', None)
        testId = testId or getattr(self, 'testId', None)
        suiteId = suiteId or getattr(self, 'suiteId', None)
        appPackage = appPackage or getattr(self, 'appPackage', None)
        appActivity = appActivity or getattr(self, 'appActivity', None)
        projectId = projectId or getattr(self, 'projectId', None)
        testdata = testdata or getattr(self, 'testdata', None)
        steps = steps or getattr(self, 'steps', None)
        description = description or getattr(self, 'description', None)
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v2/qpilot/generate-code"
        headers = {"token": self.auth_token, "Origin": Config.get_origin()}
        payload = {
            "rid": rid,
            "description": description,
            "testId": testId,
            "suiteId": suiteId,
            "appPackage": appPackage,
            "appName": appName,
            "appActivity": appActivity,
            "steps": steps,
            "projectId": projectId,
            "testdata": testdata or {}
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            return {"error": str(e)}

    async def create_script(self, testCaseId: str = None, testSuiteId: str = None, scriptType: str = "pcloudy_appium-js"):
        # Interconnect with previous API values if available
        testCaseId = testCaseId or getattr(self, 'testCaseId', None)
        testSuiteId = testSuiteId or getattr(self, 'testSuiteId', None)
        scriptType = scriptType or getattr(self, 'scriptType', "pcloudy_appium-js")
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v1/qpilot/create-script"
        headers = {"token": self.auth_token, "Origin": Config.get_origin()}
        payload = {"testCaseId": testCaseId, "testSuiteId": testSuiteId, "scriptType": scriptType}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating script: {str(e)}")
            return {"error": str(e)}
