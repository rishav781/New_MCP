from fastmcp import FastMCP
import os
import asyncio
from config import logger
from api import PCloudyAPI

# Import all tool fragments to register them
from .tools.device_management_tool import *
from .tools.device_control_tool import *
from .tools.file_app_management_tool import *
from .tools.session_analytics_tool import *

mcp = FastMCP("pcloudy_auth3.0")
api = PCloudyAPI()

if __name__ == "__main__":
    print("\n--- Starting FastMCP Server (Category-Based) ---")
    try:
        mcp.run(
            transport="streamable-http",
            port=int(os.environ.get("PORT", 8000)),
            host="0.0.0.0"
        )
    finally:
        asyncio.get_event_loop().run_until_complete(api.close()) 