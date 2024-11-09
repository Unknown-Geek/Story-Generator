import json
import os
from pathlib import Path

# Get absolute path for URL storage
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
URL_FILE = os.path.join(SCRIPT_DIR, 'ngrok_url.json')

def save_url(url):
    try:
        print(f"DEBUG: Attempting to save URL: {url}")
        if url is None:
            print("DEBUG: URL is None, not saving")
            return False
            
        # Ensure directory exists
        Path(SCRIPT_DIR).mkdir(parents=True, exist_ok=True)
        
        # Save URL with absolute path
        absolute_url = url if url.startswith('http') else f"https://{url}"
        with open(URL_FILE, 'w') as f:
            json.dump({'url': absolute_url}, f, indent=2)
            f.flush()
        print(f"DEBUG: URL saved to {URL_FILE}: {absolute_url}")
        
        # Verify save was successful
        return verify_saved_url()
    except Exception as e:
        print(f"DEBUG: Error saving URL: {str(e)}")
        return False

def get_url():
    try:
        if not os.path.exists(URL_FILE):
            print(f"DEBUG: URL file not found at {URL_FILE}")
            return None
            
        with open(URL_FILE, 'r') as f:
            data = json.load(f)
            url = data.get('url')
            print(f"DEBUG: URL file contents: {data}")
            if url and verify_saved_url():
                print(f"DEBUG: Retrieved valid URL: {url}")
                return url
            else:
                print("DEBUG: URL is invalid or None")
                return None
    except Exception as e:
        print(f"DEBUG: Error reading URL: {str(e)}")
        return None

def verify_saved_url():
    try:
        with open(URL_FILE, 'r') as f:
            data = json.load(f)
            saved_url = data.get('url')
            if saved_url and isinstance(saved_url, str):
                if saved_url.startswith('http'):
                    print(f"DEBUG: Verified saved URL: {saved_url}")
                    return True
        return False
    except Exception as e:
        print(f"DEBUG: Error verifying URL: {str(e)}")
        return False

def is_url_file_valid():
    try:
        if not os.path.exists(URL_FILE):
            return False
        with open(URL_FILE, 'r') as f:
            data = json.load(f)
            url = data.get('url')
            if url and isinstance(url, str) and url.startswith('http'):
                return True
        return False
    except Exception as e:
        print(f"DEBUG: Error checking URL file: {str(e)}")
        return False

def debug_url_file():
    try:
        if not os.path.exists(URL_FILE):
            print(f"DEBUG: URL file not found at {URL_FILE}")
            return None
            
        with open(URL_FILE, 'r') as f:
            data = f.read()
            print(f"DEBUG: URL file raw contents: {data}")
            try:
                parsed = json.loads(data)
                print(f"DEBUG: URL file parsed contents: {parsed}")
            except:
                print("DEBUG: Failed to parse URL file as JSON")
    except Exception as e:
        print(f"DEBUG: Error reading URL file: {str(e)}")

# Initialize URL file if it doesn't exist
if not os.path.exists(URL_FILE):
    save_url(None)
