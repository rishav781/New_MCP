import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from unittest.mock import patch, AsyncMock
import pytest
import asyncio
from mcp_server.tools.appium_capabilities_tool import appium_capabilities

def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

def test_appium_capabilities_success():
    mock_caps = {
        "platformName": "Android",
        "deviceName": "Pixel8",
        "automationName": "UiAutomator2"
    }
    with patch("mcp_server.tools.appium_capabilities_tool.PCloudyAPI") as MockAPI:
        instance = MockAPI.return_value
        instance.auth_token = "dummy_token"
        instance.get_appium_capabilities = AsyncMock(return_value=mock_caps)
        # Specify language to match new implementation
        result = run_async(appium_capabilities(rid="123456", platform="android", language="java"))
        assert not result["isError"]
        # The new implementation does not return a 'json' key, so just check for code output
        assert "DesiredCapabilities capabilities" in result["content"][0]["code"]

def test_appium_capabilities_java_android():
    result = run_async(appium_capabilities(rid="123456", platform="android", language="java"))
    assert not result["isError"]
    assert "DesiredCapabilities capabilities" in result["content"][0]["code"]
    assert 'automationName", "uiautomator2"' in result["content"][0]["code"]
    assert 'platformName", "Android"' in result["content"][0]["code"]

def test_appium_capabilities_java_ios():
    result = run_async(appium_capabilities(rid="123456", platform="ios", language="java"))
    assert not result["isError"]
    assert "DesiredCapabilities capabilities" in result["content"][0]["code"]
    assert 'automationName", "XCUITest"' in result["content"][0]["code"]
    assert 'platformName", "iOS"' in result["content"][0]["code"]

def test_appium_capabilities_python_android():
    result = run_async(appium_capabilities(rid="123456", platform="android", language="python"))
    assert not result["isError"]
    assert 'from appium import webdriver' in result["content"][0]["code"]
    assert '"automationName": "uiautomator2"' in result["content"][0]["code"]
    assert '"platformName": "Android"' in result["content"][0]["code"]

def test_appium_capabilities_python_ios():
    result = run_async(appium_capabilities(rid="123456", platform="ios", language="python"))
    assert not result["isError"]
    assert 'from appium import webdriver' in result["content"][0]["code"]
    assert '"automationName": "XCUITest"' in result["content"][0]["code"]
    assert '"platformName": "iOS"' in result["content"][0]["code"]

def test_appium_capabilities_js_android():
    result = run_async(appium_capabilities(rid="123456", platform="android", language="js"))
    print("\nJS Android Output:\n", result["content"][0]["code"])
    assert not result["isError"]
    assert 'const wdio = require' in result["content"][0]["code"]
    assert "automationName: 'uiautomator2'" in result["content"][0]["code"]
    assert "platformName: 'Android'" in result["content"][0]["code"]

def test_appium_capabilities_js_ios():
    result = run_async(appium_capabilities(rid="123456", platform="ios", language="js"))
    print("\nJS iOS Output:\n", result["content"][0]["code"])
    assert not result["isError"]
    assert 'const wdio = require' in result["content"][0]["code"]
    assert "automationName: 'XCUITest'" in result["content"][0]["code"]
    assert "platformName: 'iOS'" in result["content"][0]["code"]

def test_appium_capabilities_no_language():
    result = run_async(appium_capabilities(rid="123456", platform="android", language=""))
    assert result["isError"]
    assert "Please specify your preferred programming language" in result["content"][0]["text"]

def test_appium_capabilities_no_rid():
    result = run_async(appium_capabilities(rid="", platform="android", language="java"))
    assert result["isError"]
    assert "Please specify a rid" in result["content"][0]["text"]

def test_appium_capabilities_no_caps():
    with patch("mcp_server.tools.appium_capabilities_tool.PCloudyAPI") as MockAPI:
        instance = MockAPI.return_value
        instance.auth_token = "dummy_token"
        instance.get_appium_capabilities = AsyncMock(return_value=None)
        # Specify language to match new implementation
        result = run_async(appium_capabilities(rid="123456", platform="android", language="java"))
        # The new implementation does not use get_appium_capabilities, so it will always return code, not an error
        # So, check that it returns code, not an error
        assert not result["isError"]
        assert "DesiredCapabilities capabilities" in result["content"][0]["code"]

def test_appium_capabilities_unsupported_language():
    result = run_async(appium_capabilities(rid="123456", platform="android", language="ruby"))
    assert result["isError"]
    assert "Boilerplate for language" in result["content"][0]["text"]
