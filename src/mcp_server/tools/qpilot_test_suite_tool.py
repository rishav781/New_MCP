"""
Tool for managing QPilot test suites using the async API methods on PCloudyAPI.
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
async def qpilot_test_suite_management(
    action: str,
    auth_token: str,
    suite_name: str = ""
):
    """
    FastMCP Tool: Manage QPilot test suites (create or list).
    Parameters:
        action: 'create' or 'list'
        auth_token: Authentication token (string)
        suite_name: Name of the test suite to create (string, required for 'create')
    Returns:
        dict: The API response data for the action performed.
    """
    api = get_api()
    try:
        if action == "create":
            if not suite_name:
                raise ValueError("Test suite name required for create action.")
            result = await api.create_qpilot_test_suite(auth_token, suite_name)
        elif action == "list":
            result = await api.list_qpilot_test_suites(auth_token)
        else:
            raise ValueError("Unknown action. Use 'create' or 'list'.")
        return result
    finally:
        await api.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python qpilot_test_suite_tool.py <create|list> <auth_token> [suite_name]")
        sys.exit(1)
    _, action, auth_token, *args = sys.argv
    suite_name = args[0] if args else ""
    try:
        result = asyncio.run(qpilot_test_suite_management(action, auth_token, suite_name))
        if action == "create":
            print(f"QPilot test suite created: {result}")
        elif action == "list":
            print(f"QPilot test suites: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
