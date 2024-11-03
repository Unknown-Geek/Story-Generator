import json

URL_FILE = 'ngrok_url.json'

def save_url(url):
    with open(URL_FILE, 'w') as f:
        json.dump({'url': url}, f)

def get_url():
    try:
        with open(URL_FILE, 'r') as f:
            data = json.load(f)
            return data.get('url')
    except:
        return None
