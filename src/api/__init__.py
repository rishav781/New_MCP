from .auth import AuthMixin
from .device import DeviceMixin
from .file_management import FileManagementMixin
from .services import ServicesMixin
from .app_management import AppManagementMixin
from .session import SessionMixin
from .adb import AdbMixin
from .platform import PlatformMixin
from .device_control import DeviceControlMixin
import os
import httpx
from config import Config, logger
from dotenv import load_dotenv

# Ensure .env is loaded if not already
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(project_root, '.env'))

class PCloudyAPI(
    AuthMixin,
    DeviceMixin,
    FileManagementMixin,
    ServicesMixin,
    AppManagementMixin,
    SessionMixin,
    AdbMixin,
    PlatformMixin,
    DeviceControlMixin
):
    def __init__(self, base_url=None):
        AuthMixin.__init__(self)
        DeviceMixin.__init__(self)
        FileManagementMixin.__init__(self)
        ServicesMixin.__init__(self)
        AppManagementMixin.__init__(self)
        SessionMixin.__init__(self)
        AdbMixin.__init__(self)
        PlatformMixin.__init__(self)
        DeviceControlMixin.__init__(self)
        # Fix: Use correct env var names and fallback
        self.username = os.environ.get("PCLOUDY_USERNAME") or os.environ.get("PLOUDY_USERNAME")
        self.api_key = os.environ.get("PCLOUDY_API_KEY") or os.environ.get("PLOUDY_API_KEY")
        if not self.username or not self.api_key:
            logger.warning("PCLOUDY_USERNAME or PCLOUDY_API_KEY not set. Check your .env file and environment.")
        self.base_url = base_url or Config.PCLOUDY_BASE_URL
        self.auth_token = None
        self.token_timestamp = None
        self.client = httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT)
        self.rid = None
        logger.info("PCloudyAPI initialized (modular)")

    async def close(self):
        """Close the HTTP client."""
        try:
            await self.client.aclose()
            logger.info("HTTP client closed")
        except Exception as e:
            logger.error(f"Error closing HTTP client: {str(e)}")