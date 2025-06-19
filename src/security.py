"""
Security utilities for the pCloudy MCP server.

- Validates filenames for safe filesystem operations.
- Extracts package name hints from APK filenames.
- Logs security-related errors and warnings.
"""

import re
import os
from config import Config, logger

def validate_filename(filename: str) -> bool:
    """
    Validate that the filename is safe for saving to the filesystem.
    Returns True if the filename is valid, False otherwise.
    """
    # Remove any path traversal attempts (e.g., ../) and invalid characters
    if not filename or re.search(r'[\\/:*?"<>|]', filename) or ".." in filename:
        logger.error(f"Invalid filename: {filename}")
        return False
    return True

def extract_package_name_hint(filename: str) -> str:
    """
    Attempt to extract a likely package name from APK filename.
    This is a fallback method when the API doesn't provide package information.
    Returns a suggested package name for reference, or an empty string if not possible.
    """
    if not filename:
        return ""
    
    # Remove file extension and clean up the filename
    name_without_ext = os.path.splitext(filename)[0].lower()
    
    # If filename already looks like a package name (contains dots), use it
    if "." in name_without_ext and not name_without_ext.startswith("."):
        # Check if it looks like reverse domain notation
        parts = name_without_ext.split(".")
        if len(parts) >= 2 and all(part.replace("_", "").isalnum() for part in parts):
            return name_without_ext
    
    # Otherwise, try to clean up the filename to make it a valid package-like string
    # Replace common separators with dots, remove version info, etc.
    cleaned = re.sub(r'[-_\s]+', '.', name_without_ext)
    cleaned = re.sub(r'\.v?\d+(\.\d+)*.*$', '', cleaned)  # Remove version suffixes
    cleaned = re.sub(r'^\.+|\.+$', '', cleaned)  # Remove leading/trailing dots
    cleaned = re.sub(r'[^a-z0-9.]', '', cleaned)  # Remove invalid characters
    
    # If it looks reasonable, return it with a prefix to indicate it's estimated
    if cleaned and len(cleaned.split('.')) >= 2:
        return f"com.app.{cleaned}"
    elif cleaned:
        return f"com.app.{cleaned}"
    
    return ""