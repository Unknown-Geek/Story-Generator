import streamlit as st
from PIL import Image
import requests
import io
import base64
import time
import os
from urllib.parse import urljoin, quote
import logging
import tempfile
from gtts import gTTS
from dotenv import load_dotenv
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Load environment variables and configure logging
load_dotenv()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.captureWarnings(True)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Try importing gTTS, fallback to pyttsx3 only if it fails
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    st.warning("gTTS not available. Using local TTS only.")

# Load environment variables
load_dotenv()

# Configure warnings and logging
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.captureWarnings(True)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Replace Unsplash API configuration with Pexels
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
PEXELS_API_URL = "https://api.pexels.com/v1/search"

def validate_url(url):
    """Validate and clean URL"""
    if not url:
        return None
    url = url.strip()
    # Remove any file:// prefix
    if url.startswith('file://'):
        url = url[7:]
    # Ensure proper http(s) prefix
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    # Remove any /generate_story suffix
    url = url.split('/generate_story')[0]
    return url

def process_image(image):
    """Process image with proper error handling and copying"""
    try:
        # Ensure image is valid
        if not isinstance(image, Image.Image):
            raise ValueError("Invalid image input")
            
        # Create a copy and convert to RGB
        img_copy = image.copy()
        if img_copy.mode != 'RGB':
            img_copy = img_copy.convert('RGB')
        
        # Resize if needed
        max_size = (1024, 1024)
        if img_copy.size[0] > max_size[0] or img_copy.size[1] > max_size[1]:
            logger.debug(f"Resizing image from {img_copy.size}")
            img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
            
        # Save to buffer with specific format
        buffered = io.BytesIO()
        img_copy.save(buffered, format="JPEG", quality=85)
        buffered.seek(0)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        logger.debug("Image processed successfully")
        return img_str
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise

def generate_narration(text, voice_settings):
    """Generate audio narration of the text using gTTS"""
    try:
        # Create a temporary file with a specific name
        temp_dir = tempfile.mkdtemp()
        temp_audio = os.path.join(temp_dir, 'narration.mp3')
        
        # Generate the audio
        tts = gTTS(
            text=text, 
            lang='en',
            tld=voice_settings['accent'],
            slow=(voice_settings['speed'] == 'slow')
        )
        
        # Save the audio file
        tts.save(temp_audio)
        
        # Verify the file exists and is readable
        if not os.path.exists(temp_audio):
            raise FileNotFoundError("Failed to create audio file")
            
        return temp_audio
            
    except Exception as e:
        logger.error(f"Error generating narration: {str(e)}")
        raise

def format_story(story):
    """Format story with proper paragraphs and punctuation"""
    sentences = story.split('.')
    paragraphs = []
    current_para = []
    
    for sentence in sentences:
        if not sentence.strip():
            continue
        current_para.append(sentence.strip() + '.')
        if len(current_para) >= 3:  # Group 3 sentences per paragraph
            paragraphs.append(' '.join(current_para))
            current_para = []
    
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    return '\n\n'.join(paragraphs)

def calculate_sentence_duration(sentence: str, speed_factor: float = 1.0) -> float:
    """Calculate approximate duration for each sentence based on word count"""
    words = len(sentence.split())
    # Average reading speed (words per second) adjusted by speed factor
    base_speed = 2.5  # words per second
    return (words / base_speed) * speed_factor

def get_relevant_image(sentence: str) -> str:
    """Get relevant image URL from Pexels based on sentence context"""
    try:
        # Extract key terms from sentence
        keywords = sentence.lower()
        for remove in ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to']:
            keywords = keywords.replace(f' {remove} ', ' ')
        
        # Search Pexels
        response = requests.get(
            PEXELS_API_URL,
            params={
                'query': keywords,
                'per_page': 1,
                'orientation': 'landscape'
            },
            headers={
                'Authorization': PEXELS_API_KEY
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['photos']:
                return data['photos'][0]['src']['large']
        
        # Fallback to abstract placeholder if no image found
        return f"https://picsum.photos/800/400?random={quote(keywords)}"
    except Exception as e:
        logger.error(f"Error fetching image: {str(e)}")
        return "https://picsum.photos/800/400"

def get_enhanced_animation_css() -> str:
    """Return enhanced CSS for animations"""
    return """
        <style>
        @keyframes fadeSlideIn {
            0% { opacity: 0; transform: translateY(30px) scale(0.9); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        
        @keyframes imageZoom {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        @keyframes textGlow {
            0% { text-shadow: 0 0 0px rgba(255,255,255,0); }
            50% { text-shadow: 0 0 20px rgba(255,255,255,0.5); }
            100% { text-shadow: 0 0 0px rgba(255,255,255,0); }
        }
        
        .story-container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: rgba(0,0,0,0.02);
            border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .sentence {
            font-size: 28px;
            line-height: 1.6;
            text-align: center;
            padding: 30px;
            margin: 20px 0;
            background: linear-gradient(145deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            animation: fadeSlideIn 1s ease-out, textGlow 3s ease-in-out infinite;
        }
        
        .image-container {
            position: relative;
            overflow: hidden;
            border-radius: 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
            transform-origin: center;
            animation: fadeSlideIn 1s ease-out, imageZoom 5s ease-in-out infinite;
        }
        
        .image-container img {
            width: 100%;
            height: auto;
            transition: transform 0.3s ease;
        }
        
        .image-container:hover img {
            transform: scale(1.05);
        }
        </style>
    """

def display_interactive_story(story: str, audio_file: str):
    """Display story interactively with synchronized animations"""
    try:
        # Verify audio file exists and is readable
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        # Create story container
        st.markdown(get_enhanced_animation_css(), unsafe_allow_html=True)
        story_container = st.empty()
        
        # Display audio player first and wait for it to be ready
        audio_placeholder = st.empty()
        with open(audio_file, 'rb') as f:
            audio_bytes = f.read()
            audio_placeholder.audio(audio_bytes, format='audio/mp3')

        # Split story into sentences
        sentences = [s.strip() + '.' for s in story.split('.') if s.strip()]
        
        # Display sentences with images
        for sentence in sentences:
            image_url = get_relevant_image(sentence)
            html = f"""
            <div class="story-container">
                <div class="sentence">{sentence}</div>
                <div class="image-container">
                    <img src="{image_url}" alt="Story visualization">
                </div>
            </div>
            """
            story_container.markdown(html, unsafe_allow_html=True)
            time.sleep(3)  # Fixed delay per sentence

    except Exception as e:
        st.error(f"Error displaying story: {str(e)}")
        st.write(story)  # Fallback to simple text display

def main():
    # Initialize session state
    if 'story' not in st.session_state:
        st.session_state.story = None
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None
    if 'should_play' not in st.session_state:
        st.session_state.should_play = False
    if 'narration_settings' not in st.session_state:
        st.session_state.narration_settings = None

    st.title("Story Generator (with Narration)")
    
    # Manual URL input with validation
    colab_url = st.sidebar.text_input("AI Server URL", 
                                     placeholder="Enter the URL from Colab notebook")
    
    colab_url = validate_url(colab_url)
    if not colab_url:
        st.error("Please enter a valid AI server URL from your Colab notebook")
        return
    
    # Genre and Length selection
    col1, col2 = st.columns(2)
    with col1:
        genre = st.selectbox(
            "Select a story genre:",
            ["Fantasy", "Adventure", "Romance", "Horror", "Mystery", "Moral Story"]
        )
    with col2:
        story_length = st.selectbox(
            "Select story length:",
            ["Short (200 words)", "Medium (500 words)", "Long (1000 words)"]
        )
        # Extract word count from selection
        length = int(story_length.split('(')[1].split()[0])
    
    # Image upload
    uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    
    # Voice settings in sidebar
    st.sidebar.markdown("### Narration Settings")
    
    voice_type = st.sidebar.selectbox(
        "Select Voice Type:",
        [
            "US English (com)",
            "UK English (co.uk)", 
            "Indian English (co.in)",
            "Australian English (com.au)"
        ]
    )
    
    # Simplified accent mapping
    accent = voice_type.split('(')[1].strip(')')
    
    speed = st.sidebar.select_slider(
        "Speech Speed",
        options=['slow', 'normal', 'fast'],
        value='normal'
    )

    # Store current voice settings
    speed_factors = {'slow': 1.5, 'normal': 1.0, 'fast': 0.7}
    voice_settings = {
        'accent': accent,
        'speed': speed,
        'speed_factor': speed_factors[speed]
    }

    # Main content area
    col1, col2 = st.columns([2, 1])
    with col1:
        story_button = st.button("Generate Story")
    with col2:
        # Only show play button if audio exists
        if (st.session_state.audio_file and 
            os.path.exists(st.session_state.audio_file)):
            try:
                # Read audio file once
                with open(st.session_state.audio_file, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                st.audio(audio_bytes, format='audio/mp3')
            except Exception as e:
                st.error(f"Error loading audio: {str(e)}")

    # Display existing story
    if st.session_state.story:
        st.write("### Your Story:")
        st.write(st.session_state.story)

    # Handle story generation
    if story_button:
        if uploaded_image is None:
            st.error("Please upload an image to generate a story.")
            return
        
        with st.spinner('Generating story...'):
            try:
                # Save current narration settings to compare later
                st.session_state.narration_settings = {
                    'accent': accent,
                    'speed': speed
                }
                
                # Process uploaded image
                image = Image.open(uploaded_image)
                image_str = process_image(image)
                
                # Make request
                response = requests.post(
                    f"{colab_url}/generate_story",
                    json={
                        'image': image_str,
                        'genre': genre,
                        'length': length  # Pass the actual word count
                    },
                    timeout=300,  # Increase timeout to 300 seconds
                    verify=False
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        story = result.get('story')
                        if story:
                            st.session_state.story = format_story(story)
                            
                            # Generate new narration
                            with st.spinner('Generating narration...'):
                                try:
                                    # Clean up old audio file
                                    if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
                                        os.unlink(st.session_state.audio_file)

                                    # Generate new audio
                                    st.session_state.audio_file = generate_narration(
                                        st.session_state.story,
                                        voice_settings
                                    )

                                    # Display generated audio
                                    if os.path.exists(st.session_state.audio_file):
                                        with open(st.session_state.audio_file, 'rb') as audio_file:
                                            audio_bytes = audio_file.read()
                                            st.audio(audio_bytes, format='audio/mp3')
                                            st.session_state.should_play = True
                                    else:
                                        st.error("Failed to generate audio file")
                                    
                                except Exception as e:
                                    st.error(f"Failed to generate narration: {str(e)}")
                                    st.session_state.audio_file = None

                            # Display the story
                            st.write("### Your Story:")
                            st.write(st.session_state.story)
                            
                            # No rerun needed here as we want to display immediately
                        else:
                            st.error("No story was generated")
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")
                else:
                    st.error(f"Failed to generate story: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Separate audio player for existing audio
    if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
        st.sidebar.markdown("### Story Narration")
        with open(st.session_state.audio_file, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            st.sidebar.audio(audio_bytes, format='audio/mp3')

    # Display story without animation if audio isn't playing
    if st.session_state.story and not st.session_state.should_play:
        st.write("### Your Story:")
        st.write(st.session_state.story)
    # Only use interactive display when audio should play
    elif st.session_state.story and st.session_state.audio_file and st.session_state.should_play:
        display_interactive_story(st.session_state.story, st.session_state.audio_file)
        st.session_state.should_play = False  # Reset play flag after display

if __name__ == '__main__':
    main()
