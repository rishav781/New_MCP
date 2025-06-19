"""
Device Control Tool for pCloudy MCP Server (modular)

Provides device control operations as a FastMCP tool, including:
- screenshot: Capture device screenshot
- get_url: Get device page URL
- start_services: Start device logs, performance data, session recording
- adb: Run ADB commands on Android devices
- wildnet: Start wildnet network features

This tool is registered with FastMCP and can be called via the MCP server.
"""

from src.config import logger
from src.api import PCloudyAPI
import asyncio
from fastmcp import FastMCP
mcp = FastMCP("pcloudy_auth3.0")

def get_api():
    """Helper to get a new PCloudyAPI instance."""
    return PCloudyAPI()

@mcp.tool()
async def device_control(
    action: str,
    rid: str = "",
    skin: bool = True,
    adb_command: str = "",
    platform: str = "auto",
    start_device_logs: bool = True,
    start_performance_data: bool = True,
    start_session_recording: bool = True
):
    """
    FastMCP Tool: Device Control
    
    Parameters:
        action: The device control action (screenshot, get_url, start_services, adb, wildnet)
        rid: Device booking ID
        skin: Whether to include device skin in screenshot
        adb_command: ADB command to execute (for Android)
        platform: Device platform (auto/android/ios)
        start_device_logs: Enable device logs (for start_services)
        start_performance_data: Enable performance data (for start_services)
        start_session_recording: Enable session recording (for start_services)
    Returns:
        Dict with operation result and error status
    """
    api = get_api()
    logger.info(f"Tool called: device_control with action={action}, rid={rid}")
    try:
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        if action == "screenshot":
            if not rid:
                return {"content": [{"type": "text", "text": "Please specify a rid parameter for screenshot"}], "isError": True}
            return await api.capture_screenshot(rid, skin)
        elif action == "get_url":
            if not rid:
                return {"content": [{"type": "text", "text": "Please specify a rid parameter for device URL"}], "isError": True}
            return await api.get_device_page_url(rid)
        elif action == "start_services":
            if not rid:
                return {"content": [{"type": "text", "text": "Please specify a rid parameter for starting services"}], "isError": True}
            return await api.start_device_services(rid, start_device_logs, start_performance_data, start_session_recording)
        elif action == "adb":
            if not rid or not adb_command:
                return {"content": [{"type": "text", "text": "Please specify both rid and adb_command parameters"}], "isError": True}
            return await api.execute_adb_command(rid, adb_command)
        elif action == "wildnet":
            if not rid:
                return {"content": [{"type": "text", "text": "Please specify a rid parameter for wildnet"}], "isError": True}
            return await api.start_wildnet(rid)
        else:
            return {"content": [{"type": "text", "text": f"Unknown action: '{action}'."}], "isError": True}
    except Exception as e:
        logger.error(f"Error in device_control: {str(e)}")
        return {"content": [{"type": "text", "text": f"Error in device control: {str(e)}"}], "isError": True}