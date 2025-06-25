"""
Appium Capabilities Tool for pCloudy MCP Server

Provides a FastMCP tool to generate and display Appium capabilities for Android and iOS devices booked via pCloudy.
"""

from config import logger
from api import PCloudyAPI
from shared_mcp import mcp

@mcp.tool()
async def appium_capabilities(language: str = ""):
    """
    FastMCP Tool: Appium Capabilities Boilerplate (Raw)
    
    Parameters:
        language: Preferred programming language for the code snippet (e.g., 'java', 'python', 'js').
    Returns:
        Dict with Appium boilerplate code and error status, and hints for filling in real values.
    """
    logger.info(f"Tool called: appium_capabilities (raw boilerplate) with language={language}")
    try:
        if not language:
            return {
                "content": [{"type": "text", "text": "Please specify your preferred programming language (e.g., 'java', 'python', 'js')."}],
                "isError": True
            }
        lang = language.lower()
        placeholders = {
            "pCloudy_Username": "<YOUR_EMAIL>",
            "pCloudy_ApiKey": "<YOUR_API_KEY>",
            "pCloudy_ApplicationName": "<APP_FILE_NAME>",
            "pCloudy_DurationInMinutes": "<DURATION_MINUTES>",
            "pCloudy_DeviceManafacturer": "<DEVICE_MANUFACTURER>",
            "pCloudy_DeviceVersion": "<DEVICE_VERSION>",
            "pCloudy_DeviceFullName": "<DEVICE_FULL_NAME>",
            "platformVersion": "<PLATFORM_VERSION>",
            "appPackage": "<APP_PACKAGE>",
            "appActivity": "<APP_ACTIVITY>",
            "bundleId": "<BUNDLE_ID>"
        }
        # Platform-specific (default to Android, user can edit)
        plat = "android"
        automation = {"java": "uiautomator2", "python": "uiautomator2", "js": "uiautomator2", "javascript": "uiautomator2"}
        platform_name = "Android"
        driver = {"java": "AndroidDriver", "python": "webdriver.Remote", "js": "wdio.remote", "javascript": "wdio.remote"}
        # Templates
        templates = {
            "java": '''public void prepareTest() throws IOException, InterruptedException {{
    DesiredCapabilities capabilities = new DesiredCapabilities();
    capabilities.setCapability("pCloudy_Username", "{pCloudy_Username}");
    capabilities.setCapability("pCloudy_ApiKey", "{pCloudy_ApiKey}");
    capabilities.setCapability("pCloudy_ApplicationName", "{pCloudy_ApplicationName}");
    capabilities.setCapability("pCloudy_DurationInMinutes", {pCloudy_DurationInMinutes});
    //capabilities.setCapability("pCloudy_DeviceManafacturer", "{pCloudy_DeviceManafacturer}");
    //capabilities.setCapability("pCloudy_DeviceVersion", "{pCloudy_DeviceVersion}");
    capabilities.setCapability("pCloudy_DeviceFullName", "{pCloudy_DeviceFullName}");
    capabilities.setCapability("automationName", "{automationName}");
    //capabilities.setCapability("platformVersion", "{platformVersion}");
    capabilities.setCapability("platformName", "{platformName}");
    capabilities.setCapability("newCommandTimeout", 600);
    capabilities.setCapability("launchTimeout", 90000);
    //capabilities.setCapability("appPackage", "{appPackage}");
    driver = new {driver}(new URL("https://device.pcloudy.com/appiumcloud/wd/hub"), capabilities);
}}''',
            "python": '''from appium import webdriver

desired_caps = {{
    "pCloudy_Username": "{pCloudy_Username}",
    "pCloudy_ApiKey": "{pCloudy_ApiKey}",
    "pCloudy_ApplicationName": "{pCloudy_ApplicationName}",
    "pCloudy_DurationInMinutes": {pCloudy_DurationInMinutes},
    # "pCloudy_DeviceManafacturer": "{pCloudy_DeviceManafacturer}",
    # "pCloudy_DeviceVersion": "{pCloudy_DeviceVersion}",
    "pCloudy_DeviceFullName": "{pCloudy_DeviceFullName}",
    "automationName": "{automationName}",
    # "platformVersion": "{platformVersion}",
    "platformName": "{platformName}",
    "newCommandTimeout": 600,
    "launchTimeout": 90000,
    # "appPackage": "{appPackage}",
}}
driver = webdriver.Remote("https://device.pcloudy.com/appiumcloud/wd/hub", desired_caps)
''',
            "js": '''const wdio = require('webdriverio');

const opts = {{
    path: '/wd/hub',
    port: 443,
    hostname: 'device.pcloudy.com',
    protocol: 'https',
    capabilities: {{
        pCloudy_Username: '{pCloudy_Username}',
        pCloudy_ApiKey: '{pCloudy_ApiKey}',
        pCloudy_ApplicationName: '{pCloudy_ApplicationName}',
        pCloudy_DurationInMinutes: {pCloudy_DurationInMinutes},
        // pCloudy_DeviceManafacturer: '{pCloudy_DeviceManafacturer}',
        // pCloudy_DeviceVersion: '{pCloudy_DeviceVersion}',
        pCloudy_DeviceFullName: '{pCloudy_DeviceFullName}',
        automationName: '{automationName}',
        // platformVersion: '{platformVersion}',
        platformName: '{platformName}',
        newCommandTimeout: 600,
        launchTimeout: 90000,
        // appPackage: '{appPackage}',
    }}
}};
const client = await wdio.remote(opts);
''',
            "javascript": '''const wdio = require('webdriverio');

const opts = {{
    path: '/wd/hub',
    port: 443,
    hostname: 'device.pcloudy.com',
    protocol: 'https',
    capabilities: {{
        pCloudy_Username: '{pCloudy_Username}',
        pCloudy_ApiKey: '{pCloudy_ApiKey}',
        pCloudy_ApplicationName: '{pCloudy_ApplicationName}',
        pCloudy_DurationInMinutes: {pCloudy_DurationInMinutes},
        // pCloudy_DeviceManafacturer: '{pCloudy_DeviceManafacturer}',
        // pCloudy_DeviceVersion: '{pCloudy_DeviceVersion}',
        pCloudy_DeviceFullName: '{pCloudy_DeviceFullName}',
        automationName: '{automationName}',
        // platformVersion: '{platformVersion}',
        platformName: '{platformName}',
        newCommandTimeout: 600,
        launchTimeout: 90000,
        // appPackage: '{appPackage}',
    }}
}};
const client = await wdio.remote(opts);
'''
        }
        template_key = lang if lang in templates else None
        if template_key:
            code = templates[template_key].format(
                pCloudy_Username=placeholders["pCloudy_Username"],
                pCloudy_ApiKey=placeholders["pCloudy_ApiKey"],
                pCloudy_ApplicationName=placeholders["pCloudy_ApplicationName"],
                pCloudy_DurationInMinutes=placeholders["pCloudy_DurationInMinutes"],
                pCloudy_DeviceManafacturer=placeholders["pCloudy_DeviceManafacturer"],
                pCloudy_DeviceVersion=placeholders["pCloudy_DeviceVersion"],
                pCloudy_DeviceFullName=placeholders["pCloudy_DeviceFullName"],
                automationName=automation[lang],
                platformVersion=placeholders["platformVersion"],
                platformName=platform_name,
                driver=driver[lang]
            )
            helper_text = (
                "This is a raw Appium capabilities boilerplate.\n"
                "To fill in real values, use the following tools:\n"
                "- 'device_management' or 'list_devices' to get available device names and details\n"
                "- 'file_app_management' to upload or list your application files\n"
                "- 'platform' or 'detect_platform' to determine the platform if unsure\n"
                "Replace all <...> placeholders with actual values from these tools."
            )
            return {
                "content": [
                    {"type": "code", "language": lang if lang != "js" else "javascript", "code": code},
                    {"type": "text", "text": helper_text}
                ],
                "isError": False
            }
        return {
            "content": [{"type": "text", "text": f"Boilerplate for language '{language}' is not yet supported. Please specify 'java' or contact support."}],
            "isError": True
        }
    except Exception as e:
        logger.error(f"Error in appium_capabilities: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in appium_capabilities: {str(e)}"}],
            "isError": True
        }
