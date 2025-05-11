/**
 * API Service for Story Generator
 * Handles communication with the backend server for story generation
 * and related services.
 */
import axios from "axios";

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL ||
  "https://story-generator-api.onrender.com";

const api = {
  generateStory: async (images, genre, length) => {
    try {
      // Check if images is an array or single image
      const imageData = Array.isArray(images) ? images : [images];

      const response = await axios.post(
        `${BACKEND_URL}/generate_story`,
        {
          images: imageData,
          genre,
          length,
        },
        {
          timeout: 300000, // 5 minutes for processing multiple images
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.error || "Failed to generate story"
      );
    }
  },
};

export default api;
