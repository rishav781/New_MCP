# pCloudy MCP Server

This project implements an MCP server for managing Android and iOS devices on the pCloudy platform. It provides tools for authentication, device management, file operations, app management, and device interaction.

**Author**: Rishav Raj

## Project Structure

- **mcp_server.py**: Main file containing the MCP server, API client (`PCloudyAPI` class), utility functions, and tool definitions.

## Setup

1. **Clone the repository:**

   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Create a virtual environment:**

   ```bash
   python3.13 -m venv .venv
   ```

3. **Activate the virtual environment:**
   - **Linux/macOS:**

     ```bash
     source .venv/bin/activate
     ```

   - **Windows:**

     ```bash
     .venv\Scripts\activate
     ```

4. **Install dependencies:**
   The project requires the following Python packages:
   - `httpx`
   - `fastmcp`

   Install them using pip:

   ```bash
   pip install httpx fastmcp
   ```

   Alternatively, if you use Poetry, create a `pyproject.toml` file with these dependencies and run:

   ```bash
   poetry install
   ```

5. **pCloudy API Credentials:**
   - The server uses a browser-based authentication flow. You’ll be prompted to enter your pCloudy `username` and `api_key` when running the `authorize` tool. No pre-configuration of credentials is required.

## Running the MCP Server

You can start the MCP server in two ways:

- **Using FastMCP (development mode):**

  ```bash
  fastmcp dev mcp_server.py
  ```

- **Directly with Python:**

  ```bash  
  python mcp_server.py
  ```

For installation with Claude Desktop, run:

```bash
fastmcp install mcp_server.py
```

The server will listen on `http://localhost:8000` by default (port can be changed via the `PORT` environment variable).

## Available Tools

### Authentication & Device Management
- **authorize**: Authenticate with pCloudy by opening a browser window where you can enter your `username` and `api_key`. Upon successful authentication, the token is stored for use in other tools.
- **list_available_devices**: List available Android/iOS devices on the pCloudy platform.
- **book_device_by_name**: Book a device by its name (e.g., "Galaxy S10") with optional GPS location setting and automatic service startup.
- **release_device**: Release a booked device with automatic session data discovery.

### File Operations  
- **upload_file**: Upload an APK/IPA/ZIP file to the pCloudy drive with duplicate detection.
- **download_from_cloud**: Download files from the pCloudy drive.
- **download_manual_access_data**: Download files (e.g., screenshots, logs) from a booked device session.
- **list_cloud_apps**: List apps/files in the pCloudy drive.

### App Management
- **resign_ipa**: Resign iOS IPA files for deployment with duplicate detection.
- **install_and_launch_app**: Install and launch an app on a booked device with automatic performance monitoring.

### Device Control & Monitoring
- **capture_device_screenshot**: Capture a screenshot from a booked device (with optional device skin).
- **get_device_page_url**: Retrieve and automatically open the device page URL in browser.
- **start_device_services**: Start device logs, performance data collection, and session recording.
- **set_device_location**: Set GPS coordinates for a device.
- **start_performance_data**: Start performance monitoring for a specific app package.

### Advanced Operations
- **execute_adb_command**: Execute ADB commands on Android devices (with automatic platform detection).
- **detect_device_platform**: Auto-detect if a device is Android or iOS.
- **list_performance_data_files**: List all performance data files for a device session.
- **download_all_session_data**: Download all session data files to a local directory.
- **start_wildnet**: Enable wildnet feature for enhanced network capabilities on booked devices.

## Enhanced Features

### Smart File Operations
- **Duplicate Detection**: Both `upload_file` and `resign_ipa` check for existing files to prevent accidental overwrites
- **Force Operations**: Use `force_upload=True` or `force_resign=True` to override duplicate protection
- **Intelligent Suggestions**: Auto-suggest package names from APK filenames for performance monitoring

### Automatic Service Management
- **Auto-Start Services**: Device booking automatically starts logging, performance data, and session recording
- **Location Setting**: Set GPS coordinates during device booking or afterward
- **Performance Monitoring**: Automatically start performance data collection when installing apps

### Session Data Management
- **Automatic Discovery**: Device release automatically checks for available session files
- **Bulk Download**: Download all session data with one command
- **Smart Prompting**: Users are guided on how to retrieve their testing artifacts

## Notes

- **Python Version**: Requires Python 3.13.
  On Ubuntu, you might use:

  ```bash
  sudo apt install python3.13 python3.13-venv python3.13-dev
  ```

- **Logs**: Log messages are saved in `pcloudy_mcp_server.log`. Check this file for detailed error messages if issues occur.

- **Security**: Ensure you secure your credentials. The server runs a local HTTP server on `localhost` for authentication, which shuts down after use. For production, consider using HTTPS and additional security measures.

- **Enhanced User Experience**:
  - File operations include duplicate detection to prevent accidental overwrites
  - Device booking automatically starts essential services (logs, performance data, recording)
  - Performance monitoring starts automatically when installing apps with known package names
  - Session data discovery helps users collect testing artifacts after device release

- **Troubleshooting**:
  - Verify your network access to `https://device.pcloudy.com/api`.
  - Ensure your pCloudy `username` and `api_key` are correct when prompted during authentication.
  - If authentication fails, check `pcloudy_mcp_server.log` for the raw API response to diagnose the issue (e.g., invalid credentials or API errors).
  - If you encounter port conflicts (e.g., on port 8080 used for authentication), the server will automatically retry with the next available port.
  - For performance data issues, ensure the package name is correct and the app is installed and running.
  - Use `detect_device_platform` tool if unsure about device platform compatibility.

---

*Updated: June 02, 2025, 04:30 PM IST - Enhanced with smart file operations, automatic service management, wildnet feature, and session data handling*
