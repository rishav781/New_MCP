"""
FastMCP Server Main Entry Point (modular)

This script initializes the FastMCP server and registers all modular tool fragments:
- Device Management
- Device Control
- File & App Management
- Session Analytics

To start the server, run this file as the main module.
"""

from shared_mcp import mcp
import os
import asyncio
import sys

# Add the parent directory to the path to find the config module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import logger
from api import PCloudyAPI

# Import all tool fragments to register them with the shared mcp instance
import tools.device_management_tool
import tools.device_control_tool
import tools.file_app_management_tool
import tools.session_analytics_tool

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