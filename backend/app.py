from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from gtts import gTTS
import os
import time
from pathlib import Path
import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit default ports
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"]
    }
})

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Use direct ngrok URL
COLAB_URL = "https://f3e7-35-190-149-187.ngrok-free.app"

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure requests session with retries
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

@app.route('/generate_story', methods=['POST'])
def generate_story():
    try:
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'message': 'No image provided'}), 400
        
        files = {'image': request.files['image']}
        response = session.post(
            f"{COLAB_URL}/generate_story",
            files=files,
            verify=False,
            timeout=30,
            allow_redirects=True
        )
        
        if not response.ok:
            return jsonify({'status': 'error', 'message': 'Colab server error'}), response.status_code
            
        result = response.json()
        
        if result['status'] == 'success':
            story = result['story']
            audio_file = f"story_{int(time.time())}.mp3"
            audio_path = OUTPUT_DIR / audio_file
            
            tts = gTTS(text=story, lang='en')
            tts.save(str(audio_path))
            
            result['audio'] = audio_file
            return jsonify(result)
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5001,
        debug=True,
        ssl_context=None  # Disable SSL for local development
    )
