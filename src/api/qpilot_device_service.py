"""
QPilot Device/Service Control API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotDeviceServiceMixin:
    async def start_wda(self, rid: str, action: str = "start", os: str = "ios"):
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v2/qpilot/wda/control"
        headers = {"token": self.auth_token, "Origin": Config.get_origin()}
        payload = {"rid": rid, "action": action, "os": os}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error starting WDA: {str(e)}")
            return {"error": str(e)}

    async def start_appium(self, rid: str, os: str, appName: str, action: str = "start"):
        url = f"https://{Config.QPILOT_BASE_HOSTNAME}/api/v2/qpilot/appium/control"
        headers = {"token": self.auth_token, "Origin": Config.get_origin()}
        payload = {"rid": rid, "action": action, "os": os, "appName": appName}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                # After successful Appium start, get device URL and open in browser
                if result.get('status') == 200:
                    try:
                        device_url = await self.get_device_url(rid)
                        if device_url and isinstance(device_url, dict) and device_url.get('url'):
                            import webbrowser
                            webbrowser.open(device_url['url'], new=2)
                            result['device_url'] = device_url['url']
                    except Exception as e:
                        logger.warning(f"Could not open browser for device URL: {str(e)}")
                return result
        except Exception as e:
            logger.error(f"Error starting Appium: {str(e)}")
            return {"error": str(e)}
