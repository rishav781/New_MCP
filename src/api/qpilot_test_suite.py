"""
QPilot Test Suite Mixin for pCloudy MCP Server

Provides async methods to create and list QPilot test suites from the QPilot backend.
Intended to be used as a mixin in the modular API architecture.
"""
from config import Config, logger
import httpx
from utils import encode_auth, parse_response

class QPilotTestSuiteMixin:
    async def create_qpilot_test_suite(self, name: str) -> dict:
        """
        Create a new QPilot test suite with the given name.
        Args:
            name (str): The name of the test suite to create.
        Returns:
            dict: The API response data for the created test suite.
        """
        url = f"{Config.HOSTNAME}/api/v1/qpilot/create-test-suite"
        headers = {
            "token": Config.auth_token,
            "origin": Config.Bookinghost
        }
        payload = {"name": name}
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = parse_response(response)
            logger.info(f"QPilot test suite created: {data}")
            return data

    async def list_qpilot_test_suites(self) -> dict:
        """
        List all QPilot test suites from the QPilot backend.
        Returns:
            dict: The API response data for the test suites.
        """
        url = f"{Config.HOSTNAME}/api/v1/qpilot/list-test-suites"
        headers = {
            "token": Config.auth_token,
            "origin": Config.Bookinghost
        }
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = parse_response(response)
            logger.info(f"QPilot test suites listed: {data}")
            return data

    async def get_qpilot_test_suites(self) -> dict:
        """
        Get all QPilot test suites from the QPilot backend.
        Returns:
            dict: The API response data for the test suites.
        """
        url = f"{Config.HOSTNAME}/api/v1/qpilot/get-test-suites"
        headers = {
            "token": Config.auth_token,
            "origin": Config.Bookinghost
        }
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = parse_response(response)
            logger.info(f"QPilot test suites fetched: {data}")
            return data
