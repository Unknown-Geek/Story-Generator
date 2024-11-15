from flask import Flask, request, jsonify
from flask_cors import CORS
from pyngrok import ngrok, conf
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

# Define age-appropriate themes for each genre
GENRE_THEMES = {
    'fantasy': 'magical adventures, friendly creatures, and noble quests',
    'adventure': 'exploration, discovery, and overcoming challenges',
    'romance': 'friendship, kindness, and family relationships',
    'horror': 'mild mystery, spooky (but not scary) situations, and courage',
    'mystery': 'solving puzzles, helping others, and uncovering secrets',
    'moral story': 'learning life lessons, making good choices, and personal growth'
}

# Configure safety settings
SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_DANGEROUS",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

# Create generation config
generation_config = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# Initialize models with safety settings
vision_model = genai.GenerativeModel('gemini-1.5-pro', 
                                   generation_config=generation_config,
                                   safety_settings=SAFETY_SETTINGS)
story_model = genai.GenerativeModel('gemini-pro', 
                                  generation_config=generation_config,
                                  safety_settings=SAFETY_SETTINGS)

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
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
        
        try:
            logger.debug("Starting image processing")
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_data)
            logger.debug(f"Decoded image bytes: {len(image_bytes)} bytes")
            
            # Create a new BytesIO object and write the bytes
            image_buffer = io.BytesIO(image_bytes)
            image_buffer.seek(0)
            
            # Open the image from the buffer
            image = Image.open(image_buffer)
            logger.debug(f"Opened image: mode={image.mode}, size={image.size}")
            
            # Create a new RGB image and paste the original onto it
            if image.mode in ('RGBA', 'LA'):
                new_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    new_image.paste(image, mask=image.split()[3])
                else:
                    new_image.paste(image, mask=image.split()[1])
                image = new_image
                logger.debug("Converted image to RGB from RGBA/LA")
            elif image.mode != 'RGB':
                new_image = Image.new('RGB', image.size, (255, 255, 255))
                new_image.paste(image)
                image = new_image
                logger.debug("Converted image to RGB from other mode")
            
            # Resize if needed while maintaining aspect ratio
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.debug(f"Resized image to {image.size}")

            logger.debug(f"Image processed successfully: {image.mode} {image.size}")
            
            # Updated prompt generation
            image_prompt = "Describe the objects and scene in this image with detail and context."
            image_response = vision_model.generate_content([image_prompt, image])
            image_description = image_response.text
            logger.debug(f"Image description: {image_description}")
            
            # Enhanced story prompt using genre themes
            story_prompt = f"""Write a family-friendly {genre} story about {GENRE_THEMES.get(genre, 'adventure and discovery')}.
            Requirements:
            - Exactly {word_count} words (important!)
            - Age-appropriate content (suitable for ages 8-12)
            - No violence, scary elements, or adult themes
            - Focus on positive messages and character growth
            - Include descriptive but simple language
            - Clear beginning, middle, and end structure
            - Based on this scene: {image_description}

            Create an engaging story that teaches good values while entertaining young readers."""
            
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

def setup_ngrok():
    """Setup ngrok with proper error handling"""
    try:
        # Kill any existing ngrok processes first
        ngrok.kill()
        
        # Set default config path
        conf.get_default().config_path = os.path.join(os.path.expanduser("~"), ".ngrok2", "ngrok.yml")
        
        # Configure ngrok
        ngrok.set_auth_token(os.getenv('NGROK_AUTH_TOKEN'))
        
        # Start new tunnel
        public_url = ngrok.connect(5000)
        print(f'\nNgrok tunnel established at: {public_url}')
        print(f'Story generation endpoint: {public_url}/generate_story\n')
        return public_url
    except Exception as e:
        print(f"Error setting up ngrok: {str(e)}")
        print("Starting server without ngrok tunnel...")
        return None

if __name__ == '__main__':
    try:
        # Setup ngrok
        public_url = setup_ngrok()
        
        # Start Flask app
        app.run(port=5000)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
