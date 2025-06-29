"""
QPilot Test Case Management API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotTestCaseMixin:
    async def create_test_case(self, testSuiteId: str, testCaseName: str, platform: str):
        """
        Create a new QPilot test case in the specified test suite.
        Required headers: 'token' (auth token), 'Origin' (pCloudy host).
        Payload:
            {
                "testSuiteId": <str>,
                "testCaseName": <str>,
                "platform": <str>
            }
        Returns:
            dict: API response containing the created test case info.
        Example output:
            {
                "requestId": "...",
                "statusCode": 200,
                "status": "success",
                "message": "Successfully created test case",
                "data": { ... }
            }
        """
        hostname = Config.QPILOT_BASE_HOSTNAME
        url = f"https://{hostname}/api/v1/qpilot/create-test-case"
        headers = {"token": self.auth_token, "Origin": Config.PCLOUDY_BASE_HOST}
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
        Fetch all QPilot test cases for the authenticated user.

        Context for LLMs and developers:
        - This method retrieves all test cases grouped by test suite for the current authenticated user.
        - The 'getShared' parameter determines whether to include test cases shared with the user (True) or only those owned by the user (False).
        - The 'token' header must be set to the user's QPilot authentication token (same as qPilottoken in Postman collections).
        - The 'Origin' header must be set to the pCloudy host (same as bookingHost in Postman collections).
        - The 'Content-Type' header must be 'application/json' for strict API compatibility.
        - The request body is a JSON object: {"getShared": <bool>}.
        - The response contains a dictionary with test suites and their associated test cases, e.g.:
            {
                "requestId": "...",
                "statusCode": 200,
                "status": "success",
                "message": "Successfully retrieved all tests",
                "data": {
                    "testcases": {
                        "owned": [
                            {
                                "testSuiteId": "...",
                                "testSuiteName": "...",
                                ...,
                                "testcases": [
                                    {
                                        "testCaseId": "...",
                                        "testCaseName": "...",
                                        ...
                                    },
                                    ...
                                ]
                            },
                            ...
                        ],
                        "shared": [ ... ]
                    }
                }
            }
        - This method is used by the MCP QPilot tool for the 'get_tests' action.
        """
        hostname = Config.QPILOT_BASE_HOSTNAME
        url = f"https://{hostname}/api/v1/qpilot/get-tests"
        # Headers required for QPilot API authentication and CORS
        headers = {
            "token": self.auth_token,  # QPilot authentication token
            "Origin": Config.PCLOUDY_BASE_HOST,  # pCloudy host
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
