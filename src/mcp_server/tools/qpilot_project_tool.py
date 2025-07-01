"""
Tool for managing QPilot projects using the async API methods on PCloudyAPI.
Supports both FastMCP tool usage and command-line usage for create and list operations.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
# Add the parent directory to the path to find the config module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

from api import PCloudyAPI
from shared_mcp import mcp

def get_api():
    """Helper to get a new PCloudyAPI instance."""
    return PCloudyAPI()

@mcp.tool()
async def qpilot_project_management(
    action: str,
    project_name: str = ""
) -> dict:
    """
    FastMCP Tool: Manage QPilot projects (create or list).
    Parameters:
        action: 'create' or 'list'
        project_name: Name of the project to create (string, required for 'create')
    Returns:
        dict: The API response data for the action performed.
    """
    api = get_api()
    try:
        if action == "create":
            if not project_name:
                raise ValueError("Project name required for create action.")
            result = await api.create_qpilot_project(project_name)
        elif action == "list":
            result = await api.fetch_qpilot_projects()
        else:
            raise ValueError("Invalid action. Use 'create' or 'list'.")
        return result
    finally:
        await api.close()

# CLI entry point (standardized like other tools)
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python qpilot_project_tool.py <create|list> [project_name]")
        sys.exit(1)
    _, action, *args = sys.argv
    project_name = args[0] if args else ""
    try:
        result = asyncio.run(qpilot_project_management(action, project_name))
        if action == "create":
            print(f"QPilot project created: {result}")
        elif action == "list":
            print(f"QPilot projects: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
