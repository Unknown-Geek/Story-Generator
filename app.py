import streamlit as st
from PIL import Image
import requests
import io
import base64

def main():
    st.title("Granny's Tales - Story Generator")
    
    # Manual URL input
    colab_url = st.sidebar.text_input("AI Server URL", 
                                     placeholder="Enter the URL from Colab notebook")
    
    if not colab_url:
        st.error("Please enter the AI server URL from your Colab notebook")
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
                    response = requests.post(
                        colab_url,
                        json={
                            'image': f'data:image/jpeg;base64,{img_str}',
                            'genre': genre
                        },
                        timeout=30  # Increase timeout for model processing
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            story = result['story']
                            st.success("Story generated successfully!")
                            st.write("### Your Story:")
                            st.write(story)
                        else:
                            st.error(f"Error: {result.get('error', 'Unknown error')}")
                    else:
                        st.error(f"Failed to generate story. Status code: {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    st.error("Request timed out. The server took too long to respond.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Network error: {str(e)}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if __name__ == '__main__':
    main()
