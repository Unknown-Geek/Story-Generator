from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
import io
import time
import base64
import logging
import os
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from io import BytesIO
from datetime import datetime, timedelta
from collections import deque
from threading import Lock

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

# Initialize models with safety settings
vision_model = genai.GenerativeModel('gemini-1.5-flash', 
                                   generation_config=generation_config,
                                   safety_settings=SAFETY_SETTINGS)
story_model = genai.GenerativeModel('gemini-pro', 
                                  generation_config=generation_config,
                                  safety_settings=SAFETY_SETTINGS)

# Rate limiting configuration
RATE_LIMIT_WINDOW = 10  # seconds
MAX_REQUESTS = 150  # requests per window
request_times = deque()
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

app = Flask(__name__)
# Update CORS configuration to be more explicit
CORS(app, 
     resources={
         r"/*": {
             "origins": "*",
             "methods": ["GET", "POST", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "max_age": 3600
         }
     },
     supports_credentials=True)

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    header['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
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
            
            # Add retry logic for Gemini API calls
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    # Get image description using Gemini Vision
                    vision_prompt = f"Describe this image in detail for creating a {genre} story."
                    response = vision_model.generate_content([vision_prompt, image])
                    image_description = response.text

                    # Generate story using Gemini Pro
                    story_prompt = f"""
                    Create a {genre} story based on this image description: {image_description}
                    The story should be approximately {length} words long and suitable for all ages.
                    Focus on {GENRE_THEMES.get(genre.lower(), 'engaging storytelling')}.
                    """
                    story_response = story_model.generate_content(story_prompt)
                    story = story_response.text

                    return jsonify({
                        'success': True,
                        'story': story,
                        'image_description': image_description
                    })
                
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    raise

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error processing image: {str(e)}'
            }), 429 if "429" in str(e) else 400

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error generating story: {str(e)}'
        }), 500

@app.route('/generate_frame', methods=['POST'])
def generate_frame():
    try:
        if not check_rate_limit():
            return jsonify({
                'success': False, 
                'error': 'Rate limit exceeded. Please wait and try again.'
            }), 429

        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({'success': False, 'error': 'No prompt provided'}), 400

        prompt = data['prompt']
        # Add family-friendly modifiers to prompt
        safe_prompt = f"family-friendly, child-appropriate, non-violent, cute, {prompt}"

        # Stability API configuration
        API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {os.getenv('STABILITY_API_KEY')}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # Create JSON payload exactly as in images.py
        payload = {
            "text_prompts": [
                {
                    "text": safe_prompt,
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

        # Generate image using Stability API with JSON
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload  # Use json parameter instead of files
        )
        
        if response.status_code == 200:
            result = response.json()
            if "artifacts" in result and len(result["artifacts"]) > 0:
                img_data = result["artifacts"][0]["base64"]
                return jsonify({
                    'success': True,
                    'image': f'data:image/png;base64,{img_data}'
                })
            else:
                raise Exception("No image generated in response")
        else:
            error_msg = response.json() if response.headers.get('content-type', '').startswith('application/json') else str(response.content)
            logger.error(f"Stability API error: {error_msg}")
            return jsonify({
                'success': False,
                'error': f'Image generation failed: {error_msg}'
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Frame generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
