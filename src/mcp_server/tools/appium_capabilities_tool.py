"""
Appium Capabilities Tool for pCloudy MCP Server

Provides a FastMCP tool to generate and display Appium capabilities for Android and iOS devices booked via pCloudy.
"""

from config import logger
from api import PCloudyAPI
from mcp_server.shared_mcp import mcp

@mcp.tool()
async def appium_capabilities(rid: str, platform: str = "android", language: str = ""):
    """
    FastMCP Tool: Appium Capabilities Boilerplate
    
    Parameters:
        rid: Device booking ID
        platform: Device platform (android/ios)
        language: Preferred programming language for the code snippet (e.g., 'java', 'python', 'js').
    Returns:
        Dict with Appium boilerplate code and error status
    """
    api = PCloudyAPI()
    logger.info(f"Tool called: appium_capabilities with rid={rid}, platform={platform}, language={language}")
    try:
        if not language:
            return {
                "content": [{"type": "text", "text": "Please specify your preferred programming language (e.g., 'java', 'python', 'js')."}],
                "isError": True
            }
        if not api.auth_token:
            logger.info("No auth token found, attempting auto-authentication...")
            await api.authenticate()
        if not rid:
            return {
                "content": [{"type": "text", "text": "Please specify a rid (device booking ID) parameter."}],
                "isError": True
            }
        # Optimized Appium capabilities boilerplate generator
        lang = language.lower()
        plat = platform.lower()
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
        # Platform-specific
        if plat == "ios":
            automation = {"java": "XCUITest", "python": "XCUITest", "js": "XCUITest", "javascript": "XCUITest"}
            platform_name = "iOS"
            extra_caps = {"bundleId": placeholders["bundleId"]}
            driver = {"java": "IOSDriver", "python": "webdriver.Remote", "js": "wdio.remote", "javascript": "wdio.remote"}
        else:
            automation = {"java": "uiautomator2", "python": "uiautomator2", "js": "uiautomator2", "javascript": "uiautomator2"}
            platform_name = "Android"
            extra_caps = {"appPackage": placeholders["appPackage"]}
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
    {extra}
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
    {extra}
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
        {extra}
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
        {extra}
    }}
}};
const client = await wdio.remote(opts);
'''
        }
        # Compose extra caps
        if plat == "ios":
            extra = 'capabilities.setCapability("bundleId", "{bundleId}");' if lang == "java" else '"bundleId": "{bundleId}"'
        else:
            extra = 'capabilities.setCapability("appPackage", "{appPackage}");' if lang == "java" else '"appPackage": "{appPackage}"'
        # Format template
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
                extra=extra.format(**placeholders),
                driver=driver[lang]
            )
            # Add helpful prompt for next steps
            helper_text = (
                "Tip: Use the 'list_devices' tool to get available devices, "
                "and the 'file_management' tool to upload or list your application files. "
                "Refer to the documentation or tool list for more details."
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
