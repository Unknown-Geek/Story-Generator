import subprocess
import sys
import os
from pathlib import Path
import pip
from url_store import is_url_file_valid

def check_env_file():
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        print("Warning: .env file not found. Please create one with required API keys.")
        print("Required environment variables: GOOGLE_API_KEY, HUGGINGFACE_API_KEY, NGROK_AUTH_TOKEN")
        return False
    return True

def install_requirements():
    print("Installing required packages...")
    try:
        if not check_env_file():
            print("Please set up your .env file before continuing.")
            sys.exit(1)
        if not is_url_file_valid():
            print("Please ensure the URL file is valid before continuing.")
            sys.exit(1)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        # Verify gTTS installation specifically
        try:
            import gtts
            print("gTTS installed successfully!")
        except ImportError:
            print("Warning: gTTS installation may have failed. Attempting direct install...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "gTTS==2.3.2"])
        print("Installation completed!")
    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_requirements()
