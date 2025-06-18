import httpx
from typing import Dict, Any
from config import Config, logger
from .core import PCloudyAPI
from utils import parse_response

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
        if auto_start_services and rid:
            try:
                logger.info(f"Auto-starting device services for RID: {rid}")
                import asyncio
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
                    "content": [{"type": "text", "text": f"✅ Device {rid} released successfully"}],
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

async def set_device_location(self, rid: str, latitude: float, longitude: float) -> Dict[str, Any]:
    try:
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
    except Exception as e:
        logger.error(f"Error setting device location: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error setting device location: {str(e)}"}],
            "isError": True
        }

async def detect_device_platform(self, rid: str) -> Dict[str, Any]:
    try:
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
    except Exception as e:
        logger.error(f"Error detecting device platform: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error detecting device platform: {str(e)}"}],
            "isError": True,
            "platform": "unknown"
        }