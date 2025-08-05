# Deep Research Agent with Playwright Browser Automation

This is an enhanced version of the Deep Research Agent that combines the power of Azure AI's Deep Research capabilities with browser automation through the Playwright Model Context Protocol (MCP) server.

## Features

### Original Deep Research Capabilities
- Multi-step research process using Azure OpenAI's deep research models
- Bing search integration for comprehensive information gathering
- Citation tracking and formatted research reports
- Interactive conversation loop for follow-up questions

### New Browser Automation Capabilities
- Direct website browsing and interaction through Playwright MCP
- Screenshot capture for visual documentation
- Form filling and button clicking for interactive content
- JavaScript execution for dynamic content access
- Multi-tab browsing support
- Accessibility-based interaction (no pixel-based automation)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Azure AI Foundry Agent                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────────────────┐│
│  │   Deep Research     │  │     Playwright MCP Tool             ││
│  │       Tool          │  │                                     ││
│  │                     │  │  ┌─────────────────────────────────┐││
│  │ • Bing Search       │  │  │    Playwright MCP Server        │││
│  │ • Multi-step        │  │  │                                 │││
│  │   research          │  │  │ • browser_navigate              │││
│  │ • Citation          │  │  │ • browser_click                 │││
│  │   tracking          │  │  │ • browser_type                  │││
│  │                     │  │  │ • browser_screenshot            │││
│  └─────────────────────┘  │  │ • browser_evaluate              │││
│                           │  │ • browser_wait_for              │││
│                           │  └─────────────────────────────────┘││
│                           └─────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Node.js 18+** - Required for Playwright MCP server
2. **Python 3.8+** - For the Azure AI agent
3. **Azure AI Foundry Project** - With proper model deployments
4. **Bing Search Resource** - For research capabilities

## Quick Start

### 1. Install Dependencies

```bash
# Python dependencies
pip install azure-ai-projects azure-ai-agents python-dotenv

# Install Playwright MCP server
npm install -g @playwright/mcp@latest
```

### 2. Configure Environment

Copy `.env.template` to `.env` and fill in your Azure configuration:

```env
DEEP_RESEARCH_PROJECT_ENDPOINT=https://your-project.cognitiveservices.azure.com/
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP_NAME=your-resource-group
AZURE_PROJECT_NAME=your-project-name
BING_RESOURCE_NAME=your-bing-resource
DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME=your-deep-research-model
AGENT_MODEL_DEPLOYMENT_NAME=your-agent-model
PLAYWRIGHT_MCP_URL=http://localhost:8931/mcp
```

### 3. Start Playwright MCP Server

**Windows:**
```cmd
start-playwright-mcp.bat
```

**Mac/Linux:**
```bash
npx @playwright/mcp@latest --port 8931 --headless
```

### 4. Test the Setup

```bash
python test-playwright-mcp.py
```

### 5. Run the Agent

```bash
python deep-research-agent-with-playwright.py
```

## Usage Examples

The enhanced agent can now perform sophisticated research tasks that combine search and browser automation:

### Restaurant Market Research
- Search for competitors using Deep Research
- Browse competitor websites directly to analyze menus
- Take screenshots of key pages for visual documentation
- Fill out contact forms to gather information
- Access dynamic content that requires JavaScript

### Real Estate Analysis
- Research property values and market trends
- Browse real estate websites for current listings
- Capture screenshots of property photos and details
- Interact with map interfaces to analyze locations
- Access gated content through form interactions

### Technology Research
- Deep search for technical documentation
- Browse GitHub repositories and documentation sites
- Interact with demo applications and tools
- Capture screenshots of user interfaces
- Test web applications for functionality

## Configuration Options

### Playwright MCP Server Settings

```bash
# Basic configuration
npx @playwright/mcp@latest --port 8931 --headless --browser chrome

# With custom viewport
npx @playwright/mcp@latest --port 8931 --viewport-size "1920,1080"

# With security restrictions
npx @playwright/mcp@latest --port 8931 \
  --allowed-origins "https://example.com;https://trusted-site.com" \
  --blocked-origins "https://malicious-site.com"

# With proxy support
npx @playwright/mcp@latest --port 8931 \
  --proxy-server "http://proxy:3128"
```

### Agent Tool Configuration

In the Python code, you can customize which browser tools are available:

```python
playwright_mcp_tool = McpTool(
    server_label="playwright",
    server_url=playwright_mcp_url,
    allowed_tools=[
        "browser_navigate",      # Navigate to URLs
        "browser_snapshot",      # Take accessibility snapshots
        "browser_click",         # Click elements
        "browser_type",          # Type text
        "browser_wait_for",      # Wait for conditions
        "browser_take_screenshot", # Capture images
        "browser_evaluate"       # Execute JavaScript
    ]
)
```

### Approval Settings

Control when browser actions require approval:

```python
tool_resources = {
    "mcp": [
        {
            "tool_label": "playwright",
            "headers": {},
            "require_approval": "never"  # "always", "never", or specific tools
        }
    ]
}
```

## Available Browser Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `browser_navigate` | Navigate to URLs | Open websites, follow links |
| `browser_snapshot` | Accessibility snapshot | Get page structure for interaction |
| `browser_click` | Click elements | Press buttons, follow links |
| `browser_type` | Type text | Fill forms, search boxes |
| `browser_wait_for` | Wait for conditions | Wait for page loads, dynamic content |
| `browser_take_screenshot` | Capture images | Visual documentation |
| `browser_evaluate` | Execute JavaScript | Access dynamic content, custom interactions |
| `browser_hover` | Hover over elements | Trigger hover effects |
| `browser_select_option` | Select dropdown options | Fill form dropdowns |
| `browser_drag` | Drag and drop | Move elements, advanced interactions |

## Security Considerations

### Network Security
- Run MCP server on localhost for development
- Use `--allowed-origins` to restrict accessible sites
- Consider VPN/proxy for production environments

### Data Privacy
- Browser interactions may expose sensitive data
- Use `--isolated` mode for testing
- Review approval requirements for sensitive operations

### Access Control
- Set appropriate `require_approval` settings
- Monitor browser actions in production
- Use least-privilege principle for tool access

## Troubleshooting

### Common Issues

**MCP Server Connection Failed**
```bash
# Check if server is running
curl http://localhost:8931/mcp/health

# Restart server
npx @playwright/mcp@latest --port 8931
```

**Browser Not Launching**
```bash
# Install browser dependencies
npx playwright install

# Try headless mode
npx @playwright/mcp@latest --port 8931 --headless
```

**Permission Errors**
- Check file permissions for browser executable
- Run with appropriate user privileges
- Try `--no-sandbox` flag on Linux

**Authentication Issues**
- Verify Azure credentials with `az login`
- Check environment variables in `.env`
- Confirm Azure AI project permissions

### Debug Mode

Enable verbose logging:

```bash
# Playwright MCP server with debug output
npx @playwright/mcp@latest --port 8931 --debug

# Python agent with debug logging
export AZURE_LOG_LEVEL=DEBUG
python deep-research-agent-with-playwright.py
```

## Performance Considerations

### Browser Resource Usage
- Use headless mode for better performance
- Set appropriate viewport sizes
- Consider browser memory limits

### Network Efficiency
- Cache frequently accessed content
- Use selective tool enabling
- Implement request throttling if needed

### Scaling
- Multiple MCP server instances for load balancing
- Container deployment for isolated environments
- Consider browser pool management for high volume

## Advanced Usage

### Custom Browser Configuration

```python
# Custom browser settings in MCP server
playwright_args = [
    "--headless",
    "--disable-gpu", 
    "--no-sandbox",
    "--disable-dev-shm-usage"
]
```

### Integration with External Services

```python
# Example: Integrate with screenshot storage
def save_screenshot_to_azure_storage(screenshot_data):
    # Upload to Azure Blob Storage
    pass

# Example: Custom approval workflow
def custom_approval_handler(tool_call):
    # Implement custom approval logic
    return approved
```

### Multi-Agent Scenarios

The Playwright-enabled agent can be part of larger multi-agent systems:
- Research agent gathers information
- Browser agent performs interactions
- Analysis agent processes results
- Reporting agent generates final output

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project follows the same license as the original Azure AI Foundry samples.

## Support

For issues and questions:
- Check the troubleshooting section
- Review [Playwright MCP documentation](https://github.com/microsoft/playwright-mcp)
- Consult [Azure AI Foundry documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/)

---

**Note:** This enhanced agent combines the power of AI research with direct web interaction, enabling more comprehensive and accurate information gathering for complex research tasks.
