from config import logger
from utils import parse_response
import httpx
import webbrowser

class AppManagementMixin:
    async def install_and_launch_app(self, rid: str, filename: str, grant_all_permissions: bool = True, app_package_name: str = None):
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

    async def resign_ipa(self, filename: str, force_resign: bool = False):
        await self.check_token_validity()
        from security import extract_package_name_hint
        if not force_resign:
            logger.info(f"Checking if resigned version of '{filename}' already exists...")
            try:
                base_name = filename.rsplit('.', 1)[0]
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
            import asyncio
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