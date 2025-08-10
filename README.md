# Microsoft's Gartner AI App Development Magic Quadrant 2025 Companion Repo

This repository serves as a companion to Microsoft's submission for the Gartner AI App Development Magic Quadrant 2025.

## Grounding files

The restaurant grounding files (HTML and PDFs such as the menu and opening hours) are included in this repository and can also be accessed online at:

<https://mcasalainadocs.z21.web.core.windows.net/gartner/>

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

## Local Restaurant Assistant

This repository includes a local restaurant assistant (`local_restaurant_assistant.py`) that uses Microsoft's Foundry Local to run AI models directly on your device, providing privacy and offline capabilities.

### Prerequisites for Local Assistant

To use the local restaurant assistant, you need to have **Microsoft Foundry Local** installed on your system.

#### System Requirements

- **Operating System**: Windows 10 (x64), Windows 11 (x64/ARM), Windows Server 2025, or macOS
- **Hardware**: Minimum 8GB RAM, 3GB free disk space (Recommended: 16GB RAM, 15GB free disk space)
- **Network**: Internet connection for initial model download (optional for offline use afterward)
- **Acceleration (optional)**: NVIDIA GPU (2,000 series or newer), AMD GPU (6,000 series or newer), Intel iGPU, Qualcomm Snapdragon X Elite (8GB+ memory), or Apple silicon
- **Permissions**: Administrative privileges to install software

#### Install Foundry Local

**For Windows:**

```bash
winget install Microsoft.FoundryLocal
```

**For macOS:**

```bash
brew tap microsoft/foundrylocal
brew install foundrylocal
```

**Alternative Installation:**
You can also download the installer directly from the [Foundry Local GitHub repository](https://aka.ms/foundry-local-installer).

#### Verify Installation

After installation, verify that Foundry Local is working by running:

```bash
foundry --version
```

You can also test with a simple model:

```bash
foundry model run phi-4-mini
```

#### Using the Local Restaurant Assistant

Once Foundry Local is installed, you can run the local restaurant assistant:

```bash
python local_restaurant_assistant.py
```

The assistant will:

1. Automatically start the Foundry Local service if not running
2. Load the Phi-4-mini-instruct model optimized for your hardware
3. Load restaurant information from `local_assistant_info.md`
4. Prompt you to ask questions about Scheibmeir's Steaks, Snacks, and Sticks
5. Provide responses using the local AI model with restaurant context

**Note:** The first run may take several minutes as the model needs to be downloaded. Subsequent runs will be much faster as the model is cached locally.

For more information about Foundry Local, visit the [official documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started).
