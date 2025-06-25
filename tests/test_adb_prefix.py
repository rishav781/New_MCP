import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
from api.adb import AdbMixin
import asyncio
from unittest.mock import patch, AsyncMock

class DummyAdb(AdbMixin):
    def __init__(self):
        self.base_url = "http://localhost"
        self.auth_token = "dummy_token"
    async def check_token_validity(self):
        pass

def make_mock_response(command):
    class MockResponse:
        def json(self_inner):
            return {"result": {"code": 200, "msg": "success", "adbreply": "output", "command": command}}
        def raise_for_status(self_inner):
            pass
    return MockResponse()

def test_strip_adb_prefix():
    adb = DummyAdb()
    async def run():
        with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=lambda url, json, headers: make_mock_response(json["adbCommand"]))) as mock_post:
            # Should strip 'adb ' prefix
            command = 'adb shell getprop ro.build.version.release'
            result = await adb.execute_adb_command('dummy_rid', command)
            assert result['command'] == 'shell getprop ro.build.version.release'
            # Should not strip if no prefix
            command2 = 'shell getprop ro.build.version.release'
            result2 = await adb.execute_adb_command('dummy_rid', command2)
            assert result2['command'] == 'shell getprop ro.build.version.release'
    asyncio.run(run())
