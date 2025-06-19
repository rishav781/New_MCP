"""
Utility functions for the pCloudy MCP server.

- Handles HTTP authentication encoding.
- Parses and validates API responses.
- Provides logging for error handling and debugging.
"""

import base64
import json
import httpx
from typing import Dict, Any
from config import Config, logger

def encode_auth(username: str, api_key: str) -> str:
    """
    Encode username and API key for HTTP Basic Authentication.
    Returns a base64-encoded string suitable for HTTP headers.
    """
    return base64.b64encode(f"{username}:{api_key}".encode()).decode()

def parse_response(response: httpx.Response) -> Dict[str, Any]:
    """
    Parse the JSON response from the pCloudy API.
    Raises ValueError if the response is invalid or missing the 'result' key.
    Returns the 'result' dictionary from the response.
    """
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