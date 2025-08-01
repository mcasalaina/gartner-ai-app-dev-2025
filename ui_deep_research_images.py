import os
import time
import re
import threading
import base64
import uuid
import json
import requests
from datetime import datetime
from typing import Optional
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import font
from tkhtmlview import HTMLScrolledText
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import DeepResearchTool, MessageRole, ThreadMessage
from openai import AzureOpenAI

# Load environment variables from .env file if they're not already set
load_dotenv()


class ImageGenerator:
    """Image generation tool using Azure OpenAI GPT-Image-1"""
    
    def __init__(self):
        # Check if IMAGE_KEY is available for API key authentication
        self.image_key = os.environ.get("IMAGE_KEY")
        
        if self.image_key:
            # Use API key authentication
            self.token = self.image_key
            self.client = AzureOpenAI(
                api_key=self.image_key,
                api_version=os.environ.get("IMAGE_API_VERSION", "2025-04-01-preview"),
                azure_endpoint=os.environ["IMAGE_PROJECT_ENDPOINT"]
            )
        else:
            # Use Azure AD token authentication
            def get_azure_ad_token():
                token = DefaultAzureCredential().get_token("https://cognitiveservices.azure.com/.default")
                return token.token

            self.token = get_azure_ad_token()
            self.client = AzureOpenAI(
                api_version=os.environ.get("IMAGE_API_VERSION", "2025-04-01-preview"),
                azure_endpoint=os.environ["IMAGE_PROJECT_ENDPOINT"],
                azure_ad_token_provider=get_azure_ad_token
            )
        
        # Ensure images directory exists
        self.images_dir = "./images"
        os.makedirs(self.images_dir, exist_ok=True)
    
    def generate_image(self, prompt: str) -> str:
        """Generate an image from a text prompt and save it to the images directory"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"generated_image_{timestamp}_{unique_id}.png"
            filepath = os.path.join(self.images_dir, filename)

            api_version = os.environ.get("IMAGE_API_VERSION", "2025-04-01-preview")
            azure_endpoint = os.environ["IMAGE_PROJECT_ENDPOINT"]
            model = os.environ["IMAGE_MODEL"]

            # Ensure endpoint ends with /
            if not azure_endpoint.endswith('/'):
                azure_endpoint += '/'

            base_path = f'openai/deployments/{model}/images'
            params = f'?api-version={api_version}'

            generation_url = f"{azure_endpoint}{base_path}/generations{params}"
            generation_body = {
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "medium",
                "output_format": "png"
            }

            # Prepare authentication header
            if self.image_key:
                # Use API key authentication
                auth_header = {'api-key': self.image_key}
            else:
                # Use Bearer token authentication
                auth_header = {'Authorization': 'Bearer ' + self.token}

            response = requests.post(
                generation_url,
                headers={
                    **auth_header,
                    'Content-Type': 'application/json',
                },
                json=generation_body
            ).json()
            
            # Save the image
            if 'data' in response and len(response['data']) > 0 and 'b64_json' in response['data'][0]:
                image_data = base64.b64decode(response['data'][0]['b64_json'])
                with open(filepath, "wb") as f:
                    f.write(image_data)
                
                return filename
            else:
                raise Exception(f"No image data returned from API. Response: {response}")
            
        except Exception as e:
            raise Exception(f"Image generation failed: {str(e)}")


class ImageGenerationTool:
    """Tool definition for image generation that the agent can call"""
    
    def __init__(self, image_generator: ImageGenerator):
        self.image_generator = image_generator
        self.definitions = [{
            "type": "function",
            "function": {
                "name": "generate_image",
                "description": "Generate an image based on a text prompt and save it to the ./images directory. Use this to create relevant visuals for your research. The generated images are saved as PNG files with 1024x1024 resolution and medium quality.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "A detailed description of the image to generate. Be specific about style, content, colors, and composition."
                        }
                    },
                    "required": ["prompt"]
                }
            }
        }]
    
    def execute(self, function_name: str, arguments: dict) -> dict:
        """Execute the image generation function"""
        if function_name == "generate_image":
            try:
                filename = self.image_generator.generate_image(arguments["prompt"])
                return {
                    "status": "success",
                    "filename": filename,
                    "path": f"./images/{filename}",
                    "message": f"Image successfully generated and saved as {filename} in the ./images directory"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e)
                }
        else:
            return {
                "status": "error",
                "message": f"Unknown function: {function_name}"
            }


class DeepResearchAgentUI:
    """Graphical User Interface for the Deep Research Agent with Image Generation"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🔬 Deep Research Agent with Images")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Configure style
        self.setup_styles()
        
        # Initialize variables
        self.is_processing = False
        self.agent = None
        self.agents_client = None
        self.thread = None
        self.current_run = None
        self.project_client_connection = None
        
        # Initialize image generator
        try:
            self.image_generator = ImageGenerator()
            self.image_tool = ImageGenerationTool(self.image_generator)
        except Exception as e:
            self.image_generator = None
            self.image_tool = None
            print(f"Warning: Failed to initialize image generator: {e}")
        
        # Create UI elements
        self.create_widgets()
        
        # Initialize Azure clients
        self.initialize_azure_clients()
    
    def setup_styles(self):
        """Configure the application's visual style"""
        self.root.configure(bg='#f0f0f0')
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure Frame background to match window background
        style.configure('TFrame', background='#f0f0f0')
        
        # Configure button styles
        style.configure('Action.TButton', 
                       font=('Segoe UI', 10, 'bold'),
                       padding=(20, 10))
        
        style.configure('Clear.TButton',
                       font=('Segoe UI', 10),
                       padding=(15, 8))
    
    def create_widgets(self):
        """Create and layout all UI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)  # Left column (request + reasoning)
        main_frame.columnconfigure(1, weight=3)  # Right column (research report gets most space)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = tk.Label(main_frame, text="🔬 Deep Research Agent with Images", 
                              font=('Segoe UI', 18, 'bold'),
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky='w')
        
        # Left column container for input and reasoning
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky='nsew', padx=(0, 15))
        left_frame.rowconfigure(1, weight=1)  # Input section
        left_frame.rowconfigure(3, weight=2)  # Reasoning section gets more space
        left_frame.columnconfigure(0, weight=1)
        
        # Input section
        self.create_input_section(left_frame)
        
        # Reasoning section
        self.create_reasoning_section(left_frame)
        
        # Research report section (right side)
        self.create_research_report_section(main_frame)
        
        # Control buttons
        self.create_control_buttons(main_frame)
    
    def create_input_section(self, parent):
        """Create the input section with request box"""
        # Input label
        input_label = tk.Label(parent, text="📝 Research Request:", 
                              font=('Segoe UI', 12, 'bold'),
                              bg='#f0f0f0', fg='#34495e')
        input_label.grid(row=0, column=0, sticky='nw', pady=(0, 5))
        
        # Input text area
        input_frame = tk.Frame(parent, bg='white', relief='solid', bd=1)
        input_frame.grid(row=1, column=0, sticky='ew', pady=(0, 15))
        
        self.input_text = tk.Text(input_frame, height=8, width=40, 
                                 font=('Segoe UI', 11), wrap=tk.WORD,
                                 relief='flat', padx=10, pady=10)
        input_scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=input_scrollbar.set)
        
        self.input_text.grid(row=0, column=0, sticky='nsew')
        input_scrollbar.grid(row=0, column=1, sticky='ns')
        
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(0, weight=1)
        
        # Default text content
        default_text = ("I have rented a new storefront at 340 Jefferson St. in Fisherman's Wharf in San Francisco to open a new outpost of my restaurant chain, Scheibmeir's Steaks, Snacks and Sticks. Design a menu that offers a combination of steaks, american-style appetizers, chinese-inspired dishes, and fancy jello salads, and make some images of the foods and of the menu.")
        self.input_text.insert(1.0, default_text)
    
    def create_reasoning_section(self, parent):
        """Create the reasoning section"""
        # Reasoning label
        reasoning_label = tk.Label(parent, text="🧠 Agent Reasoning:", 
                                  font=('Segoe UI', 12, 'bold'),
                                  bg='#f0f0f0', fg='#34495e')
        reasoning_label.grid(row=2, column=0, sticky='nw', pady=(0, 5))
        
        # Reasoning frame
        reasoning_frame = tk.Frame(parent, bg='white', relief='solid', bd=1)
        reasoning_frame.grid(row=3, column=0, sticky='nsew', pady=(0, 15))
        
        self.reasoning_text = scrolledtext.ScrolledText(
            reasoning_frame, font=('Segoe UI', 10), wrap=tk.WORD,
            relief='flat', padx=10, pady=10, state='disabled'
        )
        self.reasoning_text.pack(fill='both', expand=True)
    
    def create_research_report_section(self, parent):
        """Create the research report section with HTML rendering"""
        # Research Report label
        report_label = tk.Label(parent, text="📄 Research Report (HTML):", 
                               font=('Segoe UI', 12, 'bold'),
                               bg='#f0f0f0', fg='#34495e')
        report_label.grid(row=1, column=1, sticky='nw', pady=(0, 5))
        
        # Research report frame with overlay for loading spinner
        self.report_frame = tk.Frame(parent, bg='white', relief='solid', bd=1)
        self.report_frame.grid(row=1, column=1, sticky='nsew', pady=(0, 15))
        
        # Report text area using HTMLScrolledText for proper HTML rendering
        self.report_text = HTMLScrolledText(
            self.report_frame, 
            html="<p>Research report will appear here...</p>",
            height=20,
            width=80,
            wrap=tk.WORD,
            relief='flat',
            padx=15,
            pady=15
        )
        self.report_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Loading overlay (initially hidden)
        self.loading_overlay = tk.Frame(self.report_frame, bg='white')
        self.loading_label = tk.Label(self.loading_overlay, 
                                     text="🔄 Processing research request...\nThis may take a few minutes.",
                                     font=('Segoe UI', 12),
                                     bg='white', fg='#7f8c8d')
        self.loading_label.pack(expand=True)
    
    def create_control_buttons(self, parent):
        """Create control buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(15, 0), sticky='ew')
        
        # Submit button
        self.submit_button = ttk.Button(button_frame, text="🚀 Start Research", 
                                       style='Action.TButton',
                                       command=self.start_research)
        self.submit_button.pack(side='left', padx=(0, 15))
        
        # Clear button
        self.clear_button = ttk.Button(button_frame, text="🗑️ Clear All", 
                                      style='Clear.TButton',
                                      command=self.clear_all)
        self.clear_button.pack(side='left', padx=(0, 15))
        
        # Stop button (initially disabled)
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop Research", 
                                     style='Clear.TButton',
                                     command=self.stop_research,
                                     state='disabled')
        self.stop_button.pack(side='left')
        
        # Copy button for research report
        self.copy_button = ttk.Button(button_frame, text="📋 Copy Report", 
                                     style='Clear.TButton',
                                     command=self.copy_report)
        self.copy_button.pack(side='right')
    
    def initialize_azure_clients(self):
        """Initialize Azure AI clients"""
        try:
            self.project_client = AIProjectClient(
                endpoint=os.environ["PROJECT_ENDPOINT"],
                subscription_id=os.environ["AZURE_SUBSCRIPTION_ID"],
                resource_group_name=os.environ["AZURE_RESOURCE_GROUP_NAME"],
                project_name=os.environ["AZURE_PROJECT_NAME"],
                credential=DefaultAzureCredential(),
            )
            
            # Initialize the project client connection
            self.project_client_connection = self.project_client.__enter__()
            self.agents_client = self.project_client_connection.agents.__enter__()
            
            conn_id = self.project_client.connections.get(name=os.environ["BING_RESOURCE_NAME"]).id
            
            # Initialize Deep Research tool
            self.deep_research_tool = DeepResearchTool(
                bing_grounding_connection_id=conn_id,
                deep_research_model=os.environ["DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME"],
            )
            
            # Update status
            self.update_reasoning("✅ Azure AI clients initialized successfully.\n")
            if self.image_generator:
                self.update_reasoning("🖼️ Image generation tool ready.\n")
            else:
                self.update_reasoning("⚠️ Image generation not available - check IMAGE_* environment variables.\n")
            
        except Exception as e:
            error_msg = f"❌ Failed to initialize Azure clients: {str(e)}"
            self.update_reasoning(error_msg)
            messagebox.showerror("Initialization Error", error_msg)
    
    def start_research(self):
        """Start the research process in a separate thread"""
        if self.is_processing:
            return
        
        # Get user input
        user_input = self.input_text.get(1.0, tk.END).strip()
        
        if not user_input:
            messagebox.showwarning("Input Required", "Please enter a research query.")
            return
        
        # Start research in background thread
        self.is_processing = True
        self.show_loading()
        self.update_button_states()
        
        # Clear previous results
        self.clear_outputs()
        
        research_thread = threading.Thread(target=self.run_research, args=(user_input,))
        research_thread.daemon = True
        research_thread.start()
    
    def run_research(self, user_input):
        """Run the research process (called in background thread)"""
        try:
            if not self.agents_client:
                self.update_reasoning("❌ Azure clients not initialized.\n")
                return
                
            # Create agent with enhanced instructions for HTML output and image generation
            self.update_reasoning("🤖 Creating research agent with image capabilities...\n")
            
            agent_instructions = """You are a helpful agent that assists in doing comprehensive research and generating rich HTML reports with images.

IMPORTANT INSTRUCTIONS:
1. Generate your output in HTML format, not markdown. Use proper HTML tags for headers, paragraphs, lists, etc.
2. To include images in your research report, use placeholder image tags like: <img src="GENERATE_IMAGE:detailed_prompt_description" alt="description">
3. Replace "detailed_prompt_description" with a detailed description of the image you want generated
4. The system will automatically generate these images and replace the placeholders with actual image filenames
5. Generate multiple relevant images throughout your research to enhance the report - charts, diagrams, illustrations, concept visualizations, etc.
6. Use proper HTML structure with headings, paragraphs, lists, and styled elements.
7. When referencing sources, use proper HTML anchor tags for links.

Create a comprehensive, visually enhanced research report using HTML format with multiple relevant image placeholders that will be automatically generated."""
            
            # Prepare tools - just use deep research for now, image generation will be handled via placeholders
            tools = self.deep_research_tool.definitions
            
            # Create or reuse agent
            if not self.agent:
                self.agent = self.agents_client.create_agent(
                    model=os.environ["AGENT_MODEL_DEPLOYMENT_NAME"],
                    name="deep-research-agent-with-images",
                    instructions=agent_instructions,
                    tools=tools,
                )
                
                # Create thread if it doesn't exist
                self.update_reasoning("📝 Creating conversation thread...\n")
                self.thread = self.agents_client.threads.create()
            
            # Create message
            self.update_reasoning("💬 Sending research request...\n")
            message = self.agents_client.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=user_input,
            )
            
            # Start run
            self.update_reasoning("🔍 Starting research process...\n\n")
            run = self.agents_client.runs.create(
                thread_id=self.thread.id, 
                agent_id=self.agent.id
            )
            
            self.current_run = run
            last_message_id = None
            
            # Poll for progress
            while run.status in ("queued", "in_progress") and self.is_processing:
                time.sleep(2)
                run = self.agents_client.runs.get(thread_id=self.thread.id, run_id=run.id)
                
                # Fetch and display intermediate responses
                last_message_id = self.fetch_and_display_progress(
                    self.thread.id, self.agents_client, last_message_id
                )
            
            # Handle completion or cancellation
            if not self.is_processing:
                self.update_reasoning("\n⏹️ Research stopped by user.\n")
                return
            
            if run.status == "failed":
                error_msg = f"❌ Research failed: {run.last_error}"
                self.update_reasoning(f"\n{error_msg}\n")
                self.root.after(0, lambda: messagebox.showerror("Research Failed", error_msg))
                return
            
            # Get final results
            self.update_reasoning("\n✅ Research completed! Processing images and generating final report...\n")
            final_message = self.agents_client.messages.get_last_message_by_role(
                thread_id=self.thread.id, role=MessageRole.AGENT
            )
            
            if final_message:
                self.display_final_results_with_images(final_message)
                    
        except Exception as e:
            error_msg = f"❌ Research error: {str(e)}"
            self.update_reasoning(f"\n{error_msg}\n")
            self.root.after(0, lambda: messagebox.showerror("Research Error", error_msg))
        
        finally:
            self.is_processing = False
            self.root.after(0, self.hide_loading)
            self.root.after(0, self.update_button_states)
    
    def fetch_and_display_progress(self, thread_id, agents_client, last_message_id):
        """Fetch and display intermediate progress"""
        try:
            response = agents_client.messages.get_last_message_by_role(
                thread_id=thread_id,
                role=MessageRole.AGENT,
            )
            
            if not response or response.id == last_message_id:
                return last_message_id
            
            # Check if this is a reasoning message
            if any(t.text.value.startswith("cot_summary:") for t in response.text_messages):
                reasoning_text = "\n".join(
                    t.text.value.replace("cot_summary:", "💭 Reasoning: ") 
                    for t in response.text_messages
                )
                self.update_reasoning(f"{reasoning_text}\n\n")
                
                # Also display citations if available
                if response.url_citation_annotations:
                    citations_text = "🔗 Sources found:\n"
                    for ann in response.url_citation_annotations[:3]:  # Show first 3
                        title = ann.url_citation.title or ann.url_citation.url
                        citations_text += f"  • [{title}]({ann.url_citation.url})\n"
                    self.update_reasoning(f"{citations_text}\n")
            
            return response.id
            
        except Exception as e:
            self.update_reasoning(f"⚠️ Progress update error: {str(e)}\n")
            return last_message_id
    
    def display_final_results_with_images(self, message):
        """Display the final research results as HTML with image generation"""
        if not message:
            self.update_report("<p>No final results received.</p>")
            return
        
        # Prepare the research report HTML
        report_content = ""
        
        # Add main content
        text_summary = "\n\n".join([t.text.value.strip() for t in message.text_messages])
        
        # Convert citations to superscript format
        text_summary = self.convert_citations_to_superscript(text_summary)
        
        # Process image generation placeholders
        text_summary = self.process_image_placeholders(text_summary)
        
        # If the content doesn't already have HTML structure, wrap in paragraphs
        if not any(tag in text_summary for tag in ['<h1>', '<h2>', '<h3>', '<p>', '<div>']):
            # Split into paragraphs and wrap
            paragraphs = text_summary.split('\n\n')
            html_paragraphs = []
            for para in paragraphs:
                if para.strip():
                    # Check if it's a header-like line
                    if para.strip().endswith(':') and len(para.strip()) < 100:
                        html_paragraphs.append(f"<h3>{para.strip()}</h3>")
                    else:
                        html_paragraphs.append(f"<p>{para.strip()}</p>")
            text_summary = '\n'.join(html_paragraphs)
        
        report_content += text_summary
        
        # Add citations section
        if message.url_citation_annotations:
            report_content += "\n\n<h2>📚 Citations</h2>\n<ul>\n"
            seen_urls = set()
            citation_dict = {}
            
            for ann in message.url_citation_annotations:
                url = ann.url_citation.url
                title = ann.url_citation.title or url
                
                if url not in seen_urls:
                    # Extract citation number
                    citation_number = None
                    if ann.text and ":" in ann.text:
                        match = re.search(r'【\d+:(\d+)', ann.text)
                        if match:
                            citation_number = int(match.group(1))
                    
                    if citation_number is not None:
                        citation_dict[citation_number] = f'<a href="{url}">{title}</a>'
                    else:
                        citation_dict[len(citation_dict) + 1] = f'<a href="{url}">{title}</a>'
                    
                    seen_urls.add(url)
            
            # Add numbered citations
            for num in sorted(citation_dict.keys()):
                report_content += f"<li>{num}. {citation_dict[num]}</li>\n"
            
            report_content += "</ul>\n"
        
        # Update the report display
        self.update_report(report_content)
    
    def process_image_placeholders(self, html_content):
        """Process image generation placeholders and replace with actual generated images"""
        # Find all image generation placeholders
        placeholder_pattern = r'<img src="GENERATE_IMAGE:([^"]+)" alt="([^"]*)"[^>]*>'
        
        def generate_and_replace(match):
            prompt = match.group(1)
            alt_text = match.group(2)
            
            try:
                if self.image_generator:
                    self.update_reasoning(f"🎨 Generating image: {prompt[:50]}...\n")
                    filename = self.image_generator.generate_image(prompt)
                    self.update_reasoning(f"✅ Image generated: {filename}\n")
                    return f'<img src="./images/{filename}" alt="{alt_text}" style="max-width: 100%; height: auto;">'
                else:
                    self.update_reasoning(f"⚠️ Image generation not available: {alt_text}\n")
                    return f'<p><strong>Image placeholder:</strong> {alt_text}</p>'
            except Exception as e:
                self.update_reasoning(f"❌ Failed to generate image: {str(e)}\n")
                return f'<p><strong>Image generation failed:</strong> {alt_text}</p>'
        
        # Replace all placeholders
        return re.sub(placeholder_pattern, generate_and_replace, html_content)
    
    def convert_citations_to_superscript(self, html_content):
        """Convert citation markers to HTML superscript format"""
        pattern = r'【\d+:(\d+)†source】'
        
        def replacement(match):
            citation_number = match.group(1)
            return f'<sup>{citation_number}</sup>'
        
        return re.sub(pattern, replacement, html_content)
    
    def update_reasoning(self, text):
        """Update the reasoning panel (thread-safe)"""
        def _update():
            self.reasoning_text.configure(state='normal')
            self.reasoning_text.insert(tk.END, text)
            self.reasoning_text.configure(state='disabled')
            self.reasoning_text.see(tk.END)
        
        self.root.after(0, _update)
    
    def update_report(self, html_text):
        """Update the research report panel with HTML rendering (thread-safe)"""
        def _update():
            self.report_text.set_html(html_text)
        
        self.root.after(0, _update)
    
    def show_loading(self):
        """Show loading spinner overlay"""
        self.loading_overlay.place(relx=0.5, rely=0.5, anchor='center', 
                                  relwidth=0.8, relheight=0.4)
    
    def hide_loading(self):
        """Hide loading spinner overlay"""
        self.loading_overlay.place_forget()
    
    def update_button_states(self):
        """Update button states based on processing status"""
        if self.is_processing:
            self.submit_button.configure(state='disabled')
            self.stop_button.configure(state='normal')
        else:
            self.submit_button.configure(state='normal')
            self.stop_button.configure(state='disabled')
    
    def stop_research(self):
        """Stop the current research process"""
        self.is_processing = False
        self.update_reasoning("\n🛑 Stopping research...\n")
    
    def clear_all(self):
        """Clear all content areas"""
        # Clear reasoning panel
        self.reasoning_text.configure(state='normal')
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.configure(state='disabled')
        
        # Clear report panel
        self.report_text.set_html("<p>Research report will appear here...</p>")
        
        # Reset input to default text
        self.input_text.delete(1.0, tk.END)
    
    def clear_outputs(self):
        """Clear only the output areas"""
        # Clear reasoning panel
        self.reasoning_text.configure(state='normal')
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.configure(state='disabled')
        
        # Clear report panel
        self.report_text.set_html("<p>Research report will appear here...</p>")
    
    def copy_report(self):
        """Copy the research report to clipboard"""
        # Get the HTML content from the HTMLScrolledText widget
        try:
            # HTMLScrolledText may not have a direct method to get HTML, so we'll get the text content
            # This is a limitation - we'll copy the visible text content
            html_content = self.report_text.get("1.0", tk.END).strip()
            if html_content and html_content != "Research report will appear here...":
                self.root.clipboard_clear()
                self.root.clipboard_append(html_content)
                messagebox.showinfo("Copied", "Research report copied to clipboard!")
            else:
                messagebox.showwarning("No Content", "No research report to copy.")
        except Exception as e:
            # Fallback: copy a placeholder message
            messagebox.showwarning("Copy Error", f"Could not copy report: {str(e)}")
    
    def cleanup(self):
        """Clean up Azure clients and connections"""
        try:
            if self.agent and self.agents_client:
                self.agents_client.delete_agent(self.agent.id)
                self.agent = None
            
            if self.agents_client:
                self.agents_client.__exit__(None, None, None)
                self.agents_client = None
                
            if self.project_client_connection:
                self.project_client_connection.__exit__(None, None, None)
                self.project_client_connection = None
                
        except Exception as e:
            print(f"Cleanup error: {e}")  # Log but don't show to user


def main():
    """Main entry point for the application"""
    # Check for required environment variables
    required_vars = [
        "PROJECT_ENDPOINT",
        "AZURE_SUBSCRIPTION_ID", 
        "AZURE_RESOURCE_GROUP_NAME",
        "AZURE_PROJECT_NAME",
        "BING_RESOURCE_NAME",
        "DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME",
        "AGENT_MODEL_DEPLOYMENT_NAME",
        "IMAGE_PROJECT_ENDPOINT",
        "IMAGE_MODEL"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        return
    
    # Create and run the application
    root = tk.Tk()
    
    # Set window icon (if available)
    try:
        root.iconbitmap(default='research.ico')  # Optional: add an icon file
    except:
        pass  # Ignore if icon file not found
    
    app = DeepResearchAgentUI(root)
    
    # Handle window close event
    def on_closing():
        if app.is_processing:
            if messagebox.askokcancel("Quit", "Research is in progress. Stop and quit?"):
                app.stop_research()
                time.sleep(1)  # Give time for cleanup
                app.cleanup()
                root.destroy()
        else:
            app.cleanup()
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI event loop
    root.mainloop()


if __name__ == "__main__":
    main()
