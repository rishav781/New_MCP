import os
import tempfile
import asyncio
from fastmcp import FastMCP
from config import Config, logger
from pcloudy_api import PCloudyAPI

# Initialize FastMCP server and PCloudyAPI
mcp = FastMCP("pcloudy_auth3.0")
api = PCloudyAPI()

# Use the system's temp directory for downloads
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "pcloudy_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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