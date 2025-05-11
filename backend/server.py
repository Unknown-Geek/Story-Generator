"""
AI-powered Story Generator Server with Multi-Image Support
Handles story generation using Gemini API based on multiple images
"""

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import logging
import os
import time
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
from datetime import datetime, timedelta
from collections import deque
from threading import Lock
from PIL import Image
import base64

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path='../.env')

# Configure Google AI
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

# Add retry configuration
GEMINI_MAX_RETRIES = 5
GEMINI_RETRY_DELAYS = [0.5, 1, 2, 4, 8]  # Exponential backoff in seconds

# Create AI models
vision_model = genai.GenerativeModel(
    'gemini-2.0-flash',
    generation_config=generation_config,
    safety_settings=SAFETY_SETTINGS
)

story_model = genai.GenerativeModel(
    'gemini-2.0-flash',
    generation_config=generation_config,
    safety_settings=SAFETY_SETTINGS
)

# Rate limiting setup
RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX_REQUESTS = 10  # 10 requests per minute
gemini_requests = deque()
gemini_lock = Lock()

def can_make_gemini_request():
    """Check if we can make a new request within rate limits"""
    with gemini_lock:
        now = datetime.now()
        # Remove requests older than the window
        while gemini_requests and (now - gemini_requests[0]).total_seconds() > RATE_LIMIT_WINDOW:
            gemini_requests.popleft()
        
        # Check if we're under the limit
        if len(gemini_requests) < RATE_LIMIT_MAX_REQUESTS:
            gemini_requests.append(now)
            return True
        
        return False

def retry_with_backoff(func, *args, **kwargs):
    """Retry function with exponential backoff"""
    last_exception = None
    for attempt, delay in enumerate(GEMINI_RETRY_DELAYS + [0] * (GEMINI_MAX_RETRIES - len(GEMINI_RETRY_DELAYS))):
        if attempt > 0 and delay > 0:
            logger.info(f"Retrying in {delay} seconds (attempt {attempt+1}/{GEMINI_MAX_RETRIES})")
            time.sleep(delay)
        
        try:
            logger.info(f"Attempt {attempt+1}/{GEMINI_MAX_RETRIES}")
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            last_exception = e
            logger.error(f"Attempt {attempt+1}/{GEMINI_MAX_RETRIES} failed: {str(e)}")
            
            # Don't retry certain errors
            if "safety" in str(e).lower():
                logger.error("Safety error, not retrying")
                raise
    
    # If we get here, all retries failed
    logger.error(f"All {GEMINI_MAX_RETRIES} attempts failed")
    if last_exception:
        raise last_exception
    else:
        raise Exception("All retry attempts failed")

# Create Flask app
app = Flask(__name__)
CORS(app)

def handle_preflight():
    """Handle preflight CORS requests"""
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

@app.route('/generate_story', methods=['POST', 'OPTIONS'])
def generate_story():
    """Generates a story based on multiple image inputs using Gemini API"""
    if request.method == "OPTIONS":
        return handle_preflight()

    try:
        # Validate request body
        if not request.is_json:
            logger.error("Request body is not JSON")
            return jsonify({
                'success': False,
                'error': 'Invalid request format. Expected JSON.'
            }), 400

        data = request.json
        if not data:
            logger.error("Empty request body")
            return jsonify({
                'success': False,
                'error': 'Request body is empty'
            }), 400

        # Extract and validate all required parameters
        image_base64_list = data.get('images', [])
        genre = data.get('genre', 'fantasy')
        length = data.get('length', 500)

        # For backward compatibility, handle single image case
        if not isinstance(image_base64_list, list):
            image_base64_list = [image_base64_list]

        if not image_base64_list or len(image_base64_list) == 0:
            logger.error("No images provided")
            return jsonify({
                'success': False,
                'error': 'No images provided'
            }), 400

        # Process all images and create descriptions
        image_descriptions = []
        try:
            for idx, image_base64 in enumerate(image_base64_list):
                # Validate base64 image
                image_data = base64.b64decode(image_base64)
                image = Image.open(BytesIO(image_data))
                
                # Validate image format
                if image.format not in ['JPEG', 'PNG', 'WEBP']:
                    logger.error(f"Invalid image format for image {idx+1}: {image.format}")
                    return jsonify({
                        'success': False,
                        'error': f'Invalid image format for image {idx+1}. Please use JPEG, PNG, or WEBP.'
                    }), 400

                # Generate description for this image
                vision_prompt = f"Describe this image in detail for creating a {genre} story."
                response = retry_with_backoff(
                    vision_model.generate_content,
                    [vision_prompt, image]
                )
                image_descriptions.append(response.text)
                logger.info(f"Generated description for image {idx+1}")

            # Combine all descriptions for the story generation
            combined_descriptions = "\n\n".join([
                f"Image {idx+1}: {desc}" for idx, desc in enumerate(image_descriptions)
            ])

            # Generate story based on all image descriptions
            story_prompt = f"""
            Create a {genre} story that incorporates all the following images:
            
            {combined_descriptions}
            
            The story should be approximately {length} words long and suitable for all ages.
            Focus on {GENRE_THEMES.get(genre.lower(), 'engaging storytelling')}.
            The story should flow naturally between the different images, creating a cohesive narrative.
            """
            
            story_response = retry_with_backoff(
                story_model.generate_content,
                story_prompt
            )
            story = story_response.text

            return jsonify({
                'success': True,
                'story': story,
                'image_descriptions': image_descriptions
            })

        except Exception as e:
            logger.exception("Error processing images or generating story")
            return jsonify({
                'success': False,
                'error': f'Error processing request: {str(e)}'
            }), 500

    except Exception as e:
        logger.exception("Unexpected server error")
        return jsonify({
            'success': False,
            'error': 'An unexpected server error occurred. Please try again.'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'services': {
            'gemini': bool(os.getenv("GOOGLE_API_KEY"))
        }
    })

if __name__ == '__main__':
    import socket

    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except OSError as e:
        if e.errno == 98:  # Address already in use
            port = find_free_port()
            print(f"Port 5000 is in use, switching to port {port}")
            app.run(host='0.0.0.0', port=port)
        else:
            print(f"Error starting server: {str(e)}")
            raise
