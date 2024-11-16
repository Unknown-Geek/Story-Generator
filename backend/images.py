import requests
import base64
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define output directory relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "generated_images")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Get API key from environment variable
API_KEY = os.getenv("STABILITY_API_KEY")
if not API_KEY:
    raise ValueError("STABILITY_API_KEY environment variable is not set")

# Endpoint for the Stability AI image generation API
API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image"

def generate_test_image(prompt="Lighthouse on a cliff overlooking the ocean"):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "text_prompts": [{"text": prompt, "weight": 1}],
        "cfg_scale": 7,
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 30,
        "style_preset": "digital-art"
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json() if response.ok else None

if __name__ == '__main__':
    result = generate_test_image()
    print("Success" if result else "Failed")
