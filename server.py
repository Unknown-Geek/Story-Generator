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

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
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

def upload_to_gemini(image_bytes, mime_type="image/jpeg"):
    """Uploads the given image bytes to Gemini."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpeg") as temp_file:
        temp_file.write(image_bytes)
        temp_file_path = temp_file.name
    file = genai.upload_file(temp_file_path, mime_type=mime_type)
    os.remove(temp_file_path)
    return file

@app.route('/generate_story', methods=['POST'])
def generate_story():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        image_data = data.get('image', '')
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[-1]
        
        genre = data.get('genre')
        
        if not image_data or not genre:
            return jsonify({'success': False, 'error': 'Missing image or genre'}), 400
        
        try:
            # Process image with explicit copying
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Handle image conversion safely
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image_copy = background
            else:
                image_copy = image.convert('RGB')
            
            # Resize if needed
            max_size = (1024, 1024)
            if image_copy.size[0] > max_size[0] or image_copy.size[1] > max_size[1]:
                image_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            buffered = io.BytesIO()
            image_copy.save(buffered, format="JPEG", quality=85)
            processed_image = buffered.getvalue()
            
            # Upload image to Gemini
            gemini_file = upload_to_gemini(processed_image)
            
            # Generate story using Gemini
            prompt = f"Generate a {genre} story based on the objects in the provided image."
            response = model.generate_content([
                prompt,
                "Image: ",
                gemini_file,
                "Story: "
            ])
            
            if response.text:
                return jsonify({
                    'success': True,
                    'story': response.text
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': 'Story generation failed. Please try again with different parameters.'
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
