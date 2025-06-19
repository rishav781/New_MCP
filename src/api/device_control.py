from config import Config, logger
from utils import encode_auth, parse_response
import httpx

class DeviceControlMixin:
    async def capture_screenshot(self, rid: str, skin: bool = True):
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

    async def get_device_page_url(self, rid: str):
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

    async def set_device_location(self, rid: str, latitude: float, longitude: float):
        await self.check_token_validity()
        logger.info(f"Setting device location for RID {rid}: lat={latitude}, lon={longitude}")
        url = f"{self.base_url}/set_deviceLocation"
        payload = {
            "token": self.auth_token,
            "rid": rid,
            "latitude": latitude,
            "longitude": longitude
        }
        headers = {"Content-Type": "application/json"}
        response = await self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = parse_response(response)
        if result.get("code") == 200 or result.get("statuscode") == 200:
            logger.info(f"Device location set successfully for RID {rid}")
            return {
                "content": [
                    {"type": "text", "text": f"✅ GPS location set successfully for device {rid}"},
                    {"type": "text", "text": f"📍 Coordinates: {latitude}, {longitude}"}
                ],
                "isError": False
            }
        else:
            error_msg = result.get("msg", result.get("message", "Unknown error"))
            logger.error(f"Failed to set device location: {error_msg}")
            return {
                "content": [{"type": "text", "text": f"Failed to set device location: {error_msg}"}],
                "isError": True
            }