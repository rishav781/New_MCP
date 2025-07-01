"""
Session Analytics Tool for pCloudy MCP Server (modular)

Provides session data and analytics operations as a FastMCP tool, including:
- download_session: Download DEVICE-RELATED files (screenshots, session data, logs)
- list_performance: List performance data files for a device

IMPORTANT: This tool uses /download_manual_access_data endpoint for device files.
For cloud storage files (APKs, IPAs), use file_app_management_tool instead.

This tool is registered with FastMCP and can be called via the MCP server.
"""

import os
import sys

# Add the parent directory to the path to find the config module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import logger
from config import Config
from api import PCloudyAPI
import asyncio
from shared_mcp import mcp

def get_api():
    """Helper to get a new PCloudyAPI instance."""
    return PCloudyAPI()

@mcp.tool()
async def session_analytics(
    action: str,
    rid: str = "",
    filename: str = "",
    download_dir: str = ""
):
    """
    FastMCP Tool: Session Data & Analytics
    
    Parameters:
        action: The analytics action (download_session, list_performance)
        rid: Device booking ID
        filename: Specific file to download (optional)
        download_dir: Directory to save downloaded files (optional)
    Returns:
        Dict with operation result and error status
    """
    api = get_api()
    logger.info(f"Tool called: session_analytics with action={action}, rid={rid}, filename={filename}")
    try:
        if not Config.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        
        if action == "download_session":
            if not rid:
                return {"content": [{"type": "text", "text": "Please specify a rid parameter for session data download"}], "isError": True}
            if download_dir:
                try:
                    import os
                    import tempfile
                    download_dir = os.path.abspath(download_dir)
                    project_root = os.path.abspath(os.getcwd())
                    temp_root = os.path.abspath(tempfile.gettempdir())
                    # Allow either project directory or temp directory for downloads
                    if not (download_dir.startswith(project_root) or download_dir.startswith(temp_root)):
                        return {"content": [{"type": "text", "text": "Error: Download directory must be within the project directory or system temp directory for security"}], "isError": True}
                except Exception:
                    return {"content": [{"type": "text", "text": "Error: Invalid download directory path"}], "isError": True}
            # When no download_dir is specified, let session.py use its temp directory default
            result = await api.download_session_data(rid, filename if filename else None, download_dir if download_dir else None)
            return result
        elif action == "list_performance":
            if not rid:
                return {"content": [{"type": "text", "text": "Please specify a rid parameter to list performance data"}], "isError": True}
            result = await api.list_performance_data_files(rid)
            return result
        else:
            return {"content": [{"type": "text", "text": f"Unknown action: '{action}'. Available actions: download_session, list_performance"}], "isError": True}
    except Exception as e:
        logger.error(f"Error in session_analytics: {str(e)}")
        return {"content": [{"type": "text", "text": f"Error in session analytics: {str(e)}"}], "isError": True}