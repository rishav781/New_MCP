"""
QPilot Project Mixin for pCloudy MCP Server

Provides async methods to manage QPilot projects.
Intended to be used as a mixin in the modular API architecture.
"""
from config import Config, logger
import httpx
from utils import encode_auth, parse_response

class QPilotProjectMixin:
    async def fetch_qpilot_projects(self) -> dict:
        """
        Fetch the list of QPilot projects (owned and shared) from the QPilot backend.
        Returns:
            dict: The project list data as returned by the API.
        """
        url = f"{Config.HOSTNAME}/api/v1/qpilot/project/fetch"
        headers = {
            "token": Config.auth_token,
            "origin": Config.Bookinghost
        }
        payload = {"getShared": True}
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = parse_response(response)
            logger.info(f"QPilot projects fetched: {data}")
            return data

    async def create_qpilot_project(self, name: str) -> dict:
        """
        Create a new QPilot project with the given name.
        Args:
            name (str): The name of the project to create.
        Returns:
            dict: The API response data for the created project.
        """
        url = f"{Config.HOSTNAME}/api/v1/qpilot/project/create"
        headers = {
            "token": Config.auth_token,
            "origin": Config.Bookinghost
        }
        payload = {"name": name}
        async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = parse_response(response)
            logger.info(f"QPilot project created: {data}")
            return data
