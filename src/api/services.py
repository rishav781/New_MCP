"""
Device Services Mixin for pCloudy MCP Server

Provides device service management for the PCloudyAPI class:
- start_device_services: Start logs, performance data, and session recording for a booked device

Intended to be used as a mixin in the modular API architecture.
"""

from config import Config, logger
import httpx
from utils import encode_auth, parse_response

class ServicesMixin:
    async def start_device_services(self, rid: str, start_device_logs: bool = True, start_performance_data: bool = True, start_session_recording: bool = True):
        """
        Start device services (logs, performance data, session recording) for a booked device.
        Returns a dict with service status and messages.
        """
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

    async def start_performance_data(self, rid: str):
        """
        Start performance data collection for a booked device using the /api/start_performance_data endpoint.
        Returns a dict with the status and response.
        """
        await self.check_token_validity()
        logger.info(f"Starting performance data for RID: {rid}")
        url = f"{self.base_url}/start_performance_data"
        payload = {
            "token": self.auth_token,
            "rid": rid
        }
        headers = {"Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Performance data response: {response.status_code}")
            logger.info(f"Performance data response text: {response.text}")
            return {
                "content": [
                    {"type": "text", "text": f"✅ Performance data request sent for RID {rid}"},
                    {"type": "text", "text": f"🔍 Response: {response.status_code} - {response.text[:200]}"}
                ],
                "isError": False
            }
        except Exception as e:
            logger.error(f"Error starting performance data: {str(e)}")
            return {
                "content": [
                    {"type": "text", "text": f"❌ Error starting performance data for RID {rid}: {str(e)}"}
                ],
                "isError": True
            }