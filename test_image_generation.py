"""
Test file for image generation functionality
Tests the generate_image function with a balloons prompt
"""

import os
import sys
import base64
import uuid
import requests
from datetime import datetime
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ImageGenerator:
    """Image generation tool using Azure OpenAI GPT-Image-1"""
    
    def __init__(self):
        # Check for IMAGE_KEY environment variable for key authentication
        self.api_key = os.environ.get("IMAGE_KEY")
        
        if self.api_key:
            # Use API key authentication
            self.token = None
            self.auth_header = {"api-key": self.api_key}
            print("🔑 Using API key authentication for image generation")
        else:
            # Use Azure AD token authentication (default)
            def get_azure_ad_token():
                token = DefaultAzureCredential().get_token("https://cognitiveservices.azure.com/.default")
                return token.token

            self.token = get_azure_ad_token()
            self.auth_header = {"Authorization": f"Bearer {self.token}"}
            print("🔒 Using Azure AD token authentication for image generation")
        
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

            response = requests.post(
                generation_url,
                headers={
                    **self.auth_header,
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


# Import the ImageGenerator class from the main file
# Note: Python module imports need the file to be accessible as a module
import sys
import os

# Add current directory to path and import
sys.path.insert(0, os.path.dirname(__file__))

def test_generate_image():
    """Test the generate_image function with a balloons prompt"""
    
    # Check for required environment variables
    required_vars = [
        "IMAGE_PROJECT_ENDPOINT",
        "IMAGE_MODEL"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        return False
    
    try:
        # Initialize the image generator
        print("🔧 Initializing image generator...")
        image_generator = ImageGenerator()
        
        # Test prompt for balloons flying away on a beach
        prompt = "balloons flying away on a beach"
        
        print(f"🎨 Generating image with prompt: '{prompt}'")
        print("⏳ This may take a moment...")
        
        # Generate the image
        filename = image_generator.generate_image(prompt)
        
        print(f"✅ Image generation successful!")
        print(f"📄 Filename: {filename}")
        print(f"📁 Saved to: ./images/{filename}")
        
        # Check if file actually exists
        filepath = os.path.join("./images", filename)
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"📊 File size: {file_size:,} bytes")
            print(f"🎉 Test completed successfully!")
            return True
        else:
            print(f"❌ Error: Generated file not found at {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Error during image generation: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Image Generation")
    print("=" * 50)
    
    success = test_generate_image()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test PASSED - Image generated successfully!")
    else:
        print("❌ Test FAILED - See errors above")
    
    return success

if __name__ == "__main__":
    main()
