import os
import tempfile
import re
import webbrowser
import json
from typing import Dict, Any
from fastmcp import FastMCP
from config import Config, logger
from api import PCloudyAPI
import asyncio

# Initialize FastMCP server and PCloudyAPI
mcp = FastMCP("pcloudy_auth3.0")
api = PCloudyAPI()

# Use the system's temp directory for downloads
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "pcloudy_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# =============================================================================
# IMPORTANT: ADB COMMAND FORMAT CONTEXT FOR LLM UNDERSTANDING
# =============================================================================
"""
CRITICAL ADB COMMAND FORMAT REQUIREMENTS:

⚠️  IMPORTANT: When executing ADB commands through pCloudy, you MUST use the complete 
    ADB command format including the 'adb shell' prefix.

❌ INCORRECT FORMAT (will return "Invalid Command"):
   - "shell getprop ro.build.version.release"
   - "getprop ro.build.version.release"  
   - "dumpsys battery"
   - "pm list packages"
   - "ls"
   - "ps"

✅ CORRECT FORMAT (will work successfully):
   - "adb shell getprop ro.build.version.release"
   - "adb shell dumpsys battery"
   - "adb shell pm list packages"
   - "adb shell ls"
   - "adb shell ps"
   - "adb shell date"
   - "adb shell cat /proc/cpuinfo"
   - "adb shell ifconfig"

PROVEN WORKING EXAMPLES FROM TESTING:
1. adb shell dumpsys battery → Returns detailed battery information
2. adb shell getprop ro.build.version.release → Returns Android version (e.g., "12")
3. adb shell getprop ro.product.model → Returns device model (e.g., "SM-G973F")
4. adb shell pm list packages | head -10 → Lists installed packages
5. adb shell cat /proc/cpuinfo | head -20 → Shows CPU information
6. adb shell cat /proc/meminfo | head -10 → Shows memory usage
7. adb shell ps | head -15 → Lists running processes
8. adb shell date → Shows current date/time
9. adb shell ifconfig → Shows network interfaces

EXAMPLE SUCCESSFUL RESPONSE FORMAT:
{
    "token": "qffs927k5xqhsgqr78p4w378",
    "rid": "3593636", 
    "adbCommand": "adb shell dumpsys battery"
}
{
    "result": {
        "token": "qffs927k5xqhsgqr78p4w378",
        "code": 200,
        "msg": "success", 
        "adbreply": "Current Battery Service state:\n  AC powered: false\n  USB powered: true..."
    }
}

Remember: Always include 'adb shell' prefix for shell commands!
"""

# =============================================================================
# CATEGORY-BASED META-TOOLS - FASTMCP COMPATIBLE
# =============================================================================

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
        # Auto-authenticate if not already authorized
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

@mcp.tool()
async def device_control(
    action: str,
    rid: str = "",
    skin: bool = True,
    adb_command: str = "",
    platform: str = "auto",
    start_device_logs: bool = True,
    start_performance_data: bool = True,
    start_session_recording: bool = True
) -> Dict[str, Any]:
    """
    Device Control & Monitoring Operations: screenshot, get_url, start_services, adb, wildnet
    
    Actions:
    - screenshot: Capture device screenshot (rid="device_id", skin=True)
    - get_url: Get device page URL and open in browser (rid="device_id")
    - start_services: Start device services (rid="device_id")
    - adb: Execute ADB command on Android (rid="device_id", adb_command="adb shell dumpsys battery")
           ⚠️  CRITICAL: Use FULL command format with 'adb shell' prefix!
    - wildnet: Start wildnet features (rid="device_id")
    """
    logger.info(f"Tool called: device_control with action={action}, rid={rid}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
            
        if action == "screenshot":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter for screenshot"}],
                    "isError": True
                }
            return await api.capture_screenshot(rid, skin)
            
        elif action == "get_url":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter to get device URL"}],
                    "isError": True
                }
            url_response = await api.get_device_page_url(rid)
            
            # Extract URL and open browser
            device_url = None
            if isinstance(url_response, dict) and "content" in url_response:
                for content_item in url_response["content"]:
                    if "text" in content_item:
                        url_text = content_item["text"]
                        if "http" in url_text:
                            url_match = re.search(r'https?://[^\s]+', url_text)
                            if url_match:
                                device_url = url_match.group(0)
                            else:
                                device_url = url_text.strip()
                            break
            else:
                device_url = str(url_response).strip()
            
            if device_url and device_url.startswith('http'):
                webbrowser.open(device_url)
                logger.info(f"Opened device page URL in browser: {device_url}")
                return {
                    "content": [{"type": "text", "text": f"Device page opened in browser: {device_url}"}],
                    "isError": False
                }
            else:
                return {
                    "content": [{"type": "text", "text": f"Error: Invalid URL received: {device_url}"}],
                    "isError": True
                }
                
        elif action == "start_services":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter to start services"}],
                    "isError": True
                }
            result = await api.start_device_services(rid, start_device_logs, start_performance_data, start_session_recording)
            return result
            
        elif action == "adb":
            if not rid or not adb_command:
                return {
                    "content": [{"type": "text", "text": "Please specify both rid and adb_command parameters"}],
                    "isError": True
                }
            
            # Auto-detect platform if requested
            if platform.lower() == "auto":
                logger.info(f"Auto-detecting platform for device RID: {rid}")
                try:
                    detection_result = await api.detect_device_platform(rid)
                    detected_platform = detection_result.get("platform", "unknown")
                    logger.info(f"Auto-detected platform: {detected_platform}")
                    platform = detected_platform
                except Exception as detection_error:
                    logger.warning(f"Platform auto-detection failed: {str(detection_error)}, defaulting to android")
                    platform = "android"
            
            # Check if the platform is iOS and return error if so
            platform = platform.lower().strip()
            if platform == "ios":
                logger.warning(f"ADB command attempted on iOS device (RID: {rid})")
                return {
                    "content": [{
                        "type": "text",
                        "text": (
                            "❌ Error: ADB commands are only supported on Android devices. "
                            "The specified device appears to be iOS. ADB (Android Debug Bridge) "
                            "is an Android-specific tool and cannot be used with iOS devices."
                        )
                    }],
                    "isError": True                }
            
            # Validate ADB command format (basic validation)
            if not adb_command.strip():
                return {
                    "content": [{"type": "text", "text": "❌ Error: ADB command cannot be empty"}],
                    "isError": True
                }
            
            # IMPORTANT: Check for correct ADB command format
            if not adb_command.startswith("adb "):
                logger.warning(f"ADB command may be missing 'adb' prefix: {adb_command}")
                return {
                    "content": [{
                        "type": "text", 
                        "text": (
                            f"⚠️  Warning: ADB command should start with 'adb shell' or 'adb '.\n"
                            f"Received: '{adb_command}'\n\n"
                            f"✅ Correct format examples:\n"
                            f"  - 'adb shell dumpsys battery'\n"
                            f"  - 'adb shell getprop ro.build.version.release'\n"
                            f"  - 'adb shell pm list packages'\n\n"
                            f"❌ Incorrect format (will fail):\n"
                            f"  - 'shell dumpsys battery'\n"
                            f"  - 'dumpsys battery'\n"
                            f"  - 'getprop ro.build.version.release'\n\n"
                            f"Please use the complete ADB command format."
                        )
                    }],
                    "isError": True
                }
            
            # Execute the ADB command
            result = await api.execute_adb_command(rid, adb_command)
            
            # Handle the response format with detailed output
            if result.get("success", False):
                # Success case
                output = result.get("output", "[No output]")
                command = result.get("command", adb_command)
                status_code = result.get("status_code", 200)
                message = result.get("message", "success")
                output_source = result.get("output_source", "unknown")
                
                return {
                    "content": [
                        {"type": "text", "text": f"✅ ADB command executed successfully"},
                        {"type": "text", "text": f"📋 Command: {command}"},
                        {"type": "text", "text": f"📊 Status: {message} (Code: {status_code})"},
                        {"type": "text", "text": f"🔍 Output Source: {output_source}"},
                        {"type": "text", "text": f"📄 Output:\n{output}"}
                    ],
                    "isError": False
                }
            else:
                # Error case
                error = result.get("error", "Unknown error")
                command = result.get("command", adb_command)
                status_code = result.get("status_code", "Unknown")
                raw_response = result.get("raw_response", {})
                
                return {
                    "content": [
                        {"type": "text", "text": f"❌ ADB command failed: {error}"},
                        {"type": "text", "text": f"📋 Command: {command}"},
                        {"type": "text", "text": f"📊 Error Code: {status_code}"},
                        {"type": "text", "text": f"🔍 Raw Response: {json.dumps(raw_response, indent=2) if raw_response else 'None'}"}
                    ],
                    "isError": True
                }
                
        elif action == "wildnet":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter to start wildnet"}],
                    "isError": True
                }
            result = await api.start_wildnet(rid)
            return result
            
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown action: '{action}'. Available actions: screenshot, get_url, start_services, adb, wildnet"}],
                "isError": True
            }
            
    except Exception as e:
        logger.error(f"Error in device_control: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in device control: {str(e)}"}],
            "isError": True
        }

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
        # Auto-authenticate if not already authorized
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
            return await api.list_cloud_apps(limit, filter_type)
            
        elif action == "install":
            if not rid or not filename:
                return {
                    "content": [{"type": "text", "text": "Please specify both rid and filename parameters for installation"}],
                    "isError": True
                }            
            # Check if iOS app needs resigning (make check more flexible)
            if platform and platform.lower() == "ios":
                filename_lower = filename.lower()
                # Allow installation if file contains any variation of "resign" or if it's a demo/test app
                resign_indicators = ["resign", "resigned", "testmunk", "demo", "test"]
                is_resigned = any(indicator in filename_lower for indicator in resign_indicators)
                
                if not is_resigned:
                    return {
                        "content": [{"type": "text", "text": "For iOS apps, please resign the IPA before installing. Use the resign action first."}],
                        "isError": True
                    }
            
            install_result = await api.install_and_launch_app(rid, filename, grant_all_permissions, app_package_name)
            
            # Note: Browser opening is already handled in the API, no need to duplicate here
            return install_result
            
        elif action == "resign":
            if not filename:
                return {
                    "content": [{"type": "text", "text": "Please specify a filename parameter for IPA resigning"}],
                    "isError": True
                }
            result = await api.resign_ipa(filename, force_resign=force_resign)
            return result
            
        elif action == "download_cloud":
            if not filename:
                return {
                    "content": [{"type": "text", "text": "Please specify a filename parameter for cloud download"}],
                    "isError": True
                }
            file_content = await api.download_from_cloud(filename)
            temp_dir = tempfile.gettempdir()
            local_path = os.path.join(temp_dir, filename)
            with open(local_path, 'wb') as f:
                f.write(file_content)
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

@mcp.tool()
async def session_analytics(
    action: str,
    rid: str = "",
    filename: str = "",
    download_dir: str = ""
) -> Dict[str, Any]:
    """
    Session Data & Analytics Operations: download_session, list_performance
    
    Actions:
    - download_session: Download session data (rid="device_id", filename="optional_specific_file", download_dir="optional_directory")
    - list_performance: List performance data files (rid="device_id")
    """
    logger.info(f"Tool called: session_analytics with action={action}, rid={rid}, filename={filename}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
            
        if action == "download_session":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter for session data download"}],
                    "isError": True
                }
            
            # Validate download directory if provided
            if download_dir:
                try:
                    download_dir = os.path.abspath(download_dir)
                    project_root = os.path.abspath(os.getcwd())
                    if not download_dir.startswith(project_root):
                        return {
                            "content": [{"type": "text", "text": "Error: Download directory must be within the project directory for security"}],
                            "isError": True
                        }
                except Exception:
                    return {
                        "content": [{"type": "text", "text": "Error: Invalid download directory path"}],
                        "isError": True
                    }
            
            result = await api.download_session_data(rid, filename if filename else None, download_dir if download_dir else None)
            return result
            
        elif action == "list_performance":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter to list performance data"}],
                    "isError": True
                }
            result = await api.list_performance_data_files(rid)
            return result
            
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown action: '{action}'. Available actions: download_session, list_performance"}],
                "isError": True
            }
            
    except Exception as e:
        logger.error(f"Error in session_analytics: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in session analytics: {str(e)}"}],
            "isError": True
        }

# =============================================================================
# PCLOUDY MCP TOOLS - CATEGORY-BASED ARCHITECTURE
# =============================================================================
# 
# 🎯 4 SMART META-TOOLS (FastMCP Compatible)
# ├── device_management          - Device operations (list, book, release, detect_platform, set_location)
# ├── device_control             - Control & monitoring (screenshot, get_url, start_services, adb, wildnet)
# ├── file_app_management        - File/app operations (upload, list_apps, install, resign, download_cloud)
# └── session_analytics          - Session data & analytics (download_session, list_performance)
#
# 🔄 USAGE EXAMPLES:
# 
# 1. device_management(action="list", platform="android")
# 2. device_management(action="book", device_name="GalaxyS10", platform="android")
# 3. device_management(action="set_location", rid="123", latitude=48.8566, longitude=2.3522)
# 4. device_control(action="screenshot", rid="123")
# 5. device_control(action="adb", rid="123", adb_command="adb shell dumpsys battery", platform="auto")
# 6. file_app_management(action="upload", file_path="/path/to/app.apk")
# 7. file_app_management(action="install", rid="123", filename="app.apk")
# 8. session_analytics(action="download_session", rid="123")
#
# 🔧 ENHANCED ADB FEATURES:
# - Auto-platform detection (platform="auto")
# - iOS device protection (prevents ADB on iOS)
# - Enhanced error reporting with raw response data
# - Structured output with detailed troubleshooting info
# - Extended timeout (120s) for long-running commands
# - Command sanitization and validation
#
# 📱 PROVEN ADB COMMAND EXAMPLES (MUST include 'adb shell' prefix):
# - device_control(action="adb", rid="123", adb_command="adb shell dumpsys battery")
# - device_control(action="adb", rid="123", adb_command="adb shell getprop ro.build.version.release")
# - device_control(action="adb", rid="123", adb_command="adb shell getprop ro.product.model")
# - device_control(action="adb", rid="123", adb_command="adb shell pm list packages | head -10")
# - device_control(action="adb", rid="123", adb_command="adb shell cat /proc/meminfo | head -10")
# - device_control(action="adb", rid="123", adb_command="adb shell ps | head -15")
# - device_control(action="adb", rid="123", adb_command="adb shell date")
# - device_control(action="adb", rid="123", adb_command="adb shell ifconfig")
#
# ✅ All tools include auto-authentication and enhanced error handling
# ✅ Compatible with FastMCP framework (no **kwargs)
# ✅ Clean, intuitive category-based interface
# =============================================================================

# Run the server
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
