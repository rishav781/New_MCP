"""
Device Management Tool for pCloudy MCP Server (modular)

Provides device management operations as a FastMCP tool, including:
- list: List available devices
- book: Book a device
- release: Release a booked device
- detect_platform: Auto-detect device platform
- set_location: Set device GPS coordinates

This tool is registered with FastMCP and can be called via the MCP server.
"""

from src.config import Config, logger
from src.api import PCloudyAPI
import asyncio

def get_api():
    """Helper to get a new PCloudyAPI instance."""
    return PCloudyAPI()

from fastmcp import FastMCP
mcp = FastMCP("pcloudy_auth3.0")

@mcp.tool()
async def device_management(
    action: str, 
    platform: str = "android", 
    device_name: str = "", 
    rid: str = "", 
    latitude: float = 0.0, 
    longitude: float = 0.0,
    auto_start_services: bool = True
):
    """
    FastMCP Tool: Device Management
    
    Parameters:
        action: The management action (list, book, release, detect_platform, set_location)
        platform: Device platform (android/ios)
        device_name: Name/model of device to book
        rid: Device booking ID
        latitude: Latitude for GPS location
        longitude: Longitude for GPS location
        auto_start_services: Whether to start logs/perf/session on booking
    Returns:
        Dict with operation result and error status
    """
    api = get_api()
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
            result = await api.set_device_location(rid, latitude, longitude)
            return result
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown action: '{action}'."}],
                "isError": True
            }
    except Exception as e:
        logger.error(f"Error in device_management: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in device management: {str(e)}"}],
            "isError": True
        }