# pCloudy MCP Server Startup Script
# This script starts the pCloudy MCP server for Claude Desktop

Write-Host "Starting pCloudy MCP Server..." -ForegroundColor Green

# Set the Python path to include the current directory
$env:PYTHONPATH = "."

# Start the MCP server
python src/mcp_server/server_main.py 