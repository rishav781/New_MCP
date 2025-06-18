import httpx
import json
import webbrowser
import re
from typing import Dict, Any
from config import Config, logger
from .core import PCloudyAPI
from utils import parse_response

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

async def execute_adb_command(self, rid: str, adb_command: str) -> Dict[str, Any]:
    try:
        await self.check_token_validity()
        
        if not adb_command.strip():
            raise ValueError("ADB command cannot be empty")
            
        adb_command = adb_command.strip().strip('"').strip("'")
        
        logger.info(f"Executing ADB command on RID {rid}: {adb_command}")
        
        url = f"{self.base_url}/execute_adb"
        payload = {
            "token": self.auth_token,
            "rid": rid,
            "adbCommand": adb_command
        }
        headers = {"Content-Type": "application/json"}
        
        timeout_config = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=30.0)
        
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            logger.debug(f"Sending ADB request to: {url}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            raw_data = response.json()
            logger.info(f"Raw ADB response: {json.dumps(raw_data, indent=2)}")
            
            if isinstance(raw_data, dict):
                result = raw_data.get("result", raw_data)
                
                status_code = result.get("code", 0)
                message = result.get("msg", "")
                
                output_content = None
                output_source = None
                
                for field_name in ["adbreply", "output", "reply", "response", "data", "result"]:
                    if field_name in result and result[field_name] is not None:
                        output_content = result[field_name]
                        output_source = field_name
                        break
                
                if output_content is not None:
                    formatted_output = str(output_content)
                    if "\\n" in formatted_output:
                        formatted_output = formatted_output.replace("\\n", "\n")
                    formatted_output = formatted_output.strip()
                    
                    if not formatted_output:
                        formatted_output = "[Command executed successfully but returned empty output]"
                else:
                    formatted_output = "[No output returned from device]"
                    logger.warning(f"No output found in response fields. Available keys: {list(result.keys())}")
                
                is_success = status_code == 200 and "Invalid Command" not in formatted_output
                
                if is_success:
                    logger.info(f"ADB command successful. Output source: {output_source}, Length: {len(formatted_output)}")
                    return {
                        "success": True,
                        "output": formatted_output,
                        "command": adb_command,
                        "rid": rid,
                        "status_code": status_code,
                        "message": message,
                        "output_source": output_source
                    }
                else:
                    error_msg = f"ADB command failed: {formatted_output}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "command": adb_command,
                        "rid": rid,
                        "status_code": status_code,
                        "raw_response": raw_data
                    }
            else:
                logger.error(f"Unexpected response format: {type(raw_data)}")
                return {
                    "success": False,
                    "error": f"Unexpected response format: {type(raw_data)}",
                    "command": adb_command,
                    "rid": rid
                }
    except httpx.TimeoutException:
        logger.error(f"ADB command timed out for RID {rid}: {adb_command}")
        return {
            "success": False,
            "error": "Command timed out after 120 seconds",
            "command": adb_command,
            "rid": rid
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error executing ADB command: {e.response.status_code} - {e.response.text}")
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "command": adb_command,
            "rid": rid
        }
    except Exception as e:
        logger.error(f"Unexpected error executing ADB command: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "command": adb_command,
            "rid": rid
        }

async def start_wildnet(self, rid: str) -> Dict[str, Any]:
    try:
        if not rid:
            raise ValueError("Device booking ID (rid) is required")
        
        url = f"{self.base_url}/api/startwildnet"
        payload = {
            "token": self.auth_token,
            "rid": rid
        }
        
        logger.info(f"Starting wildnet for device booking ID: {rid}")
        
        response = await self.client.post(url, json=payload)
        result = parse_response(response)
        
        if result.get("result") == "success":
            logger.info(f"Wildnet started successfully for device booking ID: {rid}")
            return {
                "content": [
                    {"type": "text", "text": f"✅ Wildnet started successfully for RID {rid}"},
                    {"type": "text", "text": "🌐 Enhanced network capabilities are now active on the device"}
                ],
                "isError": False
            }
        else:
            error_msg = result.get("error", "Unknown error starting wildnet")
            logger.error(f"Failed to start wildnet: {error_msg}")
            return {
                "content": [{"type": "text", "text": f"Failed to start wildnet: {error_msg}"}],
                "isError": True
            }
    except Exception as e:
        error_msg = f"Error starting wildnet for device {rid}: {str(e)}"
        logger.error(error_msg)
        return {
            "content": [{"type": "text", "text": error_msg}],
            "isError": True
        }

async def start_device_services(self, rid: str, start_device_logs: bool = True, start_performance_data: bool = True, start_session_recording: bool = True) -> Dict[str, Any]:
    try:
        await self.check_token_validity()
        logger.info(f"Starting device services for RID: {rid}")
        
        url = f"{self.base_url}/startdeviceservices"
        payload = {
            "token": self.auth_token,
            "rid": rid,
            "startDeviceLogs": str(start_device_logs).lower(),
            "startPerformanceData": str(start_performance_data).lower(),
            "startSessionRecording": str(start_session_recording).lower()
        }
        headers = {"Content-Type": "application/json"}
        response = await self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        logger.info(f"Device services response status: {response.status_code}")
        logger.info(f"Device services response text: {response.text}")
        
        services_started = []
        if start_device_logs:
            services_started.append("📝 Device Logs")
        if start_performance_data:
            services_started.append("📊 Performance Data")
        if start_session_recording:
            services_started.append("🎥 Session Recording")
        
        return {
            "content": [
                {"type": "text", "text": f"✅ Device services request sent for RID {rid}"},
                {"type": "text", "text": f"📋 Requested services: {', '.join(services_started)}"},
                {"type": "text", "text": f"🔍 Response: {response.status_code} - {response.text[:200]}"}
            ],
            "isError": False
        }
    except Exception as e:
        logger.error(f"Error starting device services: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "content": [{"type": "text", "text": f"Error starting device services: {str(e)}"}],
            "isError": True
        }