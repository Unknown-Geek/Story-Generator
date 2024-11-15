from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import io
import base64
import logging
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from PIL import Image
import os
import google.generativeai as genai
import tempfile

# Disable SSL warning using both methods
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.captureWarnings(True)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Create the models
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# Use gemini-1.5-pro for vision and text processing
vision_model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)

# Use gemini-pro for story generation
story_model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config,
)

app = Flask(__name__)
CORS(app)

# Default Colab URL - should be updated with actual URL when known
colab_url = None

@app.route('/set_colab_url', methods=['POST'])
def set_colab_url():
    global colab_url
    data = request.json
    colab_url = data.get('url')
    return jsonify({'success': True})

@app.route('/generate_story', methods=['POST'])
def generate_story():
    try:
        data = request.get_json()
        if not data:
            logger.debug("No data received in request")
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        image_data = data.get('image', '')
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[-1]
        
        genre = data.get('genre')
        word_count = data.get('length', 200)  # Get word count from request, default to 200
        
        if not image_data or not genre:
            logger.debug("Missing image or genre in request data")
            return jsonify({'success': False, 'error': 'Missing image or genre'}), 400
        
        try:
            logger.debug("Processing image data")
            # Process image with explicit copying
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            logger.debug(f"Image mode: {image.mode}")
            
            # Handle image conversion safely
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image_copy = background
                logger.debug("Converted image from RGBA/LA to RGB")
            else:
                image_copy = image.convert('RGB')
                logger.debug("Converted image to RGB")
            
            # Resize if needed
            max_size = (1024, 1024)
            if image_copy.size[0] > max_size[0] or image_copy.size[1] > max_size[1]:
                logger.debug(f"Resizing image from {image_copy.size}")
                image_copy.thumbnail(max_size, Image.LANCZOS)
            
            # Generate image description using vision model
            image_prompt = "Describe what you see in this image concisely."
            image_response = vision_model.generate_content([image_prompt, image_copy])
            image_description = image_response.text
            logger.debug(f"Image description: {image_description}")
            
            # Generate story using the text model
            story_prompt = f"""Write a {genre} story appropriate for all ages. Base it on this scene: {image_description}
            Requirements:
            - Length: approximately {word_count} words
            - Age-appropriate content
            - Clear narrative structure
            - Engaging and descriptive language
            - Positive message or moral"""
            
            story_response = story_model.generate_content(story_prompt)
            
            if story_response.text:
                logger.debug("Story generated successfully")
                return jsonify({
                    'success': True,
                    'story': story_response.text
                })
            else:
                logger.debug("Story generation failed")
                return jsonify({
                    'success': False, 
                    'error': 'Story generation failed. Please try again.'
                }), 500
            
        except Exception as img_error:
            logger.error(f"Image processing error: {str(img_error)}")
            return jsonify({'success': False, 'error': f'Image processing error: {str(img_error)}'}), 400
            
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
