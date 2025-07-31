import os
import time
import re
import threading
import base64
import uuid
import json
from datetime import datetime
from typing import Optional
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import font
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
        # Create a function that returns tokens for the Azure AD token provider
        def get_azure_ad_token():
            token = DefaultAzureCredential().get_token("https://cognitiveservices.azure.com/.default")
            return token.token
        
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

            model = os.environ["IMAGE_MODEL"]

            print(f"Generating image using {model} with prompt: {prompt}")
            
            # Generate image using Azure OpenAI
            response = self.client.images.generate(
                model=model,
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
                response_format="b64_json"
            )
            
            # Save the image
            if response.data and len(response.data) > 0 and response.data[0].b64_json:
                image_data = base64.b64decode(response.data[0].b64_json)
                with open(filepath, "wb") as f:
                    f.write(image_data)
                
                return filename
            else:
                raise Exception("No image data returned from API")
            
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


class HTMLRenderer:
    """HTML renderer for tkinter Text widgets"""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.setup_tags()
    
    def setup_tags(self):
        """Configure text tags for different HTML elements"""
        # Get default font
        default_font = font.nametofont("TkDefaultFont")
        default_size = default_font.cget("size")
        default_family = default_font.cget("family")
        
        # Headers
        self.text_widget.tag_config("h1", font=(default_family, 18, "bold"), spacing3=10)
        self.text_widget.tag_config("h2", font=(default_family, 16, "bold"), spacing3=8)
        self.text_widget.tag_config("h3", font=(default_family, 14, "bold"), spacing3=6)
        
        # Text formatting
        self.text_widget.tag_config("bold", font=(default_family, default_size, "bold"))
        self.text_widget.tag_config("italic", font=(default_family, default_size, "italic"))
        self.text_widget.tag_config("code", font=("Courier", default_size), background="#f0f0f0")
        
        # Links
        self.text_widget.tag_config("link", foreground="blue", underline=True)
        self.text_widget.tag_bind("link", "<Button-1>", self.open_link)
        self.text_widget.tag_bind("link", "<Enter>", lambda e: self.text_widget.config(cursor="hand2"))
        self.text_widget.tag_bind("link", "<Leave>", lambda e: self.text_widget.config(cursor=""))
        
        # Citations (superscript)
        self.text_widget.tag_config("citation", font=(default_family, int(default_size * 0.8)), offset=4)
        
        # Lists
        self.text_widget.tag_config("list_item", lmargin1=20, lmargin2=20)
        
        # Images (placeholder text)
        self.text_widget.tag_config("image", background="#e8f4f8", relief="solid", borderwidth=1)
    
    def open_link(self, event):
        """Handle link clicks"""
        import webbrowser
        # Get the URL from the tag
        tags = self.text_widget.tag_names(tk.CURRENT)
        for tag in tags:
            if tag.startswith("url:"):
                url = tag[4:]  # Remove "url:" prefix
                webbrowser.open(url)
                break
    
    def render_html(self, html_text):
        """Render HTML text to the text widget"""
        self.text_widget.delete(1.0, tk.END)
        
        # Simple HTML parsing
        lines = html_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Headers
            if line.startswith('<h3>') and line.endswith('</h3>'):
                content = line[4:-5]
                self.insert_with_tag(content + '\n', "h3")
            elif line.startswith('<h2>') and line.endswith('</h2>'):
                content = line[4:-5]
                self.insert_with_tag(content + '\n', "h2")
            elif line.startswith('<h1>') and line.endswith('</h1>'):
                content = line[4:-5]
                self.insert_with_tag(content + '\n', "h1")
            
            # Images
            elif '<img' in line:
                # Extract image info
                img_match = re.search(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*>', line)
                if img_match:
                    src, alt = img_match.groups()
                    image_text = f"🖼️ Image: {alt}\n   File: {src}\n"
                    self.insert_with_tag(image_text, "image")
                else:
                    # Simpler image tag
                    img_match = re.search(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*>', line)
                    if img_match:
                        src = img_match.group(1)
                        image_text = f"🖼️ Image: {src}\n"
                        self.insert_with_tag(image_text, "image")
            
            # List items
            elif line.startswith('<li>') and line.endswith('</li>'):
                content = line[4:-5]
                self.process_formatted_line("• " + content + '\n', "list_item")
            elif line.startswith('- ') or re.match(r'^\d+\.\s', line):
                self.process_formatted_line(line + '\n', "list_item")
            
            # Paragraphs
            elif line.startswith('<p>') and line.endswith('</p>'):
                content = line[3:-4]
                self.process_formatted_line(content + '\n')
            
            # Regular paragraphs (with inline formatting)
            elif line.strip() and not any(line.startswith(tag) for tag in ['<h', '<ul', '<ol', '</ul', '</ol', '<div', '</div']):
                self.process_formatted_line(line + '\n')
            
            # Empty lines and ignored tags
            elif not line.strip() or line in ['<ul>', '</ul>', '<ol>', '</ol>', '<div>', '</div>']:
                if not line.strip():
                    self.text_widget.insert(tk.END, '\n')
    
    def process_formatted_line(self, line, base_tag=None):
        """Process a line with inline formatting"""
        # Handle citations (superscript HTML tags)
        line = re.sub(r'<sup>(\d+)</sup>', r'[\1]', line)
        
        # Handle links in HTML format <a href="url">text</a>
        def replace_html_link(match):
            url, text = match.groups()
            start_pos = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, text)
            end_pos = self.text_widget.index(tk.END)
            self.text_widget.tag_add("link", start_pos, end_pos)
            self.text_widget.tag_add(f"url:{url}", start_pos, end_pos)
            return ""
        
        # Handle markdown-style links [text](url)
        def replace_md_link(match):
            text, url = match.groups()
            start_pos = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, text)
            end_pos = self.text_widget.index(tk.END)
            self.text_widget.tag_add("link", start_pos, end_pos)
            self.text_widget.tag_add(f"url:{url}", start_pos, end_pos)
            return ""
        
        # Process HTML links
        html_link_pattern = r'<a href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>'
        md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        current_pos = 0
        
        # Process HTML links first
        for match in re.finditer(html_link_pattern, line):
            # Add text before the link
            before_text = line[current_pos:match.start()]
            if before_text:
                self.insert_with_formatting(before_text, base_tag)
            
            # Add the link
            url, text = match.groups()
            start_pos = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, text)
            end_pos = self.text_widget.index(tk.END)
            self.text_widget.tag_add("link", start_pos, end_pos)
            self.text_widget.tag_add(f"url:{url}", start_pos, end_pos)
            if base_tag:
                self.text_widget.tag_add(base_tag, start_pos, end_pos)
            
            current_pos = match.end()
        
        # Process remaining text for markdown links
        remaining_text = line[current_pos:]
        current_pos = 0
        
        for match in re.finditer(md_link_pattern, remaining_text):
            # Add text before the link
            before_text = remaining_text[current_pos:match.start()]
            if before_text:
                self.insert_with_formatting(before_text, base_tag)
            
            # Add the link
            text, url = match.groups()
            start_pos = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, text)
            end_pos = self.text_widget.index(tk.END)
            self.text_widget.tag_add("link", start_pos, end_pos)
            self.text_widget.tag_add(f"url:{url}", start_pos, end_pos)
            if base_tag:
                self.text_widget.tag_add(base_tag, start_pos, end_pos)
            
            current_pos = match.end()
        
        # Add final remaining text
        final_text = remaining_text[current_pos:]
        if final_text:
            self.insert_with_formatting(final_text, base_tag)
    
    def insert_with_formatting(self, text, base_tag=None):
        """Insert text with bold/italic formatting"""
        # Handle HTML bold <b></b> and <strong></strong>
        bold_html_pattern = r'<(b|strong)>(.*?)</(b|strong)>'
        # Handle HTML italic <i></i> and <em></em>
        italic_html_pattern = r'<(i|em)>(.*?)</(i|em)>'
        # Handle markdown bold **text**
        bold_md_pattern = r'\*\*(.*?)\*\*'
        # Handle markdown italic *text*
        italic_md_pattern = r'\*(.*?)\*'
        
        current_pos = 0
        
        # Process all formatting patterns
        all_patterns = [
            (bold_html_pattern, "bold"),
            (italic_html_pattern, "italic"),
            (bold_md_pattern, "bold"),
            (italic_md_pattern, "italic")
        ]
        
        # Find all matches
        matches = []
        for pattern, tag in all_patterns:
            for match in re.finditer(pattern, text):
                content = match.group(2) if tag in ["bold", "italic"] and match.groups() else match.group(1)
                matches.append((match.start(), match.end(), content, tag))
        
        # Sort matches by position
        matches.sort(key=lambda x: x[0])
        
        # Process matches
        for start, end, content, tag in matches:
            # Add text before formatting
            before_text = text[current_pos:start]
            if before_text:
                self.insert_with_tag(before_text, base_tag)
            
            # Add formatted text
            start_pos = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, content)
            end_pos = self.text_widget.index(tk.END)
            self.text_widget.tag_add(tag, start_pos, end_pos)
            if base_tag:
                self.text_widget.tag_add(base_tag, start_pos, end_pos)
            
            current_pos = end
        
        # Add remaining text
        remaining_text = text[current_pos:]
        if remaining_text:
            self.insert_with_tag(remaining_text, base_tag)
    
    def insert_with_tag(self, text, tag=None):
        """Insert text with optional tag"""
        start_pos = self.text_widget.index(tk.END)
        self.text_widget.insert(tk.END, text)
        if tag:
            end_pos = self.text_widget.index(tk.END)
            self.text_widget.tag_add(tag, start_pos, end_pos)


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
        default_text = ("I have rented a new storefront at 340 Jefferson St. in Fisherman's Wharf in San Francisco to open a new outpost of my restaurant chain, Scheibmeir's Steaks, Snacks and Sticks. Please help me design a strategy and theme to operate the new restaurant, including but not limited to the cuisine and menu to offer, staff recruitment requirements including salary, and marketing and promotional strategies. Provide one best option rather than multiple choices. Based on the option help me also generate a FAQ document for the customer to understand the details of the restaurant.")
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
        
        # Report text area
        self.report_text = scrolledtext.ScrolledText(
            self.report_frame, font=('Segoe UI', 11), wrap=tk.WORD,
            relief='flat', padx=15, pady=15, state='disabled'
        )
        self.report_text.pack(fill='both', expand=True)
        
        # Initialize HTML renderer for report
        self.report_renderer = HTMLRenderer(self.report_text)
        
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
            with self.project_client:
                with self.project_client.agents as agents_client:
                    self.agents_client = agents_client
                    
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
                    
                    self.agent = agents_client.create_agent(
                        model=os.environ["AGENT_MODEL_DEPLOYMENT_NAME"],
                        name="deep-research-agent-with-images",
                        instructions=agent_instructions,
                        tools=tools,
                    )
                    
                    # Create thread
                    self.update_reasoning("📝 Creating conversation thread...\n")
                    self.thread = agents_client.threads.create()
                    
                    # Create message
                    self.update_reasoning("💬 Sending research request...\n")
                    message = agents_client.messages.create(
                        thread_id=self.thread.id,
                        role="user",
                        content=user_input,
                    )
                    
                    # Start run
                    self.update_reasoning("🔍 Starting research process...\n\n")
                    run = agents_client.runs.create(
                        thread_id=self.thread.id, 
                        agent_id=self.agent.id
                    )
                    
                    self.current_run = run
                    last_message_id = None
                    
                    # Poll for progress
                    while run.status in ("queued", "in_progress") and self.is_processing:
                        time.sleep(2)
                        run = agents_client.runs.get(thread_id=self.thread.id, run_id=run.id)
                        
                        # Fetch and display intermediate responses
                        last_message_id = self.fetch_and_display_progress(
                            self.thread.id, agents_client, last_message_id
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
                    final_message = agents_client.messages.get_last_message_by_role(
                        thread_id=self.thread.id, role=MessageRole.AGENT
                    )
                    
                    if final_message:
                        self.display_final_results_with_images(final_message)
                    
                    # Cleanup
                    if self.agent:
                        agents_client.delete_agent(self.agent.id)
                        self.update_reasoning("🧹 Cleanup completed.\n")
                    
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
            self.report_text.configure(state='normal')
            self.report_renderer.render_html(html_text)
            self.report_text.configure(state='disabled')
        
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
        self.report_text.configure(state='normal')
        self.report_text.delete(1.0, tk.END)
        self.report_text.configure(state='disabled')
        
        # Reset input to default text
        default_text = ("I have rented a new storefront at 340 Jefferson St. in Fisherman's Wharf in San Francisco to open a new outpost of my restaurant chain, Scheibmeir's Steaks, Snacks and Sticks. Please help me design a strategy and theme to operate the new restaurant, including but not limited to the cuisine and menu to offer, staff recruitment requirements including salary, and marketing and promotional strategies. Provide one best option rather than multiple choices. Based on the option help me also generate a FAQ document for the customer to understand the details of the restaurant.")
        self.input_text.delete(1.0, tk.END)
        self.input_text.insert(1.0, default_text)
    
    def clear_outputs(self):
        """Clear only the output areas"""
        # Clear reasoning panel
        self.reasoning_text.configure(state='normal')
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.configure(state='disabled')
        
        # Clear report panel
        self.report_text.configure(state='normal')
        self.report_text.delete(1.0, tk.END)
        self.report_text.configure(state='disabled')
    
    def copy_report(self):
        """Copy the research report to clipboard"""
        report_content = self.report_text.get(1.0, tk.END).strip()
        if report_content:
            self.root.clipboard_clear()
            self.root.clipboard_append(report_content)
            messagebox.showinfo("Copied", "Research report copied to clipboard!")
        else:
            messagebox.showwarning("No Content", "No research report to copy.")


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
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI event loop
    root.mainloop()


if __name__ == "__main__":
    main()
