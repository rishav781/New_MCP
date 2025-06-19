"""
Platform Detection Mixin for pCloudy MCP Server

Provides platform detection for the PCloudyAPI class:
- detect_device_platform: Heuristically determines if a booked device is Android or iOS

Intended to be used as a mixin in the modular API architecture.
"""

from src.config import logger
from src.utils import parse_response

class PlatformMixin:
    async def detect_device_platform(self, rid: str):
        """
        Heuristically detect the platform (Android/iOS) of a booked device using device info and log files.
        Returns a dict with detected platform and hints.
        """
        await self.check_token_validity()
        logger.info(f"Detecting platform for device RID: {rid}")
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
        platform = "unknown"
        platform_hints = []
        device_info = str(data).lower()
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
            try:
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