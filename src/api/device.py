"""
Device Management Mixin for pCloudy MCP Server

Provides device management operations for the PCloudyAPI class:
- get_devices_list: List available devices for a platform
- book_device: Book a device by ID
- release_device: Release a booked device by RID

Intended to be used as a mixin in the modular API architecture.
"""

from config import Config, logger
from utils import encode_auth, parse_response
import httpx
import asyncio

class DeviceMixin:
    async def get_devices_list(self, platform: str = Config.DEFAULT_PLATFORM, duration: int = Config.DEFAULT_DURATION, available_now: bool = True):
        """
        List available devices for a given platform and duration.
        Returns a dict with device models and availability.
        """
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

    async def book_device(self, device_id: str, duration: int = Config.DEFAULT_DURATION, auto_start_services: bool = True):
        """
        Book a device by its ID. Optionally auto-starts device services.
        Returns booking info and optionally enhanced content.
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
                {"type": "text", "text": f"\u2705 Device booked successfully. RID: {rid}"}
            ]
            if auto_start_services and rid:
                try:
                    logger.info(f"Auto-starting device services for RID: {rid}")
                    await asyncio.sleep(2)
                    services_result = await self.start_device_services(rid)
                    if not services_result.get("isError", True):
                        response_content.extend(services_result.get("content", []))
                        logger.info(f"Device services started successfully for RID: {rid}")
                    else:
                        response_content.append({
                            "type": "text", 
                            "text": "\u26a0\ufe0f Device services failed to start automatically, but device is booked successfully"
                        })
                        response_content.append({
                            "type": "text", 
                            "text": "\ud83d\udca1 You can manually start services with: start_device_services(rid=\"" + str(rid) + "\")"
                        })
                        logger.warning(f"Failed to auto-start device services: {services_result}")
                except Exception as service_error:
                    logger.warning(f"Failed to auto-start device services: {str(service_error)}")
                    response_content.append({
                        "type": "text", 
                        "text": "\u26a0\ufe0f Device services failed to start automatically, but device is booked successfully"
                    })
                    response_content.append({
                        "type": "text", 
                        "text": "\ud83d\udca1 You can manually start services with: start_device_services(rid=\"" + str(rid) + "\")"
                    })
            enhanced_result = result.copy()
            enhanced_result["enhanced_content"] = response_content
            return enhanced_result
        except httpx.RequestError as e:
            logger.error(f"Device booking request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error booking device: {str(e)}")
            raise

    async def release_device(self, rid: str, auto_download: bool = False):
        """
        Release a booked device by its RID. Optionally auto-downloads session data.
        Returns a dict with release status and messages.
        """
        try:
            await self.check_token_validity()
            logger.info(f"Releasing device with RID: {rid} (this may take 10-20 seconds)")
            url = f"{self.base_url}/release_device"
            payload = {"token": self.auth_token, "rid": int(rid)}
            headers = {"Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=30.0) as release_client:
                response = await release_client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = parse_response(response)
                if result.get("code") == 200 and result.get("msg") == "success":
                    logger.info(f"Device {rid} released successfully")
                    return {
                        "content": [{"type": "text", "text": f"\u2705 Device {rid} released successfully"}],
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