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
        self.username = os.environ.get("PCLOUDY_USERNAME")
        self.api_key = os.environ.get("PCLOUDY_API_KEY")
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