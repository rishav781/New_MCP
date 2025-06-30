"""
Appium Capabilities Tool for pCloudy MCP Server

Provides a FastMCP tool to generate and display Appium capabilities for Android and iOS devices booked via pCloudy.
"""

from config import logger
from api import PCloudyAPI
from mcp_server.shared_mcp import mcp
import os

@mcp.tool()
async def appium_capabilities(language: str = "", device_name: str = ""):
    """
    FastMCP Tool: Appium Capabilities Boilerplate (Raw)
    
    Parameters:
        language: Preferred programming language for the code snippet (e.g., 'java', 'python', 'js').
        device_name: Optional device name to use in the capabilities (if known).
    Returns:
        Dict with Appium boilerplate code and error status, and hints for filling in real values.
    """
    logger.info(f"Tool called: appium_capabilities (raw boilerplate) with language={language}, device_name={device_name}")
    try:
        if not language:
            return {
                "content": [{"type": "text", "text": "Please specify your preferred programming language (e.g., 'java', 'python', 'js')."}],
                "isError": True
            }
        lang = language.lower()
        # Fetch username and api key from environment if available
        env_username = os.environ.get("PCLOUDY_USERNAME")
        env_apikey = os.environ.get("PCLOUDY_API_KEY")
        placeholders = {
            "pCloudy_Username": env_username if env_username else os.environ.get("USER", "<YOUR_EMAIL>"),
            "pCloudy_ApiKey": env_apikey if env_apikey else os.environ.get("API_KEY", "<YOUR_API_KEY>"),
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
    //capabilities.setCapability("appPackage", "{{appPackage}}");
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
    # "appPackage": "{{appPackage}}",
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
        // appPackage: '{{appPackage}}',
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
        // appPackage: '{{appPackage}}',
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
                "- Use 'device_management' with action='list' to find available devices.\n"
                "- Use 'file_app_management' with action='list_apps' to list uploaded applications.\n"
                "- Use 'file_app_management' with action='upload' to upload a new application if required.\n"
                "- Use 'device_management' with action='detect_platform' if unsure about the platform.\n"
                "Replace all <...> placeholders with actual values from these tools."
            )
            return {
                "content": [
                    {"type": "code", "language": lang if lang != "js" else "javascript", "code": code},
                    {"type": "text", "text": helper_text}
                ],
                "isError": False
            }
        # List available devices and prompt user to choose one by name (never book a device)
        if 'device_name' not in locals() or not device_name:
            # List devices using PCloudyAPI (async context)
            api = PCloudyAPI()
            try:
                devices_result = await api.get_devices_list()
                device_names = [d.get('display_name', d.get('model', 'Unknown')) for d in devices_result.get('models', [])]
                if not device_names:
                    return {
                        "content": [{"type": "text", "text": "No devices available. Please check your device pool or try again later."}],
                        "isError": True
                    }
                device_list_text = "Available devices:\n" + "\n".join(f"- {d}" for d in device_names)
                return {
                    "content": [
                        {"type": "text", "text": device_list_text},
                        {"type": "text", "text": "Please specify the device name you want to use from the above list as 'device_name' argument to this tool. The tool will use the selected device name in the boilerplate, but will never book a device for you."}
                    ],
                    "isError": False
                }
            finally:
                await api.close()
        # If a device name is provided, use it in the boilerplate (do not book the device)
        placeholders["pCloudy_DeviceFullName"] = device_name
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
            "- Use 'device_management' with action='list' to find available devices.\n"
            "- Use 'file_app_management' with action='list_apps' to list uploaded applications.\n"
            "- Use 'file_app_management' with action='upload' to upload a new application if required.\n"
            "- Use 'device_management' with action='detect_platform' if unsure about the platform.\n"
            "Replace all <...> placeholders with actual values from these tools."
        )
        return {
            "content": [
                {"type": "code", "language": lang if lang != "js" else "javascript", "code": code},
                {"type": "text", "text": helper_text}
            ],
            "isError": False
        }
    except Exception as e:
        logger.error(f"Error in appium_capabilities: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error in appium_capabilities: {str(e)}"}],
            "isError": True
        }
