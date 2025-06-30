"""
QPilot Code/Script Management API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotCodeScriptMixin:
    async def generate_code(self, rid: str = None, description: str = None, testId: str = None, suiteId: str = None, appPackage: str = None, appName: str = None, appActivity: str = None, steps: str = None, projectId: str = None, testdata: dict = None, strict: bool = True, platform: str = None):
        """
        If strict=True (default), require all parameters to be provided explicitly by the user and do not auto-fill from self attributes.
        If strict=False, auto-fill missing parameters from self attributes as fallback.
        Before generating code, start Appium if all required data is present.
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
        # Start Appium before generating code
        device_url = None
        if hasattr(self, 'start_appium') and callable(getattr(self, 'start_appium')):
            appium_result = await self.start_appium(rid, platform, appName)
            if appium_result and appium_result.get('error'):
                return {"error": f"Failed to start Appium: {appium_result['error']}"}
            # After Appium starts, get device URL and open browser for real-time viewing
            if hasattr(self, 'get_device_url') and callable(getattr(self, 'get_device_url')):
                device_url = await self.get_device_url(rid)
                if device_url and isinstance(device_url, dict) and device_url.get('url'):
                    # Optionally, force open browser (implementation depends on your environment)
                    try:
                        import webbrowser
                        webbrowser.open(device_url['url'], new=2)
                    except Exception as e:
                        logger.warning(f"Could not open browser for device URL: {str(e)}")
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
                if device_url:
                    result['device_url'] = device_url
                return result
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
