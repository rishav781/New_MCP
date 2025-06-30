"""
QPilot Project Management API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotProjectMixin:
    async def project_list(self, getShared: bool = True):
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v1/qpilot/project/fetch"
        headers = {"token": self.auth_token, "Origin": Config.get_origin()}
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
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v1/qpilot/project/create"
        headers = {"token": self.auth_token, "Origin": Config.get_origin()}
        payload = {"name": name}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating QPilot project: {str(e)}")
            return {"error": str(e)}
