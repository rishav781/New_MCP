import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pcloudy_mcp_server.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pcloudy-mcp-server")

class Config:
    PCLOUDY_BASE_URL = "https://device.pcloudy.com/api"
    REQUEST_TIMEOUT = 60  # Increase timeout to 60 seconds (or higher as needed)
    TOKEN_REFRESH_THRESHOLD = 3600
    DEFAULT_PLATFORM = "android"
    DEFAULT_DURATION = 30
    VALID_PLATFORMS = ["android", "ios"]