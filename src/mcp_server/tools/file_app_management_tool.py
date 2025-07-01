"""
File & App Management Tool for pCloudy MCP Server (modular)

Provides file and app management operations as a FastMCP tool, including:
- upload: Upload APK/IPA files to cloud storage
- list_apps: List cloud apps
- install: Install and launch app on device
- resign: Resign iOS IPA files
- download_cloud: Download files from cloud storage (APKs, IPAs, user files)

IMPORTANT: Download Context for LLMs:
- download_cloud: For CLOUD STORAGE files only (uses /download_file endpoint)
- For DEVICE files (screenshots, session data): Use session_analytics_tool with download_session action

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
async def file_app_management(
    action: str,
    file_path: str = "",
    filename: str = "",
    rid: str = "",
    force_upload: bool = False,
    limit: int = 10,
    filter_type: str = "all",
    grant_all_permissions: bool = True,
    platform: str = "",
    app_package_name: str = "",
    force_resign: bool = False
):
    """
    FastMCP Tool: File & App Management
    
    Parameters:
        action: The management action (upload, list_apps, install, resign, download_cloud)
        file_path: Path to file for upload
        filename: Name of file for install/resign/download
        rid: Device booking ID
        force_upload: Force upload even if file exists
        limit: Limit for list_apps
        filter_type: Filter for list_apps
        grant_all_permissions: Grant all permissions on install
        platform: Device platform (android/ios)
        app_package_name: App package name (optional)
        force_resign: Force resign IPA (iOS)
    Returns:
        Dict with operation result and error status
    """
    api = get_api()
    logger.info(f"Tool called: file_app_management with action={action}, file_path={file_path}, filename={filename}, rid={rid}")
    try:
        if not Config.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        if action == "upload":
            if not file_path:
                return {"content": [{"type": "text", "text": "Please specify a file_path parameter for upload"}], "isError": True}
            return await api.upload_file(file_path, force_upload=force_upload)
        elif action == "list_apps":
            return await api.list_cloud_apps(limit, filter_type)
        elif action == "install":
            if not rid or not filename:
                return {"content": [{"type": "text", "text": "Please specify both rid and filename parameters for installation"}], "isError": True}            
            if platform and platform.lower() == "ios":
                filename_lower = filename.lower()
                resign_indicators = ["resign", "resigned", "testmunk", "demo", "test"]
                is_resigned = any(indicator in filename_lower for indicator in resign_indicators)
                if not is_resigned:
                    return {"content": [{"type": "text", "text": "For iOS apps, please resign the IPA before installing. Use the resign action first."}], "isError": True}
            install_result = await api.install_and_launch_app(rid, filename, grant_all_permissions, app_package_name)
            return install_result
        elif action == "resign":
            if not filename:
                return {"content": [{"type": "text", "text": "Please specify a filename parameter for IPA resigning"}], "isError": True}
            result = await api.resign_ipa(filename, force_resign=force_resign)
            return result
        elif action == "download_cloud":
            if not filename:
                return {"content": [{"type": "text", "text": "Please specify a filename parameter for cloud download"}], "isError": True}
            file_content = await api.download_from_cloud(filename)
            import tempfile
            temp_dir = tempfile.gettempdir()
            local_path = os.path.join(temp_dir, filename)
            with open(local_path, 'wb') as f:
                f.write(file_content)
            return {"content": [{"type": "text", "text": f"File downloaded to {local_path}"}], "isError": False}
        else:
            return {"content": [{"type": "text", "text": f"Unknown action: '{action}'. Available actions: upload, list_apps, install, resign, download_cloud"}], "isError": True}
    except Exception as e:
        logger.error(f"Error in file_app_management: {str(e)}")
        return {"content": [{"type": "text", "text": f"Error in file and app management: {str(e)}"}], "isError": True}