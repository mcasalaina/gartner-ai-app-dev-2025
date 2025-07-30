@echo off
echo Starting Playwright MCP Server...
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 18 or newer from https://nodejs.org/
    pause
    exit /b 1
)

echo Node.js version:
node --version

echo.
echo Installing/updating Playwright MCP server...
npx @playwright/mcp@latest --help >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to install Playwright MCP server
    pause
    exit /b 1
)

echo.
echo Starting Playwright MCP server on port 8931...
echo Server will be available at: http://localhost:8931/mcp
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the MCP server with common settings
npx @playwright/mcp@latest --port 8931 --headless --browser chrome --viewport-size "1280,720"
