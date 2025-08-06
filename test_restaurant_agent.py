#!/usr/bin/env python3
"""
Test script to connect to the Azure AI Foundry restaurant agent and test with Scheibmeir's restaurant queries.
"""

import os
from dotenv import load_dotenv
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

def main():
    # Load environment variables
    load_dotenv()
    
    # Get restaurant agent configuration
    assistant_id = os.getenv("RESTAURANT_ASSISTANT_ID")
    model = os.getenv("RESTAURANT_ASSISTANT_MODEL")
    project_url = os.getenv("RESTAURANT_ASSISTANT_PROJECT")
    
    print(f"Assistant ID: {assistant_id}")
    print(f"Model: {model}")
    print(f"Project URL: {project_url}")
    
    if not all([assistant_id, model, project_url]):
        print("Error: Missing restaurant agent configuration in .env file")
        return
    
    try:
        # Initialize the Agents client
        credential = DefaultAzureCredential()
        agents_client = AgentsClient(
            endpoint=project_url,
            credential=credential
        )
        
        # Test query about Scheibmeir's restaurant
        test_query = "What are the opening hours for Scheibmeir's restaurant?"
        
        print(f"\nTesting query: '{test_query}'")
        print("Connecting to restaurant agent...")
        
        # Create a thread and run in one step
        result = agents_client.create_thread_and_process_run(
            agent_id=assistant_id,
            thread={
                "messages": [
                    {
                        "role": "user",
                        "content": test_query
                    }
                ]
            }
        )
        
        print(f"Run finished with status: {result.status}")
        
        if result.status == "failed":
            print(f"Run failed: {result.last_error}")
            return
        
        # Get messages from the thread
        messages = agents_client.messages.list(thread_id=result.thread_id)
        
        # Print the conversation
        for msg in messages:
            print(f"\nRole: {msg.role}")
            print(f"Content: {msg.content[0].text.value}")
            print("-" * 40)
        
        print("\nTest completed successfully! Restaurant agent is working.")
        
    except Exception as e:
        print(f"Error connecting to restaurant agent: {e}")
        import traceback
        traceback.print_exc()
        print("Please check your Azure credentials and .env configuration.")

if __name__ == "__main__":
    main()