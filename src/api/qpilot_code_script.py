"""
QPilot Code/Script Management API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotCodeScriptMixin:
    async def generate_code(self, rid: str = None, description: str = None, testId: str = None, suiteId: str = None, appPackage: str = None, appName: str = None, appActivity: str = None, steps: str = None, projectId: str = None, testdata: dict = None, strict: bool = True, platform: str = None):
        """
        Generate automation code for a given test case and device booking.
        
        Parameters:
            rid (str): Device booking ID.
            description (str): Description of the test or feature.
            testId (str): Test case ID.
            suiteId (str): Test suite ID.
            appPackage (str): App package name.
            appName (str): App name or APK file name.
            appActivity (str): Main activity of the app.
            steps (str): Steps to automate.
            projectId (str): Project ID.
            testdata (dict): Test data for the automation.
            strict (bool): If True, require all parameters explicitly; if False, auto-fill from self attributes.
            platform (str): Platform (e.g., 'android').
        
        Returns:
            dict: Result of code generation or error details.
        
        This function will also attempt to start Appium and open the device URL in a browser if possible.
        """
        missing = []
        # Strict mode: always prompt for missing
        if strict:
            if not rid: missing.append('rid')
            if not description: missing.append('description')
            if not testId: missing.append('testId')
            if not suiteId: missing.append('suiteId')
            if not appPackage: missing.append('appPackage')
            if not appName: missing.append('appName')
            if not appActivity: missing.append('appActivity')
            if not steps: missing.append('steps')
            if not projectId: missing.append('projectId')
            if not platform: missing.append('platform')
            if missing:
                return {
                    "error": f"Missing required parameters: {', '.join(missing)}",
                    "hint": "Please provide all required parameters explicitly. Use the relevant tools or methods to fetch these values if needed."
                }
        else:
            # Fallback: auto-fill from self if not provided
            rid = rid or getattr(self, 'rid', None)
            description = description or getattr(self, 'description', None)
            testId = testId or getattr(self, 'testId', None)
            suiteId = suiteId or getattr(self, 'suiteId', None)
            appPackage = appPackage or getattr(self, 'appPackage', None)
            appName = appName or getattr(self, 'appName', None)
            appActivity = appActivity or getattr(self, 'appActivity', None)
            steps = steps or getattr(self, 'steps', None)
            projectId = projectId or getattr(self, 'projectId', None)
            testdata = testdata or getattr(self, 'testdata', None)
            platform = platform or getattr(self, 'platform', None)
            # After fallback, check if still missing
            if not (rid and description and testId and suiteId and appPackage and appName and appActivity and steps and projectId and platform):
                return {
                    "error": "Some required parameters are still missing after fallback. Please provide them explicitly.",
                    "hint": "Use the relevant tools or methods to fetch these values if needed."
                }
        # Parameter checks and API call only; Appium and device URL are handled in the tool layer
        device_url = None
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v2/qpilot/generate-code"
        cookies = {"PYPCLOUDY": self.auth_token}
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
                response = await client.post(url, json=payload, cookies=cookies)
                response.raise_for_status()
                result = response.json()
                # Automatically trigger create_script if code generation is successful and testId/suiteId are present
                if result and result.get('status', '').lower() == 'success' and testId and suiteId:
                    script_result = await self.create_script(testId, suiteId)
                    result['create_script'] = script_result
                # device_url is handled in the tool layer
                return result
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            return {"error": str(e)}

    async def create_script(self, testCaseId: str = None, testSuiteId: str = None, scriptType: str = "pcloudy_appium-js"):
        """
        Create a test script for a given test case and suite.
        
        Parameters:
            testCaseId (str): Test case ID.
            testSuiteId (str): Test suite ID.
            scriptType (str): Type of script to generate (default: 'pcloudy_appium-js').
        
        Returns:
            dict: Result of script creation or error details.
        """
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
