#!/usr/bin/env python3
"""
Test script to verify Playwright MCP server connection and basic functionality.
Run this script to ensure your Playwright MCP server is properly configured.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mcp_connection():
    """Test basic connection to the Playwright MCP server"""
    
    mcp_url = os.environ.get("PLAYWRIGHT_MCP_URL", "http://localhost:8931/mcp")
    print(f"Testing connection to Playwright MCP server at: {mcp_url}")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{mcp_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ MCP server is responding to health checks")
        else:
            print(f"⚠️  MCP server responded with status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MCP server")
        print("Make sure the Playwright MCP server is running:")
        print("  npx @playwright/mcp@latest --port 8931")
        return False
    except requests.exceptions.Timeout:
        print("❌ Connection to MCP server timed out")
        return False
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        return False
    
    try:
        # Test tools endpoint
        response = requests.get(f"{mcp_url}/tools", timeout=10)
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ MCP server tools endpoint is working")
            print(f"📋 Available tools: {len(tools)} found")
            
            # List some available tools
            tool_names = [tool.get('name', 'Unknown') for tool in tools if isinstance(tool, dict)]
            if tool_names:
                print(f"🔧 Tool names: {', '.join(tool_names[:5])}")
                if len(tool_names) > 5:
                    print(f"   ... and {len(tool_names) - 5} more")
        else:
            print(f"⚠️  Tools endpoint responded with status code: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️  Could not fetch tools information: {e}")
    
    return True

def test_azure_ai_imports():
    """Test that required Azure AI packages are installed"""
    
    print("\nTesting Azure AI package imports...")
    
    try:
        from azure.ai.projects import AIProjectClient
        print("✅ azure.ai.projects imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import azure.ai.projects: {e}")
        return False
    
    try:
        from azure.ai.agents import AgentsClient
        from azure.ai.agents.models import McpTool
        print("✅ azure.ai.agents and McpTool imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import azure.ai.agents or McpTool: {e}")
        print("Make sure you have the latest Azure AI packages installed:")
        print("  pip install azure-ai-projects azure-ai-agents")
        return False
    
    return True

def test_environment_variables():
    """Test that required environment variables are set"""
    
    print("\nTesting environment variables...")
    
    required_vars = [
        "DEEP_RESEARCH_PROJECT_ENDPOINT",
        "AZURE_SUBSCRIPTION_ID", 
        "AZURE_RESOURCE_GROUP_NAME",
        "AZURE_PROJECT_NAME",
        "BING_RESOURCE_NAME",
        "DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME",
        "AGENT_MODEL_DEPLOYMENT_NAME"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var} is set")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with the missing variables")
        return False
    
    playwright_url = os.environ.get("PLAYWRIGHT_MCP_URL")
    if playwright_url:
        print(f"✅ PLAYWRIGHT_MCP_URL is set to: {playwright_url}")
    else:
        print("⚠️  PLAYWRIGHT_MCP_URL not set, will use default: http://localhost:8931/mcp")
    
    return True

def main():
    """Main test function"""
    
    print("🧪 Playwright MCP Server Test Suite")
    print("=" * 50)
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    # Test Azure AI imports
    imports_ok = test_azure_ai_imports()
    
    # Test MCP connection
    mcp_ok = test_mcp_connection()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Environment Variables: {'✅ Pass' if env_ok else '❌ Fail'}")
    print(f"Azure AI Imports: {'✅ Pass' if imports_ok else '❌ Fail'}")
    print(f"MCP Server Connection: {'✅ Pass' if mcp_ok else '❌ Fail'}")
    
    if env_ok and imports_ok and mcp_ok:
        print("\n🎉 All tests passed! You're ready to run the Deep Research Agent with Playwright.")
        print("\nNext steps:")
        print("1. Make sure your Playwright MCP server is running:")
        print("   npx @playwright/mcp@latest --port 8931")
        print("2. Run the agent:")
        print("   python deep-research-agent-with-playwright.py")
    else:
        print("\n⚠️  Some tests failed. Please address the issues above before running the agent.")
        
        if not mcp_ok:
            print("\n🚀 To start the Playwright MCP server:")
            print("   On Windows: start-playwright-mcp.bat")
            print("   On Mac/Linux: npx @playwright/mcp@latest --port 8931")

if __name__ == "__main__":
    main()
