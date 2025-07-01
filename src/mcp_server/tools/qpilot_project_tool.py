"""
Tool for managing QPilot projects using the async API methods on PCloudyAPI.
Supports both FastMCP tool usage and command-line usage for create and list operations.
"""
import os
import sys
import asyncio
# Add the parent directory to the path to find the config module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


from api import PCloudyAPI
from shared_mcp import mcp

def get_api():
    """Helper to get a new PCloudyAPI instance."""
    return PCloudyAPI()

@mcp.tool()
async def qpilot_project_management(
    action: str,
    auth_token: str,
    project_name: str = ""
):
    """
    FastMCP Tool: Manage QPilot projects (create or list).
    Parameters:
        action: 'create' or 'list'
        auth_token: Authentication token (string)
        project_name: Name of the project to create (string, required for 'create')
    Returns:
        dict: The API response data for the action performed.
    """
    api = get_api()
    api.auth_token = auth_token
    try:
        if action == "create":
            if not project_name:
                raise ValueError("Project name required for create action.")
            result = await api.create_qpilot_project(project_name)
        elif action == "list":
            result = await api.fetch_qpilot_projects()
        else:
            raise ValueError("Unknown action. Use 'create' or 'list'.")
        return result
    finally:
        await api.close()

# CLI entry point (standardized like other tools)
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python qpilot_project_tool.py <create|list> <auth_token> [project_name]")
        sys.exit(1)
    _, action, auth_token, *args = sys.argv
    project_name = args[0] if args else ""
    try:
        result = asyncio.run(qpilot_project_management(action, auth_token, project_name))
        if action == "create":
            print(f"QPilot project created: {result}")
        elif action == "list":
            print(f"QPilot projects: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
