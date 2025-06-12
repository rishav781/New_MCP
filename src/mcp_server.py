import os
import tempfile
from typing import Dict, Any
from fastmcp import FastMCP
from config import Config, logger
from pcloudy_api import PCloudyAPI
import asyncio

# Initialize FastMCP server and PCloudyAPI
mcp = FastMCP("pcloudy_auth3.0")
api = PCloudyAPI()

# Ensure a 'downloads' directory exists in the current working directory
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@mcp.tool()
async def authorize(username: str, api_key: str) -> Dict[str, Any]:
    """Authenticate with pCloudy using username and API key."""
    logger.info(f"Tool called: authorize with username={username}")
    try:
        if not username or not api_key:
            logger.error("Username and API key cannot be empty")
            return {
                "content": [{"type": "text", "text": "Username and API key cannot be empty"}],
                "isError": True
            }
        await api.authenticate(username, api_key)
        logger.info("Authorization successful")
        return {
            "content": [{"type": "text", "text": "Authorization successful. You can now use other tools."}],
            "isError": False
        }
    except Exception as e:
        logger.error(f"Authorization failed: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Authorization failed: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def list_available_devices(platform: str = Config.DEFAULT_PLATFORM) -> Dict[str, Any]:
    """List available devices for the specified platform (android or ios)."""
    logger.info(f"Tool called: list_available_devices with platform={platform}")
    try:
        if not api.auth_token:
            return {
                "content": [{"type": "text", "text": "Not authorized. Please call authorize tool first."}],
                "isError": True
            }
        platform = platform.lower().strip()
        if platform not in Config.VALID_PLATFORMS:
            logger.error(f"Invalid platform: {platform}")
            return {
                "content": [{"type": "text", "text": f"Invalid platform: {platform}. Must be one of {Config.VALID_PLATFORMS}"}],
                "isError": True
            }
        devices_response = await api.get_devices_list(platform=platform)
        devices = devices_response.get("models", [])
        available = [d["model"] for d in devices if d["available"]]
        if not available:
            logger.info(f"No {platform} devices available")
            return {
                "content": [{"type": "text", "text": f"No {platform} devices available."}],
                "isError": True
            }
        device_list = ", ".join(available)
        logger.info(f"Found {len(available)} available {platform} devices")
        return {
            "content": [{"type": "text", "text": f"Available {platform} devices: {device_list}"}],
            "isError": False
        }
    except Exception as e:
        logger.error(f"Error listing {platform} devices: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error listing {platform} devices: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def book_device_by_name(device_name: str, platform: str = Config.DEFAULT_PLATFORM) -> Dict[str, Any]:
    """Book a device matching the provided device name for the specified platform."""
    logger.info(f"Tool called: book_device_by_name with device_name={device_name}, platform={platform}")
    try:
        if not api.auth_token:
            return {
                "content": [{"type": "text", "text": "Not authorized. Please call authorize tool first."}],
                "isError": True
            }
        platform = platform.lower().strip()
        if platform not in Config.VALID_PLATFORMS:
            return {
                "content": [{"type": "text", "text": f"Invalid platform: {platform}. Must be one of {Config.VALID_PLATFORMS}"}],
                "isError": True
            }
        devices_response = await api.get_devices_list(platform=platform)
        devices = devices_response.get("models", [])
        device_name = device_name.lower().strip()
        selected = next((d for d in devices if d["available"] and device_name in d["model"].lower()), None)
        if not selected:
            return {
                "content": [{"type": "text", "text": f"No available {platform} device found matching '{device_name}'"}],
                "isError": True
            }
        booking = await api.book_device(selected["id"])
        api.rid = booking.get("rid")
        if not api.rid:
            return {
                "content": [{"type": "text", "text": "Failed to get booking ID"}],
                "isError": True
            }
        logger.info(f"Device '{selected['model']}' booked successfully. RID: {api.rid}")
        return {
            "content": [{"type": "text", "text": f"Device '{selected['model']}' booked successfully. RID: {api.rid}"}],
            "isError": False
        }
    except Exception as e:
        logger.error(f"Error booking device: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error booking device: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def release_device(rid: str) -> Dict[str, Any]:
    """Release a booked device."""
    logger.info(f"Tool called: release_device with rid={rid}")
    try:
        if not api.auth_token:
            return {
                "content": [{"type": "text", "text": "Not authorized. Please call authorize tool first."}],
                "isError": True
            }
        try:
            # Try with a longer timeout (e.g., 30 seconds)
            result = await asyncio.wait_for(api.release_device(rid), timeout=30)
            return result
        except asyncio.TimeoutError:
            logger.warning("Timeout while releasing device. The device may have been released, but the server was slow to respond.")
            return {
                "content": [
                    {"type": "text", "text": "Timeout while releasing device. The device may have been released, but the server was slow to respond. Please check device status."}
                ],
                "isError": True
            }
    except Exception as e:
        logger.error(f"Error releasing device: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error releasing device: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def upload_file(file_path: str) -> Dict[str, Any]:
    """Upload an APK, IPA, or ZIP file to pCloudy cloud drive."""
    logger.info(f"Tool called: upload_file for {file_path}")
    try:
        return await api.upload_file(file_path)
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error uploading file: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def capture_device_screenshot(rid: str, skin: bool = True) -> Dict[str, Any]:
    """Capture a screenshot for a booked device."""
    logger.info(f"Tool called: capture_device_screenshot for RID {rid}")
    try:
        return await api.capture_screenshot(rid, skin)
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error capturing screenshot: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def download_from_cloud(filename: str) -> Dict[str, Any]:
    """Download a file from the pCloudy cloud drive and save it in the system temp folder."""
    logger.info(f"Tool called: download_from_cloud with filename={filename}")
    try:
        file_content = await api.download_from_cloud(filename)
        temp_dir = tempfile.gettempdir()
        local_path = os.path.join(temp_dir, filename)
        with open(local_path, 'wb') as f:
            f.write(file_content)
        return {
            "content": [{"type": "text", "text": f"File downloaded to {local_path}"}],
            "isError": False
        }
    except Exception as e:
        logger.error(f"Error downloading from cloud: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error downloading from cloud: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def download_manual_access_data(rid: str, filename: str) -> Dict[str, Any]:
    """Download a file using the download_manual_access_data API and save it in the system temp folder."""
    logger.info(f"Tool called: download_manual_access_data with rid={rid}, filename={filename}")
    try:
        file_content = await api.download_manual_access_data(rid, filename)
        temp_dir = tempfile.gettempdir()
        local_path = os.path.join(temp_dir, filename)
        with open(local_path, 'wb') as f:
            f.write(file_content)
        return {
            "content": [{"type": "text", "text": f"File downloaded to {local_path}"}],
            "isError": False
        }
    except Exception as e:
        logger.error(f"Error downloading manual access data: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error downloading manual access data: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def get_device_page_url(rid: str) -> Dict[str, Any]:
    """Get the URL for a device page."""
    logger.info(f"Tool called: get_device_page_url with rid={rid}")
    try:
        return await api.get_device_page_url(rid)
    except Exception as e:
        logger.error(f"Error getting device page URL: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error getting device page URL: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def list_cloud_apps(limit: int = 10, filter_type: str = "all") -> Dict[str, Any]:
    """List apps available in the pCloudy cloud drive."""
    logger.info(f"Tool called: list_cloud_apps with limit={limit}, filter_type={filter_type}")
    try:
        return await api.list_cloud_apps(limit, filter_type)
    except Exception as e:
        logger.error(f"Error listing cloud apps: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error listing cloud apps: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def install_and_launch_app(rid: str, filename: str, grant_all_permissions: bool = True, platform: str = None) -> Dict[str, Any]:
    """
    Install and launch an app on a device.
    If platform is 'ios' and the filename does not contain 'resign', advise the client to resign the app first.
    """
    logger.info(f"Tool called: install_and_launch_app with rid={rid}, filename={filename}, platform={platform}")
    try:
        # If platform is provided and is ios, check if the app is resigned
        if platform and platform.lower() == "ios":
            if "resign" not in filename.lower():
                return {
                    "content": [{
                        "type": "text",
                        "text": (
                            "For iOS apps, please resign the IPA before installing. "
                            "Use the resign_ipa tool first. The resigned file will contain 'resign' in its name."
                        )
                    }],
                    "isError": True
                }
        return await api.install_and_launch_app(rid, filename, grant_all_permissions)
    except Exception as e:
        logger.error(f"Error installing and launching app: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error installing and launching app: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def resign_ipa(filename: str) -> Dict[str, Any]:
    """Resign an IPA file and return a reference to the resigned file. Download only when requested."""
    logger.info(f"Tool called: resign_ipa with filename={filename}")
    try:
        resigned_file_reference = await api.resign_ipa(filename)
        # Do not download or save the file here!
        return {
            "content": [{"type": "text", "text": f"IPA file '{filename}' has been resigned. Use the download tool to retrieve the file if needed.", "file_reference": resigned_file_reference}],
            "isError": False
        }
    except Exception as e:
        logger.error(f"Error resigning IPA: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error resigning IPA: {str(e)}"}],
            "isError": True
        }

# IMPORTANT:
# - To download any file from a device (e.g., logs, screenshots, app data), always use the download_manual_access_data tool.
# - To download any file from the pCloudy cloud drive, always use the download_from_cloud tool.
# - Do NOT use other tools or methods for downloading files from devices or cloud storage.

# Run the server
if __name__ == "__main__":
    print("\n--- Starting FastMCP Server ---")
    try:
        mcp.run(
            transport="streamable-http",
            port=int(os.environ.get("PORT", 8000)),
            host="0.0.0.0"
        )
    finally:
        asyncio.get_event_loop().run_until_complete(api.close())