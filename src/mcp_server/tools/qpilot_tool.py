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
import httpx
from mcp_server.shared_mcp import mcp
import os

class QpilotAPI(AuthMixin, QpilotCreditsMixin, QpilotProjectMixin, QpilotTestCaseMixin, QpilotTestSuiteMixin):
    def __init__(self, base_url=None):
        AuthMixin.__init__(self)
        QpilotCreditsMixin.__init__(self)
        QpilotProjectMixin.__init__(self)
        QpilotTestCaseMixin.__init__(self)
        QpilotTestSuiteMixin.__init__(self)
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
    feature: str = "",
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
    getShared: bool = True
):
    """
    QPilot Tool: Houses all QPilot API functions.

    Context for LLMs and developers:
    - This tool acts as a single entrypoint for all QPilot-related actions (credits, projects, test suites, test cases, code generation, etc.).
    - 'action': The QPilot action to perform (e.g., 'get_credits', 'project_list', 'create_project', 'get_test_suites', 'create_test_suite', 'create_test_case', 'get_tests', 'start_wda', 'start_appium', 'generate_code', 'create_script').
    - Other parameters are mapped directly to the corresponding QPilot API endpoints. For example:
        - 'platform', 'feature', 'rid', 'testcaseid', 'testSuiteId', 'testCaseName', 'projectId', 'appName', 'appPackage', 'appActivity', 'steps', 'testdata', 'name', 'getShared'.
    - Authentication: Uses QPilot token (from environment variables PCLOUDY_USERNAME and PCLOUDY_API_KEY).
    - Headers: Sets 'token', 'Origin', and 'Content-Type' as required by QPilot APIs.
    - Returns: Dict with API result or error, matching the structure of the underlying QPilot API response.
    - Example usage: qpilot(action='get_tests', getShared=True) will list all test cases for the authenticated user.
    - This tool is used by the MCP server to expose QPilot automation to LLMs and users.
    """
    api = QpilotAPI()
    await api.authenticate()
    # Use duration from config
    duration = getattr(Config, 'QPILOT_DEFAULT_DURATION', 30)
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
        elif action == "get_tests":
            return await api.get_test_cases(getShared)
        elif action == "start_wda":
            return await api.start_wda(rid)
        elif action == "start_appium":
            return await api.start_appium(rid, platform, appName)
        elif action == "generate_code":
            return await api.generate_code(rid, feature, testcaseid, testSuiteId, appPackage, appName, appActivity, steps, projectId, testdata)
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
