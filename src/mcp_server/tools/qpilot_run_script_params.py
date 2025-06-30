"""
Parameter definitions and validation for QPilot run_script action.
"""

from typing import List, Dict, Any

REQUIRED_PARAMS = [
    ("projectId", "Project (projectId)", "Please enter a Project ID or pick from the list."),
    ("suiteId", "Test Suite (suiteId)", "Please enter a Test Suite ID or pick from the list."),
    ("testId", "Test Case (testId)", "Please enter a Test Case ID or pick from the list."),
    ("appName", "App Name (appName)", "Please enter an App file name (APK/IPA) or pick from the list."),
    ("appPackage", "App Package (appPackage)", "Please enter the App Package name or pick from the list."),
    ("appActivity", "App Activity (appActivity)", "Please enter the App Activity or pick from the list."),
    ("description", "Test Description (description)", "Please enter a description for the test or feature."),
    ("steps", "Test Steps (steps)", "Please enter the automation steps."),
    ("rid", "Device Booking ID (rid)", "Please enter the Device Booking ID or pick from the list.")
]

def get_missing_params(params: Dict[str, Any], required_keys=None) -> List[str]:
    missing = []
    keys = required_keys if required_keys else [key for key, _, _ in REQUIRED_PARAMS]
    for key, label, _ in REQUIRED_PARAMS:
        if key in keys and not params.get(key):
            missing.append(key)
    return missing

def get_param_prompt(param: str) -> str:
    for key, label, prompt in REQUIRED_PARAMS:
        if key == param:
            return prompt
    return f"Please provide value for {param}."

def get_required_param_keys() -> List[str]:
    return [key for key, _, _ in REQUIRED_PARAMS]
