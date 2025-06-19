from config import logger
from api import PCloudyAPI
import asyncio
import os
from fastmcp import FastMCP
mcp = FastMCP("pcloudy_auth3.0")

def get_api():
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
    File and App Management Operations: upload, list_apps, install, resign, download_cloud
    """
    api = get_api()
    logger.info(f"Tool called: file_app_management with action={action}, file_path={file_path}, filename={filename}, rid={rid}")
    try:
        if not api.auth_token:
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