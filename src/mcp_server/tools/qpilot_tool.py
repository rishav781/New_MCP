"""
QPilot Tool for pCloudy MCP Server

A comprehensive FastMCP tool that houses all QPilot-related API functions.
"""

from config import logger, Config
from api.qpilot_credits import QpilotCreditsMixin
from api.qpilot_project import QpilotProjectMixin
import httpx
from mcp_server.shared_mcp import mcp

class QpilotAPI(QpilotCreditsMixin, QpilotProjectMixin):
    pass

@mcp.tool()
async def qpilot(
    action: str,
    platform: str = "Android",
    feature: str = "",
    qpilotRid: str = "",
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
    Args:
        action: The QPilot action to perform (e.g., get_credits, project_list, create_project, etc.)
        Other args: Parameters for the specific action
    Returns:
        Dict with API result or error
    """
    api = QpilotAPI()
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
            return await api.get_test_suites()
        elif action == "create_test_suite":
            return await api.create_test_suite(name)
        elif action == "create_test_case":
            return await api.create_test_case(testSuiteId, testCaseName, platform)
        elif action == "get_tests":
            return await api.get_tests(getShared)
        elif action == "start_wda":
            return await api.start_wda(qpilotRid)
        elif action == "start_appium":
            return await api.start_appium(qpilotRid, platform, appName)
        elif action == "generate_code":
            return await api.generate_code(qpilotRid, feature, testcaseid, testSuiteId, appPackage, appName, appActivity, steps, projectId, testdata)
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
