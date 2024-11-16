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

# Set the request parameters
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

try:
    # Create JSON payload
    payload = {
        "text_prompts": [
            {
                "text": "Lighthouse on a cliff overlooking the ocean",
                "weight": 1
            }
        ],
        "cfg_scale": 7,
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 30,
        "style_preset": "digital-art"
    }

    # Send a POST request to the Stability API
    response = requests.post(
        API_URL,
        headers=headers,
        json=payload  # Use json parameter instead of files
    )

    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        if "artifacts" in result and len(result["artifacts"]) > 0:
            img_data = base64.b64decode(result["artifacts"][0]["base64"])
            
            # Save the image
            output_file = os.path.join(OUTPUT_DIR, "lighthouse.png")
            with open(output_file, "wb") as file:
                file.write(img_data)
            print(f"Image successfully saved as '{output_file}'")

            # Load and display the image
            image = Image.open(BytesIO(img_data))
            image.show()  # Opens the image in the default viewer
        else:
            raise Exception("No image data in response")
    else:
        # Raise an exception if the API returned an error
        raise Exception(f"API Error: {response.text}")

except Exception as e:
    print(f"An error occurred: {e}")
