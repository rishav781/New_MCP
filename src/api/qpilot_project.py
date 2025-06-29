"""
QPilot Project Management API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotProjectMixin:
    async def project_list(self, getShared: bool = True):
        hostname = Config.QPILOT_BASE_HOSTNAME
        url = f"https://{hostname}/api/v1/qpilot/project/fetch"
        headers = {"token": self.auth_token, "Origin": f"https://{hostname}"}
        payload = {"getShared": getShared}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching QPilot project list: {str(e)}")
            return {"error": str(e)}

    async def create_project(self, name: str):
        hostname = Config.QPILOT_BASE_HOSTNAME
        url = f"https://{hostname}/api/v1/qpilot/project/create"
        headers = {"token": self.auth_token, "Origin": f"https://{hostname}"}
        payload = {"name": name}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating QPilot project: {str(e)}")
            return {"error": str(e)}
