import json
import re
import webbrowser
from typing import Dict, Any
from config import Config, logger
from pcloudy_api import PCloudyAPI
from fastmcp import FastMCP

mcp = FastMCP("pcloudy_auth3.0")
api = PCloudyAPI()

# =============================================================================
# IMPORTANT: ADB COMMAND FORMAT CONTEXT FOR LLM UNDERSTANDING
# =============================================================================
"""
CRITICAL ADB COMMAND FORMAT REQUIREMENTS:

⚠️  IMPORTANT: When executing ADB commands through pCloudy, you MUST use the complete 
    ADB command format including the 'adb shell' prefix.

❌ INCORRECT FORMAT (will return "Invalid Command"):
   - "shell getprop ro.build.version.release"
   - "getprop ro.build.version.release"  
   - "dumpsys battery"
   - "pm list packages"
   - "ls"
   - "ps"

✅ CORRECT FORMAT (will work successfully):
   - "adb shell getprop ro.build.version.release"
   - "adb shell dumpsys battery"
   - "adb shell pm list packages"
   - "adb shell ls"
   - "adb shell ps"
   - "adb shell date"
   - "adb shell cat /proc/cpuinfo"
   - "adb shell ifconfig"

PROVEN WORKING EXAMPLES FROM TESTING:
1. adb shell dumpsys battery → Returns detailed battery information
2. adb shell getprop ro.build.version.release → Returns Android version (e.g., "12")
3. adb shell getprop ro.product.model → Returns device model (e.g., "SM-G973F")
4. adb shell pm list packages | head -10 → Lists installed packages
5. adb shell cat /proc/cpuinfo | head -20 → Shows CPU information
6. adb shell cat /proc/meminfo | head -10 → Shows memory usage
7. adb shell ps | head -15 → Lists running processes
8. adb shell date → Shows current date/time
9. adb shell ifconfig → Shows network interfaces

EXAMPLE SUCCESSFUL RESPONSE FORMAT:
{
    "token": "qffs927k5xqhsgqr78p4w378",
    "rid": "3593636", 
    "adbCommand": "adb shell dumpsys battery"
}
{
    "result": {
        "token": "qffs927k5xqhsgqr78p4w378",
        "code": 200,
        "msg": "success", 
        "adbreply": "Current Battery Service state:\n  AC powered: false\n  USB powered: true..."
    }
}

Remember: Always include 'adb shell' prefix for shell commands!
"""

@mcp.tool()
async def device_control(
    action: str,
    rid: str = "",
    skin: bool = True,
    adb_command: str = "",
    platform: str = "auto",
    start_device_logs: bool = True,
    start_performance_data: bool = True,
    start_session_recording: bool = True
) -> Dict[str, Any]:
    """
    Device Control & Monitoring Operations: screenshot, get_url, start_services, adb, wildnet
    
    Actions:
    - screenshot: Capture device screenshot (rid="device_id", skin=True)
    - get_url: Get device page URL and open in browser (rid="device_id")
    - start_services: Start device services (rid="device_id")
    - adb: Execute ADB command on Android (rid="device_id", adb_command="adb shell dumpsys battery")
           ⚠️  CRITICAL: Use FULL command format with 'adb shell' prefix!
    - wildnet: Start wildnet features (rid="device_id")
    """
    logger.info(f"Tool called: device_control with action={action}, rid={rid}")
    try:
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
            
        if action == "screenshot":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter for screenshot"}],
                    "isError": True
                }
            return await api.capture_screenshot(rid, skin)
            
        elif action == "get_url":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter to get device URL"}],
                    "isError": True
                }
            url_response = await api.get_device_page_url(rid)
            
            device_url = None
            if isinstance(url_response, dict) and "content" in url_response:
                for content_item in url_response["content"]:
                    if "text" in content_item:
                        url_text = content_item["text"]
                        if "http" in url_text:
                            url_match = re.search(r'https?://[^\s]+', url_text)
                            if url_match:
                                device_url = url_match.group(0)
                            else:
                                device_url = url_text.strip()
                            break
            else:
                device_url = str(url_response).strip()
            
            if device_url and device_url.startswith('http'):
                webbrowser.open(device_url)
                logger.info(f"Opened device page URL in browser: {device_url}")
                return {
                    "content": [{"type": "text", "text": f"Device page opened in browser: {device_url}"}],
                    "isError": False
                }
            else:
                return {
                    "content": [{"type": "text", "text": f"Error: Invalid URL received: {device_url}"}],
                    "isError": True
                }
                
        elif action == "start_services":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter to start services"}],
                    "isError": True
                }
            result = await api.start_device_services(rid, start_device_logs, start_performance_data, start_session_recording)
            return result
            
        elif action == "adb":
            if not rid or not adb_command:
                return {
                    "content": [{"type": "text", "text": "Please specify both rid and adb_command parameters"}],
                    "isError": True
                }
            
            if platform.lower() == "auto":
                logger.info(f"Auto-detecting platform for device RID: {rid}")
                try:
                    detection_result = await api.detect_device_platform(rid)
                    detected_platform = detection_result.get("platform", "unknown")
                    logger.info(f"Auto-detected platform: {detected_platform}")
                    platform = detected_platform
                except Exception as detection_error:
                    logger.warning(f"Platform auto-detection failed: {str(detection_error)}, defaulting to android")
                    platform = "android"
            
            platform = platform.lower().strip()
            if platform == "ios":
                logger.warning(f"ADB command attempted on iOS device (RID: {rid})")
                return {
                    "content": [{
                        "type": "text",
                        "text": (
                            "❌ Error: ADB commands are only supported on Android devices. "
                            "The specified device appears to be iOS. ADB (Android Debug Bridge) "
                            "is an Android-specific tool and cannot be used with iOS devices."
                        )
                    }],
                    "isError": True
                }
            
            if not adb_command.strip():
                return {
                    "content": [{"type": "text", "text": "❌ Error: ADB command cannot be empty"}],
                    "isError": True
                }
            
            if not adb_command.startswith("adb "):
                logger.warning(f"ADB command may be missing 'adb' prefix: {adb_command}")
                return {
                    "content": [{
                        "type": "text", 
                        "text": (
                            f"⚠️  Warning: ADB command should start with 'adb shell' or 'adb '.\n"
                            f"Received: '{adb_command}'\n\n"
                            f"✅ Correct format examples:\n"
                            f"  - 'adb shell dumpsys battery'\n"
                            f"  - 'adb shell getprop ro.build.version.release'\n"
                            f"  - 'adb shell pm list packages'\n\n"
                            f"❌ Incorrect format (will fail):\n"
                            f"  - 'shell dumpsys battery'\n"
                            f"  - 'dumpsys battery'\n"
                            f"  - 'getprop ro.build.version.release'\n\n"
                            f"Please use the complete ADB command format."
                        )
                    }],
                    "isError": True
                }
            
            result = await api.execute_adb_command(rid, adb_command)
            
            if result.get("success", False):
                output = result.get("output", "[No output]")
                command = result.get("command", adb_command)
                status_code = result.get("status_code", 200)
                message = result.get("message", "success")
                output_source = result.get("output_source", "unknown")
                
                return {
                    "content": [
                        {"type": "text", "text": f"✅ ADB command executed successfully"},
                        {"type": "text", "text": f"📋 Command: {command}"},
                        {"type": "text", "text": f"📊 Status: {message} (Code: {status_code})"},
                        {"type": "text", "text": f"🔍 Output Source: {output_source}"},
                        {"type": "text", "text": f"📄 Output:\n{output}"}
                    ],
                    "isError": False
                }
            else:
                error = result.get("error", "Unknown error")
                command = result.get("command", adb_command)
                status_code = result.get("status_code", "Unknown")
                raw_response = result.get("raw_response", {})
                
                return {
                    "content": [
                        {"type": "text", "text": f"❌ ADB command failed: {error}"},
                        {"type": "text", "text": f"📋 Command: {command}"},
                        {"type": "text", "text": f"📊 Error Code: {status_code}"},
                        {"type": "text", "text": f"🔍 Raw Response: {json.dumps(raw_response, indent=2) if raw_response else 'None'}"}
                    ],
                    "isError": True
                }
                
        elif action == "wildnet":
            if not rid:
                return {
                    "content": [{"type": "text", "text": "Please specify a rid parameter to start wildnet"}],
                    "isError": True
                }
            result = await api.start_wildnet(rid)
            return result
            
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown action: '{action}'. Available actions: screenshot, get_url, start_services, adb, wildnet"}],
                "isError": True
            }
            
    except Exception as e:
        logger.error(f"Error in device_control: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in device control: {str(e)}"}],
            "isError": True
        }