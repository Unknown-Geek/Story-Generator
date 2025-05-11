"""
AI-powered Story Generator Server
Handles story generation using Gemini API and image generation using FLUX Pro API
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
from queue import Queue
from huggingface_hub import login

# Move logger configuration before any logger usage
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path='../.env')

# Initialize Hugging Face authentication
hf_token = os.getenv("HUGGINGFACE_API_KEY")  # Changed from HUGGING_FACE_TOKEN
if hf_token:
    login(token=hf_token)
    logger.info("Logged in to Hugging Face")
else:
    logger.warning("No Hugging Face API key found, running with limited quota")

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
    'gemini-2.0-flash',
    generation_config=generation_config,
    safety_settings=SAFETY_SETTINGS
)

story_model = genai.GenerativeModel(
    'gemini-2.0-flash',
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
        "origins": [
            "https://storygeneratorfrontend.vercel.app",
            "http://localhost:3000"
        ],
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
    """Generates a story based on image input using Gemini API"""
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
        image_base64 = data.get('image')
        genre = data.get('genre', 'fantasy')  # Add this line
        length = data.get('length', 500)      # Add this line

        if not image_base64:
            logger.error("No image data provided")
            return jsonify({
                'success': False,
                'error': 'No image data provided'
            }), 400

        try:
            # Validate base64 image
            image_data = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_data))
            
            # Validate image format and size
            if image.format not in ['JPEG', 'PNG', 'WEBP']:
                logger.error(f"Invalid image format: {image.format}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid image format. Please use JPEG, PNG, or WEBP.'
                }), 400

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
            logger.exception("Error processing image or generating story")
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

# Add new configuration for frame generation
FRAME_IMAGE_SIZE = {
    'width': 256,  # Updated to match FLUX Pro default
    'height': 256  # Updated to match FLUX Pro default
}
MAX_CACHED_FRAMES = 100
CACHE_CLEANUP_THRESHOLD = 80
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

# Initialize FLUX Pro API client
flux_pro_client = Client("NihalGazi/FLUX-Pro-Unlimited")

# Add new constants for frame generation
FRAME_GENERATION_CONFIG = {
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 60,  # 1 minute between retries
    'QUOTA_WAIT_TIME': 720,  # 12 minutes wait when quota exceeded
    'MAX_QUEUE_SIZE': 50
}

# Add queue and tracking for frame generation
frame_queue = Queue(maxsize=FRAME_GENERATION_CONFIG['MAX_QUEUE_SIZE'])
last_quota_exceeded = None
frame_generation_lock = Lock()

# Update the frame generation function to use FLUX Pro API - making it synchronous
def generate_frame_with_retry(prompt):
    """Generates frame with retry logic for quota limits"""
    global last_quota_exceeded
    
    for attempt in range(FRAME_GENERATION_CONFIG['MAX_RETRIES']):
        try:
            # Check if we need to wait due to previous quota exceed
            if last_quota_exceeded:
                wait_time = (last_quota_exceeded + 
                           timedelta(seconds=FRAME_GENERATION_CONFIG['QUOTA_WAIT_TIME']) - 
                           datetime.now()).total_seconds()
                if wait_time > 0:
                    logger.info(f"Waiting {wait_time:.0f}s for quota reset")
                    time.sleep(wait_time)
                last_quota_exceeded = None

            # Make the API call to FLUX Pro
            result = flux_pro_client.predict(
                prompt=prompt,
                width=FRAME_IMAGE_SIZE['width'],
                height=FRAME_IMAGE_SIZE['height'],
                seed=42,
                randomize=True,
                server_choice="Google US Server",
                api_name="/generate_image"
            )
            
            # Check if the result is valid
            if result and isinstance(result, str) and os.path.exists(result):
                # Read the image and encode to base64
                with open(result, 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                return {'success': True, 'image': f"data:image/png;base64,{image_data}"}
            else:
                logger.error(f"Invalid result from FLUX Pro API: {result}")
                if attempt < FRAME_GENERATION_CONFIG['MAX_RETRIES'] - 1:
                    time.sleep(FRAME_GENERATION_CONFIG['RETRY_DELAY'])
                    continue
                return {'success': False, 'error': f'Invalid result from image generation API: {result}'}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"FLUX Pro API error: {error_msg}")
            if 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                last_quota_exceeded = datetime.now()
                wait_time = FRAME_GENERATION_CONFIG['QUOTA_WAIT_TIME']
                logger.warning(f"API quota exceeded. Waiting {wait_time}s before retry")
                if attempt < FRAME_GENERATION_CONFIG['MAX_RETRIES'] - 1:
                    time.sleep(FRAME_GENERATION_CONFIG['RETRY_DELAY'])
                    continue
            if attempt < FRAME_GENERATION_CONFIG['MAX_RETRIES'] - 1:
                time.sleep(FRAME_GENERATION_CONFIG['RETRY_DELAY'])
                continue
            return {'success': False, 'error': f"Frame generation failed: {error_msg}"}

    return {'success': False, 'error': 'Max retries exceeded for frame generation'}

# Update the generate_frame route to be synchronous
@app.route('/generate_frame', methods=['POST'])
def generate_frame():
    """Handles frame generation requests with quota management"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Invalid request format'}), 400

        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({'success': False, 'error': 'No prompt provided'}), 400

        prompt = data['prompt']
        
        try:
            result = generate_frame_with_retry(prompt)
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 500
            
        except Exception as e:
            error_msg = str(e)
            if 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                wait_time = FRAME_GENERATION_CONFIG['QUOTA_WAIT_TIME']
                return jsonify({
                    'success': False,
                    'error': f'API quota exceeded. Please try again in {wait_time//60} minutes.',
                    'retry_after': wait_time
                }), 429
            return jsonify({'success': False, 'error': error_msg}), 500

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
