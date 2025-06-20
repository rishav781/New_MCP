import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import asyncio
import pytest
from api import PCloudyAPI

@pytest.mark.asyncio
async def test_get_devices_list():
    username = os.environ.get("PCLOUDY_USERNAME")
    api_key = os.environ.get("PCLOUDY_API_KEY")
    assert username and api_key, "PCLOUDY_USERNAME or PCLOUDY_API_KEY not set in environment."
    api = PCloudyAPI()
    try:
        await api.authenticate()
        devices = await api.get_devices_list()
        models = devices.get('models', [])
        assert isinstance(models, list), "Device list is not a list."
        assert len(models) > 0, "No devices found."
    finally:
        await api.close()
