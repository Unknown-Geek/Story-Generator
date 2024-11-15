from flask import Flask, request, jsonify
from flask_cors import CORS
from pyngrok import ngrok
import requests
import io
import base64
import logging
import os
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from huggingface_hub import login
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def login_with_retry(api_key, retries=3, backoff_factor=0.3):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    
    try:
        login(api_key)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to login to Hugging Face: {e}")
        raise

# Load environment variables
load_dotenv()
login_with_retry(os.getenv('HUGGINGFACE_API_KEY'))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logging.captureWarnings(True)

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Create generation config
generation_config = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# Initialize models
vision_model = genai.GenerativeModel('gemini-1.5-pro', generation_config=generation_config)
story_model = genai.GenerativeModel('gemini-pro', generation_config=generation_config)

# Configure ngrok with auth token
ngrok.set_auth_token(os.getenv('NGROK_AUTH_TOKEN'))

app = Flask(__name__)
CORS(app)

@app.route('/generate_story', methods=['POST'])
def generate_story():
    try:
        data = request.get_json()
        if not data:
            logger.debug("No data received in request")
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        image_data = data.get('image', '')
        genre = data.get('genre', 'fantasy').lower()
        word_count = data.get('length', 200)
        
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
        
        try:
            # Process image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            logger.debug(f"Image mode: {image.mode}")
            
            # Handle image conversion
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Generate image description
            image_prompt = "Describe what you see in this image concisely."
            image_response = vision_model.generate_content([image_prompt, image])
            image_description = image_response.text
            logger.debug(f"Image description: {image_description}")
            
            # Generate story
            story_prompt = f"""Write a {genre} story appropriate for all ages. Base it on this scene: {image_description}
            Requirements:
            - Length: approximately {word_count} words
            - Age-appropriate content
            - Clear narrative structure
            - Engaging and descriptive language
            - Positive message or moral"""
            
            story_response = story_model.generate_content(story_prompt)
            
            if story_response.text:
                return jsonify({'success': True, 'story': story_response.text})
            else:
                return jsonify({'success': False, 'error': 'Story generation failed'}), 500
                
        except Exception as img_error:
            logger.error(f"Image processing error: {str(img_error)}")
            return jsonify({'success': False, 'error': str(img_error)}), 400
            
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    try:
        # Start ngrok tunnel
        public_url = ngrok.connect(5000)
        logger.info(f'Ngrok tunnel established at: {public_url}')
        logger.info(f'Story generation endpoint: {public_url}/generate_story')
        
        # Start Flask app
        app.run(port=5000)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
