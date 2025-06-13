import httpx
import time
import os
import asyncio
import json
from typing import Dict, Any
from config import Config, logger  # Import logger and Config
from utils import encode_auth, parse_response
import re

# Utility Functions

def validate_filename(filename: str) -> bool:
    """Validate that the filename is safe for saving to the filesystem."""
    # Remove any path traversal attempts (e.g., ../) and invalid characters
    if not filename or re.search(r'[\\/:*?"<>|]', filename) or ".." in filename:
        logger.error(f"Invalid filename: {filename}")
        return False
    return True

def extract_package_name_hint(filename: str) -> str:
    """
    Attempt to extract a likely package name from APK filename.
    This is a fallback method when the API doesn't provide package information.
    Returns a suggested package name that users can try with start_performance_data.
    """
    if not filename:
        return ""
    
    # Remove file extension and clean up the filename
    name_without_ext = os.path.splitext(filename)[0].lower()
    
    # If filename already looks like a package name (contains dots), use it
    if "." in name_without_ext and not name_without_ext.startswith("."):
        # Check if it looks like reverse domain notation
        parts = name_without_ext.split(".")
        if len(parts) >= 2 and all(part.replace("_", "").isalnum() for part in parts):
            return name_without_ext
    
    # Otherwise, try to clean up the filename to make it a valid package-like string
    # Replace common separators with dots, remove version info, etc.
    cleaned = re.sub(r'[-_\s]+', '.', name_without_ext)
    cleaned = re.sub(r'\.v?\d+(\.\d+)*.*$', '', cleaned)  # Remove version suffixes
    cleaned = re.sub(r'^\.+|\.+$', '', cleaned)  # Remove leading/trailing dots
    cleaned = re.sub(r'[^a-z0-9.]', '', cleaned)  # Remove invalid characters
    
    # If it looks reasonable, return it with a prefix to indicate it's estimated
    if cleaned and len(cleaned.split('.')) >= 2:
        return f"com.app.{cleaned}"
    elif cleaned:
        return f"com.app.{cleaned}"
    
    return ""

class PCloudyAPI:
    def __init__(self, base_url=None):
        self.username = os.environ.get("PCLOUDY_USERNAME")
        self.api_key = os.environ.get("PCLOUDY_API_KEY")
        self.base_url = base_url or Config.PCLOUDY_BASE_URL
        self.auth_token = None
        self.token_timestamp = None
        self.client = httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT)
        self.rid = None
        logger.info("PCloudyAPI initialized")

    async def authenticate(self) -> str:
        try:
            if not self.username or not self.api_key:
                logger.error("PCLOUDY_USERNAME or PCLOUDY_API_KEY environment variable not set.")
                raise ValueError("PCLOUDY_USERNAME or PCLOUDY_API_KEY environment variable not set.")
            logger.info("Authenticating with pCloudy")
            url = f"{self.base_url}/access"
            auth = encode_auth(self.username, self.api_key)
            headers = {"Authorization": f"Basic {auth}"}
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            self.auth_token = result.get("token")
            if not self.auth_token:
                logger.error("Authentication failed: No token received")
                raise ValueError("Authentication failed: No token received")
            self.token_timestamp = time.time()
            logger.info("Authentication successful")
            return self.auth_token
        except httpx.RequestError as e:
            logger.error(f"Authentication request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise

    async def check_token_validity(self) -> str:
        if not self.auth_token:
            logger.error("Not authenticated. Please call authorize tool first.")
            raise ValueError("Not authenticated. Please call authorize tool first.")
        if self.token_timestamp and (time.time() - self.token_timestamp) > Config.TOKEN_REFRESH_THRESHOLD:
            logger.info("Token expired, refreshing...")
            await self.authenticate()
        return self.auth_token

    async def get_devices_list(self, platform: str = Config.DEFAULT_PLATFORM, duration: int = Config.DEFAULT_DURATION, available_now: bool = True) -> Dict[str, Any]:
        try:
            platform = platform.lower().strip()
            if platform not in Config.VALID_PLATFORMS:
                logger.error(f"Invalid platform: {platform}. Must be one of {Config.VALID_PLATFORMS}")
                raise ValueError(f"Invalid platform: {platform}. Must be one of {Config.VALID_PLATFORMS}")
            await self.check_token_validity()
            logger.info(f"Getting device list for platform {platform}")
            url = f"{self.base_url}/devices"
            payload = {
                "token": self.auth_token,
                "platform": platform,
                "duration": duration,
                "available_now": str(available_now).lower()
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            logger.info(f"Retrieved {len(result.get('models', []))} devices for {platform}")
            return result
        except httpx.RequestError as e:
            logger.error(f"Device list request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting device list: {str(e)}")
            raise
    
    async def book_device(self, device_id: str, duration: int = Config.DEFAULT_DURATION, auto_start_services: bool = True) -> Dict[str, Any]:
        """
        Book a device and automatically start device services.
        
        Parameters:
        - device_id: ID of the device to book
        - duration: Booking duration in minutes
        - auto_start_services: Automatically start device services (logs, performance data, recording)
        """
        try:
            await self.check_token_validity()
            logger.info(f"Booking device with ID {device_id}")
            url = f"{self.base_url}/book_device"
            payload = {
                "token": self.auth_token,
                "id": device_id,
                "duration": duration
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            
            rid = result.get('rid')
            logger.info(f"Device booked successfully. RID: {rid}")
            
            response_content = [
                {"type": "text", "text": f"✅ Device booked successfully. RID: {rid}"}
            ]
            # Automatically start device services if enabled
            if auto_start_services and rid:
                try:
                    logger.info(f"Auto-starting device services for RID: {rid}")
                    # Add a small delay to ensure device is fully ready
                    await asyncio.sleep(2)
                    services_result = await self.start_device_services(rid)
                    if not services_result.get("isError", True):
                        response_content.extend(services_result.get("content", []))
                        logger.info(f"Device services started successfully for RID: {rid}")
                    else:
                        response_content.append({
                            "type": "text", 
                            "text": "⚠️ Device services failed to start automatically, but device is booked successfully"
                        })
                        response_content.append({
                            "type": "text", 
                            "text": "💡 You can manually start services with: start_device_services(rid=\"" + str(rid) + "\")"
                        })
                        logger.warning(f"Failed to auto-start device services: {services_result}")
                except Exception as service_error:
                    logger.warning(f"Failed to auto-start device services: {str(service_error)}")
                    response_content.append({
                        "type": "text", 
                        "text": "⚠️ Device services failed to start automatically, but device is booked successfully"
                    })
                    response_content.append({
                        "type": "text", 
                        "text": "💡 You can manually start services with: start_device_services(rid=\"" + str(rid) + "\")"
                    })
            
            # Return enhanced result with all operations
            enhanced_result = result.copy()
            enhanced_result["enhanced_content"] = response_content
            return enhanced_result
            
        except httpx.RequestError as e:
            logger.error(f"Device booking request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error booking device: {str(e)}")
            raise

    async def release_device(self, rid: str, auto_download: bool = False) -> Dict[str, Any]:
        """
        Release a booked device using the pCloudy release device endpoint.
        
        Parameters:
        - rid: The device RID to release
        - auto_download: Should ONLY be True if explicitly requested by user. 
                        Default False ensures user is always prompted about session data.
        """
        try:
            await self.check_token_validity()
            logger.info(f"Releasing device with RID: {rid} (this may take 10-20 seconds)")
            url = f"{self.base_url}/release_device"
            payload = {"token": self.auth_token, "rid": int(rid)}
            headers = {"Content-Type": "application/json"}
            
            # Use extended timeout for release operation (30 seconds)
            async with httpx.AsyncClient(timeout=30.0) as release_client:
                response = await release_client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                # Parse the response to check if release was successful
                result = parse_response(response)
                if result.get("code") == 200 and result.get("msg") == "success":
                    logger.info(f"Device {rid} released successfully")
                    
                    response_content = [
                        {"type": "text", "text": f"✅ Device {rid} released successfully"}
                    ]
                    
                    # ALWAYS check for session data files and prompt user (unless auto_download is explicitly True)
                    if not auto_download:
                        try:
                            # Check if there are any session files available
                            files_result = await self.list_performance_data_files(rid)
                            if not files_result.get("isError", True):
                                files_content = files_result.get("content", [])
                                if files_content and "No performance data files found" not in str(files_content[0].get("text", "")):
                                    response_content.append({
                                        "type": "text", 
                                        "text": "📁 Session data files are available for this device session."
                                    })
                                    response_content.append({
                                        "type": "text", 
                                        "text": "💡 To download all session data, use: download_all_session_data(rid=\"" + rid + "\")"
                                    })
                                    response_content.append({
                                        "type": "text", 
                                        "text": "📋 To see what files are available first, use: list_performance_data_files(rid=\"" + rid + "\")"
                                    })
                                    response_content.append({
                                        "type": "text", 
                                        "text": "ℹ️ Session data includes logs, performance metrics, screenshots, and other testing artifacts."
                                    })
                                else:
                                    response_content.append({
                                        "type": "text", 
                                        "text": "ℹ️ No session data files found for this device."
                                    })
                        except Exception as check_error:
                            logger.warning(f"Could not check for session files: {str(check_error)}")
                            response_content.append({
                                "type": "text", 
                                "text": "ℹ️ To check for session data files, use: list_performance_data_files(rid=\"" + rid + "\")"
                            })
                            response_content.append({
                                "type": "text", 
                                "text": "📥 To download session data if available, use: download_all_session_data(rid=\"" + rid + "\")"
                            })                    
                    return {
                        "content": response_content,
                        "isError": False
                    }
                else:
                    error_msg = result.get("msg", "Unknown error")
                    logger.error(f"Device release failed: {error_msg}")
                    return {
                        "content": [{"type": "text", "text": f"Device release failed: {error_msg}"}],
                        "isError": True
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"Release device request timed out after 30 seconds for RID: {rid}")
            return {
                "content": [{"type": "text", "text": f"Release device request timed out. The device may still be released, but the server was slow to respond. Please check device status."}],
                "isError": True
            }
        except Exception as e:
            logger.error(f"Error releasing device {rid}: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error releasing device: {str(e)}"}],
                "isError": True
            }

    async def upload_file(self, file_path: str, source_type: str = "raw", filter_type: str = "all", force_upload: bool = False) -> Dict[str, Any]:
        try:
            await self.check_token_validity()
            file_path = file_path.strip('"').strip("'")
            logger.info(f"Uploading file: {file_path}")
            if not os.path.isfile(file_path):
                logger.error(f"Provided path is not a file: {file_path}")
                return {
                    "content": [{"type": "text", "text": f"Provided path is not a file: {file_path}"}],
                    "isError": True
                }
            
            file_name = os.path.basename(file_path)
            
            # Check if file already exists in cloud (unless force_upload is True)
            if not force_upload:
                logger.info(f"Checking if file '{file_name}' already exists in cloud...")
                try:
                    cloud_apps_result = await self.list_cloud_apps(limit=100, filter_type="all")
                    if not cloud_apps_result.get("isError", True):
                        cloud_content = cloud_apps_result.get("content", [])
                        if cloud_content:
                            cloud_files_text = str(cloud_content[0].get("text", "")).lower()
                            if file_name.lower() in cloud_files_text:
                                logger.warning(f"File '{file_name}' already exists in cloud")
                                return {
                                    "content": [
                                        {"type": "text", "text": f"⚠️ File '{file_name}' already exists in the cloud drive"},
                                        {"type": "text", "text": "💡 To upload anyway (replace existing), call: upload_file(file_path=\"" + file_path + "\", force_upload=True)"},
                                        {"type": "text", "text": "📋 To see all cloud files, use: list_cloud_apps()"}
                                    ],
                                    "isError": False,
                                    "duplicate_detected": True
                                }
                except Exception as check_error:
                    logger.warning(f"Could not check for existing files: {str(check_error)}")
                    # Continue with upload if check fails
            
            url = f"{self.base_url}/upload_file"
            with open(file_path, "rb") as f:
                files = {"file": (file_name, f)}
                data = {
                    "source_type": source_type,
                    "token": self.auth_token,
                    "filter": filter_type
                }
                response = await self.client.post(url, files=files, data=data)
                response.raise_for_status()
                result = parse_response(response)
                file_name = result.get("file")
                if not file_name:
                    logger.error("Failed to get uploaded file name")
                    return {
                        "content": [{"type": "text", "text": "Failed to get uploaded file name"}],
                        "isError": True
                    }
                
                upload_message = f"File '{file_name}' uploaded successfully"
                if force_upload:
                    upload_message += " (replaced existing file)"
                
                logger.info(upload_message)
                return {
                    "content": [{"type": "text", "text": upload_message}],
                    "isError": False
                }
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error uploading file: {str(e)}"}],
                "isError": True
            }

    async def capture_screenshot(self, rid: str, skin: bool = True) -> Dict[str, Any]:
        try:
            await self.check_token_validity()
            logger.info(f"Capturing screenshot for RID: {rid}")
            url = f"{self.base_url}/capture_device_screenshot"
            payload = {
                "token": self.auth_token,
                "rid": rid,
                "skin": str(skin).lower()
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            filename = result.get("filename")
            if not filename:
                logger.error("Failed to get screenshot filename")
                return {
                    "content": [{"type": "text", "text": "Failed to get screenshot filename"}],
                    "isError": True
                }
            logger.info(f"Screenshot captured: {filename}")
            return {
                "content": [{"type": "text", "text": f"Screenshot filename: {filename}"}],
                "isError": False
            }
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error capturing screenshot: {str(e)}"}],
                "isError": True
            }

    async def download_from_cloud(self, filename: str) -> bytes:
        """Download a file from the pCloudy cloud drive and return it as bytes for streaming."""
        try:
            await self.check_token_validity()
            url = f"{self.base_url}/download_file"
            payload = {
                "token": self.auth_token,
                "filename": filename,
                "dir": "data"
            }
            headers = {"Content-Type": "application/json"}
            # Use a temporary AsyncClient for this request
            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            logger.info(f"File '{filename}' downloaded successfully")
            return response.content
        except httpx.TimeoutException as te:
            logger.error("Download request timed out. Please try again or increase the timeout.")
            raise ValueError("Request timed out. Please try again or increase the timeout value.")
        except Exception as e:
            logger.error(f"Error downloading file from cloud: {str(e)}")
            raise ValueError(f"Error downloading file from cloud: {str(e)}")

    async def get_device_page_url(self, rid: str) -> Dict[str, Any]:
        try:
            await self.check_token_validity()
            logger.info(f"Getting device page URL for RID: {rid}")
            url = f"{self.base_url}/get_device_url"
            payload = {
                "token": self.auth_token,
                "rid": rid
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            result = data.get("result", {})
            device_url = result.get("URL")
            if not device_url:
                logger.error(f"Device page URL not found in API response: {data}")
                return {
                    "content": [{"type": "text", "text": f"Device page URL not found. API response: {data}"}],
                    "isError": True
                }
            logger.info(f"Device page URL for RID {rid}: {device_url}")
            return {
                "content": [{"type": "text", "text": device_url}],
                "isError": False
            }
        except Exception as e:
            logger.error(f"Error getting device page URL: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error getting device page URL: {str(e)}"}],
                "isError": True
            }

    async def list_cloud_apps(self, limit: int = 10, filter_type: str = "all") -> Dict[str, Any]:
        try:
            await self.check_token_validity()
            url = f"{self.base_url}/drive"
            payload = {
                "token": self.auth_token,
                "limit": limit,
                "filter": filter_type
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            files = result.get("files", [])
            app_names = [f.get("file") for f in files if f.get("file")]
            logger.info(f"Found {len(app_names)} apps in cloud drive")
            return {
                "content": [{"type": "text", "text": f"Apps in cloud drive: {', '.join(app_names) if app_names else 'None found'}"}],
                "isError": False
            }
        except Exception as e:
            logger.error(f"Error listing cloud apps: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error listing cloud apps: {str(e)}"}],
                "isError": True
            }

    async def install_and_launch_app(self, rid: str, filename: str, grant_all_permissions: bool = True, app_package_name: str = None) -> Dict[str, Any]:
        try:
            await self.check_token_validity()
            url = f"{self.base_url}/install_app"
            payload = {
                "token": self.auth_token,
                "rid": rid,
                "filename": filename,
                "grant_all_permissions": grant_all_permissions
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            if result.get("code") == 200 and result.get("msg") == "success":
                package = result.get("package", "")
                logger.info(f"App '{filename}' installed and launched successfully on RID: {rid}")
                
                # Prepare success response content
                response_content = [
                    {"type": "text", "text": f"✅ App '{filename}' installed and launched successfully on RID: {rid}"}
                ]
                
                if package:
                    response_content.append({"type": "text", "text": f"📱 Package: {package}"})
                
                # Start performance data collection if package name is available
                if package:
                    try:
                        logger.info(f"Starting performance data collection for package '{package}' on RID {rid}")
                        perf_result = await self.start_performance_data(rid, package)
                        if not perf_result.get("isError", True):
                            response_content.append({
                                "type": "text", 
                                "text": "📊 Performance data collection started automatically. Use 'list_performance_data_files' tool to view collected metrics later."
                            })
                            logger.info(f"Performance monitoring started successfully for {package}")
                        else:
                            error_text = perf_result.get('content', [{}])[0].get('text', 'Unknown error')
                            response_content.append({
                                "type": "text", 
                                "text": f"⚠️ Performance data collection failed: {error_text}"
                            })
                            logger.warning(f"Performance monitoring failed for {package}: {error_text}")
                    except Exception as perf_error:
                        logger.warning(f"Failed to start performance data collection: {str(perf_error)}")
                        response_content.append({
                            "type": "text", 
                            "text": f"⚠️ Performance data collection failed: {str(perf_error)}"
                        })
                else:
                    # Try to use the provided app_package_name as fallback
                    fallback_package = app_package_name or extract_package_name_hint(filename)
                    
                    if fallback_package:
                        try:
                            logger.info(f"Using provided/suggested package name '{fallback_package}' for performance data collection on RID {rid}")
                            perf_result = await self.start_performance_data(rid, fallback_package)
                            if not perf_result.get("isError", True):
                                response_content.append({
                                    "type": "text", 
                                    "text": f"📊 Performance data collection started using {'provided' if app_package_name else 'suggested'} package name: {fallback_package}"
                                })
                                logger.info(f"Performance monitoring started successfully with fallback package {fallback_package}")
                            else:
                                error_text = perf_result.get('content', [{}])[0].get('text', 'Unknown error')
                                response_content.append({
                                    "type": "text", 
                                    "text": f"⚠️ Performance data collection failed with {'provided' if app_package_name else 'suggested'} package '{fallback_package}': {error_text}"
                                })
                                logger.warning(f"Performance monitoring failed with fallback package {fallback_package}: {error_text}")
                        except Exception as perf_error:
                            logger.warning(f"Failed to start performance data collection with fallback package {fallback_package}: {str(perf_error)}")
                            response_content.append({
                                "type": "text", 
                                "text": f"⚠️ Performance data collection failed with {'provided' if app_package_name else 'suggested'} package '{fallback_package}': {str(perf_error)}"
                            })
                    else:
                        response_content.append({
                            "type": "text", 
                            "text": "ℹ️ Performance data collection not started (package name not available from API response)"
                        })
                        response_content.append({
                            "type": "text", 
                            "text": "💡 Tip: Provide 'app_package_name' parameter when calling install_and_launch_app, or use 'start_performance_data' tool manually"
                        })
                        response_content.append({
                            "type": "text", 
                            "text": "📱 For Android APKs, you can also use ADB to find the package: adb shell pm list packages | grep <app_name>"
                        })
                    
                    logger.debug(f"Package name not found in API response for {filename}. Full response: {result}")
                
                return {
                    "content": response_content,
                    "isError": False
                }
            else:
                logger.error(f"Install and launch failed: {result}")
                return {
                    "content": [{"type": "text", "text": f"Install and launch failed: {result}"}],
                    "isError": True
                }
        except Exception as e:
            logger.error(f"Error installing and launching app: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error installing and launching app: {str(e)}"}],
                "isError": True
            }

    async def resign_ipa(self, filename: str, force_resign: bool = False) -> Dict[str, Any]:
        """
        Resign an IPA file. Returns a dictionary with content and error status.
        
        Parameters:
        - filename: Name of the IPA file to resign
        - force_resign: If True, resign even if a resigned version already exists
        """
        try:
            await self.check_token_validity()
            
            # Check ifhot resigned version already exists (unless force_resign is True)
            if not force_resign:
                logger.info(f"Checking if resigned version of '{filename}' already exists...")
                try:
                    # Generate expected resigned filename pattern
                    base_name = os.path.splitext(filename)[0]
                    expected_resigned_names = [
                        f"{base_name}_resign.ipa",
                        f"{base_name}-resign.ipa",
                        f"resign_{base_name}.ipa",
                        f"{filename}_resign",
                        f"resign_{filename}"
                    ]
                    
                    cloud_apps_result = await self.list_cloud_apps(limit=100, filter_type="all")
                    if not cloud_apps_result.get("isError", True):
                        cloud_content = cloud_apps_result.get("content", [])
                        if cloud_content:
                            cloud_files_text = str(cloud_content[0].get("text", "")).lower()
                            
                            # Check if any resigned version exists
                            for resigned_name in expected_resigned_names:
                                if resigned_name.lower() in cloud_files_text:
                                    logger.warning(f"Resigned version '{resigned_name}' already exists in cloud")
                                    return {
                                        "content": [
                                            {"type": "text", "text": f"⚠️ A resigned version of '{filename}' already exists in the cloud drive"},
                                            {"type": "text", "text": f"🔍 Found existing resigned file: {resigned_name}"},
                                            {"type": "text", "text": "💡 To resign anyway (replace existing), call: resign_ipa(filename=\"" + filename + "\", force_resign=True)"},
                                            {"type": "text", "text": "📋 To see all cloud files, use: list_cloud_apps()"}
                                        ],
                                        "isError": False,
                                        "duplicate_detected": True,
                                        "existing_resigned_file": resigned_name
                                    }
                except Exception as check_error:
                    logger.warning(f"Could not check for existing resigned files: {str(check_error)}")
                    # Continue with resign if check fails
            
            headers = {"Content-Type": "application/json"}
            url_initiate = f"{self.base_url}/resign/initiate"
            payload_initiate = {"token": self.auth_token, "filename": filename}
            response = await self.client.post(url_initiate, json=payload_initiate, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            resign_token = result.get("resign_token")
            resign_filename = result.get("resign_filename")
            if not resign_token or not resign_filename:
                raise Exception(f"Failed to initiate resigning IPA. API response: {result}")
            
            logger.info(f"Resigning IPA '{filename}' - this may take up to 60 seconds...")
            url_progress = f"{self.base_url}/resign/progress"
            for _ in range(30):
                payload_progress = {
                    "token": self.auth_token,
                    "resign_token": resign_token,
                    "filename": filename
                }
                response = await self.client.post(url_progress, json=payload_progress, headers=headers)
                response.raise_for_status()
                result = parse_response(response)
                resign_status = result.get("resign_status")
                if resign_status == 100:
                    break
                await asyncio.sleep(2)
            url_download = f"{self.base_url}/resign/download"
            payload_download = {
                "token": self.auth_token,
                "resign_token": resign_token,
                "filename": filename
            }
            response = await self.client.post(url_download, json=payload_download, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            resigned_file = result.get("resign_file")
            if not resigned_file:
                raise Exception(f"Failed to download resigned IPA. API response: {result}")
            
            resign_message = f"IPA file '{filename}' has been resigned successfully"
            if force_resign:
                resign_message += " (replaced existing resigned version)"
            
            logger.info(resign_message)
            return {
                "content": [{"type": "text", "text": resign_message}],
                "isError": False,
                "resigned_file": resigned_file
            }
        except Exception as e:
            logger.error(f"Error resigning IPA: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error resigning IPA: {str(e)}"}],
                "isError": True
            }

    async def download_manual_access_data(self, rid: str, filename: str) -> bytes:
        """Download a file using the download_manual_access_data endpoint and return it as bytes for streaming."""
        try:
            await self.check_token_validity()
            if not validate_filename(filename):
                logger.error(f"Invalid filename for download: {filename}")
                raise ValueError(f"Invalid filename: {filename}")
            
            url = f"{self.base_url}/download_manual_access_data"
            payload = {
                "token": self.auth_token,
                "rid": rid,
                "filename": filename
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "").lower()
            if "application/json" in content_type:
                # If the response is JSON, it's likely an error or info message
                result = parse_response(response)
                logger.info(f"download_manual_access_data returned JSON: {result}")
                # Convert the JSON to a string and then to bytes to maintain consistency in return type
                return json.dumps(result).encode('utf-8')
            else:
                # If it's binary data, return it directly
                logger.info(f"File '{filename}' downloaded successfully via download_manual_access_data")
                return response.content
        except httpx.TimeoutException as te:
            logger.error("Download request timed out. Please try again or increase the timeout.")
            raise ValueError("Request timed out. Please try again or increase the timeout value.")
        except Exception as e:
            logger.error(f"Error downloading file via download_manual_access_data: {str(e)}")
            raise ValueError(f"Error downloading file via download_manual_access_data: {str(e)}")

    async def execute_adb_command(self, rid: str, adb_command: str) -> Dict[str, Any]:
        """
        Execute an ADB command on an Android device and return structured output.
        Only works with Android devices.
        
        Args:
            rid: Device reservation ID
            adb_command: ADB command to execute
            
        Returns:
            Dict containing structured response with content and error status
        """
        try:
            await self.check_token_validity()
            logger.info(f"Executing ADB command on RID {rid}: {adb_command}")
            
            url = f"{self.base_url}/execute_adb"
            payload = {
                "token": self.auth_token,
                "rid": rid,
                "adbCommand": adb_command
            }
            headers = {"Content-Type": "application/json"}
            
            # Use extended timeout for ADB commands
            timeout_config = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=30.0)
            
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                logger.debug(f"Sending ADB request to: {url}")
                logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
                
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                # Parse response
                raw_data = response.json()
                logger.info(f"Raw ADB response: {json.dumps(raw_data, indent=2)}")
                
                # Handle different response structures
                if isinstance(raw_data, dict):
                    # Check for top-level result
                    result = raw_data.get("result", raw_data)
                    
                    # Get status code
                    status_code = result.get("code", 0)
                    message = result.get("msg", "")
                    
                    if status_code == 200:
                        # Success - try to extract output from multiple possible fields
                        output_content = None
                        output_source = None
                        
                        # Try different output field names
                        for field_name in ["adbreply", "output", "reply", "response", "data", "result"]:
                            if field_name in result and result[field_name] is not None:
                                output_content = result[field_name]
                                output_source = field_name
                                break
                        
                        # Format the output
                        if output_content is not None:
                            # Convert to string and handle newlines
                            formatted_output = str(output_content)
                            if "\\n" in formatted_output:
                                formatted_output = formatted_output.replace("\\n", "\n")
                            formatted_output = formatted_output.strip()
                            
                            if not formatted_output:
                                formatted_output = "[Command executed successfully but returned empty output]"
                        else:
                            formatted_output = "[No output returned from device]"
                            logger.warning(f"No output found in response fields. Available keys: {list(result.keys())}")
                        
                        logger.info(f"ADB command successful. Output source: {output_source}, Length: {len(formatted_output)}")
                        
                        return {
                            "success": True,
                            "output": formatted_output,
                            "command": adb_command,
                            "rid": rid,
                            "status_code": status_code,
                            "message": message,
                            "output_source": output_source
                        }
                    
                    else:
                        # Error response
                        error_msg = message or "ADB command failed"
                        logger.error(f"ADB command failed with code {status_code}: {error_msg}")
                        
                        return {
                            "success": False,
                            "error": error_msg,
                            "command": adb_command,
                            "rid": rid,
                            "status_code": status_code,
                            "raw_response": raw_data
                        }
                else:
                    # Unexpected response format
                    logger.error(f"Unexpected response format: {type(raw_data)}")
                    return {
                        "success": False,
                        "error": f"Unexpected response format: {type(raw_data)}",
                        "command": adb_command,
                        "rid": rid,
                        "raw_response": raw_data
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"ADB command timed out for RID {rid}: {adb_command}")
            return {
                "success": False,
                "error": "Command timed out after 120 seconds",
                "command": adb_command,
                "rid": rid
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error executing ADB command: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "command": adb_command,
                "rid": rid
            }
            
        except Exception as e:
            logger.error(f"Unexpected error executing ADB command: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "command": adb_command,
                "rid": rid
            }

    async def start_performance_data(self, rid: str, package_name: str) -> Dict[str, Any]:
        """Start performance data collection for an app on a device."""
        try:
            await self.check_token_validity()
            logger.info(f"Starting performance data collection for package '{package_name}' on RID {rid}")
            url = f"{self.base_url}/start_performance_data"
            payload = {
                "token": self.auth_token,
                "rid": rid,
                "pkg": package_name
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            
            # Check if the performance data collection started successfully
            if result.get("code") == 200:
                logger.info(f"Performance data collection started successfully for package '{package_name}' on RID {rid}")
                return {
                    "content": [
                        {"type": "text", "text": f"Performance data collection started successfully for package '{package_name}' on RID {rid}"}
                    ],
                    "isError": False
                }
            else:
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"Failed to start performance data collection: {error_msg}")
                return {
                    "content": [{"type": "text", "text": f"Failed to start performance data collection: {error_msg}"}],
                    "isError": True
                }
        except Exception as e:
            logger.error(f"Error starting performance data collection: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error starting performance data collection: {str(e)}"}],
                "isError": True
            }

    async def list_performance_data_files(self, rid: str) -> Dict[str, Any]:
        """List all performance data files for a device."""
        try:
            await self.check_token_validity()
            logger.info(f"Listing performance data files for RID {rid}")
            url = "https://device.pcloudy.com/api/manual_access_files_list"
            payload = {
                "token": self.auth_token,
                "rid": rid
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            
            if result.get("code") == 200:
                files = result.get("files", [])
                if files:
                    file_list = []
                    for file_info in files:
                        file_name = file_info.get("file", "Unknown")
                        file_size = file_info.get("size", "Unknown")
                        file_type = file_info.get("type", "Unknown")
                        file_list.append(f"📁 {file_name} ({file_size}, {file_type})")
                    
                    files_text = "\n".join(file_list)
                    logger.info(f"Found {len(files)} performance data files for RID {rid}")
                    return {
                        "content": [
                            {"type": "text", "text": f"Performance Data Files for Device {rid}:\n\n{files_text}"}
                        ],
                        "isError": False
                    }
                else:
                    logger.info(f"No performance data files found for RID {rid}")
                    return {
                        "content": [
                            {"type": "text", "text": f"No performance data files found for device {rid}"}
                        ],
                        "isError": False
                    }
            else:
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"Failed to list performance data files: {error_msg}")
                return {
                    "content": [{"type": "text", "text": f"Failed to list performance data files: {error_msg}"}],
                    "isError": True
                }
        except Exception as e:
            logger.error(f"Error listing performance data files: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error listing performance data files: {str(e)}"}],
                "isError": True
            }

    async def download_all_session_data(self, rid: str, download_dir: str = None) -> Dict[str, Any]:
        """
        Download all available session data files for a device session.
        Uses the manual_access_files_list endpoint to get all files, then downloads each one.
        """
        try:
            await self.check_token_validity()
            logger.info(f"Starting bulk download of all session data for RID {rid}")
              # Set default download directory if not provided
            if not download_dir:
                import tempfile
                download_dir = os.path.join(tempfile.gettempdir(), "pcloudy_downloads", f"session_{rid}")
            
            # Create download directory if it doesn't exist
            os.makedirs(download_dir, exist_ok=True)
            
            # First, get the list of all available files
            url = "https://device.pcloudy.com/api/manual_access_files_list"
            payload = {
                "token": self.auth_token,
                "rid": rid
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = parse_response(response)
            
            if result.get("code") != 200:
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"Failed to list session files: {error_msg}")
                return {
                    "content": [{"type": "text", "text": f"Failed to list session files: {error_msg}"}],
                    "isError": True
                }
            
            files = result.get("files", [])
            if not files:
                logger.info(f"No session data files found for RID {rid}")
                return {
                    "content": [{"type": "text", "text": f"No session data files found for device {rid}"}],
                    "isError": False
                }
            
            # Download each file
            downloaded_files = []
            failed_files = []
            total_files = len(files)
            
            logger.info(f"Found {total_files} files to download for RID {rid}")
            
            for i, file_info in enumerate(files, 1):
                filename = file_info.get("file")
                if not filename:
                    logger.warning(f"Skipping file {i}/{total_files}: no filename provided")
                    continue
                
                try:
                    logger.info(f"Downloading file {i}/{total_files}: {filename}")
                    
                    # Download the file using download_manual_access_data
                    file_content = await self.download_manual_access_data(rid, filename)
                    
                    # Save to local filesystem
                    local_path = os.path.join(download_dir, filename)
                    
                    # Handle potential filename conflicts
                    counter = 1
                    original_path = local_path
                    while os.path.exists(local_path):
                        name, ext = os.path.splitext(original_path)
                        local_path = f"{name}_{counter}{ext}"
                        counter += 1
                    
                    with open(local_path, 'wb') as f:
                        f.write(file_content)
                    
                    downloaded_files.append({
                        "filename": filename,
                        "local_path": local_path,
                        "size": file_info.get("size", "Unknown"),
                        "type": file_info.get("type", "Unknown")
                    })
                    
                    logger.info(f"Successfully downloaded {filename} to {local_path}")
                    
                except Exception as file_error:
                    logger.error(f"Failed to download {filename}: {str(file_error)}")
                    failed_files.append({
                        "filename": filename,
                        "error": str(file_error)
                    })
            
            # Prepare summary response
            success_count = len(downloaded_files)
            failure_count = len(failed_files)
            
            response_content = []
            
            if success_count > 0:
                response_content.append({
                    "type": "text",
                    "text": f"📥 Successfully downloaded {success_count}/{total_files} files to: {download_dir}"
                })
                
                # List successfully downloaded files
                success_list = []
                for file_info in downloaded_files:
                    success_list.append(f"✅ {file_info['filename']} ({file_info['size']}, {file_info['type']})")
                
                response_content.append({
                    "type": "text",
                    "text": f"Downloaded Files:\n" + "\n".join(success_list)
                })
            if failure_count > 0:
                response_content.append({
                    "type": "text",
                    "text": f"⚠️ Failed to download {failure_count} files:"
                })
                
                # List failed files
                failure_list = []
                for file_info in failed_files:
                    failure_list.append(f"❌ {file_info['filename']}: {file_info['error']}")
                
                response_content.append({
                    "type": "text",
                    "text": "\n".join(failure_list)
                })
            
            logger.info(f"Bulk download completed: {success_count} success, {failure_count} failures")
            
            return {
                "content": response_content,
                "isError": failure_count > 0 and success_count == 0  # Only error if all downloads failed
            }
            
        except Exception as e:
            logger.error(f"Error during bulk download: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error during bulk download: {str(e)}"}],
                "isError": True
            }

    async def detect_device_platform(self, rid: str) -> Dict[str, Any]:
        """
        Auto-detect the platform (Android/iOS) of a booked device using device information.
        This helps in automatically determining the correct platform for operations like ADB commands.
        """
        try:
            await self.check_token_validity()
            logger.info(f"Detecting platform for device RID: {rid}")
            
            # Get device information - this might be available through device status or session info
            # First, try to get device page URL which might contain platform info in response
            url = f"{self.base_url}/get_device_url"
            payload = {
                "token": self.auth_token,
                "rid": rid
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            result = data.get("result", {})
            
            # Platform detection logic - look for hints in device info
            platform = "unknown"
            platform_hints = []
            
            # Check if we can get platform info from the response
            # This is implementation-specific and may need adjustment based on actual API response
            device_info = str(data).lower()
            
            # Look for platform indicators
            ios_indicators = ["ios", "iphone", "ipad", "apple", "safari"]
            android_indicators = ["android", "samsung", "pixel", "chrome", "google"]
            
            ios_score = sum(1 for indicator in ios_indicators if indicator in device_info)
            android_score = sum(1 for indicator in android_indicators if indicator in device_info)
            
            if ios_score > android_score:
                platform = "ios"
                platform_hints.append(f"iOS indicators found: {ios_score}")
            elif android_score > ios_score:
                platform = "android"
                platform_hints.append(f"Android indicators found: {android_score}")
            else:
                # Try alternative method - check available files/capabilities
                try:
                    # iOS devices typically don't support ADB, Android devices do
                    # We can test this by attempting to list performance data which might show platform-specific files
                    files_result = await self.list_performance_data_files(rid)
                    if not files_result.get("isError"):
                        files_content = str(files_result.get("content", "")).lower()
                        if "logcat" in files_content or "adb" in files_content:
                            platform = "android"
                            platform_hints.append("Android-specific log files detected")
                        elif "syslog" in files_content or "crash" in files_content:
                            platform = "ios"
                            platform_hints.append("iOS-specific log files detected")
                except Exception:
                    # Ignore errors in secondary detection method
                    pass
            
            logger.info(f"Platform detection for RID {rid}: {platform}")
            
            return {
                "content": [
                    {"type": "text", "text": f"🔍 Detected platform for device {rid}: {platform.upper()}"},
                    {"type": "text", "text": f"Detection hints: {', '.join(platform_hints) if platform_hints else 'Limited platform indicators found'}"},
                    {"type": "text", "text": f"ℹ️ Note: Platform detection is heuristic-based. If incorrect, manually specify platform in tool calls."}
                ],
                "isError": False,
                "platform": platform
            }
            
        except Exception as e:
            logger.error(f"Error detecting device platform: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error detecting device platform: {str(e)}"}],
                "isError": True,
                "platform": "unknown"
            }

    async def start_device_services(self, rid: str, start_device_logs: bool = True, start_performance_data: bool = True, start_session_recording: bool = True) -> Dict[str, Any]:
        """
        Start device services including logs, performance data, and session recording.
        This is automatically called when booking a device.
        
        Parameters:
        - rid: Device RID
        - start_device_logs: Enable device logs collection (default: True)
        - start_performance_data: Enable performance data collection (default: True)
        - start_session_recording: Enable session recording (default: True)
        """
        try:
            await self.check_token_validity()
            logger.info(f"Starting device services for RID: {rid}")
            
            url = f"{self.base_url}/startdeviceservices"
            payload = {
                "token": self.auth_token,
                "rid": rid,
                "startDeviceLogs": str(start_device_logs).lower(),
                "startPerformanceData": str(start_performance_data).lower(),
                "startSessionRecording": str(start_session_recording).lower()
            }
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Device services response status: {response.status_code}")
            logger.info(f"Device services response text: {response.text}")
            
            # Simple success response for now
            logger.info(f"Device services request completed for RID {rid}")
            services_started = []
            if start_device_logs:
                services_started.append("📝 Device Logs")
            if start_performance_data:
                services_started.append("📊 Performance Data")
            if start_session_recording:
                services_started.append("🎥 Session Recording")
            
            return {
                "content": [
                    {"type": "text", "text": f"✅ Device services request sent for RID {rid}"},
                    {"type": "text", "text": f"📋 Requested services: {', '.join(services_started)}"},
                    {"type": "text", "text": f"🔍 Response: {response.status_code} - {response.text[:200]}"}
                ],
                "isError": False
            }
                
        except Exception as e:
            logger.error(f"Error starting device services: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "content": [{"type": "text", "text": f"Error starting device services: {str(e)}"}],
                "isError": True
            }

    async def start_wildnet(self, rid: str) -> Dict[str, Any]:
        """Start wildnet feature for a booked device.
        
        Args:
            rid: Device booking ID
            
        Returns:
            Dict containing wildnet startup response
        """
        try:
            if not rid:
                raise ValueError("Device booking ID (rid) is required")
            
            url = f"{self.base_url}/api/startwildnet"
            payload = {
                "token": self.auth_token,
                "rid": rid
            }
            
            logger.info(f"Starting wildnet for device booking ID: {rid}")
            
            response = await self.client.post(url, json=payload)
            result = parse_response(response)
            
            if result.get("result") == "success":
                logger.info(f"Wildnet started successfully for device booking ID: {rid}")
                return {
                    "content": [
                        {"type": "text", "text": f"✅ Wildnet started successfully for RID {rid}"},
                        {"type": "text", "text": "🌐 Enhanced network capabilities are now active on the device"}
                    ],
                    "isError": False
                }
            else:
                error_msg = result.get("error", "Unknown error starting wildnet")
                logger.error(f"Failed to start wildnet: {error_msg}")
                return {
                    "content": [{"type": "text", "text": f"Failed to start wildnet: {error_msg}"}],
                    "isError": True
                }
                
        except Exception as e:
            error_msg = f"Error starting wildnet for device {rid}: {str(e)}"
            logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }

    async def close(self):
        """Close the HTTP client."""
        try:
            await self.client.aclose()
            logger.info("HTTP client closed")
        except Exception as e:
            logger.error(f"Error closing HTTP client: {str(e)}")