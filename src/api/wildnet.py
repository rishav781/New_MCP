from config import Config, logger
from utils import encode_auth, parse_response

class WildnetMixin:
    async def start_wildnet(self, rid: str):
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