"""
Tool for managing QPilot test cases using the async API methods on PCloudyAPI.
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
async def qpilot_test_case_management(
    action: str,
    auth_token: str,
    testSuiteId: str = "",
    testCaseName: str = "",
    platform: str = ""
):
    """
    FastMCP Tool: Manage QPilot test cases (create or list).
    Parameters:
        action: 'create' or 'list'
        auth_token: Authentication token (string)
        testSuiteId: The ID of the test suite (required for 'create')
        testCaseName: The name of the test case (required for 'create')
        platform: The platform for the test case (required for 'create')
    Returns:
        dict: The API response data for the action performed.
    """
    api = get_api()
    try:
        if action == "create":
            if not (testSuiteId and testCaseName and platform):
                raise ValueError("testSuiteId, testCaseName, and platform are required for create action.")
            result = await api.create_qpilot_test_case(auth_token, testSuiteId, testCaseName, platform)
        elif action == "list":
            result = await api.get_qpilot_test_cases(auth_token)
        else:
            raise ValueError("Unknown action. Use 'create' or 'list'.")
        return result
    finally:
        await api.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python qpilot_test_case_tool.py <create|list> <auth_token> [testSuiteId testCaseName platform]")
        sys.exit(1)
    _, action, auth_token, *args = sys.argv
    testSuiteId = args[0] if len(args) > 0 else ""
    testCaseName = args[1] if len(args) > 1 else ""
    platform = args[2] if len(args) > 2 else ""
    try:
        result = asyncio.run(qpilot_test_case_management(action, auth_token, testSuiteId, testCaseName, platform))
        if action == "create":
            print(f"QPilot test case created: {result}")
        elif action == "list":
            print(f"QPilot test cases: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
