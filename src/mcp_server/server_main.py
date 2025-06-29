"""
FastMCP Server Main Entry Point (modular)

This script initializes the FastMCP server and registers all modular tool fragments:
- Device Management
- Device Control
- File & App Management
- Session Analytics
- QPilot Automation

To start the server, run this file as the main module.
"""

import os
import sys
import asyncio

# Always add the src directory to sys.path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from mcp_server.shared_mcp import mcp
from config import logger
from api import PCloudyAPI

# Import all tool fragments to register them with the shared mcp instance
from mcp_server.tools import device_management_tool
from mcp_server.tools import device_control_tool
from mcp_server.tools import file_app_management_tool
from mcp_server.tools import session_analytics_tool
from mcp_server.tools import appium_capabilities_tool
from mcp_server.tools import qpilot_tool

api = PCloudyAPI()

if __name__ == "__main__":
    print("\n--- Starting FastMCP Server (Category-Based) ---")
    try:
        mcp.run(
            transport="streamable-http",
            port=int(os.environ.get("PORT", 8000)),
            host="0.0.0.0"
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(api.close())
            else:
                loop.run_until_complete(api.close())
        except RuntimeError:
            # Event loop not available, skip cleanup
            pass