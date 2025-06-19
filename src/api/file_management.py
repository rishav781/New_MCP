from config import logger
from utils import parse_response
import os
import httpx

class FileManagementMixin:
    async def upload_file(self, file_path: str, source_type: str = "raw", filter_type: str = "all", force_upload: bool = False):
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

    async def download_from_cloud(self, filename: str) -> bytes:
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