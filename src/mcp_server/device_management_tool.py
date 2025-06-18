from typing import Dict, Any
from config import Config, logger
from pcloudy_api import PCloudyAPI
from fastmcp import FastMCP

mcp = FastMCP("pcloudy_auth3.0")
api = PCloudyAPI()

@mcp.tool()
async def device_management(
    action: str, 
    platform: str = "android", 
    device_name: str = "", 
    rid: str = "", 
    latitude: float = 0.0, 
    longitude: float = 0.0,
    auto_start_services: bool = True
) -> Dict[str, Any]:
    """
    Device Management Operations: list, book, release, detect_platform, set_location
    
    Actions:
    - list: List available devices (platform="android"/"ios")
    - book: Book device (device_name="GalaxyS10", platform="android", auto_start_services=True)
    - release: Release device (rid="device_id")
    - detect_platform: Auto-detect device platform (rid="device_id")
    - set_location: Set device GPS coordinates (rid="device_id", latitude=48.8566, longitude=2.3522)
    """
    logger.info(f"Tool called: device_management with action={action}, platform={platform}, device_name={device_name}, rid={rid}")
    try:
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
            
        if action == "list":
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
            
        elif action == "book":
            if not device_name:
                return {
                    "content": [{"type": "text", "text": "Please specify a device_name parameter for booking"}],
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
            device_name_lower = device_name.lower().strip()
            selected = next((d for d in devices if d["available"] and device_name_lower in d["model"].lower()), None)
            if not selected:
                return {
                    "content": [{"type": "text", "text": f"No available {platform} device found matching '{device_name}'"}],
                    "isError": True
                }
            booking = await api.book_device(selected["id"], auto_start_services=auto_start_services)
            api.rid = booking.get("rid")
            if not api.rid:
                return {
                    "content": [{"type": "text", "text": "Failed to get booking ID"}],
                    "isError": True
                }
            enhanced_content = booking.get("enhanced_content")
            if enhanced_content:
                logger.info(f"Device '{selected['model']}' booked successfully with enhanced features. RID: {api.rid}")
                return {
                    "content": enhanced_content,
                    "isError": False
                }
            else:
                logger.info(f"Device '{selected['model']}' booked successfully. RID: {api.rid}")
                return {
                    "content": [{"type": "text", "text": f"Device '{selected['model']}' booked successfully. RID: {api.rid}"}],
                    "isError": False
                }
                
        elif action == "release":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter for device release"}],
                    "isError": True
                }
            logger.info("Releasing device... This may take 10-20 seconds.")
            result = await api.release_device(rid, auto_download=False)
            return result
            
        elif action == "detect_platform":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter for platform detection"}],
                    "isError": True
                }
            if not rid.strip():
                return {
                    "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
                    "isError": True
                }
            result = await api.detect_device_platform(rid)
            return result
            
        elif action == "set_location":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify rid, latitude, and longitude parameters"}],
                    "isError": True
                }
            if not rid.strip():
                return {
                    "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
                    "isError": True
                }
            if latitude == 0.0 and longitude == 0.0:
                return {
                    "content": [{"type": "text", "text": "Please specify non-zero latitude and longitude values"}],
                    "isError": True
                }
            if not (-90 <= latitude <= 90):
                return {
                    "content": [{"type": "text", "text": "Error: Latitude must be between -90 and 90 degrees"}],
                    "isError": True
                }
            if not (-180 <= longitude <= 180):
                return {
                    "content": [{"type": "text", "text": "Error: Longitude must be between -180 and 180 degrees"}],
                    "isError": True
                }
            result = await api.set_device_location(rid, latitude, longitude)
            return result
            
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown action: '{action}'. Available actions: list, book, release, detect_platform, set_location"}],
                "isError": True
            }
            
    except Exception as e:
        logger.error(f"Error in device_management: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in device management: {str(e)}"}],
            "isError": True
        }