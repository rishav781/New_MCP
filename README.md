# pCloudy MCP Server (Category-Based Architecture)

This project implements a streamlined MCP server for managing Android and iOS devices on the pCloudy platform. It features a **category-based tool architecture** with 4 meta-tools that intelligently route operations, replacing the previous 17 individual tools for a cleaner, more intuitive interface. It also includes Appium capabilities code generation for seamless integration with automated testing frameworks.

**Author**: Rishav Raj

## 🎯 Category-Based Tool Architecture (4 Meta-Tools)

### 📱 Device Management (`device_management`)

**Actions**: `list`, `book`, `release`, `detect_platform`, `set_location`

- **list**: List available devices (`platform="android"`/`"ios"`)
- **book**: Book device (`device_name="GalaxyS10"`, `platform="android"`, `auto_start_services=True`)
- **release**: Release device (`rid="device_id"`)
- **detect_platform**: Auto-detect device platform (`rid="device_id"`)
- **set_location**: Set GPS coordinates (`rid="device_id"`, `latitude=48.8566`, `longitude=2.3522`)

### 📸 Device Control & Monitoring (`device_control`)

**Actions**: `screenshot`, `get_url`, `start_services`, `adb`

- **screenshot**: Capture device screenshot (`rid="device_id"`, `skin=True`)
- **get_url**: Get device page URL and open in browser (`rid="device_id"`)
- **start_services**: Start device services (`rid="device_id"`, `start_device_logs=True`, `start_performance_data=True`, `start_session_recording=True`)
- **adb**: Execute ADB command on Android (`rid="device_id"`, `adb_command="logcat"`, `platform="auto"`)

### 📦 File & App Management (`file_app_management`)

**Actions**: `upload`, `list_apps`, `install`, `resign`, `download_cloud`

- **upload**: Upload APK/IPA file (`file_path="/path/to/app.apk"`, `force_upload=False`)
- **list_apps**: List cloud apps (`limit=10`, `filter_type="all"`)
- **install**: Install and launch app (`rid="device_id"`, `filename="app.apk"`, `grant_all_permissions=True`, `platform="android"`, `app_package_name="com.example.app"`)
- **resign**: Resign iOS IPA file (`filename="app.ipa"`, `force_resign=False`)
- **download_cloud**: Download file from cloud (`filename="app.apk"`)

### 📊 Session Data & Analytics (`session_analytics`)

**Actions**: `download_session`, `list_performance`

- **download_session**: Download session data (`rid="device_id"`, `filename="optional_specific_file"`, `download_dir="optional_directory"`)
- **list_performance**: List performance data files (`rid="device_id"`)

### 🤖 Appium Capabilities Code Generation (`appium_capabilities`)

**Action**: `generate` (parameter: `language`)

- **generate**: Produces Appium capabilities boilerplate code for Android/iOS in your preferred language (`java`, `python`, `js`).
    - Returns a code snippet with placeholders for all required values (username, API key, app name, device details, etc.).
    - Includes helper text on how to fill in real values using other tools (e.g., `device_management`, `file_app_management`).
    - Example usage:

```python
# Generate Appium capabilities for Python
appium_capabilities(language="python")
```

- The tool does not fetch real device/app data but provides a template and instructions for integration with your automation scripts.

## 📋 Usage Examples

### 🔄 Complete Testing Workflow

```python
# 1. List available devices
device_management(action="list", platform="android")

# 2. Book a device
device_management(action="book", device_name="GalaxyS10") 

# 3. Set GPS location for location-based testing
device_management(action="set_location", rid="123", latitude=48.8566, longitude=2.3522)

# 4. Install and launch app (auto-opens device in browser)
file_app_management(action="install", rid="123", filename="MyApp.apk")

# 5. Take a screenshot
device_control(action="screenshot", rid="123")

# 6. Download session data
session_analytics(action="download_session", rid="123")

# 7. Release device
device_management(action="release", rid="123")
```

### 📱 iOS App Testing

```python
# 1. Upload iOS app
file_app_management(action="upload", file_path="MyApp.ipa")

# 2. Resign the IPA for deployment
file_app_management(action="resign", filename="MyApp.ipa") 

# 3. Book iOS device
device_management(action="book", device_name="iPhone", platform="ios")

# 4. Install resigned app
file_app_management(action="install", rid="123", filename="MyApp_resign.ipa")
```

### 🐛 Android Debugging

```python
# 1. Book Android device
device_management(action="book", device_name="Pixel")

# 2. Execute ADB commands
device_control(action="adb", rid="123", adb_command="logcat")

# 3. List performance data
session_analytics(action="list_performance", rid="123")

# 4. Download specific log files
session_analytics(action="download_session", rid="123", filename="specific_log.txt")
```

### 🤖 Appium Capabilities Generation

```python
# Generate Appium capabilities for a booked device and uploaded app
appium_capabilities(language="python")
```

## Setup

1. **Clone the repository:**

   ```powershell
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Create a virtual environment:**

   ```powershell
   python3.13 -m venv .venv
   ```

3. **Activate the virtual environment:**
   - **Windows (PowerShell):**

     ```powershell
     .venv\Scripts\Activate.ps1
     ```

   - **Linux/macOS:**

     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies:**
   The project requires the following Python packages (see `pyproject.toml`):
   - `aiofiles`
   - `fastapi`
   - `fastmcp`
   - `python-dotenv`

   Install them using pip:

   ```powershell
   pip install aiofiles fastapi fastmcp python-dotenv
   ```

   Or, if you use Poetry or uv:

   ```powershell
   poetry install
   # OR
   uv sync
   ```

5. **pCloudy API Credentials:**
   - Copy `.env.template` to `.env` and fill in your credentials.
   - The server uses a browser-based authentication flow. You'll be prompted to enter your pCloudy `username` and `api_key` when running any tool if not set in `.env`.

## Running the MCP Server

You can start the MCP server in multiple ways:

- **Using FastMCP (development mode):**

  ```powershell
  fastmcp dev src/mcp_server/server_main.py
  ```

- **Directly with Python:**

  ```powershell
  python src/mcp_server/server_main.py
  ```

The server will listen on `http://localhost:8000` by default (port can be changed via the `PORT` environment variable).

## ✅ Enhanced Features

### 🎯 Category-Based Architecture Benefits

- **Simplified Interface**: 4 meta-tools instead of 17 individual tools
- **Logical Grouping**: Related operations organized under single tools
- **Intelligent Routing**: System automatically selects correct method based on action
- **Cleaner Documentation**: Easier to understand and maintain
- **Better User Experience**: Less tool discovery, more focused workflows

### 🚀 Smart Automation

- **Auto-Authentication**: Seamless authentication across all operations
- **Auto-Service Startup**: Device booking automatically starts logs, performance data, and session recording
- **Auto-Browser Opening**: App installation and device URL requests automatically open in browser
- **Auto-Platform Detection**: ADB commands automatically detect device platform
- **Auto-Session Discovery**: Device release automatically prompts for session data download

### 🔧 Advanced Capabilities

- **GPS Location Setting**: Simulate location-based testing with precise coordinates
- **Unified Download System**: Single function handles both individual files and bulk session downloads
- **iOS App Resigning**: Automatic IPA resigning for iOS deployment
- **Performance Monitoring**: Real-time performance data collection during app testing
- **ADB Command Execution**: Full Android debugging capabilities with safety checks
- **Appium Capabilities Generation**: Instantly generate Appium capabilities for your automation scripts

### 🛡️ Security & Validation

- **Input Validation**: Comprehensive validation for all parameters
- **Path Security**: Download directory validation prevents security issues
- **Platform Compatibility**: Automatic platform detection prevents incompatible operations
- **Error Handling**: Detailed error messages and graceful failure handling

## 📁 Project File Structure

The project is organized as follows:

```text
Pcloudy/
├── .env                  # Your pCloudy credentials (not committed)
├── .env.template         # Example template for .env
├── pcloudy_mcp_server.log # Log file for server activity
├── pyproject.toml        # Project metadata and dependencies
├── README.md             # Project documentation
├── uv.lock               # UV lock file for dependency management
├── src/                  # All source code
│   ├── __init__.py       # Package initialization
│   ├── config.py         # Configuration and logging setup
│   ├── security.py       # Security utilities
│   ├── utils.py          # General utility functions
│   ├── api/              # API mixins for pCloudy endpoints
│   │   ├── __init__.py   # API package initialization
│   │   ├── auth.py       # Authentication logic
│   │   ├── device.py     # Device management
│   │   ├── adb.py        # ADB command handling
│   │   ├── app_management.py # App installation and management
│   │   ├── device_control.py # Device control operations
│   │   ├── file_management.py # File upload/download
│   │   ├── platform.py   # Platform detection
│   │   ├── services.py   # Device services management
│   │   └── session.py    # Session data handling
│   └── mcp_server/       # Main server and tool definitions
│       ├── __init__.py   # MCP server package initialization
│       ├── server_main.py    # Main entry point for FastMCP server
│       ├── shared_mcp.py     # Shared FastMCP instance
│       └── tools/            # Category-based tool implementations
│           ├── device_management_tool.py     # Device management operations
│           ├── device_control_tool.py        # Device control and monitoring
│           ├── file_app_management_tool.py   # File and app management
│           ├── session_analytics_tool.py     # Session data and analytics
│           └── appium_capabilities_tool.py   # Appium capabilities code generation
```

- **.env**: Your pCloudy credentials and environment variables. Use `.env.template` as a starting point.
- **src/api/**: Contains modular mixins for each pCloudy API area (auth, device, file, etc.).
- **src/mcp_server/tools/**: Each meta-tool (device management, control, etc.) is implemented here.
- **src/mcp_server/server_main.py**: The main entry point that registers all tools and starts the FastMCP server.
- **config.py, utils.py, security.py**: Shared configuration, utility, and security logic.
- **pcloudy_mcp_server.log**: All logs are written here for debugging and audit.

This structure keeps configuration, API logic, and tool implementations modular and easy to maintain.

## Notes

- **Python Version**: Requires Python 3.13.
  On Ubuntu, you might use:

  ```bash
  sudo apt install python3.13 python3.13-venv python3.13-dev
  ```

- **Logs**: Log messages are saved in `pcloudy_mcp_server.log`. Check this file for detailed error messages if issues occur.
- **Environment**: Place your `.env` file in the project root. Use `.env.template` as a starting point.
- **Security**: Ensure you secure your credentials. The server runs a local HTTP server on `localhost` for authentication, which shuts down after use. For production, consider using HTTPS and additional security measures.
- **Troubleshooting**:
  - **Import Errors**: If you encounter "ModuleNotFoundError", ensure you're running the server from the project root directory.
  - **Python Path Issues**: The project includes automatic path resolution for module imports.
  - Verify your network access to `https://device.pcloudy.com/api`.
  - Ensure your pCloudy `username` and `api_key` are correct when prompted during authentication.
  - If authentication fails, check `pcloudy_mcp_server.log` for the raw API response to diagnose the issue (e.g., invalid credentials or API errors).
  - If you encounter port conflicts (e.g., on port 8080 used for authentication), the server will automatically retry with the next available port.
  - For performance data issues, ensure the package name is correct and the app is installed and running.
  - Use `device_management(action="detect_platform", rid="device_id")` if unsure about device platform compatibility.
  - **Windows Users**: Use PowerShell commands as shown in the setup instructions.

## Migration from Previous Version

If upgrading from the previous 17-tool architecture:

**Old Approach:**

```python
list_available_devices(platform="android")
book_device_by_name(device_name="GalaxyS10")
capture_device_screenshot(rid="123")
```

**New Category-Based Approach:**

```python
device_management(action="list", platform="android")
device_management(action="book", device_name="GalaxyS10")
device_control(action="screenshot", rid="123")
```

The new approach provides the same functionality with a cleaner, more organized interface.

---

## 🔄 Recent Updates (June 26, 2025)

### ✅ Bug Fixes & Improvements

- **Fixed Import Issues**: Resolved ModuleNotFoundError for config and api modules
- **Enhanced Error Handling**: Improved server shutdown and cleanup processes
- **Cross-Platform Support**: Better Windows PowerShell compatibility
- **Path Resolution**: Automatic module path resolution for all tool components
- **Dependencies**: Added python-dotenv for better environment variable handling

### 🏗️ Architecture Enhancements

- **Modular Design**: Clean separation between API logic and MCP tools
- **Robust Import System**: Automatic path management for nested module structure
- **Improved Logging**: Better error tracking and debugging capabilities

---

## Updated: June 26, 2025

Streamlined with category-based architecture, intelligent routing, enhanced automation, and resolved import issues for seamless deployment.
