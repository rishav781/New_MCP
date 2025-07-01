import sys
import os
import asyncio
# Add the parent directory to the path to find the config and mixin modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared_mcp import mcp
from api.qpilot_appium_control import QPilotAppiumControlMixin

@mcp.tool()
async def appium_control(rid: int, action: str, os: str, appName: str) -> dict:
    """
    FastMCP Tool: Control Appium for a QPilot session (start/stop).
    Args:
        rid (str): The QPilot RID.
        action (str): The action to perform (e.g., 'start', 'stop').
        os (str): The platform (e.g., 'android', 'ios').
        appName (str): The app name.
    Returns:
        dict: The API response data for the Appium control action.
    """
    appium_control = QPilotAppiumControlMixin()
    result = await appium_control.control_qpilot_appium(rid, action, os, appName)
    return result
