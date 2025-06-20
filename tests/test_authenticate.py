import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import asyncio
import pytest
from api import PCloudyAPI

@pytest.mark.asyncio
async def test_authenticate():
    username = os.environ.get("PCLOUDY_USERNAME")
    api_key = os.environ.get("PCLOUDY_API_KEY")
    assert username and api_key, "PCLOUDY_USERNAME or PCLOUDY_API_KEY not set in environment."
    api = PCloudyAPI()
    try:
        token = await api.authenticate()
        assert token, "Authentication failed, no token returned."
    finally:
        await api.close()
