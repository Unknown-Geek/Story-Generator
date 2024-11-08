from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import io
import base64
import logging
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from PIL import Image

# Disable SSL warning using both methods
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.captureWarnings(True)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
            
            # Create a copy before conversion
            image_copy = image.copy()
            if image_copy.mode != 'RGB':
                logger.debug(f"Converting image from {image_copy.mode} to RGB")
                image_copy = image_copy.convert('RGB')
            
            buffered = io.BytesIO()
            image_copy.save(buffered, format="JPEG")
            processed_image = base64.b64encode(buffered.getvalue()).decode()
            
            payload = {
                'image': processed_image,
                'genre': genre
            }
            logger.debug("Image processed successfully")
            
        except Exception as img_error:
            logger.error(f"Image processing error: {str(img_error)}")
            return jsonify({'success': False, 'error': f'Image processing error: {str(img_error)}'}), 400
        
        response = requests.post(
            colab_url.rstrip('/'),
            json=payload,
            verify=False,
            timeout=120  # Increase timeout to 120 seconds
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'story': response.json().get('story', 'No story generated')
            })
        else:
            return jsonify({
                'success': False, 
                'error': f'Colab server error: {response.text}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
