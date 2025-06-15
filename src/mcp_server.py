import os
import tempfile
import re
import webbrowser
import json
from typing import Dict, Any
from fastmcp import FastMCP
from config import Config, logger
from pcloudy_api import PCloudyAPI
import asyncio

# Initialize FastMCP server and PCloudyAPI
mcp = FastMCP("pcloudy_auth3.0")
api = PCloudyAPI()

# Use the system's temp directory for downloads
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "pcloudy_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# =============================================================================
# CATEGORY-BASED META-TOOLS
# =============================================================================

@mcp.tool()
async def device_management(action: str, **kwargs) -> Dict[str, Any]:
    """
    Device Management Operations: list, book, release, detect_platform, set_location
    
    Actions:
    - list: List available devices (platform="android"/"ios")
    - book: Book device (device_name="GalaxyS10", platform="android", auto_start_services=True)
    - release: Release device (rid="device_id")
    - detect_platform: Auto-detect device platform (rid="device_id")
    - set_location: Set device GPS coordinates (rid="device_id", latitude=48.8566, longitude=2.3522)
    """
    logger.info(f"Tool called: device_management with action={action}, kwargs={kwargs}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
            
        if action == "list":
            platform = kwargs.get("platform", Config.DEFAULT_PLATFORM)
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
            device_name = kwargs.get("device_name")
            platform = kwargs.get("platform", Config.DEFAULT_PLATFORM)
            auto_start_services = kwargs.get("auto_start_services", True)
            if not device_name:
                return {
                    "content": [{"type": "text", "text": "Error: device_name is required for booking"}],
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
            rid = kwargs.get("rid")
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Error: rid is required for release"}],
                    "isError": True
                }
            logger.info("Releasing device... This may take 10-20 seconds.")
            result = await api.release_device(rid, auto_download=False)
            return result
            
        elif action == "detect_platform":
            rid = kwargs.get("rid")
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Error: rid is required for platform detection"}],
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
            rid = kwargs.get("rid")
            latitude = kwargs.get("latitude")
            longitude = kwargs.get("longitude")
            if not all([rid, latitude is not None, longitude is not None]):
                return {
                    "content": [{"type": "text", "text": "Error: rid, latitude, and longitude are required for set_location"}],
                    "isError": True
                }
            if not rid.strip():
                return {
                    "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
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
                "content": [{"type": "text", "text": f"Error: Unknown action '{action}'. Available: list, book, release, detect_platform, set_location"}],
                "isError": True
            }
    except Exception as e:
        logger.error(f"Error in device_management: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in device_management: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def device_control(action: str, **kwargs) -> Dict[str, Any]:
    """
    Device Control & Monitoring Operations: screenshot, get_url, start_services, adb, wildnet
    
    Actions:
    - screenshot: Capture device screenshot (rid="device_id", skin=True)
    - get_url: Get device page URL and open in browser (rid="device_id")
    - start_services: Start device services (rid="device_id", start_device_logs=True, start_performance_data=True, start_session_recording=True)
    - adb: Execute ADB command on Android (rid="device_id", adb_command="logcat", platform="auto")
    - wildnet: Start wildnet features (rid="device_id")
    """
    logger.info(f"Tool called: device_control with action={action}, kwargs={kwargs}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
            
        if action == "screenshot":
            rid = kwargs.get("rid")
            skin = kwargs.get("skin", True)
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Error: rid is required for screenshot"}],
                    "isError": True
                }
            return await api.capture_screenshot(rid, skin)
            
        elif action == "get_url":
            rid = kwargs.get("rid")
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Error: rid is required for get_url"}],
                    "isError": True
                }
            url_response = await api.get_device_page_url(rid)
            
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
                logger.error(f"Invalid URL received: {device_url}")
                return {
                    "content": [{"type": "text", "text": f"Error: Invalid URL received: {device_url}"}],
                    "isError": True
                }
                
        elif action == "start_services":
            rid = kwargs.get("rid")
            start_device_logs = kwargs.get("start_device_logs", True)
            start_performance_data = kwargs.get("start_performance_data", True)
            start_session_recording = kwargs.get("start_session_recording", True)
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Error: rid is required for start_services"}],
                    "isError": True
                }
            if not rid.strip():
                return {
                    "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
                    "isError": True
                }
            result = await api.start_device_services(rid, start_device_logs, start_performance_data, start_session_recording)
            return result
            
        elif action == "adb":
            rid = kwargs.get("rid")
            adb_command = kwargs.get("adb_command")
            platform = kwargs.get("platform", "auto")
            if not all([rid, adb_command]):
                return {
                    "content": [{"type": "text", "text": "Error: rid and adb_command are required for adb"}],
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
                    "isError": True
                }
            
            # Validate ADB command format
            if not adb_command.strip():
                return {
                    "content": [{"type": "text", "text": "❌ Error: ADB command cannot be empty"}],
                    "isError": True
                }
            
            # Execute the ADB command
            result = await api.execute_adb_command(rid, adb_command)
            
            # Handle the response format
            if result.get("success", False):
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
            rid = kwargs.get("rid")
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Error: rid is required for wildnet"}],
                    "isError": True
                }
            if not rid.strip():
                return {
                    "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
                    "isError": True
                }
            result = await api.start_wildnet(rid)
            return result
        else:
            return {
                "content": [{"type": "text", "text": f"Error: Unknown action '{action}'. Available: screenshot, get_url, start_services, adb, wildnet"}],
                "isError": True
            }
    except Exception as e:
        logger.error(f"Error in device_control: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in device_control: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def file_app_management(action: str, **kwargs) -> Dict[str, Any]:
    """
    File & App Management Operations: upload, list_apps, install, resign, download_cloud
    
    Actions:
    - upload: Upload APK/IPA file (file_path="/path/to/app.apk", force_upload=False)
    - list_apps: List cloud apps (limit=10, filter_type="all")
    - install: Install and launch app (rid="device_id", filename="app.apk", grant_all_permissions=True, platform="android", app_package_name="com.example.app")
    - resign: Resign iOS IPA file (filename="app.ipa", force_resign=False)
    - download_cloud: Download file from cloud (filename="app.apk")
    """
    logger.info(f"Tool called: file_app_management with action={action}, kwargs={kwargs}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
            
        if action == "upload":
            file_path = kwargs.get("file_path")
            force_upload = kwargs.get("force_upload", False)
            if not file_path:
                return {
                    "content": [{"type": "text", "text": "Error: file_path is required for upload"}],
                    "isError": True
                }
            return await api.upload_file(file_path, force_upload=force_upload)
            
        elif action == "list_apps":
            limit = kwargs.get("limit", 10)
            filter_type = kwargs.get("filter_type", "all")
            return await api.list_cloud_apps(limit, filter_type)
            
        elif action == "install":
            rid = kwargs.get("rid")
            filename = kwargs.get("filename")
            grant_all_permissions = kwargs.get("grant_all_permissions", True)
            platform = kwargs.get("platform")
            app_package_name = kwargs.get("app_package_name")
            if not all([rid, filename]):
                return {
                    "content": [{"type": "text", "text": "Error: rid and filename are required for install"}],
                    "isError": True
                }
            
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
            
            # Install and launch the app
            install_result = await api.install_and_launch_app(rid, filename, grant_all_permissions, app_package_name)
            
            # If installation was successful, automatically open the device screen
            if not install_result.get("isError", True):
                try:
                    # Get the device page URL
                    url_response = await api.get_device_page_url(rid)
                    
                    # Extract URL from response
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
                    
                    if device_url and device_url.startswith('http'):
                        # Open the URL in the default browser
                        webbrowser.open(device_url)
                        logger.info(f"Opened device screen in browser: {device_url}")
                        
                        # Update the response to include browser opening info
                        original_content = install_result.get("content", [])
                        original_content.append({
                            "type": "text", 
                            "text": f"Device screen automatically opened in browser: {device_url}"
                        })
                        install_result["content"] = original_content
                    else:
                        logger.warning(f"Could not extract valid URL from response: {url_response}")
                        
                except Exception as url_error:
                    logger.warning(f"Failed to auto-open device screen: {str(url_error)}")
                    # Don't fail the entire operation if URL opening fails
                    original_content = install_result.get("content", [])
                    original_content.append({
                        "type": "text", 
                        "text": f"Note: Could not auto-open device screen (use get_device_page_url tool manually)"
                    })
                    install_result["content"] = original_content
            
            return install_result
            
        elif action == "resign":
            filename = kwargs.get("filename")
            force_resign = kwargs.get("force_resign", False)
            if not filename:
                return {
                    "content": [{"type": "text", "text": "Error: filename is required for resign"}],
                    "isError": True
                }
            
            result = await api.resign_ipa(filename, force_resign=force_resign)
            
            # Check if duplicate was detected
            if result.get("duplicate_detected"):
                return result
            
            # If successful resignation
            if not result.get("isError", True):
                resigned_file_reference = result.get("resigned_file")
                return {
                    "content": [{"type": "text", "text": f"IPA file '{filename}' has been resigned successfully. Use the download tool to retrieve the file if needed.", "file_reference": resigned_file_reference}],
                    "isError": False
                }
            else:
                return result
                
        elif action == "download_cloud":
            filename = kwargs.get("filename")
            if not filename:
                return {
                    "content": [{"type": "text", "text": "Error: filename is required for download_cloud"}],
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
                "content": [{"type": "text", "text": f"Error: Unknown action '{action}'. Available: upload, list_apps, install, resign, download_cloud"}],
                "isError": True
            }
    except Exception as e:
        logger.error(f"Error in file_app_management: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in file_app_management: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def session_analytics(action: str, **kwargs) -> Dict[str, Any]:
    """
    Session Data & Analytics Operations: download_session, list_performance
    
    Actions:
    - download_session: Download session data (rid="device_id", filename="optional_specific_file", download_dir="optional_directory")
    - list_performance: List performance data files (rid="device_id")
    """
    logger.info(f"Tool called: session_analytics with action={action}, kwargs={kwargs}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
            
        if action == "download_session":
            rid = kwargs.get("rid")
            filename = kwargs.get("filename")
            download_dir = kwargs.get("download_dir")
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Error: rid is required for download_session"}],
                    "isError": True
                }
            if not rid.strip():
                return {
                    "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
                    "isError": True
                }
            
            # Validate download directory path if provided
            if download_dir:
                try:
                    download_dir = os.path.abspath(download_dir)
                    # Ensure we're not writing outside the project directory for security
                    project_root = os.path.abspath(os.getcwd())
                    if not download_dir.startswith(project_root):
                        return {
                            "content": [{"type": "text", "text": "Error: Download directory must be within the project directory for security"}],
                            "isError": True
                        }
                except Exception as path_error:
                    return {
                        "content": [{"type": "text", "text": f"Error: Invalid download directory path: {str(path_error)}"}],
                        "isError": True
                    }
            
            # Call the merged API function
            result = await api.download_session_data(rid, filename, download_dir)
            return result
            
        elif action == "list_performance":
            rid = kwargs.get("rid")
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Error: rid is required for list_performance"}],
                    "isError": True
                }
            if not rid.strip():
                return {
                    "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
                    "isError": True
                }
            result = await api.list_performance_data_files(rid)
            return result
        else:
            return {
                "content": [{"type": "text", "text": f"Error: Unknown action '{action}'. Available: download_session, list_performance"}],
                "isError": True
            }
    except Exception as e:
        logger.error(f"Error in session_analytics: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in session_analytics: {str(e)}"}],
            "isError": True
        }

# =============================================================================
# CATEGORY-BASED MCP TOOLS DOCUMENTATION
# =============================================================================
# 
# 🎯 STREAMLINED TOOL ARCHITECTURE (4 META-TOOLS)
# ├── device_management       - Device lifecycle: list, book, release, detect, locate
# ├── device_control          - Device interaction: screenshot, URL, services, ADB, wildnet
# ├── file_app_management     - App lifecycle: upload, list, install, resign, download
# └── session_analytics       - Data collection: download sessions, performance metrics
#
# 📋 USAGE EXAMPLES:
#
# 🔄 Complete Testing Workflow:
# 1. device_management(action="list", platform="android")
# 2. device_management(action="book", device_name="GalaxyS10") 
# 3. device_management(action="set_location", rid="123", latitude=48.8566, longitude=2.3522)
# 4. file_app_management(action="install", rid="123", filename="MyApp.apk")
# 5. device_control(action="screenshot", rid="123")
# 6. session_analytics(action="download_session", rid="123")
# 7. device_management(action="release", rid="123")
#
# 📱 iOS App Testing:
# 1. file_app_management(action="upload", file_path="MyApp.ipa")
# 2. file_app_management(action="resign", filename="MyApp.ipa") 
# 3. device_management(action="book", device_name="iPhone", platform="ios")
# 4. file_app_management(action="install", rid="123", filename="MyApp_resign.ipa")
#
# 🐛 Android Debugging:
# 1. device_management(action="book", device_name="Pixel")
# 2. device_control(action="adb", rid="123", adb_command="logcat")
# 3. session_analytics(action="list_performance", rid="123")
# 4. session_analytics(action="download_session", rid="123", filename="specific_log.txt")
#
# ✅ BENEFITS OF CATEGORY-BASED APPROACH:
# - Simplified interface: 4 tools instead of 17
# - Logical grouping: Related operations under single tool
# - Intelligent routing: System selects correct method based on action
# - Cleaner documentation: Easier to understand and maintain
# - Better user experience: Less tool discovery, more focused workflows
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
