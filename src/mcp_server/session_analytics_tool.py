import os
import tempfile
from typing import Dict, Any
from config import Config, logger
from pcloudy_api import PCloudyAPI
from fastmcp import FastMCP

mcp = FastMCP("pcloudy_auth3.0")
api = PCloudyAPI()

# Use the system's temp directory for downloads
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "pcloudy_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@mcp.tool()
async def session_analytics(
    action: str,
    rid: str = "",
    filename: str = "",
    download_dir: str = DOWNLOAD_DIR
) -> Dict[str, Any]:
    """
    Session Analytics Operations: list_files, download_data
    
    Actions:
    - list_files: List performance data files (rid="device_id")
    - download_data: Download session data (rid="device_id", filename="file.zip", download_dir="/path/to/dir")
    """
    logger.info(f"Tool called: session_analytics with action={action}, rid={rid}, filename={filename}")
    try:
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
            
        if action == "list_files":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter to list files"}],
                    "isError": True
                }
            return await api.list_performance_data_files(rid)
            
        elif action == "download_data":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter to download data"}],
                    "isError": True
                }
            if download_dir != DOWNLOAD_DIR:
                os.makedirs(download_dir, exist_ok=True)
            return await api.download_session_data(rid, filename, download_dir)
            
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown action: '{action}'. Available actions: list_files, download_data"}],
                "isError": True
            }
            
    except Exception as e:
        logger.error(f"Error in session_analytics: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in session analytics: {str(e)}"}],
            "isError": True
        }