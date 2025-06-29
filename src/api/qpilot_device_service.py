"""
QPilot Device/Service Control API Mixin for pCloudy MCP Server
"""

import httpx
from config import logger, Config

class QpilotDeviceServiceMixin:
    async def start_wda(self, rid: str, action: str = "start", os: str = "ios"):
        hostname = Config.QPILOT_BASE_HOSTNAME
        url = f"https://{hostname}/api/v2/qpilot/wda/control"
        headers = {"token": self.auth_token, "Origin": f"https://{hostname}"}
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
        hostname = Config.QPILOT_BASE_HOSTNAME
        url = f"https://{hostname}/api/v2/qpilot/appium/control"
        headers = {"token": self.auth_token, "Origin": f"https://{hostname}"}
        payload = {"rid": rid, "action": action, "os": os, "appName": appName}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error starting Appium: {str(e)}")
            return {"error": str(e)}
