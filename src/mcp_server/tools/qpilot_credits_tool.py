"""
Tool for getting QPilot credits left using the async API method on PCloudyAPI.
Supports both FastMCP tool usage and command-line usage.
"""
import os
import sys
import asyncio
# Add the parent directory to the path to find the config module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api import PCloudyAPI
from shared_mcp import mcp

def get_api():
    return PCloudyAPI()

@mcp.tool()
async def qpilot_credits_tool(auth_token: str):
    """
    FastMCP Tool: Get QPilot credits left.
    Parameters:
        auth_token: Authentication token (string)
    Returns:
        dict: The API response data for credits left.
    """
    api = get_api()
    api.auth_token = auth_token
    try:
        credits = await api.get_qpilot_credits_left()
        return credits
    finally:
        await api.close()

if __name__ == "__main__":
    auth_token = input("Auth Token: ").strip()
    try:
        result = asyncio.run(qpilot_credits_tool(auth_token))
        print(f"QPilot credits left: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
