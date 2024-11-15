
import axios from 'axios';

const api = {
  generateStory: async (serverUrl, imageData, genre, length) => {
    try {
      const response = await axios.post(
        `${serverUrl}/generate_story`,
        {
          image: imageData,
          genre,
          length
        },
        {
          timeout: 300000,
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to generate story');
    }
  },

  textToSpeech: async (text, voiceSettings) => {
    // Implementation will depend on your TTS service
    // This is a placeholder for the gTTS functionality
    throw new Error('TTS not implemented in frontend');
  }
};

export default api;