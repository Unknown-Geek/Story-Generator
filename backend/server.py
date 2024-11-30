"""
AI-powered Story Generator Server
Handles story generation using Gemini API and image generation using SDXL-Lightning
"""

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests  # Add this import
import logging
import os
import time  # Add this for sleep function
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
from datetime import datetime, timedelta  # Add timedelta
from collections import deque
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from gradio_client import Client
import base64

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logging.captureWarnings(True)

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

# Add new retry configuration
GEMINI_MAX_RETRIES = 5
GEMINI_RETRY_DELAYS = [0.5, 1, 2, 4, 8]  # Exponential backoff in seconds
GEMINI_TIMEOUT = 30  # seconds

# Update model configuration without timeouts
vision_model = genai.GenerativeModel(
    'gemini-1.5-pro',
    generation_config=generation_config,
    safety_settings=SAFETY_SETTINGS
)

story_model = genai.GenerativeModel(
    'gemini-pro',
    generation_config=generation_config,
    safety_settings=SAFETY_SETTINGS
)

# Rate limiting configuration
RATE_LIMIT_WINDOW = 60  # Increased to 1 minute
MAX_REQUESTS = 60  # Adjusted for better performance
request_times = deque(maxlen=MAX_REQUESTS)  # Add maxlen for automatic cleanup
rate_limit_lock = Lock()

def check_rate_limit():
    """Check if we're within rate limits"""
    now = datetime.now()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    
    with rate_limit_lock:
        # Remove old requests
        while request_times and request_times[0] < window_start:
            request_times.popleft()
        
        # Check if we're at the limit
        if len(request_times) >= MAX_REQUESTS:
            return False
        
        # Add current request
        request_times.append(now)
        return True

# Add these constants near the top with other configurations
GEMINI_RATE_LIMIT_WINDOW = 60  # 1 minute
GEMINI_MAX_REQUESTS = 60  # Adjust based on your quota
gemini_request_times = deque()
gemini_rate_limit_lock = Lock()

def check_gemini_rate_limit():
    """Check if we're within Gemini API rate limits"""
    now = datetime.now()
    window_start = now - timedelta(seconds=GEMINI_RATE_LIMIT_WINDOW)
    
    with gemini_rate_limit_lock:
        while gemini_request_times and request_times[0] < window_start:
            gemini_request_times.popleft()
        
        if len(gemini_request_times) >= GEMINI_MAX_REQUESTS:
            return False
        
        gemini_request_times.append(now)
        return True

# Instead handle timeouts in the retry mechanism
def retry_with_backoff(func, *args, **kwargs):
    """Retries function calls with exponential backoff on failure"""
    last_exception = None
    for attempt, delay in enumerate(GEMINI_RETRY_DELAYS):
        try:
            # Remove timeout parameter
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if any(error_code in str(e) for error_code in ['503', '504', 'overloaded', 'Deadline Exceeded']):
                if attempt < len(GEMINI_RETRY_DELAYS) - 1:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s... Error: {str(e)}")
                    time.sleep(delay)
                    continue
            raise
    raise last_exception

app = Flask(__name__)
# Update CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

@app.after_request
def after_request(response):
    response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '3600'
    })
    return response

# Add OPTIONS route handler for all routes
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Max-Age', '3600')
        return response

@app.route('/generate_story', methods=['POST', 'OPTIONS'])
def generate_story():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        })
        return response

    """Generates a story based on image input using Gemini API"""
    try:
        if not check_gemini_rate_limit():
            return jsonify({
                'success': False,
                'error': 'Gemini API rate limit exceeded. Please try again in a minute.'
            }), 429

        data = request.json
        image_base64 = data.get('image')
        genre = data.get('genre', 'fantasy')
        length = data.get('length', 500)

        if not image_base64:
            return jsonify({'success': False, 'error': 'No image provided'}), 400

        try:
            image_data = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_data))
            
            # Use retry mechanism for vision analysis
            vision_prompt = f"Describe this image in detail for creating a {genre} story."
            response = retry_with_backoff(
                vision_model.generate_content,
                [vision_prompt, image]
            )
            image_description = response.text

            # Use retry mechanism for story generation
            story_prompt = f"""
            Create a {genre} story based on this image description: {image_description}
            The story should be approximately {length} words long and suitable for all ages.
            Focus on {GENRE_THEMES.get(genre.lower(), 'engaging storytelling')}.
            """
            story_response = retry_with_backoff(
                story_model.generate_content,
                story_prompt
            )
            story = story_response.text

            return jsonify({
                'success': True,
                'story': story,
                'image_description': image_description
            })

        except Exception as e:
            error_msg = str(e)
            if any(code in error_msg for code in ['503', '504', 'overloaded', 'Deadline Exceeded']):
                return jsonify({
                    'success': False,
                    'error': 'The AI service is currently overloaded. Please try again in a few moments.'
                }), 503
            return jsonify({
                'success': False,
                'error': f'Error processing request: {error_msg}'
            }), 400

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again later.'
        }), 500

# Add new configuration for frame generation
FRAME_IMAGE_SIZE = 320  # Minimum allowed size for Stability API v1.6
MAX_CACHED_FRAMES = 100  # Increased from 50 to 100
CACHE_CLEANUP_THRESHOLD = 80  # Clean when we reach 80% capacity
frame_cache = {}

def clean_old_frames():
    """Remove old frames from cache if limit exceeded"""
    if len(frame_cache) > CACHE_CLEANUP_THRESHOLD:
        # Remove oldest frames more aggressively
        oldest_frames = sorted(frame_cache.items(), key=lambda x: x[1]['timestamp'])[:20]
        for frame_id, _ in oldest_frames:
            del frame_cache[frame_id]

# Add parallel processing for frame generation
executor = ThreadPoolExecutor(max_workers=4)

# Initialize SDXL-Lightning client
sdxl_client = Client("ByteDance/SDXL-Lightning")

# Modify the generate_frame route
@app.route('/generate_frame', methods=['POST'])
def generate_frame():
    """Generates image frames using SDXL-Lightning"""
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({'success': False, 'error': 'No prompt provided'}), 400

        prompt = data['prompt']
        
        # Generate image using SDXL-Lightning
        try:
            result = sdxl_client.predict(
                prompt=prompt,
                ckpt="4-Step",  # You can adjust steps based on speed/quality needs
                api_name="/generate_image"
            )
            
            # Convert the local file path to base64
            with open(result, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'image': f"data:image/png;base64,{image_data}"
            })
            
        except Exception as e:
            raise Exception(f"SDXL-Lightning generation failed: {str(e)}")

    except Exception as e:
        logger.error(f"Frame generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Simplify health check to remove SDXL server check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'services': {
            'gemini': bool(os.getenv("GOOGLE_API_KEY")),
        }
    })

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        raise
