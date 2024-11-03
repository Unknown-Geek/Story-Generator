import streamlit as st
from PIL import Image
import requests
import io
import base64
from url_store import get_url

def main():
    st.title("Granny's Tales - Story Generator")
    
    # Automatically get Colab URL
    colab_url = get_url()
    if not colab_url:
        st.error("AI server URL not found. Please ensure the server is running.")
        return
    
    # Genre selection
    genre = st.selectbox(
        "Select a story genre:",
        ["Fantasy", "Adventure", "Romance", "Horror", "Mystery", "Moral Story"]
    )
    
    # Image upload
    uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    
    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        st.image(image, caption='Uploaded Image', use_column_width=True)
        
        if st.button("Generate Story"):
            with st.spinner('Generating your story...'):
                try:
                    # Convert image to base64
                    buffered = io.BytesIO()
                    image.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    # Send to Colab
                    payload = {
                        'image': f'data:image/jpeg;base64,{img_str}',
                        'genre': genre
                    }
                    
                    response = requests.post(colab_url, json=payload)
                    
                    if response.status_code == 200 and response.json().get('success', False):
                        story = response.json()['story']
                        st.success("Story generated successfully!")
                        st.write("### Your Story:")
                        st.write(story)
                    else:
                        st.error("Failed to generate story. Please check your Colab URL and try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if __name__ == '__main__':
    main()
