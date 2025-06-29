"""
QPilot Test Suite Management API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotTestSuiteMixin:
    async def get_test_suites(self):
        hostname = Config.QPILOT_BASE_HOSTNAME
        url = f"https://{hostname}/api/v1/qpilot/get-test-suites"
        headers = {"token": self.auth_token, "Origin": f"https://{hostname}"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching QPilot test suites: {str(e)}")
            return {"error": str(e)}

    async def create_test_suite(self, testSuiteName: str):
        hostname = Config.QPILOT_BASE_HOSTNAME
        url = f"https://{hostname}/api/v1/qpilot/create-test-suite"
        headers = {"token": self.auth_token, "Origin": f"https://{hostname}"}
        payload = {"testSuiteName": testSuiteName}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating QPilot test suite: {str(e)}")
            return {"error": str(e)}
