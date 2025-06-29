import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
import asyncio
from src.mcp_server.tools import qpilot_tool

import types

@pytest.mark.asyncio
@pytest.mark.parametrize("action,params,should_error", [
    ("get_credits", {}, False),
    ("project_list", {}, False),
    ("create_project", {"name": "TestProject"}, False),
    ("get_test_suites", {}, False),
    ("create_test_suite", {"name": "TestSuite"}, False),
    ("create_test_case", {"testSuiteId": "1", "testCaseName": "TestCase", "platform": "Android"}, False),
    ("get_tests", {}, False),
    ("start_wda", {"rid": "dummy_rid"}, True),  # Likely to error without real rid
    ("start_appium", {"rid": "dummy_rid", "platform": "Android", "appName": "TestApp"}, True),
    ("generate_code", {"rid": "dummy_rid", "feature": "login", "testcaseid": "1", "testSuiteId": "1", "appPackage": "com.example", "appName": "TestApp", "appActivity": "MainActivity", "steps": "step1", "projectId": "1", "testdata": {}}, True),
    ("create_script", {"testcaseid": "1", "testSuiteId": "1"}, True),
    ("unknown_action", {}, True),
])
async def test_qpilot_tool_all_actions(monkeypatch, action, params, should_error):
    # Set dummy env vars for authentication
    monkeypatch.setenv("PCLOUDY_USERNAME", "dummyuser")
    monkeypatch.setenv("PCLOUDY_API_KEY", "dummykey")
    # Patch QpilotAPI methods to avoid real HTTP calls
    class DummyAPI:
        async def authenticate(self): return None
        async def get_qpilot_credits(self): return {"credits": 10}
        async def project_list(self, getShared): return {"projects": []}
        async def create_project(self, name): return {"project": name}
        async def get_test_suites(self): return {"suites": []}
        async def create_test_suite(self, name): return {"suite": name}
        async def create_test_case(self, testSuiteId, testCaseName, platform): return {"test_case": testCaseName}
        async def get_test_cases(self, getShared): return {"tests": []}
        async def start_wda(self, rid): raise Exception("No device")
        async def start_appium(self, rid, platform, appName): raise Exception("No device")
        async def generate_code(self, *a, **k): raise Exception("No device")
        async def create_script(self, testcaseid, testSuiteId): raise Exception("No device")
        async def close(self): return None
    monkeypatch.setattr(qpilot_tool, "QpilotAPI", lambda *a, **k: DummyAPI())
    # Call the tool
    coro = qpilot_tool.qpilot(action=action, **params)
    result = await coro
    if should_error:
        assert "error" in result or "warning" in result
    else:
        assert isinstance(result, dict)
        assert not ("error" in result and result["error"]) 