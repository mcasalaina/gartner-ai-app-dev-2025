import os, time, re
from typing import Optional
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import DeepResearchTool, MessageRole, ThreadMessage, McpTool

# Load environment variables from .env file if they're not already set
load_dotenv()


def convert_citations_to_superscript(markdown_content):
    """
    Convert citation markers in markdown content to HTML superscript format.
    
    This function finds citation patterns like 【78:12†source】 and converts them to 
    HTML superscript tags <sup>12</sup> for better formatting in markdown documents.
    
    Args:
        markdown_content (str): The markdown content containing citation markers
        
    Returns:
        str: The markdown content with citations converted to HTML superscript format"
    """
    # Pattern to match 【number:number†source】
    pattern = r'【\d+:(\d+)†source】'
    
    # Replace with <sup>captured_number</sup>
    def replacement(match):
        citation_number = match.group(1)
        return f'<sup>{citation_number}</sup>'
    
    return re.sub(pattern, replacement, markdown_content)


def fetch_and_print_new_agent_response(
    thread_id: str,
    agents_client: AgentsClient,
    last_message_id: Optional[str] = None,
) -> Optional[str]:
    """
    Fetch the interim agent responses and citations from a thread and print them to the terminal.
    
    Args:
        thread_id (str): The ID of the thread to fetch messages from
        agents_client (AgentsClient): The Azure AI agents client instance
        last_message_id (Optional[str], optional): ID of the last processed message 
            to avoid duplicates. Defaults to None.
            
    Returns:
        Optional[str]: The ID of the latest message if new content was found, 
            otherwise returns the last_message_id
    """
    response = agents_client.messages.get_last_message_by_role(
        thread_id=thread_id,
        role=MessageRole.AGENT,
    )
    if not response or response.id == last_message_id:
        return last_message_id  # No new content

    # if not a "cot_summary" return
    if not any(t.text.value.startswith("cot_summary:") for t in response.text_messages):
        return last_message_id    

    print("\nAGENT>")
    print("\n".join(t.text.value.replace("cot_summary:", "Reasoning:") for t in response.text_messages))
    print()

    for ann in response.url_citation_annotations:
        print(f"Citation: [{ann.url_citation.title}]({ann.url_citation.url})")

    return response.id


def create_research_summary(
        message : ThreadMessage,
) -> None:
    """
    Create a formatted research report from an agent's thread message with numbered citations 
    and a references section, printed to the terminal.
    
    Args:
        message (ThreadMessage): The thread message containing the agent's research response
            
    Returns:
        None: This function doesn't return a value, it prints to the terminal
    """
    if not message:
        print("No message content provided, cannot create research report.")
        return

    print("\n" + "="*80)
    print("FINAL RESEARCH REPORT")
    print("="*80)

    # Print text summary
    text_summary = "\n\n".join([t.text.value.strip() for t in message.text_messages])
    # Convert citations to superscript format
    text_summary = convert_citations_to_superscript(text_summary)
    print(text_summary)

    # Print unique URL citations with numbered bullets, if present
    if message.url_citation_annotations:
        print("\n\n## Citations")
        seen_urls = set()
        citation_dict = {}
        
        for ann in message.url_citation_annotations:
            url = ann.url_citation.url
            title = ann.url_citation.title or url
            
            if url not in seen_urls:
                # Extract citation number from annotation text like "【58:1†...】"
                citation_number = None
                if ann.text and ":" in ann.text:
                    match = re.search(r'【\d+:(\d+)', ann.text)
                    if match:
                        citation_number = int(match.group(1))
                
                if citation_number is not None:
                    citation_dict[citation_number] = f"[{title}]({url})"
                else:
                    # Fallback for citations without proper format
                    citation_dict[len(citation_dict) + 1] = f"[{title}]({url})"
                
                seen_urls.add(url)
        
        # Print citations in numbered order
        for num in sorted(citation_dict.keys()):
            print(f"{num}. {citation_dict[num]}")

    print("="*80)
    print("Research report completed.")
    print("="*80)


if __name__ == "__main__":
    project_client = AIProjectClient(
        endpoint=os.environ["PROJECT_ENDPOINT"],
        subscription_id=os.environ["AZURE_SUBSCRIPTION_ID"],
        resource_group_name=os.environ["AZURE_RESOURCE_GROUP_NAME"],
        project_name=os.environ["AZURE_PROJECT_NAME"],
        credential=DefaultAzureCredential(),
    )

    conn_id = project_client.connections.get(name=os.environ["BING_RESOURCE_NAME"]).id

    # Initialize a Deep Research tool with Bing Connection ID and Deep Research model deployment name
    deep_research_tool = DeepResearchTool(
        bing_grounding_connection_id=conn_id,
        deep_research_model=os.environ["DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME"],
    )

    # Set up Playwright MCP server connection
    # This requires a running Playwright MCP server or you can configure to use a remote endpoint
    playwright_mcp_url = os.environ.get("PLAYWRIGHT_MCP_URL", "http://localhost:8931/mcp")
    playwright_mcp_tool = McpTool(
        server_label="playwright",
        server_url=playwright_mcp_url,
        allowed_tools=[]  # Empty list means all tools are allowed
    )
    # Set approval mode to never require approval for browser actions
    playwright_mcp_tool.set_approval_mode("never")

    # Create Agent with both Deep Research and Playwright MCP tools
    with project_client:

        with project_client.agents as agents_client:
            # Create a new agent that has both Deep Research and Playwright MCP tools attached
            agent = agents_client.create_agent(
                # This model runs the actual agent, and it calls the Deep Research model as a tool
                model=os.environ["AGENT_MODEL_DEPLOYMENT_NAME"],
                name="web-browser-researcher",
                instructions="""You are a helpful agent that assists in doing research for restaurants and other businesses.
                
You have access to two powerful tools:
1. Deep Research tool - for comprehensive web research using Bing search
2. Playwright browser automation - for directly browsing websites, taking screenshots, filling forms, clicking buttons, and interacting with web pages

When conducting research:
- Use the Deep Research tool for broad information gathering and search-based research
- Use the Playwright browser tools when you need to:
  * Access dynamic content that requires JavaScript
  * Fill out forms or interact with web applications  
  * Take screenshots of specific pages or sections
  * Navigate through multi-page workflows
  * Access content that might be behind forms or interactions
  * Verify information by directly viewing the source

Always explain which tool you're using and why it's appropriate for the specific research task. You output your results in Markdown without embedded images.""",
                tools=deep_research_tool.definitions + playwright_mcp_tool.definitions,
            )

            print(f"Created agent with Deep Research and Playwright MCP tools, ID: {agent.id}")

            # Create thread for communication
            thread = agents_client.threads.create()
            print(f"Created thread, ID: {thread.id}")

            # Interactive conversation loop
            while True:
                # Get user input for the message
                if 'message' not in locals():
                    # First message - restaurant research example that could benefit from browser automation
                    user_content = """I have rented a new storefront at 340 Jefferson St. in Fisherman's Wharf in San Francisco to open a new outpost of my restaurant chain, Scheibmeir's Steaks, Snacks and Sticks. 

Please help me design a strategy and theme to operate the new restaurant. I'd like you to:

1. Research the area using both your deep research capabilities and by browsing relevant websites directly
2. Look at competitor websites in the area to understand their menus and pricing
3. Take screenshots of key competitor sites for visual reference
4. Check local tourism and visitor websites to understand the customer base
5. Provide one best strategy option rather than multiple choices
6. Generate a FAQ document for customers

Use your browser automation capabilities to gather visual and interactive information that complements your research."""
                else:
                    # Subsequent messages
                    print("\n" + "-"*80)
                    print("Would you like to continue the conversation?")
                    print("Enter your message (or 'quit' to exit):")
                    user_content = input("> ").strip()
                    
                    if user_content.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if not user_content:
                        print("Empty message. Please enter a message or 'quit' to exit.")
                        continue

                # Create message to thread
                message = agents_client.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=user_content,
                )

                print(f"Processing the message... This may take a few minutes to finish. Be patient!")
                
                # Poll the run as long as run status is queued or in progress
                run = agents_client.runs.create(
                    thread_id=thread.id, 
                    agent_id=agent.id,
                    tool_resources=playwright_mcp_tool.resources
                )
                last_message_id = None
                
                while run.status in ("queued", "in_progress"):
                    time.sleep(1)
                    run = agents_client.runs.get(thread_id=thread.id, run_id=run.id)

                    last_message_id = fetch_and_print_new_agent_response(
                        thread_id=thread.id,
                        agents_client=agents_client,
                        last_message_id=last_message_id,
                    )
                    print(f"Run status: {run.status}")

                # Handle approval requirements if needed
                if run.status == "requires_action":
                    print(f"Tool requires approval. Action details available but auto-approval not implemented.")
                    print("Please manually approve the action or modify approval settings.")
                    # For now, we'll continue without implementing complex approval logic
                    continue

                # Once the run is finished, print the final status and ID
                print(f"Run finished with status: {run.status}, ID: {run.id}")

                if run.status == "failed":
                    print(f"Run failed: {run.last_error}")
                    continue  # Allow user to try again

                # Fetch the final message from the agent in the thread and create a research summary
                final_message = agents_client.messages.get_last_message_by_role(
                    thread_id=thread.id, role=MessageRole.AGENT
                )
                if final_message:
                    create_research_summary(final_message)

            # Clean-up and delete the agent once the conversation is finished.
            # NOTE: Comment out this line if you plan to reuse the agent later.
            agents_client.delete_agent(agent.id)
            print("Conversation ended. Deleted agent.")
