# Microsoft's Gartner AI App Development Magic Quadrant 2025 Companion Repo

This repository serves as a companion to Microsoft's submission for the Gartner AI App Development Magic Quadrant 2025.

## Getting Started

To set up the project and get it working for yourself, you'll need to populate the `.env` file with the appropriate environment variables.

### Environment Variables

Create a `.env` file in the root directory by copying the `env.template` file and filling in your actual values:

```bash
cp env.template .env
```

Then edit the `.env` file with your actual configuration. Here's where to find each variable:

#### Required Azure AI Project Configuration

```plaintext
# Azure AI Project endpoint URL
# Get from: Azure AI Foundry Studio > Your Project > Overview > Endpoint
DEEP_RESEARCH_PROJECT_ENDPOINT=https://your-project-endpoint.services.ai.azure.com/api/projects/your-project-name

# Azure subscription information
# Get from: Azure Portal > Subscriptions
AZURE_SUBSCRIPTION_ID=your-azure-subscription-id

# Resource group containing your AI project
# Get from: Azure Portal > Resource Groups
AZURE_RESOURCE_GROUP_NAME=your-resource-group-name

# Name of your Azure AI project
# Get from: Azure AI Foundry Studio > Your Project > Settings
AZURE_PROJECT_NAME=your-azure-ai-project-name

# Name of your Bing search resource for web searches
# Get from: Azure Portal > Cognitive Services > Bing Search > Resource name
BING_RESOURCE_NAME=your-bing-resource-name

# Model deployment names from your AI project
# Get from: Azure AI Foundry Studio > Your Project > Deployments
DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME=your-deep-research-model-deployment
AGENT_MODEL_DEPLOYMENT_NAME=your-model-deployment-name
```

#### Azure AI Foundry Tracing Configuration

This application includes comprehensive tracing to Azure AI Foundry for monitoring and debugging:

```plaintext
# Set to "true" to capture full content in traces (may include personal data)
# Set to "false" for metadata-only tracing (recommended for production)
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true

# Application Insights Connection String (Required for tracing)
# Get from: Azure Portal > Application Insights > Overview > Connection String
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=12345678-1234-1234-1234-123456789012;IngestionEndpoint=https://...
```

**To get the Application Insights Connection String:**

1. Go to Azure Portal → Application Insights
2. Select your Application Insights resource (or create one if needed)
3. Go to Overview
4. Copy the "Connection String" value

**What the tracing captures:**

- User research requests and responses
- Agent creation and configuration
- Thread and message management
- Research execution with timing metrics
- All OpenAI API calls with token usage
- Error handling and performance metrics

Traces will appear in your Azure AI Foundry project under the "Tracing" section, typically within 1-2 minutes of execution.

## Installation

1. Clone the repository:

    ```sh
    git clone <repository-url>
    ```

2. Navigate to the project directory:

    ```sh
    cd gartner-ai-app-dev-2025
    ```

3. Create a virtual environment:

    ```sh
    python -m venv venv
    ```

4. Activate the virtual environment:

    ```sh
    .\venv\Scripts\Activate.ps1
    ```

5. Install the dependencies:

    ```sh
    pip install -r requirements.txt
    ```

You're all set to start using the application!
