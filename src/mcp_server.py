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
mcp = FastMCP("pcloudy_auth3.0", description="MCP server for pCloudy device authentication, booking, releasing, file operations and resigning")
api = PCloudyAPI()

# Use the system's temp directory for downloads
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "pcloudy_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@mcp.tool()
async def list_available_devices(platform: str = Config.DEFAULT_PLATFORM) -> Dict[str, Any]:
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
    the option to download them manually using the 'download_all_session_data' tool.
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
async def download_manual_access_data(rid: str, filename: str) -> Dict[str, Any]:
    """Download a file using the download_manual_access_data API and save it in the system temp folder."""
    logger.info(f"Tool called: download_manual_access_data with rid={rid}, filename={filename}")
    try:
        # Auto-authenticate if not already authorized
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
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
            "isError": True
        }

@mcp.tool()
async def download_all_session_data(rid: str, download_dir: str = None) -> Dict[str, Any]:
    """
    Download all available session data files for a device session.
    This includes logs, performance data, screenshots, and any other files generated during the session.
    Files will be saved to a local directory in the system temp folder (defaults to {tempdir}/pcloudy_downloads/session_{rid}).
    """
    logger.info(f"Tool called: download_all_session_data with rid={rid}, download_dir={download_dir}")
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
        
        # If no download directory specified, use default
        if not download_dir:
            download_dir = os.path.join(os.getcwd(), "downloads", f"session_{rid}")
        
        # Validate download directory path
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
        
        # Download all session data
        result = await api.download_all_session_data(rid, download_dir)
        return result
        
    except Exception as e:
        logger.error(f"Error downloading all session data: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error downloading all session data: {str(e)}"}],
            "isError": True
        }

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
    This is useful when you want to manually control device services after booking.
    
    Parameters:
    - rid: Device RID
    - start_device_logs: Enable device logs collection (default: True)  
    - start_performance_data: Enable performance data collection (default: True)
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
async def start_performance_data(rid: str, package_name: str) -> Dict[str, Any]:
    """
    Start performance data collection for a specific app on a device.
    This monitors CPU usage, memory consumption, and other metrics for the specified app.
    
    Parameters:
    - rid: Device RID
    - package_name: Package name of the app (e.g., 'com.example.app', 'com.android.chrome')
    
    Tips:
    - For Android APKs, you can use ADB to find package names: 'adb shell pm list packages | grep <app_name>'
    - Package names typically follow reverse domain notation (com.company.appname)
    """
    logger.info(f"Tool called: start_performance_data with rid={rid}, package_name={package_name}")
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
        
        # Validate package name
        if not package_name.strip():
            return {
                "content": [{"type": "text", "text": "Error: Package name cannot be empty"}],
                "isError": True
            }
        
        # Start performance data collection
        result = await api.start_performance_data(rid, package_name)
        return result
        
    except Exception as e:
        logger.error(f"Error starting performance data: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error starting performance data: {str(e)}"}],
            "isError": True        }

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