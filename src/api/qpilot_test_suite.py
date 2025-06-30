"""
QPilot Test Suite Management API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotTestSuiteMixin:
    async def get_test_suites(self):
        """
        Fetch all QPilot test suites for the authenticated user.
        This endpoint requires only headers: 'token' (auth token) and 'Origin' (pCloudy host).
        No payload/body is required for this request.
        Returns:
            dict: API response containing test suites.
        Example output:
            {
                "requestId": "...",
                "statusCode": 200,
                "status": "success",
                "message": "Successfully retrieved all testSuites",
                "data": {
                    "testSuites": {
                        "owned": [...],
                        "shared": [...]
                    }
                }
            }
        """
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v1/qpilot/get-test-suites"
        headers = {"token": self.auth_token, "Origin": Config.get_origin()}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching QPilot test suites: {str(e)}")
            return {"error": str(e)}

    async def create_test_suite(self, testSuiteName: str):
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v1/qpilot/create-test-suite"
        headers = {"token": self.auth_token, "Origin": Config.get_origin()}
        payload = {"testSuiteName": testSuiteName}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating QPilot test suite: {str(e)}")
            return {"error": str(e)}
