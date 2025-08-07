import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import openai
from foundry_local import FoundryLocalManager
import os
from PIL import Image, ImageTk

class RestaurantAssistantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Scheibmeir's Restaurant Assistant")
        self.root.state('zoomed')  # Start maximized on Windows
        self.root.configure(bg='#F4E8D5')  # Warmer cream background
        self.root.minsize(700, 600)
        
        # Initialize the AI components
        self.setup_ai()
        
        # Load restaurant information
        self.load_restaurant_info()
        
        # Load logo
        self.load_logo()
        
        # Setup the UI
        self.setup_ui()
    
    def setup_ai(self):
        """Initialize the Foundry Local manager and OpenAI client"""
        try:
            self.alias = "Phi-4-mini-instruct-cuda-gpu"
            self.manager = FoundryLocalManager(self.alias)
            self.client = openai.OpenAI(
                base_url=self.manager.endpoint,
                api_key=self.manager.api_key
            )
        except Exception as e:
            messagebox.showerror("AI Setup Error", f"Failed to initialize AI: {str(e)}")
            self.manager = None
            self.client = None
    
    def load_restaurant_info(self):
        """Load restaurant information from file"""
        try:
            with open('local_assistant_info.md', 'r', encoding='utf-8') as f:
                self.restaurant_info = f.read()
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to load restaurant info: {str(e)}")
            self.restaurant_info = "Restaurant information not available."
    
    def load_logo(self):
        """Load and resize the restaurant logo"""
        try:
            # Load the logo image
            logo_path = "Scheibmeirs Logo.png"
            if os.path.exists(logo_path):
                # Open and resize the image
                pil_image = Image.open(logo_path)
                # Resize to fit nicely in the header (maintain aspect ratio)
                pil_image = pil_image.resize((300, 150), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(pil_image)
            else:
                self.logo_image = None
        except Exception as e:
            print(f"Could not load logo: {e}")
            self.logo_image = None
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#F4E8D5', padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo (if available)
        if self.logo_image:
            logo_label = tk.Label(main_frame, image=self.logo_image, bg='#F4E8D5')
            logo_label.pack(pady=(0, 20))
        else:
            # Fallback title if logo can't be loaded
            title_label = tk.Label(
                main_frame,
                text="🍽️ Scheibmeir's Restaurant Assistant",
                font=('Georgia', 24, 'bold'),
                bg='#F4E8D5',
                fg='#8B1538'  # Rich burgundy from logo
            )
            title_label.pack(pady=(0, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_frame,
            text="Ask me anything about our menu, hours, or restaurant!",
            font=('Georgia', 14),
            bg='#F4E8D5',
            fg='#654321'  # Warm brown
        )
        subtitle_label.pack(pady=(0, 25))
        
        # Question input frame
        input_frame = tk.Frame(main_frame, bg='#F4E8D5')
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Question label
        question_label = tk.Label(
            input_frame,
            text="Your Question:",
            font=('Georgia', 14, 'bold'),
            bg='#F4E8D5',
            fg='#8B1538'
        )
        question_label.pack(anchor='w')
        
        # Question input
        self.question_entry = tk.Text(
            input_frame,
            height=3,
            font=('Georgia', 12),
            bg='white',
            fg='#333333',
            relief=tk.SOLID,
            bd=2,
            padx=15,
            pady=15,
            wrap=tk.WORD,
            selectbackground='#8B1538',
            selectforeground='white'
        )
        self.question_entry.pack(fill=tk.X, pady=(8, 0))
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg='#F4E8D5')
        button_frame.pack(fill=tk.X, pady=15)
        
        # Ask button
        self.ask_button = tk.Button(
            button_frame,
            text="Ask Assistant",
            command=self.ask_question,
            font=('Georgia', 14, 'bold'),
            bg='#8B1538',  # Burgundy from logo
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=25,
            pady=12,
            activebackground='#A0294D',
            activeforeground='white'
        )
        self.ask_button.pack(side=tk.LEFT, padx=(0, 15))
        
        # Clear button
        self.clear_button = tk.Button(
            button_frame,
            text="Clear All",
            command=self.clear_all,
            font=('Georgia', 14),
            bg='#D2691E',  # Warm orange/brown
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=25,
            pady=12,
            activebackground='#E6751F',
            activeforeground='white'
        )
        self.clear_button.pack(side=tk.RIGHT, padx=(15, 0))
        
        # Response frame
        response_frame = tk.Frame(main_frame, bg='#F4E8D5')
        response_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        # Response label
        response_label = tk.Label(
            response_frame,
            text="Assistant Response:",
            font=('Georgia', 14, 'bold'),
            bg='#F4E8D5',
            fg='#8B1538'
        )
        response_label.pack(anchor='w')
        
        # Response text area
        self.response_text = scrolledtext.ScrolledText(
            response_frame,
            font=('Georgia', 12),
            bg='white',
            fg='#333333',
            relief=tk.SOLID,
            bd=2,
            padx=20,
            pady=20,
            wrap=tk.WORD,
            state=tk.DISABLED,
            selectbackground='#8B1538',
            selectforeground='white'
        )
        self.response_text.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Ready to answer your questions!",
            font=('Georgia', 11),
            bg='#F4E8D5',
            fg='#654321'
        )
        self.status_label.pack(pady=(10, 0))
        
        # Bind Enter key to ask question
        self.question_entry.bind('<Control-Return>', lambda e: self.ask_question())
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        
        # Get window size
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        
        # Get screen size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        
        # Set the geometry
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def ask_question(self):
        """Handle the ask question button click"""
        if not self.client:
            messagebox.showerror("Error", "AI client not initialized. Please restart the application.")
            return
        
        question = self.question_entry.get("1.0", tk.END).strip()
        if not question:
            messagebox.showwarning("No Question", "Please enter a question first.")
            return
        
        # Disable the ask button and show loading status
        self.ask_button.config(state=tk.DISABLED, text="Thinking...")
        self.status_label.config(text="Processing your question...")
        
        # Clear previous response
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete("1.0", tk.END)
        self.response_text.config(state=tk.DISABLED)
        
        # Start the AI processing in a separate thread
        thread = threading.Thread(target=self.process_question, args=(question,))
        thread.daemon = True
        thread.start()
    
    def process_question(self, question):
        """Process the question with AI in a separate thread"""
        try:
            # Create the formatted prompt
            prompt = f"""Answer the following question about Scheibmeir's Steaks, Snacks, and Sticks:

{question}

Here is the information to use when answering:

{self.restaurant_info}"""
            
            # Get streaming response
            stream = self.client.chat.completions.create(
                model=self.manager.get_model_info(self.alias).id,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            # Update the response text with streaming content
            self.response_text.config(state=tk.NORMAL)
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    self.response_text.insert(tk.END, content)
                    self.response_text.see(tk.END)
                    self.response_text.update()
            
            self.response_text.config(state=tk.DISABLED)
            
            # Update status
            self.root.after(0, lambda: self.status_label.config(text="Response complete!"))
            
        except Exception as e:
            error_msg = f"Error processing question: {str(e)}"
            self.root.after(0, lambda: self.show_error_response(error_msg))
        
        finally:
            # Re-enable the ask button
            self.root.after(0, lambda: self.ask_button.config(state=tk.NORMAL, text="Ask Assistant"))
    
    def show_error_response(self, error_msg):
        """Show error message in the response area"""
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete("1.0", tk.END)
        self.response_text.insert("1.0", f"❌ {error_msg}")
        self.response_text.config(state=tk.DISABLED)
        self.status_label.config(text="Error occurred. Please try again.")
    
    def clear_all(self):
        """Clear both input and output areas"""
        self.question_entry.delete("1.0", tk.END)
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete("1.0", tk.END)
        self.response_text.config(state=tk.DISABLED)
        self.status_label.config(text="Ready to answer your questions!")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

def main():
    """Main function to run the application"""
    try:
        app = RestaurantAssistantGUI()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application: {e}")

if __name__ == "__main__":
    main()
