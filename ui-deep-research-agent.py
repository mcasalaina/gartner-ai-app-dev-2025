import os
import time
import re
import threading
from typing import Optional
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import DeepResearchTool, MessageRole, ThreadMessage
from tkinter import font
from datetime import datetime

# Load environment variables from .env file if they're not already set
load_dotenv()


class MarkdownRenderer:
    """Simple Markdown renderer for tkinter Text widgets"""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.setup_tags()
    
    def setup_tags(self):
        """Configure text tags for different markdown elements"""
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
    
    def render_markdown(self, markdown_text):
        """Render markdown text to the text widget"""
        self.text_widget.delete(1.0, tk.END)
        
        lines = markdown_text.split('\n')
        current_pos = 1.0
        
        for line in lines:
            line = line.rstrip()
            
            # Headers
            if line.startswith('### '):
                self.insert_with_tag(line[4:] + '\n', "h3")
            elif line.startswith('## '):
                self.insert_with_tag(line[3:] + '\n', "h2")
            elif line.startswith('# '):
                self.insert_with_tag(line[2:] + '\n', "h1")
            
            # List items
            elif line.startswith('- ') or re.match(r'^\d+\.\s', line):
                self.process_formatted_line(line + '\n', "list_item")
            
            # Regular paragraphs
            elif line.strip():
                self.process_formatted_line(line + '\n')
            
            # Empty lines
            else:
                self.text_widget.insert(tk.END, '\n')
    
    def process_formatted_line(self, line, base_tag=None):
        """Process a line with inline formatting"""
        # Handle citations (superscript HTML tags)
        line = re.sub(r'<sup>(\d+)</sup>', r'[\1]', line)
        
        # Handle links in markdown format [text](url)
        def replace_link(match):
            text, url = match.groups()
            start_pos = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, text)
            end_pos = self.text_widget.index(tk.END)
            self.text_widget.tag_add("link", start_pos, end_pos)
            self.text_widget.tag_add(f"url:{url}", start_pos, end_pos)
            return ""
        
        # Process links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        current_pos = 0
        for match in re.finditer(link_pattern, line):
            # Add text before the link
            before_text = line[current_pos:match.start()]
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
        
        # Add remaining text
        remaining_text = line[current_pos:]
        if remaining_text:
            self.insert_with_formatting(remaining_text, base_tag)
    
    def insert_with_formatting(self, text, base_tag=None):
        """Insert text with bold/italic formatting"""
        # Handle bold **text**
        bold_pattern = r'\*\*(.*?)\*\*'
        current_pos = 0
        
        for match in re.finditer(bold_pattern, text):
            # Add text before bold
            before_text = text[current_pos:match.start()]
            if before_text:
                self.insert_with_tag(before_text, base_tag)
            
            # Add bold text
            bold_text = match.group(1)
            start_pos = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, bold_text)
            end_pos = self.text_widget.index(tk.END)
            self.text_widget.tag_add("bold", start_pos, end_pos)
            if base_tag:
                self.text_widget.tag_add(base_tag, start_pos, end_pos)
            
            current_pos = match.end()
        
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
    """Graphical User Interface for the Deep Research Agent"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🔬 Deep Research Agent")
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
        title_label = tk.Label(main_frame, text="🔬 Deep Research Agent", 
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
        
        # Initialize markdown renderer for reasoning
        self.reasoning_renderer = MarkdownRenderer(self.reasoning_text)
    
    def create_research_report_section(self, parent):
        """Create the research report section"""
        # Research Report label
        report_label = tk.Label(parent, text="📄 Research Report:", 
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
        
        # Initialize markdown renderer for report
        self.report_renderer = MarkdownRenderer(self.report_text)
        
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
        
        # Right side buttons
        # Copy button for research report
        self.copy_button = ttk.Button(button_frame, text="📋 Copy Report", 
                                     style='Clear.TButton',
                                     command=self.copy_report)
        self.copy_button.pack(side='right', padx=(15, 0))
        
        # PDF Export button
        self.pdf_button = ttk.Button(button_frame, text="📄 Export to PDF", 
                                    style='Clear.TButton',
                                    command=self.export_to_pdf)
        self.pdf_button.pack(side='right')
    
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
                    
                    # Create agent
                    self.update_reasoning("🤖 Creating research agent...\n")
                    self.agent = agents_client.create_agent(
                        model=os.environ["AGENT_MODEL_DEPLOYMENT_NAME"],
                        name="deep-research-agent-ui",
                        instructions="You are a helpful agent that assists in doing comprehensive research.",
                        tools=self.deep_research_tool.definitions,
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
                    self.update_reasoning("\n✅ Research completed! Generating final report...\n")
                    final_message = agents_client.messages.get_last_message_by_role(
                        thread_id=self.thread.id, role=MessageRole.AGENT
                    )
                    
                    if final_message:
                        self.display_final_results(final_message)
                    
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
    
    def display_final_results(self, message):
        """Display the final research results"""
        if not message:
            self.update_report("No final results received.")
            return
        
        # Prepare the research report
        report_content = ""
        
        # Add main content
        text_summary = "\n\n".join([t.text.value.strip() for t in message.text_messages])
        # Convert citations to superscript format
        text_summary = self.convert_citations_to_superscript(text_summary)
        report_content += text_summary
        
        # Add citations section
        if message.url_citation_annotations:
            report_content += "\n\n## 📚 Citations\n\n"
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
                        citation_dict[citation_number] = f"[{title}]({url})"
                    else:
                        citation_dict[len(citation_dict) + 1] = f"[{title}]({url})"
                    
                    seen_urls.add(url)
            
            # Add numbered citations
            for num in sorted(citation_dict.keys()):
                report_content += f"{num}. {citation_dict[num]}\n\n"
        
        # Update the report display
        self.update_report(report_content)
    
    def convert_citations_to_superscript(self, markdown_content):
        """Convert citation markers to HTML superscript format"""
        pattern = r'【\d+:(\d+)†source】'
        
        def replacement(match):
            citation_number = match.group(1)
            return f'<sup>{citation_number}</sup>'
        
        return re.sub(pattern, replacement, markdown_content)
    
    def update_reasoning(self, text):
        """Update the reasoning panel (thread-safe)"""
        def _update():
            self.reasoning_text.configure(state='normal')
            self.reasoning_text.insert(tk.END, text)
            self.reasoning_text.configure(state='disabled')
            self.reasoning_text.see(tk.END)
        
        self.root.after(0, _update)
    
    def update_report(self, markdown_text):
        """Update the research report panel (thread-safe)"""
        def _update():
            self.report_text.configure(state='normal')
            self.report_renderer.render_markdown(markdown_text)
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
    
    def export_to_pdf(self):
        """Export the research report to PDF"""
        report_content = self.report_text.get(1.0, tk.END).strip()
        if not report_content:
            messagebox.showwarning("No Content", "No research report to export.")
            return
        
        try:
            # Import PDF libraries here to avoid import errors if not installed
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
            from reportlab.lib import colors
            from reportlab.lib.colors import HexColor
            
            # Ask user for save location
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"research_report_{timestamp}.pdf"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=default_filename,
                title="Export Research Report to PDF"
            )
            
            if not file_path:
                return  # User cancelled
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=letter,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=HexColor('#2c3e50')
            )
            
            heading1_style = ParagraphStyle(
                'CustomHeading1',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20,
                textColor=HexColor('#34495e')
            )
            
            heading2_style = ParagraphStyle(
                'CustomHeading2', 
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=10,
                spaceBefore=16,
                textColor=HexColor('#34495e')
            )
            
            heading3_style = ParagraphStyle(
                'CustomHeading3',
                parent=styles['Heading3'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=12,
                textColor=HexColor('#34495e')
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=6,
                alignment=TA_JUSTIFY,
                leftIndent=0,
                rightIndent=0
            )
            
            citation_style = ParagraphStyle(
                'Citations',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=4,
                leftIndent=20
            )
            
            # Build story (content) for PDF
            story = []
            
            # Add title
            story.append(Paragraph("🔬 Deep Research Report", title_style))
            story.append(Spacer(1, 20))
            
            # Add timestamp
            timestamp_text = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
            story.append(Paragraph(timestamp_text, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Process the report content
            lines = report_content.split('\n')
            current_paragraph = ""
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    # Empty line - finish current paragraph if any
                    if current_paragraph.strip():
                        # Clean up markdown formatting for PDF
                        cleaned_text = self.clean_markdown_for_pdf(current_paragraph)
                        story.append(Paragraph(cleaned_text, body_style))
                        story.append(Spacer(1, 6))
                        current_paragraph = ""
                    continue
                
                # Headers
                if line.startswith('### '):
                    if current_paragraph.strip():
                        cleaned_text = self.clean_markdown_for_pdf(current_paragraph)
                        story.append(Paragraph(cleaned_text, body_style))
                        current_paragraph = ""
                    story.append(Spacer(1, 12))
                    story.append(Paragraph(line[4:], heading3_style))
                    
                elif line.startswith('## '):
                    if current_paragraph.strip():
                        cleaned_text = self.clean_markdown_for_pdf(current_paragraph)
                        story.append(Paragraph(cleaned_text, body_style))
                        current_paragraph = ""
                    story.append(Spacer(1, 16))
                    story.append(Paragraph(line[3:], heading2_style))
                    
                elif line.startswith('# '):
                    if current_paragraph.strip():
                        cleaned_text = self.clean_markdown_for_pdf(current_paragraph)
                        story.append(Paragraph(cleaned_text, body_style))
                        current_paragraph = ""
                    story.append(Spacer(1, 20))
                    story.append(Paragraph(line[2:], heading1_style))
                
                # List items
                elif line.startswith('- ') or re.match(r'^\d+\.\s', line):
                    if current_paragraph.strip():
                        cleaned_text = self.clean_markdown_for_pdf(current_paragraph)
                        story.append(Paragraph(cleaned_text, body_style))
                        current_paragraph = ""
                    
                    # Handle list items
                    cleaned_line = self.clean_markdown_for_pdf(line)
                    story.append(Paragraph(cleaned_line, citation_style))
                
                # Citation numbers (standalone)
                elif re.match(r'^\d+\.\s.*', line) and '(' in line and ')' in line:
                    if current_paragraph.strip():
                        cleaned_text = self.clean_markdown_for_pdf(current_paragraph)
                        story.append(Paragraph(cleaned_text, body_style))
                        current_paragraph = ""
                    
                    cleaned_line = self.clean_markdown_for_pdf(line)
                    story.append(Paragraph(cleaned_line, citation_style))
                
                # Regular content
                else:
                    current_paragraph += line + " "
            
            # Handle any remaining paragraph
            if current_paragraph.strip():
                cleaned_text = self.clean_markdown_for_pdf(current_paragraph)
                story.append(Paragraph(cleaned_text, body_style))
            
            # Build PDF
            doc.build(story)
            
            messagebox.showinfo("Export Successful", f"Research report exported to:\n{file_path}")
            
        except ImportError:
            messagebox.showerror("Missing Dependency", 
                               "The reportlab library is required for PDF export.\n"
                               "Please install it using: pip install reportlab")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF:\n{str(e)}")
    
    def clean_markdown_for_pdf(self, text):
        """Clean markdown formatting for PDF rendering"""
        # Convert markdown links [text](url) to just text with URL in parentheses
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', text)
        
        # Convert bold **text** to <b>text</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Convert italic *text* to <i>text</i>
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Convert citations [n] to superscript
        text = re.sub(r'\[(\d+)\]', r'<sup>\1</sup>', text)
        
        # Remove HTML superscript tags and convert to plain text
        text = re.sub(r'<sup>(\d+)</sup>', r'[\1]', text)
        
        return text


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
        "AGENT_MODEL_DEPLOYMENT_NAME"
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
