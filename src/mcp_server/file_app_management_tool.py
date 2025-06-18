import os
import tempfile
from typing import Dict, Any
from config import Config, logger
from pcloudy_api import PCloudyAPI
from fastmcp import FastMCP

mcp = FastMCP("pcloudy_auth3.0")
api = PCloudyAPI()

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
) -> Dict[str, Any]:
    """
    File & App Management Operations: upload, list_apps, install, resign, download_cloud
    
    Actions:
    - upload: Upload APK/IPA file (file_path="/path/to/app.apk", force_upload=False)
    - list_apps: List cloud apps (limit=10, filter_type="all")
    - install: Install and launch app (rid="device_id", filename="app.apk")
    - resign: Resign iOS IPA file (filename="app.ipa", force_resign=False)
    - download_cloud: Download file from cloud (filename="app.apk")
    """
    logger.info(f"Tool called: file_app_management with action={action}, file_path={file_path}, filename={filename}, rid={rid}")
    try:
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
            
        if action == "upload":
            if not file_path:
                return {
                    "content": [{"type": "text", "text": "Please specify a file_path parameter for upload"}],
                    "isError": True
                }
            return await api.upload_file(file_path, force_upload=force_upload)
            
        elif action == "list_apps":
            return await api.list_cloud_apps(limit=limit, filter_type=filter_type)
            
        elif action == "install":
            if not rid or not filename:
                return {
                    "content": [{"type": "text", "text": "Please specify both rid and filename parameters for install"}],
                    "isError": True
                }
            return await api.install_and_launch_app(rid, filename, grant_all_permissions, app_package_name)
            
        elif action == "resign":
            if not filename:
                return {
                    "content": [{"type": "text", "text": "Please specify a filename parameter for resign"}],
                    "isError": True
                }
            return await api.resign_ipa(filename, force_resign)
            
        elif action == "download_cloud":
            if not filename:
                return {
                    "content": [{"type": "text", "text": "Please specify a filename parameter for download"}],
                    "isError": True
                }
            download_dir = os.path.join(tempfile.gettempdir(), "pcloudy_downloads")
            os.makedirs(download_dir, exist_ok=True)
            content = await api.download_from_cloud(filename)
            local_path = os.path.join(download_dir, filename)
            with open(local_path, 'wb') as f:
                f.write(content)
            logger.info(f"File downloaded to {local_path}")
            return {
                "content": [{"type": "text", "text": f"File downloaded to {local_path}"}],
                "isError": False
            }
            
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown action: '{action}'. Available actions: upload, list_apps, install, resign, download_cloud"}],
                "isError": True
            }
            
    except Exception as e:
        logger.error(f"Error in file_app_management: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in file and app management: {str(e)}"}],
            "isError": True
        }