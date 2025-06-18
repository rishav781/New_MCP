import base64
import json
import logging
import os
import re
from typing import Dict, Any
import httpx

logger = logging.getLogger("pcloudy-mcp-server")

def encode_auth(username: str, api_key: str) -> str:
    return base64.b64encode(f"{username}:{api_key}".encode()).decode()

def parse_response(response: httpx.Response) -> Dict[str, Any]:
    try:
        data = response.json()
        if "result" not in data:
            logger.error(f"Invalid response format: {json.dumps(data)}")
            raise ValueError(f"Invalid response format: {json.dumps(data)}")
        return data["result"]
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON response: {response.text}")
        raise ValueError(f"Invalid JSON response: {response.text}")
    except Exception as e:
        logger.error(f"Error parsing response: {str(e)}")
        raise

def validate_filename(filename: str) -> bool:
    """Validate if filename is safe and exists"""
    if not filename or not isinstance(filename, str):
        return False
    # Check for dangerous characters
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    return not any(char in filename for char in dangerous_chars)

def extract_package_name_hint(filename: str) -> str:
    """Extract package name hint from filename"""
    if not filename:
        return ""
    # Remove file extension and common prefixes/suffixes
    name = os.path.splitext(filename)[0]
    # Remove common patterns
    name = re.sub(r'[_-]?(debug|release|prod|test)[_-]?', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[_-]?v?\d+(\.\d+)*[_-]?', '', name)  # Remove version numbers
    return name.lower()