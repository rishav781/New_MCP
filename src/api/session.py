"""
Session Data & Analytics Mixin for pCloudy MCP Server

Provides session data download and analytics for the PCloudyAPI class:
- download_session_data: Download one or all session files for a device
- list_performance_data_files: List all performance data files for a device

Intended to be used as a mixin in the modular API architecture.
"""

from config import Config, logger
from utils import encode_auth, parse_response
from security import validate_filename
import os
import httpx
import tempfile

class SessionMixin:
    async def download_session_data(self, rid: str, filename: str = None, download_dir: str = None):
        """
        Download session data for a device. If filename is provided, download a single file; otherwise, download all files.
        Returns a dict with download status and messages.
        """
        await self.check_token_validity()
        if filename:
            return await self._download_single_file(rid, filename, download_dir)
        else:
            return await self._download_all_files(rid, download_dir)

    async def _download_single_file(self, rid: str, filename: str, download_dir: str = None):
        """
        Download a single session file for a device.
        Returns a dict with download status and messages.
        """
        if not validate_filename(filename):
            logger.error(f"Invalid filename for download: {filename}")
            raise ValueError(f"Invalid filename: {filename}")
        if not download_dir:
            download_dir = os.path.join(tempfile.gettempdir(), "pcloudy_downloads", f"session_{rid}")
        os.makedirs(download_dir, exist_ok=True)
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
            result = parse_response(response)
            logger.info(f"download_session_data returned JSON: {result}")
            return {
                "content": [{"type": "text", "text": f"Download response: {result}"}],
                "isError": True
            }
        else:
            local_path = os.path.join(download_dir, filename)
            counter = 1
            original_path = local_path
            while os.path.exists(local_path):
                name, ext = os.path.splitext(original_path)
                local_path = f"{name}_{counter}{ext}"
                counter += 1
            with open(local_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"File '{filename}' downloaded successfully to {local_path}")
            return {
                "content": [{"type": "text", "text": f"\ud83d\udce5 Successfully downloaded '{filename}' to: {local_path}"}],
                "isError": False
            }

    async def _download_all_files(self, rid: str, download_dir: str = None):
        """
        Download all session files for a device.
        Returns a dict with download status and messages for all files.
        """
        logger.info(f"Starting bulk download of all session data for RID {rid}")
        if not download_dir:
            download_dir = os.path.join(tempfile.gettempdir(), "pcloudy_downloads", f"session_{rid}")
        os.makedirs(download_dir, exist_ok=True)
        url = f"{self.base_url}/manual_access_files_list"
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
                url = f"{self.base_url}/download_manual_access_data"
                payload = {
                    "token": self.auth_token,
                    "rid": rid,
                    "filename": filename
                }
                headers = {"Content-Type": "application/json"}
                response = await self.client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                local_path = os.path.join(download_dir, filename)
                counter = 1
                original_path = local_path
                while os.path.exists(local_path):
                    name, ext = os.path.splitext(original_path)
                    local_path = f"{name}_{counter}{ext}"
                    counter += 1
                with open(local_path, 'wb') as f:
                    f.write(response.content)
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
        success_count = len(downloaded_files)
        failure_count = len(failed_files)
        response_content = []
        if success_count > 0:
            response_content.append({
                "type": "text",
                "text": f"\ud83d\udce5 Successfully downloaded {success_count}/{total_files} files to: {download_dir}"
            })
            success_list = []
            for file_info in downloaded_files:
                success_list.append(f"\u2705 {file_info['filename']} ({file_info['size']}, {file_info['type']})")
            response_content.append({
                "type": "text",
                "text": f"Downloaded Files:\n" + "\n".join(success_list)
            })
        if failure_count > 0:
            response_content.append({
                "type": "text",
                "text": f"\u26a0\ufe0f Failed to download {failure_count} files:"
            })
            failure_list = []
            for file_info in failed_files:
                failure_list.append(f"\u274c {file_info['filename']}: {file_info['error']}")
            response_content.append({
                "type": "text",
                "text": "\n".join(failure_list)
            })
        logger.info(f"Bulk download completed: {success_count} success, {failure_count} failures")
        return {
            "content": response_content,
            "isError": failure_count > 0 and success_count == 0
        }

    async def list_performance_data_files(self, rid: str):
        """
        List all performance data files for a device.
        Returns a dict with file info and status.
        """
        await self.check_token_validity()
        logger.info(f"Listing performance data files for RID {rid}")
        url = f"{self.base_url}/manual_access_files_list"
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
                    file_list.append(f"\ud83d\udcc1 {file_name} ({file_size}, {file_type})")
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