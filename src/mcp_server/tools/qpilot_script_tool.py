"""
Tool for creating/getting a QPilot script using the async API method on PCloudyAPI.
Supports both FastMCP tool usage and command-line usage.
Prompts the user for required parameters if run from CLI.
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
async def qpilot_script_tool(
    hostname: str,
    auth_token: str,
    booking_host: str,
    testCaseId: str,
    testSuiteId: str,
    scriptType: str
):
    """
    FastMCP Tool: Create/Get QPilot script.
    Parameters:
        hostname: The hostname to use in the URL.
        auth_token: Authentication token (string)
        booking_host: The booking host for the origin header
        testCaseId: The test case ID
        testSuiteId: The test suite ID
        scriptType: The script type (e.g., 'pcloudy_appium-js')
    Returns:
        dict: The API response data for the script creation.
    """
    api = get_api()
    try:
        result = await api.create_qpilot_script(hostname, auth_token, booking_host, testCaseId, testSuiteId, scriptType)
        return result
    finally:
        await api.close()

if __name__ == "__main__":
    print("Enter the following parameters for QPilot script creation:")
    hostname = input("Hostname (e.g. https://prod-backend.qpilot.pcloudy.com): ").strip()
    auth_token = input("Auth Token: ").strip()
    booking_host = input("Booking Host (for origin header): ").strip()
    testCaseId = input("Test Case ID: ").strip()
    testSuiteId = input("Test Suite ID: ").strip()
    scriptType = input("Script Type (e.g. pcloudy_appium-js): ").strip()
    try:
        result = asyncio.run(qpilot_script_tool(hostname, auth_token, booking_host, testCaseId, testSuiteId, scriptType))
        print(f"QPilot script creation result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
