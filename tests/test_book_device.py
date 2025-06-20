import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import asyncio
import pytest
from api import PCloudyAPI

@pytest.mark.asyncio
async def test_book_device():
    username = os.environ.get("PCLOUDY_USERNAME")
    api_key = os.environ.get("PCLOUDY_API_KEY")
    assert username and api_key, "PCLOUDY_USERNAME or PCLOUDY_API_KEY not set in environment."
    api = PCloudyAPI()
    try:
        await api.authenticate()
        devices = await api.get_devices_list()
        models = devices.get('models', [])
        assert models, "No devices available to book."
        device_id = models[0]['id']
        booking = await api.book_device(device_id, auto_start_services=False)
        rid = booking.get('rid')
        assert rid, "Failed to book device."
        await api.release_device(rid)
    finally:
        await api.close()
