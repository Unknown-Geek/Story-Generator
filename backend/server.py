from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
import io
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

# Configure APIs
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
            
            # Ensure image_data is properly formatted
            if ',' in image_data:
                # Remove data URL prefix if present
                image_data = image_data.split(',', 1)[1]
            
            # Decode base64 with error handling
            try:
                image_bytes = base64.b64decode(image_data)
            except Exception as decode_error:
                logger.error(f"Base64 decode error: {str(decode_error)}")
                return jsonify({'success': False, 'error': 'Invalid image format'}), 400
            
            if not image_bytes:
                return jsonify({'success': False, 'error': 'Empty image data'}), 400
                
            logger.debug(f"Decoded image bytes: {len(image_bytes)} bytes")
            
            # Create a new BytesIO object and write the bytes
            image_buffer = io.BytesIO(image_bytes)
            image_buffer.seek(0)
            
            # Open the image with error handling
            try:
                image = Image.open(image_buffer)
                image.verify()  # Verify image integrity
                image_buffer.seek(0)  # Reset buffer after verify
                image = Image.open(image_buffer)  # Reopen after verify
            except Exception as img_error:
                logger.error(f"Image open error: {str(img_error)}")
                return jsonify({'success': False, 'error': 'Invalid or corrupted image'}), 400
            
            logger.debug(f"Opened image: mode={image.mode}, size={image.size}")
            
            # Validate image size
            if image.size[0] < 1 or image.size[1] < 1:
                return jsonify({'success': False, 'error': 'Invalid image dimensions'}), 400
            
            # Create a new RGB image and paste the original onto it
            try:
                if image.mode in ('RGBA', 'LA'):
                    new_image = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'RGBA':
                        if len(image.split()) >= 4:  # Ensure alpha channel exists
                            new_image.paste(image, mask=image.split()[3])
                        else:
                            new_image.paste(image)
                    else:
                        if len(image.split()) >= 2:  # Ensure alpha channel exists
                            new_image.paste(image, mask=image.split()[1])
                        else:
                            new_image.paste(image)
                    image = new_image
                    logger.debug("Converted image to RGB from RGBA/LA")
                elif image.mode != 'RGB':
                    new_image = Image.new('RGB', image.size, (255, 255, 255))
                    new_image.paste(image)
                    image = new_image
                    logger.debug("Converted image to RGB from other mode")
            except Exception as convert_error:
                logger.error(f"Image conversion error: {str(convert_error)}")
                return jsonify({'success': False, 'error': 'Failed to process image format'}), 400
            
            # Rest of the existing code...
            
            # Updated prompt generation with error handling
            try:
                image_prompt = "Describe the objects and scene in this image with detail and context."
                image_response = vision_model.generate_content([image_prompt, image])
                if not image_response or not hasattr(image_response, 'text'):
                    return jsonify({'success': False, 'error': 'Failed to analyze image'}), 500
                    
                image_description = image_response.text
                logger.debug(f"Image description: {image_description}")
                
                # Rest of story generation...
                
            except Exception as vision_error:
                logger.error(f"Vision model error: {str(vision_error)}")
                return jsonify({'success': False, 'error': 'Failed to analyze image'}), 500
                
        except Exception as img_error:
            logger.error(f"Image processing error: {str(img_error)}")
            return jsonify({'success': False, 'error': str(img_error)}), 400
            
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generate_frame', methods=['POST', 'OPTIONS'])
def generate_frame():
    # Handle OPTIONS request
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Max-Age', '3600')
        return response

    # Regular POST request handling
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
        API_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"
        headers = {
            "Authorization": f"Bearer {os.getenv('STABILITY_API_KEY')}",
            "Accept": "image/*",
            "Content-Type": "application/json"
        }
        
        # Request body
        request_data = {
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
            "steps": 1,
        }

        # Generate image using Stability API
        response = requests.post(API_URL, headers=headers, json=request_data)
        
        if response.status_code == 200:
            # Convert to base64
            img_data = response.content
            img_str = base64.b64encode(img_data).decode()
            return jsonify({
                'success': True,
                'image': f'data:image/webp;base64,{img_str}'
            })
        else:
            error_msg = response.json() if 'application/json' in response.headers.get('content-type', '') else str(response.content)
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
