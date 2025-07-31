"""
Test file for image generation functionality
Tests the generate_image function with a balloons prompt
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the ImageGenerator class from the main UI file
from ui_deep_research_images import ImageGenerator

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
