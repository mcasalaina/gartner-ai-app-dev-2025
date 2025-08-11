#!/usr/bin/env python3
"""
Avatar Server - Serves a pre-configured avatar_menu_chat.html with environment variables
"""

import os
import socket
import sys
import webbrowser
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AvatarRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/avatar_menu_chat.html' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Read the original avatar_menu_chat.html
            with open('avatar_menu_chat.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Read the system message content
            system_message = ""
            try:
                with open('voice_avatar_system_message.txt', 'r', encoding='utf-8') as f:
                    system_message = f.read().strip()
            except FileNotFoundError:
                system_message = "You are an AI assistant that helps people find information."
            
            # Get environment variables
            region = os.getenv('RESTAURANT_EVALUATION_MODEL_REGION', 'eastus2')
            api_key = os.getenv('RESTAURANT_API_KEY', '')
            openai_endpoint = os.getenv('RESTAURANT_EVALUATION_MODEL_ENDPOINT', '')
            openai_api_key = os.getenv('RESTAURANT_API_KEY', '')
            deployment_name = os.getenv('RESTAURANT_EVALUATION_MODEL', 'gpt-4')
            
            # JavaScript to auto-fill the form
            # Escape the system message for JavaScript
            escaped_system_message = system_message.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
            
            auto_fill_script = f"""
<script>
window.addEventListener('DOMContentLoaded', function() {{
    // Auto-fill form fields with environment variables
    const fields = [
        {{ id: 'region', value: '{region}' }},
        {{ id: 'APIKey', value: '{api_key}' }},
        {{ id: 'azureOpenAIEndpoint', value: '{openai_endpoint}' }},
        {{ id: 'azureOpenAIApiKey', value: '{openai_api_key}' }},
        {{ id: 'azureOpenAIDeploymentName', value: '{deployment_name}' }},
        {{ id: 'prompt', value: '{escaped_system_message}' }}
    ];
    
    // Fill fields and trigger events for validation
    fields.forEach(field => {{
        const element = document.getElementById(field.id);
        if (element) {{
            element.value = field.value;
            // Trigger input and change events to ensure validation
            element.dispatchEvent(new Event('input', {{ bubbles: true }}));
            element.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}
    }});
    
    // Enable continuous conversation by default
    const continuousConversationCheckbox = document.getElementById('continuousConversation');
    if (continuousConversationCheckbox) {{
        continuousConversationCheckbox.checked = true;
        continuousConversationCheckbox.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }}
    
    console.log('Form fields auto-filled. Ready to start session manually.');
}});
</script>
"""
            
            # Insert the script before the closing body tag
            html_content = html_content.replace('</body>', auto_fill_script + '\n</body>')
            
            self.wfile.write(html_content.encode('utf-8'))
        else:
            # Serve static files (CSS, JS, images, menu directory, etc.) normally
            super().do_GET()

def find_free_port():
    """Find a free port to use for the server"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def open_browser(url):
    """Open the browser to the specified URL after a short delay"""
    def delayed_open():
        time.sleep(2)  # Wait for server to fully start
        print(f"Opening browser to {url}")
        webbrowser.open(url)
    
    threading.Thread(target=delayed_open, daemon=True).start()

def main():
    # Change to the directory containing the HTML files
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Find a free port
    port = find_free_port()
    
    # Create and start the server
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, AvatarRequestHandler)
    
    # Construct the URL
    url = f"http://localhost:{port}/avatar_menu_chat.html"
    
    print(f"Avatar Server starting...")
    print(f"Serving on http://localhost:{port}")
    print(f"Opening {url} in your browser")
    print("The form fields will be auto-filled with environment variables")
    print("Click 'Start Session' to begin the avatar chat")
    print("Press Ctrl+C to stop the server")
    
    # Start browser opening in background thread
    open_browser(url)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down server...")
        httpd.shutdown()
        httpd.server_close()
        print("Server stopped.")
        os._exit(0)

if __name__ == '__main__':
    main()
