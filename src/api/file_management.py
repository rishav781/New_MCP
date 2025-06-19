"""
File & App Management Mixin for pCloudy MCP Server

Provides file and app management operations for the PCloudyAPI class:
- upload_file: Upload APK/IPA files to cloud storage
- download_from_cloud: Download files from cloud storage (APKs, IPAs, etc.)
- list_cloud_apps: List all apps/files in cloud drive

IMPORTANT: Download Endpoint Usage Context for LLMs:
- For DEVICE-RELATED files (screenshots, session data, logs, performance data):
  Use {base_url}/download_manual_access_data (implemented in session.py)
- For CLOUD STORAGE files (uploaded APKs, IPAs, user files):
  Use {base_url}/download_file (implemented in this file)

Intended to be used as a mixin in the modular API architecture.
"""

from config import Config, logger
from utils import encode_auth, parse_response
import os
import httpx

class FileManagementMixin:
    async def upload_file(self, file_path: str, source_type: str = "raw", filter_type: str = "all", force_upload: bool = False):
        """
        Upload a file (APK/IPA) to the pCloudy cloud drive.
        Checks for duplicates unless force_upload is True.
        Returns a dict with upload status and messages.
        """
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
                                    {"type": "text", "text": f"\u26a0\ufe0f File '{file_name}' already exists in the cloud drive"},
                                    {"type": "text", "text": "\ud83d\udca1 To upload anyway (replace existing), call: upload_file(file_path=\"" + file_path + "\", force_upload=True)"},
                                    {"type": "text", "text": "\ud83d\udccb To see all cloud files, use: list_cloud_apps()"}
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

    async def download_from_cloud(self, filename: str) -> bytes:
        """
        Download a file from the pCloudy cloud storage (APKs, IPAs, user-uploaded files).
        
        IMPORTANT: This is for CLOUD STORAGE files only!
        For device-related files (screenshots, session data, logs), use the session.py
        download_session_data method which uses /download_manual_access_data endpoint.
        
        Returns the file content as bytes.
        """
        await self.check_token_validity()
        url = f"{self.base_url}/download_file"
        payload = {
            "token": self.auth_token,
            "filename": filename,
            "dir": "data"
        }
        headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"File '{filename}' downloaded successfully")
        return response.content

    async def list_cloud_apps(self, limit: int = 10, filter_type: str = "all"):
        """
        List all apps/files in the pCloudy cloud drive.
        Returns a dict with app names and status.
        """
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