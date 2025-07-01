"""
QPilot Test Case Mixin for pCloudy MCP Server

Provides async methods to get and create QPilot test cases from the QPilot backend.
Intended to be used as a mixin in the modular API architecture.
"""
from config import Config, logger
import httpx

class QPilotTestCaseMixin:
    async def get_qpilot_test_cases(self, auth_token: str) -> dict:
        """
        Get all QPilot test cases from the QPilot backend.
        Args:
            auth_token (str): The authentication token to use in the request header.
        Returns:
            dict: The API response data for the test cases.
        """
        url = f"{Config.HOSTNAME}/api/v1/qpilot/get-tests"
        headers = {
            "token": auth_token,
            "origin": Config.Bookinghost
        }
        payload = {"getShared": True}
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"QPilot test cases fetched: {data.get('message')}")
            return data

    async def create_qpilot_test_case(self, auth_token: str, testSuiteId: str, testCaseName: str, platform: str) -> dict:
        """
        Create a new QPilot test case in a test suite.
        Args:
            auth_token (str): The authentication token to use in the request header.
            testSuiteId (str): The ID of the test suite.
            testCaseName (str): The name of the test case.
            platform (str): The platform for the test case.
        Returns:
            dict: The API response data for the created test case.
        """
        url = f"{Config.HOSTNAME}/api/v1/qpilot/create-test-case"
        headers = {
            "token": auth_token,
            "origin": Config.Bookinghost
        }
        payload = {
            "testSuiteId": testSuiteId,
            "testCaseName": testCaseName,
            "platform": platform
        }
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"QPilot test case created: {data.get('result', {}).get('message')}")
            return data
