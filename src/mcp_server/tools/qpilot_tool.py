"""
QPilot Tool for pCloudy MCP Server

A comprehensive FastMCP tool that houses all QPilot-related API functions.
"""

from config import logger, Config
from api.qpilot_credits import QpilotCreditsMixin
from api.qpilot_project import QpilotProjectMixin
from api.auth import AuthMixin
from api.qpilot_test_case import QpilotTestCaseMixin
from api.qpilot_test_suite import QpilotTestSuiteMixin
from api.qpilot_code_script import QpilotCodeScriptMixin
import httpx
from mcp_server.shared_mcp import mcp
import os
from mcp_server.tools.qpilot_run_script_params import get_missing_params, get_param_prompt, REQUIRED_PARAMS

class QpilotAPI(AuthMixin, QpilotCreditsMixin, QpilotProjectMixin, QpilotTestCaseMixin, QpilotTestSuiteMixin, QpilotCodeScriptMixin):
    def __init__(self, base_url=None):
        AuthMixin.__init__(self)
        QpilotCreditsMixin.__init__(self)
        QpilotProjectMixin.__init__(self)
        QpilotTestCaseMixin.__init__(self)
        QpilotTestSuiteMixin.__init__(self)
        QpilotCodeScriptMixin.__init__(self)
        self.username = os.environ.get("PCLOUDY_USERNAME") or os.environ.get("PLOUDY_USERNAME")
        self.api_key = os.environ.get("PCLOUDY_API_KEY") or os.environ.get("PLOUDY_API_KEY")
        if not self.username or not self.api_key:
            logger.warning("PCLOUDY_USERNAME or PCLOUDY_API_KEY not set. Check your .env file and environment.")
        self.base_url = base_url or Config.PCLOUDY_BASE_URL
        self.auth_token = None
        self.token_timestamp = None
        self.client = httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT)
        logger.info("QpilotAPI initialized (modular)")
    async def close(self):
        try:
            await self.client.aclose()
            logger.info("HTTP client closed")
        except Exception as e:
            logger.error(f"Error closing HTTP client: {str(e)}")

@mcp.tool()
async def qpilot(
    action: str,
    platform: str = "Android",
    description: str = "",  # Renamed from 'feature' for clarity
    rid: str = "",
    testcaseid: str = "",
    testSuiteId: str = "",
    testCaseName: str = "",
    projectId: str = "",
    appName: str = "",
    appPackage: str = "",
    appActivity: str = "",
    steps: str = "",
    testdata: dict = None,
    name: str = "",
    getShared: bool = True,
    strict: bool = True,
    suiteId: str = "",
    testId: str = ""
):
    """
    QPilot Tool: Houses all QPilot API functions.

    Context for LLMs and developers:
    - This tool acts as a single entrypoint for all QPilot-related actions (credits, projects, test suites, test cases, code generation, etc.).
    - 'action': The QPilot action to perform (e.g., 'get_credits', 'project_list', 'create_project', 'get_test_suites', 'create_test_suite', 'create_test_case', 'get_tests', 'get_test_cases', 'start_wda', 'start_appium', 'run_script', 'create_script').
    - Other parameters are mapped directly to the corresponding QPilot API endpoints. For example:
        - 'platform', 'description', 'rid', 'testcaseid', 'testSuiteId', 'testCaseName', 'projectId', 'appName', 'appPackage', 'appActivity', 'steps', 'testdata', 'name', 'getShared'.
    - 'strict': If True, require all parameters explicitly for code generation; if False, auto-fill from context.
    - Authentication: Uses QPilot token (from environment variables PCLOUDY_USERNAME and PCLOUDY_API_KEY).
    - Returns: Dict with API result or error, matching the structure of the underlying QPilot API response.
    - Example usage: qpilot(action='get_tests', getShared=True) will list all test cases for the authenticated user.
    - This tool is used by the MCP server to expose QPilot automation to LLMs and users.
    - If an action name is a common typo or variant (e.g., 'get_testcase', 'get_testcasez'), the LLM should map it to the correct function (e.g., 'get_test_cases').
    """
    api = QpilotAPI()
    await api.authenticate()
    try:
        # Check QPilot credits before any action except get_credits
        if action != "get_credits":
            try:
                credits = await api.get_qpilot_credits()
                if not credits or (isinstance(credits, dict) and credits.get("credits", 1) <= 0):
                    logger.error("No QPilot credits available. Please recharge your credits to use this API.")
                    return {"error": "No QPilot credits available. Please recharge your credits to use this API."}
            except Exception as e:
                logger.error(f"Error checking QPilot credits: {str(e)}")
                return {"error": f"Error checking QPilot credits: {str(e)}"}
        # Map common typos or variants to the correct action
        typo_map = {
            "get_testcase": "get_test_cases",
            "get_testcasez": "get_test_cases",
            "get_testcasess": "get_test_cases",
            "get_test": "get_test_cases",
            "gettests": "get_test_cases",
            "gettestcases": "get_test_cases",
            "get_test_suites": "get_test_suites",
            "gettestsuites": "get_test_suites",
            "gettestsuite": "get_test_suites",
            "get_test_suite": "get_test_suites",
            "generate_code": "run_natural_script"
        }
        if action in typo_map:
            action = typo_map[action]
        if action == "get_credits":
            return await api.get_qpilot_credits()
        elif action == "project_list":
            return await api.project_list(getShared)
        elif action == "create_project":
            return await api.create_project(name)
        elif action == "get_test_suites":
            if projectId:
                logger.warning("get_test_suites called with projectId. Use 'testsuite_list' for project-specific suites.")
                return {"warning": "get_test_suites ignores projectId. Use 'testsuite_list' for project-specific suites.", "result": await api.get_test_suites()}
            return await api.get_test_suites()
        elif action == "create_test_suite":
            return await api.create_test_suite(name)
        elif action == "create_test_case":
            return await api.create_test_case(testSuiteId, testCaseName, platform)
        elif action == "get_test_cases":
            return await api.get_test_cases(getShared)
        elif action == "get_tests":
            return await api.get_test_cases(getShared)
        elif action == "start_wda":
            return await api.start_wda(rid)
        elif action == "start_appium":
            return await api.start_appium(rid, platform, appName)
        elif action == "run_natural_script":
            # Always use qpilot_run_script_params to collect/validate parameters
            params = {
                "projectId": projectId,
                "suiteId": testSuiteId or suiteId,
                "testId": testcaseid or testId,
                "appName": appName,
                "appPackage": appPackage,
                "appActivity": appActivity,
                "description": description,
                "steps": steps,
                "rid": rid
            }
            detected_platform = None
            if appName:
                if appName.lower().endswith(".apk"):
                    detected_platform = "Android"
                elif appName.lower().endswith(".ipa"):
                    detected_platform = "iOS"
            platform_final = platform or detected_platform or "Android"
            missing = get_missing_params(params, required_keys=["rid", "description", "testId", "suiteId", "appPackage", "appName", "appActivity", "steps", "projectId", "testdata"])
            if missing:
                # Build hints for each missing param
                hints = {}
                for key in missing:
                    if key == "rid":
                        hints[key] = (
                            "You can use the device_management tool to list available devices (action='list'), "
                            "or book a device (action='book'). If you already have a booked device, you can use its ID. "
                            "Would you like to use a currently booked device or see a list to book one?"
                        )
                    else:
                        hints[key] = f"Use the appropriate tool to fetch this parameter. For example, use 'project_list' for projectId, 'get_test_suites' for suiteId, etc."
                return {
                    "error": "Missing required parameters for LCA code generation.",
                    "prompt": (
                        "To help you create an LCA (Low Code Automation) test, I need a bit more information specific to your environment:\n"
                        "- Application under test (appName): APK/IPA file or cloud app name.\n"
                        "- Test case: Provide a scenario or say 'sample' for a generated one.\n"
                        "- Test management: Are you using BrowserStack Test Management, or do you want local code/scripts (Playwright, Selenium, etc.)?\n"
                        "- Project/folder: If using BrowserStack, do you have a project and folder set up, or should I help you create them?\n"
                        "- Device: Do you want to use a specific device, or should I list available ones for you?\n"
                        f"\nMissing: {', '.join(missing)}\nPlease provide these details so I can proceed with your LCA code generation."
                    ),
                    "missing": missing,
                    "hints": hints
                }
            # All parameters present: proceed with strict sequence
            # 1. Start Appium with correct payload
            appium_payload = {
                "rid": rid,
                "action": "start",
                "os": platform_final,
                "appName": appName
            }
            appium_result = await api.start_appium(**appium_payload)
            if not appium_result or (isinstance(appium_result, dict) and appium_result.get('status') != 200):
                return {"error": f"Failed to start Appium: {appium_result.get('error', appium_result)}"}
            # 2. Run Script with new parameter names
            script_result = await api.run_natural_script(
                rid=rid,
                description=description,
                testId=params["testId"],
                suiteId=params["suiteId"],
                appPackage=appPackage,
                appName=appName,
                appActivity=appActivity,
                steps=steps,
                projectId=projectId,
                testdata=testdata or {},
                strict=True,
                platform=platform_final
            )
            if not script_result or (isinstance(script_result, dict) and script_result.get('status') != 200):
                return {"error": f"Failed to run script: {script_result.get('error', script_result)}"}
            # 3. Create Script with correct payload
            script_type = "pcloudy_appium-js"  # You may want to make this dynamic or configurable
            create_result = await api.create_script(testCaseId=params["testId"], testSuiteId=params["suiteId"], scriptType=script_type)
            if not create_result or (isinstance(create_result, dict) and create_result.get('status') != 200):
                return {"error": f"Failed to create script: {create_result.get('error', create_result)}"}
            return {
                "appium_result": appium_result,
                "script_result": script_result,
                "create_result": create_result
            }
        else:
            # Default action handling
            action_map = {
                "get_credits": api.get_qpilot_credits,
                "project_list": api.project_list,
                "create_project": api.create_project,
                "get_test_suites": api.get_test_suites,
                "create_test_suite": api.create_test_suite,
                "create_test_case": api.create_test_case,
                "get_test_cases": api.get_test_cases,
                "get_tests": api.get_test_cases,
                "start_wda": api.start_wda,
                "start_appium": api.start_appium,
                "run_natural_script": api.run_natural_script
            }
            if action in action_map:
                func = action_map[action]
                # Call the mapped function with the appropriate parameters
                return await func(
                    projectId=projectId,
                    testSuiteId=testSuiteId,
                    testcaseid=testcaseid,
                    appName=appName,
                    appPackage=appPackage,
                    appActivity=appActivity,
                    description=description,
                    steps=steps,
                    rid=rid,
                    getShared=getShared,
                    name=name,
                    strict=strict
                )
            else:
                logger.error(f"Unknown action: {action}")
                return {"error": f"Unknown action: {action}"}
    except Exception as e:
        logger.error(f"Error in qpilot function: {str(e)}")
        return {"error": f"Error in qpilot function: {str(e)}"}
    finally:
        await api.close()
