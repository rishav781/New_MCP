pytest_plugins = ["pytest_asyncio"]

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from unittest.mock import patch
import pytest
import asyncio
import types

class DummyMCP:
    def tool(self):
        def decorator(fn):
            return fn
        return decorator

# Patch sys.modules to allow 'from shared_mcp import mcp' to work in test context
sys.modules['shared_mcp'] = types.SimpleNamespace(mcp=DummyMCP())
from mcp_server.tools.appium_capabilities_tool import appium_capabilities

@pytest.mark.asyncio
async def test_appium_capabilities_java():
    result = await appium_capabilities(language="java")
    assert not result["isError"]
    assert "DesiredCapabilities capabilities" in result["content"][0]["code"]
    assert 'automationName' in result["content"][0]["code"]
    assert 'platformName' in result["content"][0]["code"]

@pytest.mark.asyncio
async def test_appium_capabilities_python():
    result = await appium_capabilities(language="python")
    assert not result["isError"]
    assert 'from appium import webdriver' in result["content"][0]["code"]
    assert 'automationName' in result["content"][0]["code"]
    assert 'platformName' in result["content"][0]["code"]

@pytest.mark.asyncio
async def test_appium_capabilities_js():
    result = await appium_capabilities(language="js")
    assert not result["isError"]
    assert 'const wdio = require' in result["content"][0]["code"]
    assert 'automationName' in result["content"][0]["code"]
    assert 'platformName' in result["content"][0]["code"]

@pytest.mark.asyncio
async def test_appium_capabilities_javascript():
    result = await appium_capabilities(language="javascript")
    assert not result["isError"]
    assert 'const wdio = require' in result["content"][0]["code"]
    assert 'automationName' in result["content"][0]["code"]
    assert 'platformName' in result["content"][0]["code"]

@pytest.mark.asyncio
async def test_appium_capabilities_no_language():
    result = await appium_capabilities(language="")
    assert result["isError"]
    assert "Please specify your preferred programming language" in result["content"][0]["text"]

@pytest.mark.asyncio
async def test_appium_capabilities_unsupported_language():
    result = await appium_capabilities(language="ruby")
    assert result["isError"]
    assert "Boilerplate for language" in result["content"][0]["text"]
