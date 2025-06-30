"""
QPilot Test Case Management API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotTestCaseMixin:
    async def create_test_case(self, testSuiteId: str, testCaseName: str, platform: str):
        """
        Create a new QPilot test case in the specified test suite.

        Parameters:
            testSuiteId (str): ID of the test suite to add the test case to.
            testCaseName (str): Name of the new test case.
            platform (str): Platform for the test case (e.g., 'android').
        
        Returns:
            dict: API response containing the created test case info or error details.
        """
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v1/qpilot/create-test-case"
        headers = {"token": self.auth_token, "Origin": Config.get_origin()}
        payload = {"testSuiteId": testSuiteId, "testCaseName": testCaseName, "platform": platform}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating QPilot test case: {str(e)}")
            return {"error": str(e)}

    async def get_test_cases(self, getShared: bool = True):
        """
        Fetch all QPilot test cases for the authenticated user, grouped by test suite.

        Parameters:
            getShared (bool): Whether to include shared test cases (default: True).
        
        Returns:
            dict: API response containing test cases grouped by suite, or error details.
        """
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v1/qpilot/get-tests"
        # Headers required for QPilot API authentication and CORS
        headers = {
            "token": self.auth_token,  # QPilot authentication token
            "Origin": Config.get_origin(),  # pCloudy host
            "Content-Type": "application/json"  # Ensure JSON body is accepted
        }
        payload = {"getShared": getShared}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching QPilot tests: {str(e)}")
            return {"error": str(e)}
