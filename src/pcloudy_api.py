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

class PCloudyAPI:
    def __init__(self, base_url=None):
        self.username = None
        self.api_key = None
        self.base_url = base_url or Config.PCLOUDY_BASE_URL
        self.auth_token = None
        self.token_timestamp = None
        self.client = httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT)
        self.rid = None
        logger.info("PCloudyAPI initialized")

    async def authenticate(self, username: str, api_key: str) -> str:
        try:
            self.username = username
            self.api_key = api_key
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
            await self.authenticate(self.username, self.api_key)
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

    async def book_device(self, device_id: str, duration: int = Config.DEFAULT_DURATION) -> Dict[str, Any]:
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
            logger.info(f"Device booked successfully. RID: {result.get('rid')}")
            return result
        except httpx.RequestError as e:
            logger.error(f"Device booking request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error booking device: {str(e)}")
            raise

    async def release_device(self, rid: str) -> Dict[str, Any]:
        """Release a booked device using the pCloudy release device endpoint."""
        try:
            await self.check_token_validity()
            url = f"{self.base_url}/release_device"
            payload = {"token": self.auth_token, "rid": rid}
            headers = {"Content-Type": "application/json"}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Device released successfully")
            return {
                "content": [{"type": "text", "text": "Device released successfully"}],
                "isError": False
            }
        except httpx.TimeoutException as te:
            logger.error("Release device request timed out. Consider increasing the timeout in Config.REQUEST_TIMEOUT.")
            raise ValueError("Request timed out. Please try again or increase the timeout value.")
        except Exception as e:
            logger.error(f"Error releasing device: {str(e)}")
            raise ValueError(f"Error releasing device: {str(e)}")

    async def upload_file(self, file_path: str, source_type: str = "raw", filter_type: str = "all") -> Dict[str, Any]:
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
                logger.info(f"File '{file_name}' uploaded successfully")
                return {
                    "content": [{"type": "text", "text": f"File '{file_name}' uploaded successfully"}],
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

    async def install_and_launch_app(self, rid: str, filename: str, grant_all_permissions: bool = True) -> Dict[str, Any]:
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
                return {
                    "content": [
                        {"type": "text", "text": f"App '{filename}' installed and launched successfully on RID: {rid}."},
                        {"type": "text", "text": f"Package: {package}" if package else ""}
                    ],
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

    async def resign_ipa(self, filename: str):
        try:
            await self.check_token_validity()
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
            return resigned_file
        except Exception as e:
            logger.error(f"Error resigning IPA: {str(e)}")
            raise

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

    async def close(self):
        """Close the HTTP client."""
        try:
            await self.client.aclose()
            logger.info("HTTP client closed")
        except Exception as e:
            logger.error(f"Error closing HTTP client: {str(e)}")
