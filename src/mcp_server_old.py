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
    """List available devices for the specified platform (android or ios)."""
    logger.info(f"Tool called: list_available_devices with platform={platform}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
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
async def book_device_by_name(device_name: str, platform: str = Config.DEFAULT_PLATFORM, auto_start_services: bool = True) -> Dict[str, Any]:
    """
    Book a device matching the provided device name for the specified platform.
    Automatically starts device services.
    
    Parameters:
    - device_name: Name or partial name of the device to book
    - platform: Platform (android or ios)
    - auto_start_services: Automatically start device logs, performance data, and session recording (default: True)
    """
    logger.info(f"Tool called: book_device_by_name with device_name={device_name}, platform={platform}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
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
          # Book device with enhanced features
        booking = await api.book_device(selected["id"], auto_start_services=auto_start_services)
        api.rid = booking.get("rid")
        if not api.rid:
            return {
                "content": [{"type": "text", "text": "Failed to get booking ID"}],
                "isError": True
            }
        
        # Use enhanced response content if available
        enhanced_content = booking.get("enhanced_content")
        if enhanced_content:
            logger.info(f"Device '{selected['model']}' booked successfully with enhanced features. RID: {api.rid}")
            return {
                "content": enhanced_content,
                "isError": False
            }
        else:
            # Fallback to basic response
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
    """
    Release a booked device. This operation may take 10-20 seconds to complete.
    
    After release, the user will be prompted about available session data files and given
    the option to download them manually using the 'download_session_data' tool.
    """
    logger.info(f"Tool called: release_device with rid={rid}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        
        # The API method handles timeout and response parsing internally
        # Note: This operation typically takes 10-20 seconds to complete
        logger.info("Releasing device... This may take 10-20 seconds.")
        
        # Always call with auto_download=False to ensure user is prompted
        result = await api.release_device(rid, auto_download=False)
        
        return result
        
    except Exception as e:
        logger.error(f"Error releasing device: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error releasing device: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def upload_file(file_path: str, force_upload: bool = False) -> Dict[str, Any]:
    """
    Upload an APK, IPA, or ZIP file to pCloudy cloud drive.
    
    Parameters:
    - file_path: Path to the file to upload
    - force_upload: If True, upload even if a file with the same name already exists (default: False)
    """
    logger.info(f"Tool called: upload_file for {file_path}, force_upload={force_upload}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        return await api.upload_file(file_path, force_upload=force_upload)
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
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        return await api.capture_screenshot(rid, skin)
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error capturing screenshot: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def set_device_location(rid: str, latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Set GPS coordinates for a device.
    
    Parameters:
    - rid: Device RID
    - latitude: Latitude coordinate (e.g., 48.8566 for Paris)
    - longitude: Longitude coordinate (e.g., 2.3522 for Paris)
    """
    logger.info(f"Tool called: set_device_location with rid={rid}, lat={latitude}, lon={longitude}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        
        # Validate RID format (basic validation)
        if not rid.strip():
            return {
                "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
                "isError": True
            }
        
        # Validate latitude range
        if not (-90 <= latitude <= 90):
            return {
                "content": [{"type": "text", "text": "Error: Latitude must be between -90 and 90 degrees"}],
                "isError": True
            }
        
        # Validate longitude range  
        if not (-180 <= longitude <= 180):
            return {
                "content": [{"type": "text", "text": "Error: Longitude must be between -180 and 180 degrees"}],
                "isError": True
            }
        
        result = await api.set_device_location(rid, latitude, longitude)
        return result
        
    except Exception as e:
        logger.error(f"Error setting device location: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error setting device location: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def download_from_cloud(filename: str) -> Dict[str, Any]:
    """Download a file from the pCloudy cloud drive and save it in the system temp folder."""
    logger.info(f"Tool called: download_from_cloud with filename={filename}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
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
async def download_session_data(rid: str, filename: str = None, download_dir: str = None) -> Dict[str, Any]:
    """
    Download session data files. Can download a specific file or all available files.
    
    Parameters:
    - rid: Device RID (required)
    - filename: Specific file to download (optional). If not provided, downloads all files
    - download_dir: Directory to save files (optional). If not provided, uses temp directory
    
    This tool replaces both download_manual_access_data and download_all_session_data.
    """
    logger.info(f"Tool called: download_session_data with rid={rid}, filename={filename}, download_dir={download_dir}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        
        # Validate RID format (basic validation)
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
        
    except Exception as e:
        logger.error(f"Error downloading session data: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error downloading session data: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def get_device_page_url(rid: str) -> Dict[str, Any]:
    """Get the URL for a device page and automatically open it in the default browser."""
    logger.info(f"Tool called: get_device_page_url with rid={rid}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        
        # Get the device page URL
        url_response = await api.get_device_page_url(rid)
        
        # Extract URL from response
        if isinstance(url_response, dict) and "content" in url_response:
            # If the response has content, try to extract URL from it
            for content_item in url_response["content"]:
                if "text" in content_item:
                    url_text = content_item["text"]
                    # Look for URL in the text
                    if "http" in url_text:
                        # Extract URL (assuming it's the full text or contains the URL)
                        import re
                        url_match = re.search(r'https?://[^\s]+', url_text)
                        if url_match:
                            device_url = url_match.group(0)
                        else:
                            device_url = url_text.strip()
                        break
            else:
                device_url = None
        else:
            # If response is a string URL directly
            device_url = str(url_response).strip()
        
        if device_url and device_url.startswith('http'):
            # Open the URL in the default browser
            import webbrowser
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
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        return await api.list_cloud_apps(limit, filter_type)
    except Exception as e:
        logger.error(f"Error listing cloud apps: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error listing cloud apps: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def install_and_launch_app(rid: str, filename: str, grant_all_permissions: bool = True, platform: str = None, app_package_name: str = None) -> Dict[str, Any]:
    """
    Install and launch an app on a device and automatically open the device screen in browser.
    If platform is 'ios' and the filename does not contain 'resign', advise the client to resign the app first.
    
    Parameters:
    - rid: Device RID to install the app on
    - filename: Name of the app file to install (must be uploaded to pCloudy first)
    - grant_all_permissions: Whether to grant all permissions during installation (default: True)
    - platform: Platform hint for better guidance (optional)
    - app_package_name: Package name for performance monitoring (optional, e.g., 'com.example.app')
    """
    logger.info(f"Tool called: install_and_launch_app with rid={rid}, filename={filename}, platform={platform}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
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
        
    except Exception as e:
        logger.error(f"Error installing and launching app: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error installing and launching app: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def resign_ipa(filename: str, force_resign: bool = False) -> Dict[str, Any]:
    """
    Resign an IPA file and return a reference to the resigned file.
    
    Parameters:
    - filename: Name of the IPA file to resign (must be uploaded to pCloudy first)
    - force_resign: If True, resign even if a resigned version already exists (default: False)
    """
    logger.info(f"Tool called: resign_ipa with filename={filename}, force_resign={force_resign}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        
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
            
    except Exception as e:
        logger.error(f"Error resigning IPA: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error resigning IPA: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def execute_adb_command(rid: str, adb_command: str, platform: str = "auto") -> Dict[str, Any]:
    """
    Execute an ADB command on an Android device. 
    This tool only works with Android devices. For iOS devices, it will return an error.
    If platform is set to 'auto', the system will attempt to detect the device platform automatically.
    """
    logger.info(f"Tool called: execute_adb_command with rid={rid}, adb_command={adb_command}, platform={platform}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        
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
        
        # Validate ADB command format (basic validation)
        if not adb_command.strip():
            return {
                "content": [{"type": "text", "text": "❌ Error: ADB command cannot be empty"}],
                "isError": True
            }
        
        # Execute the ADB command
        result = await api.execute_adb_command(rid, adb_command)
        
        # Handle the new response format
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
        
    except Exception as e:
        logger.error(f"Error executing ADB command: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"❌ Error executing ADB command: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def list_performance_data_files(rid: str) -> Dict[str, Any]:
    """
    List all performance data files for a device.
    This includes CPU usage, memory consumption, and other performance metrics collected during app testing.
    """
    logger.info(f"Tool called: list_performance_data_files with rid={rid}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        
        # Validate RID format (basic validation)
        if not rid.strip():
            return {
                "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
                "isError": True
            }
        
        # List performance data files
        result = await api.list_performance_data_files(rid)
        return result
        
    except Exception as e:
        logger.error(f"Error listing performance data files: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error listing performance data files: {str(e)}"}],
            "isError": True        }

@mcp.tool()
async def detect_device_platform(rid: str) -> Dict[str, Any]:
    """
    Auto-detect the platform (Android/iOS) of a booked device.
    This is useful for determining compatibility with platform-specific operations like ADB commands.
    """
    logger.info(f"Tool called: detect_device_platform with rid={rid}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        
        # Validate RID format (basic validation)
        if not rid.strip():
            return {
                "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
                "isError": True
            }
        
        # Detect platform
        result = await api.detect_device_platform(rid)
        return result
        
    except Exception as e:
        logger.error(f"Error detecting device platform: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error detecting device platform: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def start_device_services(rid: str, start_device_logs: bool = True, start_performance_data: bool = True, start_session_recording: bool = True) -> Dict[str, Any]:
    """
    Start device services for logging, performance monitoring, and session recording.
    This is automatically called when booking a device, but can be used manually if needed.
    
    Note: Performance data is collected for all apps running on the device automatically.
    
    Parameters:
    - rid: Device RID
    - start_device_logs: Enable device logs collection (default: True)  
    - start_performance_data: Enable performance data collection for all apps (default: True)
    - start_session_recording: Enable session recording (default: True)
    """
    logger.info(f"Tool called: start_device_services with rid={rid}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        
        # Validate RID format (basic validation)
        if not rid.strip():
            return {
                "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
                "isError": True
            }
          # Start device services
        result = await api.start_device_services(rid, start_device_logs, start_performance_data, start_session_recording)
        logger.info(f"Device services result type: {type(result)}")
        logger.info(f"Device services result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error starting device services: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error starting device services: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def start_wildnet(rid: str) -> Dict[str, Any]:
    """
    Start wildnet feature for a booked device.
    Wildnet provides enhanced network capabilities for device testing.
    
    Parameters:
    - rid: Device RID (booking ID)
    """
    logger.info(f"Tool called: start_wildnet with rid={rid}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        
        # Validate RID format (basic validation)
        if not rid.strip():
            return {
                "content": [{"type": "text", "text": "Error: Device RID cannot be empty"}],
                "isError": True
            }
        
        # Start wildnet
        result = await api.start_wildnet(rid)
        return result
        
    except Exception as e:
        logger.error(f"Error starting wildnet: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error starting wildnet: {str(e)}"}],
            "isError": True
        }

# =============================================================================
# CATEGORY-BASED META-TOOLS
# These tools provide intelligent routing based on user intent and category
# =============================================================================

@mcp.tool()
async def device_management(action: str, **kwargs) -> Dict[str, Any]:
    """
    Smart device management tool that routes to the appropriate device operation based on user intent.
    
    Parameters:
    - action: What you want to do with devices. Examples:
      * "list android devices" / "show available ios devices" -> list_available_devices
      * "book galaxy s10" / "get iphone 12" -> book_device_by_name  
      * "release device 12345" / "free up device" -> release_device
      * "detect platform 12345" / "what platform is device" -> detect_device_platform
      * "set location paris" / "gps coordinates 48.8566,2.3522" -> set_device_location
    - **kwargs: Additional parameters extracted from the action string or provided separately
    """
    logger.info(f"Meta-tool called: device_management with action='{action}', kwargs={kwargs}")
    
    try:
        action_lower = action.lower().strip()
        
        # Parse action and route to appropriate tool
        if any(word in action_lower for word in ["list", "show", "available", "devices"]):
            # Extract platform from action
            platform = "android"  # default
            if "ios" in action_lower or "iphone" in action_lower:
                platform = "ios"
            elif "android" in action_lower:
                platform = "android"
            return await list_available_devices(platform=platform)
            
        elif any(word in action_lower for word in ["book", "get", "reserve", "take"]):
            # Extract device name from action
            device_name = kwargs.get("device_name")
            platform = kwargs.get("platform", "android")
            
            if not device_name:
                # Try to extract device name from action string
                import re
                # Look for device patterns
                device_patterns = [
                    r"book\s+([a-zA-Z0-9\s]+?)(?:\s|$)",
                    r"get\s+([a-zA-Z0-9\s]+?)(?:\s|$)", 
                    r"reserve\s+([a-zA-Z0-9\s]+?)(?:\s|$)"
                ]
                for pattern in device_patterns:
                    match = re.search(pattern, action_lower)
                    if match:
                        device_name = match.group(1).strip()
                        break
                        
            if not device_name:
                return {
                    "content": [{"type": "text", "text": "Please specify a device name. Example: 'book galaxy s10' or provide device_name parameter"}],
                    "isError": True
                }
                
            # Detect platform from device name if not specified
            if "iphone" in device_name.lower() or "ios" in action_lower:
                platform = "ios"
            
            return await book_device_by_name(device_name=device_name, platform=platform)
            
        elif any(word in action_lower for word in ["release", "free", "return", "end"]):
            # Extract RID from action or kwargs
            rid = kwargs.get("rid")
            if not rid:
                # Try to extract RID from action string
                import re
                rid_match = re.search(r"(?:device|rid)\s*([a-zA-Z0-9-]+)", action_lower)
                if rid_match:
                    rid = rid_match.group(1)
                    
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a device RID. Example: 'release device 12345' or provide rid parameter"}],
                    "isError": True
                }
                
            return await release_device(rid=rid)
            
        elif any(word in action_lower for word in ["detect", "platform", "what"]):
            # Extract RID from action or kwargs
            rid = kwargs.get("rid")
            if not rid:
                import re
                rid_match = re.search(r"(?:device|rid|platform)\s*([a-zA-Z0-9-]+)", action_lower)
                if rid_match:
                    rid = rid_match.group(1)
                    
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a device RID. Example: 'detect platform 12345' or provide rid parameter"}],
                    "isError": True
                }
                
            return await detect_device_platform(rid=rid)
            
        elif any(word in action_lower for word in ["location", "gps", "coordinates", "lat", "lon"]):
            # Extract RID and coordinates
            rid = kwargs.get("rid")
            latitude = kwargs.get("latitude")
            longitude = kwargs.get("longitude")
            
            if not rid:
                import re
                rid_match = re.search(r"(?:device|rid)\s*([a-zA-Z0-9-]+)", action_lower)
                if rid_match:
                    rid = rid_match.group(1)
                    
            # Try to extract coordinates from action string
            if latitude is None or longitude is None:
                import re
                coord_patterns = [
                    r"(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)",  # "48.8566,2.3522"
                    r"lat[:\s]*(-?\d+\.?\d*)\s+lon[:\s]*(-?\d+\.?\d*)",  # "lat: 48.8566 lon: 2.3522"
                    r"(\d+\.?\d*)\s+(\d+\.?\d*)"  # "48.8566 2.3522"
                ]
                for pattern in coord_patterns:
                    match = re.search(pattern, action_lower)
                    if match:
                        latitude = float(match.group(1))
                        longitude = float(match.group(2))
                        break
                        
                # Handle city names
                if latitude is None and longitude is None:
                    city_coords = {
                        "paris": (48.8566, 2.3522),
                        "london": (51.5074, -0.1278),
                        "newyork": (40.7128, -74.0060),
                        "tokyo": (35.6762, 139.6503),
                        "bangalore": (12.9716, 77.5946),
                        "mumbai": (19.0760, 72.8777)
                    }
                    for city, coords in city_coords.items():
                        if city in action_lower:
                            latitude, longitude = coords
                            break
                            
            if not rid or latitude is None or longitude is None:
                return {
                    "content": [{"type": "text", "text": "Please specify RID and coordinates. Example: 'set location device 12345 paris' or 'gps 12345 48.8566,2.3522'"}],
                    "isError": True
                }
                
            return await set_device_location(rid=rid, latitude=latitude, longitude=longitude)
            
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown device management action: '{action}'. Available actions: list, book, release, detect, location"}],
                "isError": True
            }
            
    except Exception as e:
        logger.error(f"Error in device_management meta-tool: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in device management: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def device_control(action: str, **kwargs) -> Dict[str, Any]:
    """
    Smart device control tool for monitoring and interaction operations.
    
    Parameters:
    - action: What you want to do with device control. Examples:
      * "screenshot device 12345" / "capture screen" -> capture_device_screenshot
      * "open device page 12345" / "show device screen" -> get_device_page_url
      * "start services 12345" / "enable monitoring" -> start_device_services
      * "adb logcat" / "run adb shell" -> execute_adb_command
      * "start wildnet 12345" / "enable network" -> start_wildnet
    - **kwargs: Additional parameters (rid, adb_command, etc.)
    """
    logger.info(f"Meta-tool called: device_control with action='{action}', kwargs={kwargs}")
    
    try:
        action_lower = action.lower().strip()
        
        if any(word in action_lower for word in ["screenshot", "capture", "screen", "image"]):
            rid = kwargs.get("rid")
            skin = kwargs.get("skin", True)
            
            if not rid:
                import re
                rid_match = re.search(r"(?:device|rid)\s*([a-zA-Z0-9-]+)", action_lower)
                if rid_match:
                    rid = rid_match.group(1)
                    
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a device RID. Example: 'screenshot device 12345'"}],
                    "isError": True
                }
                
            return await capture_device_screenshot(rid=rid, skin=skin)
            
        elif any(word in action_lower for word in ["open", "show", "page", "url", "browser"]):
            rid = kwargs.get("rid")
            
            if not rid:
                import re
                rid_match = re.search(r"(?:device|rid)\s*([a-zA-Z0-9-]+)", action_lower)
                if rid_match:
                    rid = rid_match.group(1)
                    
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a device RID. Example: 'open device page 12345'"}],
                    "isError": True
                }
                
            return await get_device_page_url(rid=rid)
            
        elif any(word in action_lower for word in ["start", "services", "monitoring", "logs"]):
            rid = kwargs.get("rid")
            
            if not rid:
                import re
                rid_match = re.search(r"(?:device|rid)\s*([a-zA-Z0-9-]+)", action_lower)
                if rid_match:
                    rid = rid_match.group(1)
                    
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a device RID. Example: 'start services 12345'"}],
                    "isError": True
                }
                
            return await start_device_services(rid=rid)
            
        elif any(word in action_lower for word in ["adb", "shell", "logcat", "command"]):
            rid = kwargs.get("rid")
            adb_command = kwargs.get("adb_command")
            
            if not adb_command:
                # Extract ADB command from action
                import re
                adb_match = re.search(r"adb\s+(.+?)(?:\s+(?:device|rid)|$)", action_lower)
                if adb_match:
                    adb_command = adb_match.group(1).strip()
                    
            if not rid:
                import re
                rid_match = re.search(r"(?:device|rid)\s*([a-zA-Z0-9-]+)", action_lower)
                if rid_match:
                    rid = rid_match.group(1)
                    
            if not rid or not adb_command:
                return {
                    "content": [{"type": "text", "text": "Please specify RID and ADB command. Example: 'adb logcat device 12345' or provide rid and adb_command parameters"}],
                    "isError": True
                }
                
            return await execute_adb_command(rid=rid, adb_command=adb_command)
            
        elif any(word in action_lower for word in ["wildnet", "network", "enhanced"]):
            rid = kwargs.get("rid")
            
            if not rid:
                import re
                rid_match = re.search(r"(?:device|rid)\s*([a-zA-Z0-9-]+)", action_lower)
                if rid_match:
                    rid = rid_match.group(1)
                    
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a device RID. Example: 'start wildnet 12345'"}],
                    "isError": True
                }
                
            return await start_wildnet(rid=rid)
            
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown device control action: '{action}'. Available actions: screenshot, open, services, adb, wildnet"}],
                "isError": True
            }
            
    except Exception as e:
        logger.error(f"Error in device_control meta-tool: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in device control: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def file_and_app_management(action: str, **kwargs) -> Dict[str, Any]:
    """
    Smart file and app management tool for upload, download, and app operations.
    
    Parameters:
    - action: What you want to do with files/apps. Examples:
      * "upload MyApp.apk" / "upload file /path/to/app.ipa" -> upload_file
      * "list apps" / "show cloud apps" -> list_cloud_apps
      * "install MyApp.apk on 12345" / "launch app" -> install_and_launch_app
      * "resign MyApp.ipa" / "sign ios app" -> resign_ipa
      * "download MyFile.zip" / "get cloud file" -> download_from_cloud
    - **kwargs: Additional parameters (file_path, filename, rid, etc.)
    """
    logger.info(f"Meta-tool called: file_and_app_management with action='{action}', kwargs={kwargs}")
    
    try:
        action_lower = action.lower().strip()
        
        if any(word in action_lower for word in ["upload", "send", "put"]):
            file_path = kwargs.get("file_path")
            force_upload = kwargs.get("force_upload", False)
            
            if not file_path:
                # Try to extract file path from action
                import re
                file_match = re.search(r"upload\s+([^\s]+)", action_lower)
                if file_match:
                    file_path = file_match.group(1)
                    
            if not file_path:
                return {
                    "content": [{"type": "text", "text": "Please specify a file path. Example: 'upload MyApp.apk' or provide file_path parameter"}],
                    "isError": True
                }
                
            return await upload_file(file_path=file_path, force_upload=force_upload)
            
        elif any(word in action_lower for word in ["list", "show", "apps", "cloud"]):
            limit = kwargs.get("limit", 10)
            filter_type = kwargs.get("filter_type", "all")
            
            return await list_cloud_apps(limit=limit, filter_type=filter_type)
            
        elif any(word in action_lower for word in ["install", "launch", "run", "start"]):
            rid = kwargs.get("rid")
            filename = kwargs.get("filename")
            grant_all_permissions = kwargs.get("grant_all_permissions", True)
            platform = kwargs.get("platform")
            
            if not filename:
                # Try to extract filename from action
                import re
                file_match = re.search(r"(?:install|launch)\s+([^\s]+)", action_lower)
                if file_match:
                    filename = file_match.group(1)
                    
            if not rid:
                # Try to extract RID from action
                import re
                rid_match = re.search(r"(?:on|device|rid)\s*([a-zA-Z0-9-]+)", action_lower)
                if rid_match:
                    rid = rid_match.group(1)
                    
            if not rid or not filename:
                return {
                    "content": [{"type": "text", "text": "Please specify RID and filename. Example: 'install MyApp.apk on device 12345'"}],
                    "isError": True
                }
                
            return await install_and_launch_app(rid=rid, filename=filename, grant_all_permissions=grant_all_permissions, platform=platform)
            
        elif any(word in action_lower for word in ["resign", "sign", "ios", "ipa"]):
            filename = kwargs.get("filename")
            force_resign = kwargs.get("force_resign", False)
            
            if not filename:
                # Try to extract filename from action
                import re
                file_match = re.search(r"(?:resign|sign)\s+([^\s]+)", action_lower)
                if file_match:
                    filename = file_match.group(1)
                    
            if not filename:
                return {
                    "content": [{"type": "text", "text": "Please specify an IPA filename. Example: 'resign MyApp.ipa'"}],
                    "isError": True
                }
                
            return await resign_ipa(filename=filename, force_resign=force_resign)
            
        elif any(word in action_lower for word in ["download", "get", "fetch"]):
            filename = kwargs.get("filename")
            
            if not filename:
                # Try to extract filename from action
                import re
                file_match = re.search(r"(?:download|get|fetch)\s+([^\s]+)", action_lower)
                if file_match:
                    filename = file_match.group(1)
                    
            if not filename:
                return {
                    "content": [{"type": "text", "text": "Please specify a filename. Example: 'download MyFile.zip'"}],
                    "isError": True
                }
                
            return await download_from_cloud(filename=filename)
            
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown file/app action: '{action}'. Available actions: upload, list, install, resign, download"}],
                "isError": True
            }
            
    except Exception as e:
        logger.error(f"Error in file_and_app_management meta-tool: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in file and app management: {str(e)}"}],
            "isError": True
        }

@mcp.tool()
async def session_data_analytics(action: str, **kwargs) -> Dict[str, Any]:
    """
    Smart session data and analytics tool for performance monitoring and data retrieval.
    
    Parameters:
    - action: What you want to do with session data. Examples:
      * "download session data 12345" / "get all logs" -> download_session_data
      * "list performance files 12345" / "show metrics" -> list_performance_data_files
      * "download specific log.txt from 12345" -> download_session_data with filename
    - **kwargs: Additional parameters (rid, filename, download_dir, etc.)
    """
    logger.info(f"Meta-tool called: session_data_analytics with action='{action}', kwargs={kwargs}")
    
    try:
        action_lower = action.lower().strip()
        
        if any(word in action_lower for word in ["download", "get", "fetch", "session", "data", "logs"]):
            rid = kwargs.get("rid")
            filename = kwargs.get("filename")
            download_dir = kwargs.get("download_dir")
            
            if not rid:
                # Try to extract RID from action
                import re
                rid_match = re.search(r"(?:device|rid|from)\s*([a-zA-Z0-9-]+)", action_lower)
                if rid_match:
                    rid = rid_match.group(1)
                    
            # Try to extract specific filename if mentioned
            if not filename:
                import re
                file_match = re.search(r"(?:specific|file)\s+([^\s]+)", action_lower)
                if file_match:
                    filename = file_match.group(1)
                    
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a device RID. Example: 'download session data 12345'"}],
                    "isError": True
                }
                
            return await download_session_data(rid=rid, filename=filename, download_dir=download_dir)
            
        elif any(word in action_lower for word in ["list", "show", "performance", "metrics", "files"]):
            rid = kwargs.get("rid")
            
            if not rid:
                # Try to extract RID from action
                import re
                rid_match = re.search(r"(?:device|rid|files)\s*([a-zA-Z0-9-]+)", action_lower)
                if rid_match:
                    rid = rid_match.group(1)
                    
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a device RID. Example: 'list performance files 12345'"}],
                    "isError": True
                }
                
            return await list_performance_data_files(rid=rid)
            
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown session data action: '{action}'. Available actions: download, list"}],
                "isError": True
            }
            
    except Exception as e:
        logger.error(f"Error in session_data_analytics meta-tool: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in session data analytics: {str(e)}"}],
            "isError": True
        }

# =============================================================================
# ORIGINAL INDIVIDUAL TOOLS (maintained for direct access if needed)
# =============================================================================

# =============================================================================
# PCLOUDY MCP TOOLS CATEGORIZATION - SMART META-TOOLS + INDIVIDUAL TOOLS
# =============================================================================
# 
# 🧠 SMART META-TOOLS (4 category-based tools with natural language routing)
# ├── device_management          - Smart routing for all device operations
# ├── device_control             - Smart routing for device control & monitoring  
# ├── file_and_app_management    - Smart routing for file/app operations
# └── session_data_analytics     - Smart routing for session data & analytics
#
# 📱 DEVICE MANAGEMENT (5 individual tools)
# ├── list_available_devices      - List available devices for android/ios platform
# ├── book_device_by_name         - Book a device by name with auto-service startup  
# ├── release_device              - Release a booked device with session data prompts
# ├── detect_device_platform      - Auto-detect if device is Android or iOS
# └── set_device_location         - Set GPS coordinates for location-based testing
#
# 📸 DEVICE CONTROL & MONITORING (5 individual tools)
# ├── capture_device_screenshot   - Take screenshot with optional device skin
# ├── get_device_page_url         - Get device page URL and open in browser
# ├── start_device_services       - Start logs, performance data, session recording
# ├── execute_adb_command         - Execute ADB commands on Android devices
# └── start_wildnet               - Enable enhanced network capabilities
#
# 📦 FILE & APP MANAGEMENT (5 individual tools)
# ├── upload_file                 - Upload APK/IPA files to pCloudy cloud drive
# ├── list_cloud_apps             - List apps available in cloud drive
# ├── install_and_launch_app      - Install app + auto-open device in browser
# ├── resign_ipa                  - Resign iOS IPA files for installation
# └── download_from_cloud         - Download files from pCloudy cloud storage
#
# 📊 SESSION DATA & ANALYTICS (2 individual tools)
# ├── download_session_data       - Download session files (single/bulk)
# └── list_performance_data_files - List performance metrics and logs
#
# 🎯 TOTAL: 4 META-TOOLS + 17 INDIVIDUAL TOOLS = 21 TOOLS
# =============================================================================
# 
# 🧠 SMART META-TOOL EXAMPLES:
# 
# 🔄 Natural Language Usage with Meta-Tools:
# 1. device_management(action="list android devices")
# 2. device_management(action="book galaxy s10")
# 3. device_management(action="set location device 12345 paris")
# 4. device_control(action="screenshot device 12345")
# 5. device_control(action="adb logcat device 12345")
# 6. file_and_app_management(action="upload MyApp.apk")
# 7. file_and_app_management(action="install MyApp.apk on device 12345")
# 8. session_data_analytics(action="download session data 12345")
#
# 🎯 Traditional Workflow (using individual tools):
# 1. list_available_devices(platform="android")
# 2. book_device_by_name(device_name="GalaxyS10") 
# 3. set_device_location(rid="123", latitude=48.8566, longitude=2.3522)
# 4. install_and_launch_app(rid="123", filename="MyApp.apk")
# 5. capture_device_screenshot(rid="123")
# 6. download_session_data(rid="123")
# 7. release_device(rid="123")
#
# 📱 iOS App Testing with Meta-Tools:
# 1. file_and_app_management(action="upload MyApp.ipa")
# 2. file_and_app_management(action="resign MyApp.ipa") 
# 3. device_management(action="book iPhone 12", platform="ios")
# 4. file_and_app_management(action="install MyApp_resign.ipa on device 123")
#
# 🐛 Android Debugging with Meta-Tools:
# 1. device_management(action="book Pixel device")
# 2. device_control(action="adb logcat device 123")
# 3. session_data_analytics(action="list performance files 123")
# 4. session_data_analytics(action="download specific log.txt from 123")
# =============================================================================

# IMPORTANT NOTES:
# - Meta-tools provide intelligent natural language routing to individual tools
# - Individual tools remain available for direct, precise control
# - Users can choose between conversational (meta-tools) or programmatic (individual) interfaces
# - All tools include auto-authentication and enhanced error handling