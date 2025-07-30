@echo off
echo Starting Playwright MCP Server...
echo.

echo.
echo Starting Playwright MCP server on port 8931...
echo Server will be available at: http://localhost:8931/mcp
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the MCP server with common settings
npx @playwright/mcp@latest --port 8931 --headless --browser chrome --viewport-size "1280,720"
