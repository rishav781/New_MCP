"""
Configuration and logging setup for the pCloudy MCP server.

- Loads environment variables from the .env file.
- Configures logging to both file and console.
- Defines the Config class for global constants.
"""

import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file in project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Configure logging with absolute path to project root
project_root = os.path.dirname(os.path.dirname(__file__))
log_file_path = os.path.join(project_root, "pcloudy_mcp_server.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pcloudy-mcp-server")

class Config:
    """
    Global configuration constants for the MCP server.
    """
    PCLOUDY_BASE_URL = "https://device.pcloudy.com/api"
    REQUEST_TIMEOUT = 60  # Increase timeout to 60 seconds (or higher as needed)
    TOKEN_REFRESH_THRESHOLD = 3600
    DEFAULT_PLATFORM = "android"
    DEFAULT_DURATION = 30
    VALID_PLATFORMS = ["android", "ios"]
    HOSTNAME = "https://prod-backend.qpilot.pcloudy.com"
    Bookinghost ="https://device.pcloudy.com"