"""
QPilot Test Case Management API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotTestCaseMixin:
    async def create_test_case(self, testSuiteId: str, testCaseName: str, platform: str):
        hostname = Config.QPILOT_BASE_HOSTNAME
        url = f"https://{hostname}/api/v1/qpilot/create-test-case"
        headers = {"token": self.auth_token, "Origin": f"https://{hostname}"}
        payload = {"testSuiteId": testSuiteId, "testCaseName": testCaseName, "platform": platform}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating QPilot test case: {str(e)}")
            return {"error": str(e)}

    async def get_tests(self, getShared: bool = True):
        hostname = Config.QPILOT_BASE_HOSTNAME
        url = f"https://{hostname}/api/v1/qpilot/get-tests"
        headers = {"token": self.auth_token, "Origin": f"https://{hostname}"}
        payload = {"getShared": getShared}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching QPilot tests: {str(e)}")
            return {"error": str(e)}
