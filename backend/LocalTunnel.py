# %% [markdown]
# https://colab.research.google.com/drive/1hc8G2WY_4P_0Tri-lZ0HmVDdX6MKy5LV?usp=sharing

# %%
!pip install torch torchvision diffusers transformers flask flask-cors xformers
!npm install -g localtunnel

import torch
from diffusers import AutoPipelineForText2Image
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import base64
import io
import os
from datetime import datetime
import logging
from threading import Thread
import time
import subprocess

# Basic Flask setup
app = Flask(__name__)
CORS(app)
logger = logging.getLogger(__name__)

# Global variables
pipeline = None

def setup_pipeline():
    pipeline = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True
    )
    pipeline.enable_xformers_memory_efficient_attention()
    return pipeline, None

def find_free_port(start_port=5001, max_attempts=10):
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find free port")

def setup_tunnel(port):
    try:
        timestamp = datetime.now().strftime('%H%M%S')
        subdomain = f"story-gen-{timestamp}"
        command = f'npx localtunnel --port {port} --subdomain {subdomain}'
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, text=True)
        
        for _ in range(30):  # 30 seconds timeout
            output = process.stdout.readline()
            if 'your url is:' in output.lower():
                return output.split('is: ')[-1].strip()
            time.sleep(1)
        raise Exception("Tunnel setup timeout")
    except Exception as e:
        print(f"Tunnel setup failed: {str(e)}")
        raise

@app.route('/generate_image', methods=['POST'])
def generate_image():
    global pipeline
    try:
        if pipeline is None:
            pipeline, _ = setup_pipeline()

        data = request.get_json()
        prompt = data.get('prompt', '')

        with torch.inference_mode():
            image = pipeline(
                prompt=prompt,
                num_inference_steps=1,
                guidance_scale=0.0,
                width=384,
                height=384
            ).images[0]

        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            'success': True,
            'image': f'data:image/jpeg;base64,{img_str}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'gpu_available': torch.cuda.is_available()
    })

@app.route('/pipeline_status', methods=['GET'])
def pipeline_status():
    return jsonify({
        'initialized': pipeline is not None
    })

if __name__ == '__main__':
    try:
        print("Initializing SDXL pipeline...")
        pipeline, _ = setup_pipeline()
        
        port = find_free_port()
        server = Thread(target=lambda: app.run(host='0.0.0.0', port=port))
        server.daemon = True
        server.start()
        
        tunnel_url = setup_tunnel(port)
        print(f"\nServer URL: {tunnel_url}")
        print("Copy this URL to use in the Story Generator app")
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        os.system('pkill -f lt')
    except Exception as e:
        print(f"\nError: {str(e)}")
        os.system('pkill -f lt')
        raise



