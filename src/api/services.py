from config import logger
import httpx

class ServicesMixin:
    async def start_device_services(self, rid: str, start_device_logs: bool = True, start_performance_data: bool = True, start_session_recording: bool = True):
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