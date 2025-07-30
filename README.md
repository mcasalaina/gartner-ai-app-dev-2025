# Microsoft's Gartner AI App Development Magic Quadrant 2025 Companion Repo

This repository serves as a companion to Microsoft's submission for the Gartner AI App Development Magic Quadrant 2025.

## Getting Started

To set up the project and get it working for yourself, you'll need to populate the `.env` file with the appropriate environment variables.

### Environment Variables

Create a `.env` file in the root directory by copying the `env.template` file and filling in your actual values:

```bash
cp env.template .env
```

Then edit the `.env` file with the following required variables:

```plaintext
# Azure AI Project Configuration

# Azure AI Project endpoint URL
PROJECT_ENDPOINT=https://your-project-endpoint.services.ai.azure.com/api/projects/your-project-name

# Azure subscription information
AZURE_SUBSCRIPTION_ID=your-azure-subscription-id
AZURE_RESOURCE_GROUP_NAME=your-resource-group-name
AZURE_PROJECT_NAME=your-azure-ai-project-name

# Name of your Bing search resource
BING_RESOURCE_NAME=your-bing-resource-name

# Name of your deep research model deployment
DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME=your-deep-research-model-deployment

# Name of your the model deployment driving the agent
AGENT_MODEL_DEPLOYMENT_NAME=your-model-deployment-name
```

Replace all the placeholder values with your actual Azure AI project configuration details.

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
