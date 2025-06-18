# pCloudy MCP Server (Category-Based Architecture)

This project implements a streamlined MCP server for managing Android and iOS devices on the pCloudy platform. It features a **category-based tool architecture** with 4 meta-tools that intelligently route operations, replacing the previous 17 individual tools for a cleaner, more intuitive interface.

**Author**: Rishav Raj

## �️ Architecture Overview

The project is organized into a modular structure:

- **`src/mcp_server/`** - FastMCP server implementation with category-based tools
- **`src/pcloudy_api/`** - Clean API wrapper for pCloudy platform operations  
- **`env/`** - Environment configuration with template for easy setup
- **Modern tooling** - Uses `uv` for dependency management and `pyproject.toml` for project configuration

## �🎯 Category-Based Tool Architecture (4 Meta-Tools)

### 📱 Device Management (`device_management`)

**Actions**: `list`, `book`, `release`, `detect_platform`, `set_location`

- **list**: List available devices (platform="android"/"ios")
- **book**: Book device (device_name="GalaxyS10", platform="android", auto_start_services=True)
- **release**: Release device (rid="device_id")
- **detect_platform**: Auto-detect device platform (rid="device_id")
- **set_location**: Set GPS coordinates (rid="device_id", latitude=48.8566, longitude=2.3522)

### 📸 Device Control & Monitoring (`device_control`)

**Actions**: `screenshot`, `get_url`, `start_services`, `adb`, `wildnet`

- **screenshot**: Capture device screenshot (rid="device_id", skin=True)
- **get_url**: Get device page URL and open in browser (rid="device_id")
- **start_services**: Start device services (rid="device_id", start_device_logs=True, start_performance_data=True, start_session_recording=True)
- **adb**: Execute ADB command on Android (rid="device_id", adb_command="logcat", platform="auto")
- **wildnet**: Start wildnet features (rid="device_id")

### 📦 File & App Management (`file_app_management`)

**Actions**: `upload`, `list_apps`, `install`, `resign`, `download_cloud`

- **upload**: Upload APK/IPA file (file_path="/path/to/app.apk", force_upload=False)
- **list_apps**: List cloud apps (limit=10, filter_type="all")
- **install**: Install and launch app (rid="device_id", filename="app.apk", grant_all_permissions=True, platform="android", app_package_name="com.example.app")
- **resign**: Resign iOS IPA file (filename="app.ipa", force_resign=False)
- **download_cloud**: Download file from cloud (filename="app.apk")

### 📊 Session Data & Analytics (`session_analytics`)

**Actions**: `download_session`, `list_performance`

- **download_session**: Download session data (rid="device_id", filename="optional_specific_file", download_dir="optional_directory")
- **list_performance**: List performance data files (rid="device_id")

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

## 🚀 Setup

### 📁 Project Structure

```text
pcloudy-mcp-server/
├── .venv/                    # Virtual environment
├── env/                      # Environment configuration
│   ├── .env                  # Your credentials (gitignored)
│   └── .env.template         # Template with setup instructions
├── src/                      # Source code
│   ├── mcp_server/          # MCP server implementation
│   │   ├── server.py        # Main server file
│   │   ├── device_control_tool.py
│   │   ├── device_management_tool.py
│   │   ├── file_app_management_tool.py
│   │   └── session_analytics_tool.py
│   ├── pcloudy_api/         # pCloudy API wrapper
│   │   ├── core.py          # Core API functionality
│   │   ├── device_control.py
│   │   ├── device_management.py
│   │   ├── file_management.py
│   │   └── session_management.py
│   ├── config.py            # Configuration settings
│   └── utils.py             # Utility functions
├── pyproject.toml           # Project dependencies
└── uv.lock                  # Dependency lock file
```

### 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone <repository_url>
   cd pcloudy-mcp-server
   ```

2. **Install dependencies using uv (recommended):**

   ```bash
   uv sync
   ```

   **Or using pip:**

   ```bash
   python -m venv .venv
   # Activate virtual environment
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Configure environment:**

   ```bash
   # Copy the template
   cp env/.env.template env/.env
   
   # Edit with your pCloudy credentials
   # Replace placeholders with:
   # - PCLOUDY_USERNAME: your-email@domain.com
   # - PCLOUDY_API_KEY: your-api-key-here
   ```

4. **Dependencies included:**
   - `fastmcp>=2.5.1` - MCP server framework
   - `fastapi>=0.115.12` - Web framework
   - `aiofiles>=24.1.0` - Async file operations

## 🎯 Running the Server

### Method 1: Direct Python execution

```bash
cd src
python mcp_server/server.py
```

### Method 2: Using FastMCP (development)

```bash
fastmcp dev src/mcp_server/server.py
```

### Method 3: Install for Claude Desktop

```bash
fastmcp install src/mcp_server/server.py
```

The server will start on `http://0.0.0.0:8000/mcp` by default.

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
- **Wildnet Integration**: Enhanced network testing capabilities

### 🛡️ Security & Validation

- **Input Validation**: Comprehensive validation for all parameters
- **Path Security**: Download directory validation prevents security issues
- **Platform Compatibility**: Automatic platform detection prevents incompatible operations
- **Error Handling**: Detailed error messages and graceful failure handling

## 🛠️ Quick Troubleshooting

### Server Won't Start

```bash
# Check if running from correct directory
cd src && python mcp_server/server.py

# Verify environment file exists
ls ../env/.env

# Check dependencies
uv sync
```

### Import Errors

```bash
# Ensure all modules are in the correct structure:
src/
├── mcp_server/server.py
├── pcloudy_api/
└── config.py
```

### Authentication Issues

- Check credentials in `env/.env`
- Verify pCloudy account access
- Check `pcloudy_mcp_server.log` for detailed errors

## Notes

- **Python Version**: Requires Python 3.13.
  On Ubuntu, you might use:

  ```bash
  sudo apt install python3.13 python3.13-venv python3.13-dev
  ```

- **Logs**: Log messages are saved in `pcloudy_mcp_server.log`. Check this file for detailed error messages if issues occur.

- **Security**: Ensure you secure your credentials. The server runs a local HTTP server on `localhost` for authentication, which shuts down after use. For production, consider using HTTPS and additional security measures.

- **Troubleshooting**:
  - Verify your network access to `https://device.pcloudy.com/api`.
  - Ensure your pCloudy `username` and `api_key` are correct when prompted during authentication.
  - If authentication fails, check `pcloudy_mcp_server.log` for the raw API response to diagnose the issue (e.g., invalid credentials or API errors).
  - If you encounter port conflicts (e.g., on port 8080 used for authentication), the server will automatically retry with the next available port.
  - For performance data issues, ensure the package name is correct and the app is installed and running.
  - Use `device_management(action="detect_platform", rid="device_id")` if unsure about device platform compatibility.

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

## Updated: June 18, 2025

Streamlined with category-based architecture, intelligent routing, enhanced automation, and updated project structure.
