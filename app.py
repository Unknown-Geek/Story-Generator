import streamlit as st
from PIL import Image
import requests
import io
import base64
from urllib.parse import urljoin
import logging
import pyttsx3
import tempfile
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Try importing gTTS, fallback to pyttsx3 only if it fails
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    st.warning("gTTS not available. Using local TTS only.")

# Configure warnings and logging
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.captureWarnings(True)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def validate_url(url):
    if not url:
        return None
    url = url.strip()  # Remove any leading/trailing whitespace
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
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

def generate_narration(text, voice_option="gTTS", voice_settings=None):
    """Generate audio narration of the text"""
    try:
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        
        if voice_option == "gTTS" and GTTS_AVAILABLE:
            # Google Text-to-Speech
            tts = gTTS(text=text, lang=voice_settings.get('lang', 'en'), slow=voice_settings.get('slow', False))
            tts.save(temp_audio.name)
        else:
            # Local TTS with pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            # Set voice
            if voice_settings and voice_settings.get('voice'):
                for voice in voices:
                    if voice_settings['voice'] in voice.name:
                        engine.setProperty('voice', voice.id)
                        break
            
            # Set speed and volume
            speed = voice_settings.get('speed', 1.0) if voice_settings else 1.0
            volume = voice_settings.get('volume', 0.8) if voice_settings else 0.8
            
            engine.setProperty('rate', int(engine.getProperty('rate') * speed))
            engine.setProperty('volume', volume)
            
            # Generate audio
            engine.save_to_file(text, temp_audio.name)
            engine.runAndWait()
            
        return temp_audio.name
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

def main():
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
            ["Short (200 words)", "Medium (400 words)", "Long (600 words)"]
        )
        # Extract length value
        length = story_length.split()[0].lower()
    
    # Voice options with more controls
    st.sidebar.markdown("### Narration Settings")
    voice_option = st.sidebar.radio(
        "Select Voice Engine:",
        ["gTTS (Google)", "Local TTS"] if GTTS_AVAILABLE else ["Local TTS"]
    )
    
    voice_settings = {}
    if voice_option == "Local TTS":
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        voice_names = [voice.name for voice in voices]
        voice_settings['voice'] = st.sidebar.selectbox("Select Voice:", voice_names)
        voice_settings['speed'] = st.sidebar.slider("Speech Speed:", 0.5, 2.0, 1.0, 0.1)
        voice_settings['volume'] = st.sidebar.slider("Volume:", 0.0, 1.0, 0.8, 0.1)
    else:
        voice_settings['lang'] = st.sidebar.selectbox("Select Language:", ["en-US", "en-GB", "en-AU"])
        voice_settings['slow'] = st.sidebar.checkbox("Slow Mode", False)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        story_button = st.button("Generate Story")
    with col2:
        auto_narrate = st.checkbox("Auto-Narrate", True)
    
    if story_button:
        with st.spinner('Generating story...'):
            try:
                # Make request
                base_url = colab_url.rstrip('/').split('/generate_story')[0]
                response = requests.post(
                    f"{base_url}/generate_story",
                    json={
                        'genre': genre,
                        'length': length  # Send selected length
                    },
                    timeout=120,  # Increase timeout to 120 seconds
                    verify=False
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        story = result.get('story')
                        if story:
                            # Format and display story
                            formatted_story = format_story(story)
                            st.success("Story generated successfully!")
                            st.write("### Your Story:")
                            st.write(formatted_story)
                            
                            # Generate narration if auto-narrate is enabled
                            if auto_narrate:
                                with st.spinner('Generating narration...'):
                                    try:
                                        audio_file = generate_narration(
                                            formatted_story,
                                            "gTTS" if voice_option == "gTTS (Google)" else "Local",
                                            voice_settings
                                        )
                                        
                                        # Audio player with controls
                                        st.write("### Story Narration")
                                        audio_player = st.audio(audio_file, format='audio/mp3')
                                        
                                        # Cleanup
                                        os.unlink(audio_file)
                                        
                                    except Exception as e:
                                        st.error(f"Failed to generate narration: {str(e)}")
                            else:
                                if st.button("Generate Narration"):
                                    with st.spinner('Generating narration...'):
                                        try:
                                            audio_file = generate_narration(
                                                formatted_story,
                                                "gTTS" if voice_option == "gTTS (Google)" else "Local",
                                                voice_settings
                                            )
                                            
                                            # Audio player with controls
                                            st.write("### Story Narration")
                                            audio_player = st.audio(audio_file, format='audio/mp3')
                                            
                                            # Cleanup
                                            os.unlink(audio_file)
                                        except Exception as e:
                                            st.error(f"Failed to generate narration: {str(e)}")
                        else:
                            st.error("No story was generated")
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")
                else:
                    st.error(f"Failed to generate story: {response.text}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == '__main__':
    main()
