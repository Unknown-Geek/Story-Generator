from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import io
import base64

app = Flask(__name__)
CORS(app)

@app.route('/generate_story', methods=['POST'])
def generate_story():
    try:
        # Get image and genre from request
        image_file = request.files['file']
        genre = request.form['genre']
        
        # Convert image to base64
        image_data = base64.b64encode(image_file.read()).decode()
        
        # Send to Colab notebook
        payload = {
            'image': image_data,
            'genre': genre
        }
        
        response = requests.post(colab_url, json=payload)
        
        if response.status_code == 200:
            return jsonify({'story': response.json()['story']})
        else:
            return jsonify({'error': 'Failed to generate story'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
