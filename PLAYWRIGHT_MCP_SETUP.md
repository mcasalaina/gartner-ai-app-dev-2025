# Setup Script for Playwright MCP Server with Deep Research Agent

This script helps you set up the Playwright MCP server to work with the Deep Research Agent.

## Prerequisites

1. Node.js 18 or newer installed
2. Python environment with Azure AI packages
3. Azure AI Foundry project set up with proper credentials

## Installation Steps

### 1. Install Playwright MCP Server

```bash
# Install the Playwright MCP server globally
npm install -g @playwright/mcp@latest

# Or run directly with npx (recommended)
npx @playwright/mcp@latest --help
```

### 2. Start Playwright MCP Server

For local development, start the MCP server on a specific port:

```bash
# Start the server on port 8931 with HTTP transport
npx @playwright/mcp@latest --port 8931 --headless
```

For headed browser (with GUI):
```bash
npx @playwright/mcp@latest --port 8931
```

### 3. Environment Variables

Add the following to your `.env` file:

```env
# Playwright MCP Server URL (if running locally)
PLAYWRIGHT_MCP_URL=http://localhost:8931/mcp

# If using a remote Playwright MCP server
# PLAYWRIGHT_MCP_URL=https://your-remote-mcp-server.com/mcp
```

### 4. Alternative: Docker Setup

You can also run the Playwright MCP server in Docker:

```bash
# Build the Docker image
docker build -t playwright-mcp https://github.com/microsoft/playwright-mcp.git

# Run the container
docker run -p 8931:8931 playwright-mcp --port 8931 --host 0.0.0.0
```

## Configuration Options

The Playwright MCP server supports many configuration options:

### Basic Configuration
```bash
npx @playwright/mcp@latest \
  --port 8931 \
  --headless \
  --browser chrome \
  --viewport-size "1280,720"
```

### With Authentication/Proxy
```bash
npx @playwright/mcp@latest \
  --port 8931 \
  --proxy-server "http://proxy:3128" \
  --user-agent "Custom User Agent"
```

### Security Options
```bash
npx @playwright/mcp@latest \
  --port 8931 \
  --allowed-origins "https://example.com;https://trusted-site.com" \
  --blocked-origins "https://malicious-site.com" \
  --ignore-https-errors
```

## Testing the Setup

Once you have the Playwright MCP server running, test the connection:

```python
# Test script to verify MCP connection
import requests

mcp_url = "http://localhost:8931/mcp"
try:
    response = requests.get(f"{mcp_url}/tools")
    print("MCP Server is running!")
    print(f"Available tools: {response.json()}")
except Exception as e:
    print(f"Error connecting to MCP server: {e}")
```

## Running the Deep Research Agent with Playwright

1. Ensure your Playwright MCP server is running
2. Set the `PLAYWRIGHT_MCP_URL` environment variable
3. Run the agent:

```bash
python deep-research-agent-with-playwright.py
```

## Available Playwright Tools

The agent has access to these Playwright MCP tools:

- `browser_navigate` - Navigate to URLs
- `browser_snapshot` - Take accessibility snapshots
- `browser_click` - Click on elements
- `browser_type` - Type text into fields
- `browser_wait_for` - Wait for elements or conditions
- `browser_take_screenshot` - Capture screenshots
- `browser_evaluate` - Execute JavaScript

## Troubleshooting

### Common Issues

1. **MCP Server not starting:**
   - Check Node.js version (needs 18+)
   - Try running with `--no-sandbox` flag on Linux

2. **Connection refused:**
   - Verify the server is running on the correct port
   - Check firewall settings
   - Ensure PLAYWRIGHT_MCP_URL is correct

3. **Browser not launching:**
   - Install browsers: `npx playwright install`
   - Try `--headless` mode
   - Check system dependencies

4. **Permission errors:**
   - Run with appropriate user permissions
   - Check browser executable permissions

### Debug Mode

Run the MCP server with verbose logging:

```bash
npx @playwright/mcp@latest --port 8931 --debug
```

## Security Considerations

When using the Playwright MCP server:

1. **Network Security:** Only expose the MCP server to trusted networks
2. **Origin Control:** Use `--allowed-origins` to restrict which sites can be accessed
3. **Approval Mode:** Set `require_approval: "always"` for sensitive operations
4. **Isolation:** Use `--isolated` mode for testing to avoid persistent state

## Example MCP Configuration for VS Code

If you want to use this with VS Code MCP extension:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--port", "8931",
        "--headless"
      ]
    }
  }
}
```
