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
    strict: bool = True
):
    """
    QPilot Tool: Houses all QPilot API functions.

    Context for LLMs and developers:
    - This tool acts as a single entrypoint for all QPilot-related actions (credits, projects, test suites, test cases, code generation, etc.).
    - 'action': The QPilot action to perform (e.g., 'get_credits', 'project_list', 'create_project', 'get_test_suites', 'create_test_suite', 'create_test_case', 'get_tests', 'get_test_cases', 'start_wda', 'start_appium', 'generate_code', 'create_script').
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
            "generate_code": "generate_code"
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
        elif action == "generate_code":
            # Step-by-step prompt for each required parameter
            missing = []
            param_hints = {
                'rid': "Device booking ID. Use the 'book_device' tool to fetch this.",
                'description': "Test/feature description. Provide a summary of the scenario.",
                'testcaseid': "Test case ID. Use the 'create_test_case' or 'get_test_cases' tool to fetch this.",
                'testSuiteId': "Test suite ID. Use the 'create_test_suite' or 'get_test_suites' tool to fetch this.",
                'appPackage': "App package name. Use the 'get_app_details' or similar tool to fetch this.",
                'appName': "App file name (e.g., APK/IPA). Use the 'upload_app' or 'get_app_list' tool to fetch this.",
                'appActivity': "Main activity (Android) or entry point (iOS). Use the 'get_app_details' tool to fetch this.",
                'steps': "Automation steps. Provide a step-by-step description.",
                'projectId': "Project ID. Use the 'project_list' tool to fetch this.",
            }
            param_values = {
                'rid': rid,
                'description': description,
                'testcaseid': testcaseid,
                'testSuiteId': testSuiteId,
                'appPackage': appPackage,
                'appName': appName,
                'appActivity': appActivity,
                'steps': steps,
                'projectId': projectId,
            }
            for key, value in param_values.items():
                if not value:
                    missing.append(f"{key}: {param_hints[key]}")
            if missing:
                return {
                    "error": "Missing required parameters for code generation.",
                    "missing": missing,
                    "hint": "Provide the missing values or use the suggested tool(s) to fetch them. Repeat this process for each parameter."
                }
            # Auto-detect platform
            detected_platform = None
            if appName:
                if appName.lower().endswith(".apk"):
                    detected_platform = "Android"
                elif appName.lower().endswith(".ipa"):
                    detected_platform = "iOS"
            platform_final = detected_platform or "Android"
            # Start Appium before generating code
            appium_result = await api.start_appium(rid, platform_final, appName)
            if appium_result and appium_result.get('error'):
                return {"error": f"Failed to start Appium: {appium_result['error']}"}
            # Open device URL in browser if available
            device_url = None
            if hasattr(api, 'get_device_url') and callable(getattr(api, 'get_device_url')):
                device_url = await api.get_device_url(rid)
                if device_url and isinstance(device_url, dict) and device_url.get('url'):
                    try:
                        import webbrowser
                        webbrowser.open(device_url['url'], new=2)
                    except Exception as e:
                        logger.warning(f"Could not open browser for device URL: {str(e)}")
            result = await api.generate_code(rid, description, testcaseid, testSuiteId, appPackage, appName, appActivity, steps, projectId, testdata, True, platform_final)
            if device_url:
                result['device_url'] = device_url
            return result
        elif action == "create_script":
            return await api.create_script(testcaseid, testSuiteId)
        # Add stubs for other QPilot actions here, e.g.:
        # elif action == "some_other_action":
        #     ...
        else:
            logger.error(f"Unknown or unimplemented QPilot action: {action}")
            return {"error": f"Unknown or unimplemented QPilot action: {action}"}
    except httpx.RequestError as e:
        logger.error(f"Network error in QPilot tool: {str(e)}")
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in QPilot tool: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}
