<<<<<<< HEAD
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

- **authorize**: Authenticate with pCloudy by opening a browser window where you can enter your `username` and `api_key`. Upon successful authentication, the token is stored for use in other tools.
- **list_available_devices**: List available Android/iOS devices on the pCloudy platform.
- **book_device_by_name**: Book a device by its name (e.g., "Galaxy S10").
- **upload_file**: Upload an APK/IPA/ZIP file to the pCloudy drive.
- **download_from_cloud**: Download files from the pCloudy drive.
- **download_manual_access_data**: Download files (e.g., screenshots) from a booked device session.
- **list_cloud_apps**: List apps/files in the pCloudy drive.
- **resign_ipa**: Resign iOS IPA files for deployment.
- **install_and_launch_app**: Install and launch an app on a booked device (with an optional `grant_all_permissions` parameter, defaults to `True`).
- **capture_device_screenshot**: Capture a screenshot from a booked device (with an optional `skin` parameter to include device skin, defaults to `True`).
- **get_device_page_url**: Retrieve the device page URL from pCloudy for a booked device.

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

---

*Updated: June 02, 2025, 03:44 PM IST*
=======
# New_MCP
>>>>>>> 2d34048950637c241a4a83bfbdf97bd468753f50
