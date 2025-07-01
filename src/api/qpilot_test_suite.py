"""
QPilot Test Suite Mixin for pCloudy MCP Server

Provides async methods to create and list QPilot test suites from the QPilot backend.
Intended to be used as a mixin in the modular API architecture.
"""
from config import Config, logger
import httpx

class QPilotTestSuiteMixin:
    async def create_qpilot_test_suite(self, auth_token: str, name: str) -> dict:
        """
        Create a new QPilot test suite with the given name.
        Args:
            auth_token (str): The authentication token to use in the request header.
            name (str): The name of the test suite to create.
        Returns:
            dict: The API response data for the created test suite.
        """
        url = f"{Config.HOSTNAME}/api/v1/qpilot/create-test-suite"
        headers = {
            "token": auth_token,
            "origin": Config.Bookinghost
        }
        payload = {"name": name}
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"QPilot test suite created: {data.get('message')}")
            return data

    async def list_qpilot_test_suites(self, auth_token: str) -> dict:
        """
        List all QPilot test suites from the QPilot backend.
        Args:
            auth_token (str): The authentication token to use in the request header.
        Returns:
            dict: The API response data for the test suites.
        """
        url = f"{Config.HOSTNAME}/api/v1/qpilot/list-test-suites"
        headers = {
            "token": auth_token,
            "origin": Config.Bookinghost
        }
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"QPilot test suites listed: {data.get('message')}")
            return data

    async def get_qpilot_test_suites(self, auth_token: str) -> dict:
        """
        Get all QPilot test suites from the QPilot backend.
        Args:
            auth_token (str): The authentication token to use in the request header.
        Returns:
            dict: The API response data for the test suites.
        """
        url = f"{Config.HOSTNAME}/api/v1/qpilot/get-test-suites"
        headers = {
            "token": auth_token,
            "origin": Config.Bookinghost
        }
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"QPilot test suites fetched: {data.get('message')}")
            return data
