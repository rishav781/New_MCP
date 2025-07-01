"""
Tool for generating QPilot code steps using the async API method on PCloudyAPI.
Supports both FastMCP tool usage and command-line usage.
Prompts the user for required parameters if run from CLI.
"""
import os
import sys
import asyncio
# Add the parent directory to the path to find the config module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api import PCloudyAPI
from shared_mcp import mcp
from api.qpilot_appium_control import QPilotAppiumControlMixin

def get_api():
    """Helper to get a new PCloudyAPI instance."""
    return PCloudyAPI()

@mcp.tool()
async def qpilot_steps_management(
    rid: int,
    description: str,
    #testId: str,
    #suiteId: str,
    appPackage: str,
    appName: str,
    appActivity: str,
    steps: str,
    #projectId: str,
    platform: str,
    testdata: dict = {}):
    """
    FIrst need to start appium then generate QPilot code steps.
    This function uses the PCloudyAPI to generate QPilot code steps after ensuring Appium is started successfully.
    Parameters:
      rid, "start", platform, appName
    FastMCP Tool: Generate QPilot code steps, but only after Appium is started successfully.
    Parameters:
        rid: QPilot RID
        description: Feature description
        testId: Test case ID
        suiteId: Test suite ID
        appPackage: App package name
        appName: App name
        appActivity: App activity
        steps: Steps description
        projectId: Project ID
        platform: Platform (android/ios)
        auth_token: Authentication token for Appium control
        testdata: Test data (dict, optional)
    Returns:
        dict: The API response data for the generated code steps, or Appium error if Appium start fails.
    """
    api = get_api()
    # Start Appium first
    """
    appium_control = QPilotAppiumControlMixin()
    appium_result = await appium_control.control_qpilot_appium(
         rid, "start", platform, appName
         """
    
    
   #if appium_result.get("statusCode") == 200:
    payload = {
            "rid": rid,
            "description": description,
            "testId": "1d271e6f-638a-4902-8adc-2401532516a1",
            "suiteId": "e4902c91-170f-480d-ba00-1e60d21cd26f",
            "appPackage": appPackage,
            "appName": appName,
            "appActivity": appActivity,
            "steps": steps,
            "platform": "Android",
            "projectId": "b022b45b-7d9d-4212-8a68-5cbeee44667b",
            "testdata": testdata or {}
        }

    try:
            result = await api.execute_qpilot_code_steps(payload)
            return result
    finally:
            await api.close()
   # else:
        #await api.close()
        #return appium_result

#if __name__ == "__main__":
    # Prompt user for all required parameters
    print("Enter the following parameters for QPilot code step generation:")
    booking_host = input("Booking Host (e.g. https://prod-backend.qpilot.pcloudy.com): ").strip()
    rid = input("QPilot RID: ").strip()
    description = input("Feature Description: ").strip()
    testId = input("Test Case ID: ").strip()
    suiteId = input("Test Suite ID: ").strip()
    appPackage = input("App Package: ").strip()
    appName = input("App Name: ").strip()
    appActivity = input("App Activity: ").strip()
    steps = input("Steps: ").strip()
    projectId = input("Project ID: ").strip()
    platform = input("Platform (android/ios): ").strip()
    auth_token = input("Auth Token: ").strip()
    testdata_str = input("Test Data (JSON, optional): ").strip()
    import json
    testdata = json.loads(testdata_str) if testdata_str else {}
    try:
        result = asyncio.run(qpilot_steps_management(
            booking_host, rid, description, testId, suiteId, appPackage, appName, appActivity, steps, projectId, platform, auth_token, testdata
        ))
        if result.get("statusCode") == 200:
            print(f"QPilot code steps generated: {result}")
        else:
            print(f"Appium control failed: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
