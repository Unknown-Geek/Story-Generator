"""
AI-powered Story Generator Server
Handles story generation and frame animation using Gemini and Stability AI APIs
"""

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
import base64
import logging
import os
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
from datetime import datetime, timedelta
from collections import deque
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

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
        while gemini_request_times and gemini_request_times[0] < window_start:
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

# Update rate limiting configuration for Stability API
STABILITY_RATE_LIMIT_WINDOW = 60  # Increase to 60 seconds
STABILITY_MAX_REQUESTS = 50  # Reduce max requests
STABILITY_RETRY_DELAYS = [5, 10, 20, 30, 60]  # Longer delays between retries
STABILITY_KEY_COOLDOWN = {}  # Track per-key cooldown
stability_request_times = deque()
stability_rate_limit_lock = Lock()

def check_stability_rate_limit():
    """Check if we're within Stability API rate limits"""
    now = datetime.now()
    window_start = now - timedelta(seconds=STABILITY_RATE_LIMIT_WINDOW)
    
    with stability_rate_limit_lock:
        while stability_request_times and stability_request_times[0] < window_start:
            stability_request_times.popleft()
        
        if len(stability_request_times) >= STABILITY_MAX_REQUESTS:
            return False
        
        stability_request_times.append(now)
        return True

# Add after the existing configurations
STABILITY_API_KEYS = [
    os.getenv('STABILITY_API_KEY_1'),
    os.getenv('STABILITY_API_KEY_2'),
    os.getenv('STABILITY_API_KEY_3')
]
STABILITY_API_KEYS = [key for key in STABILITY_API_KEYS if key]  # Remove any None values
current_api_key_index = 0

def get_next_stability_api_key():
    """Rotate through available API keys"""
    global current_api_key_index
    if not STABILITY_API_KEYS:
        raise Exception("No Stability API keys configured")
    
    api_key = STABILITY_API_KEYS[current_api_key_index]
    current_api_key_index = (current_api_key_index + 1) % len(STABILITY_API_KEYS)
    return api_key

# Modify the Stability API request function to be synchronous
def try_stability_request(prompt, retries=3):
    """Try request with different API keys if one fails"""
    last_error = None
    
    for attempt in range(retries):
        try:
            api_key = get_next_stability_api_key()
            
            # Check if key is in cooldown
            cooldown_time = STABILITY_KEY_COOLDOWN.get(api_key)
            if cooldown_time and datetime.now() < cooldown_time:
                logger.warning(f"API key in cooldown, trying next key")
                continue
                
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text_prompts": [{"text": prompt, "weight": 1}],
                "cfg_scale": 6,
                "height": FRAME_IMAGE_SIZE,
                "width": FRAME_IMAGE_SIZE,
                "samples": 1,
                "steps": 15,
                "style_preset": "digital-art"
            }

            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit hit
                # Put key in cooldown for 60 seconds
                STABILITY_KEY_COOLDOWN[api_key] = datetime.now() + timedelta(seconds=60)
                delay = STABILITY_RETRY_DELAYS[min(attempt, len(STABILITY_RETRY_DELAYS)-1)]
                logger.warning(f"Rate limit hit, cooling down key for 60s and waiting {delay}s")
                time.sleep(delay)
                continue
            else:
                response.raise_for_status()
                
        except Exception as e:
            last_error = e
            logger.warning(f"API key failed, trying next one. Error: {str(e)}")
            
            # Add delay between attempts
            delay = STABILITY_RETRY_DELAYS[min(attempt, len(STABILITY_RETRY_DELAYS)-1)]
            time.sleep(delay)
            continue
            
    raise last_error or Exception("All API keys failed")

# Modify the generate_frame route
@app.route('/generate_frame', methods=['POST'])
def generate_frame():
    """Generates animation frames using Stability AI API with failover"""
    try:
        # More strict rate limiting
        if not check_rate_limit() or not check_stability_rate_limit():
            return jsonify({
                'success': False, 
                'error': 'Rate limit exceeded. Please wait 60 seconds and try again.'
            }), 429

        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({'success': False, 'error': 'No prompt provided'}), 400

        prompt = data['prompt']
        prompt_hash = hash(prompt)  # Use prompt hash as cache key

        # Check cache first
        if prompt_hash in frame_cache:
            cached_frame = frame_cache[prompt_hash]
            # Update timestamp to mark as recently used
            cached_frame['timestamp'] = datetime.now()
            return jsonify({
                'success': True,
                'image': cached_frame['image'],
                'cached': True
            })

        # Add family-friendly modifiers to prompt
        safe_prompt = f"family-friendly, child-appropriate, non-violent, cute, {prompt}"

        # Stability API configuration with reduced image size
        API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {os.getenv('STABILITY_API_KEY')}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # Optimize payload for faster generation
        payload = {
            "text_prompts": [
                {
                    "text": safe_prompt,
                    "weight": 1
                }
            ],
            "cfg_scale": 6,  # Slightly reduced for faster generation
            "height": FRAME_IMAGE_SIZE,
            "width": FRAME_IMAGE_SIZE,
            "samples": 1,
            "steps": 15,  # Further reduced steps for faster generation
            "style_preset": "digital-art"
        }

        try:
            result = try_stability_request(safe_prompt)
            if "artifacts" in result and len(result["artifacts"]) > 0:
                img_data = result["artifacts"][0]["base64"]
                image_url = f'data:image/png;base64,{img_data}'
                
                # Cache the generated frame
                frame_cache[prompt_hash] = {
                    'image': image_url,
                    'timestamp': datetime.now()
                }
                
                # Clean old frames if needed
                clean_old_frames()
                
                return jsonify({
                    'success': True,
                    'image': image_url,
                    'cached': False
                })
            else:
                raise Exception("No image generated in response")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Stability API error with all keys: {error_msg}")
            return jsonify({
                'success': False,
                'error': f'Image generation failed: {error_msg}'
            }), 500

    except Exception as e:
        logger.error(f"Frame generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Update health check to monitor all API keys
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'services': {
            'gemini': bool(os.getenv("GOOGLE_API_KEY")),
            'stability': {
                'available_keys': len(STABILITY_API_KEYS),
                'status': bool(STABILITY_API_KEYS)
            }
        }
    })

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        raise
