import httpx
import os
import re
from typing import Dict, Any
from config import Config, logger
from .core import PCloudyAPI
from utils import parse_response, validate_filename, extract_package_name_hint

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
            
            response_content = [
                {"type": "text", "text": f"✅ App '{filename}' installed and launched successfully on RID: {rid}"}
            ]
            if package:
                response_content.append({"type": "text", "text": f"📱 Package: {package}"})
            
            try:
                logger.info(f"Getting device page URL for RID: {rid}")
                url_result = await self.get_device_page_url(rid)
                
                if not url_result.get("isError", True):
                    device_url = url_result.get("content", [{}])[0].get("text", "")
                    if device_url:
                        webbrowser.open(device_url)
                        response_content.append({"type": "text", "text": f"🌐 Device page opened in browser: {device_url}"})
                        logger.info(f"Device page opened in browser: {device_url}")
                    else:
                        response_content.append({"type": "text", "text": "⚠️ Could not retrieve device page URL"})
                else:
                    response_content.append({"type": "text", "text": "⚠️ Could not retrieve device page URL"})
            except Exception as url_error:
                logger.warning(f"Failed to open device page URL: {str(url_error)}")
                response_content.append({"type": "text", "text": f"⚠️ Could not open device page: {str(url_error)}"})
            
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
    try:
        await self.check_token_validity()
        
        if not force_resign:
            logger.info(f"Checking if resigned version of '{filename}' already exists...")
            try:
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

async def download_from_cloud(self, filename: str) -> bytes:
    try:
        await self.check_token_validity()
        url = f"{self.base_url}/download_file"
        payload = {
            "token": self.auth_token,
            "filename": filename,
            "dir": "data"
        }
        headers = {"Content-Type": "application/json"}
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