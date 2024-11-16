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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add this after load_dotenv()
logger.info(f"Using Google API Key: {os.getenv('GOOGLE_API_KEY')[-6:]}") # Only log last 6 chars for security

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
GEMINI_RETRY_DELAYS = [0.5, 1, 2, 4, 8]  # Exponential backoff
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

# Rate limiting configuration - make it more lenient
RATE_LIMIT_WINDOW = 60  # 1 minute window
MAX_REQUESTS = 100      # Increased from 60 to 100
GEMINI_RATE_LIMIT_WINDOW = 60
GEMINI_MAX_REQUESTS = 100  # Increased from 60 to 100

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

def retry_with_backoff(func, *args, **kwargs):
    """Generic retry function with exponential backoff"""
    last_exception = None
    for attempt, delay in enumerate(GEMINI_RETRY_DELAYS):
        try:
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
# Optimize CORS configuration
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def after_request(response):
    response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
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

@app.route('/generate_story', methods=['POST'])
def generate_story():
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

@app.route('/generate_frame', methods=['POST'])
def generate_frame():
    try:
        if not check_rate_limit():
            return jsonify({
                'success': False, 
                'error': 'Rate limit exceeded. Please wait and try again.'
            }), 429

        # Add API key validation
        stability_key = os.getenv('STABILITY_API_KEY')
        if not stability_key:
            logger.error("Stability API key not found")
            return jsonify({
                'success': False,
                'error': 'Image generation service is not configured properly.',
                'disable_stop_motion': True
            }), 503

        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({'success': False, 'error': 'No prompt provided'}), 400

        prompt = data['prompt']
        safe_prompt = f"family-friendly, child-appropriate, non-violent, cute, {prompt}"

        API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image"
        headers = {
            "Authorization": f"Bearer {stability_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        payload = {
            "text_prompts": [{"text": safe_prompt, "weight": 1}],
            "cfg_scale": 7,
            "height": 512,
            "width": 512,
            "samples": 1,
            "steps": 30,
            "style_preset": "digital-art"
        }

        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            error_data = None
            try:
                error_data = response.json()
            except:
                error_data = str(response.content)

            logger.error(f"Stability API error: Status {response.status_code}, Response: {error_data}")

            if response.status_code == 429:
                if isinstance(error_data, dict) and ('insufficient_balance' in str(error_data) or 'exceeded' in str(error_data)):
                    logger.error("Stability API balance depleted or quota exceeded")
                    return jsonify({
                        'success': False,
                        'error': 'Image generation quota exceeded. Stop motion feature has been disabled.',
                        'disable_stop_motion': True
                    }), 503
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again later.',
                    'disable_stop_motion': True
                }), 429

            return jsonify({
                'success': False,
                'error': f'Image generation failed: {str(error_data)}',
                'disable_stop_motion': True
            }), response.status_code

        result = response.json()
        if "artifacts" in result and result["artifacts"]:
            return jsonify({
                'success': True,
                'image': f'data:image/png;base64,{result["artifacts"][0]["base64"]}'
            })
        
        return jsonify({
            'success': False,
            'error': 'No image generated',
            'disable_stop_motion': True
        }), 500
            
    except Exception as e:
        logger.error(f"Frame generation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'disable_stop_motion': True
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'services': {
            'gemini': bool(os.getenv("GOOGLE_API_KEY")),
            'stability': bool(os.getenv("STABILITY_API_KEY"))  # Update to check Stability API key
        }
    })

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        raise
