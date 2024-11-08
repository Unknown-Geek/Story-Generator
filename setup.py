import subprocess
import sys
import pip

def install_requirements():
    print("Installing required packages...")
    try:
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
