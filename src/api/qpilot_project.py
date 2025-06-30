"""
QPilot Project Management API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotProjectMixin:
    async def project_list(self, getShared: bool = True):
        """
        Fetch the list of QPilot projects for the authenticated user.

        Parameters:
            getShared (bool): Whether to include shared projects (default: True).
        
        Returns:
            dict: API response containing the list of projects or error details.
        """
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v1/qpilot/project/fetch"
        headers = {"token": self.auth_token, "Origin": Config.get_origin()}
        payload = {"getShared": getShared}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                # Hide 'id' field in each project (if present)
                if data and 'data' in data and 'projects' in data['data']:
                    for project in data['data']['projects']:
                        if 'id' in project:
                            project.pop('id')
                return data
        except Exception as e:
            logger.error(f"Error fetching QPilot project list: {str(e)}")
            return {"error": str(e)}

    async def create_project(self, name: str):
        """
        Create a new QPilot project with the given name.

        Parameters:
            name (str): Name of the new project.
        
        Returns:
            dict: API response containing the created project info or error details.
        """
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
