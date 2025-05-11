/**
 * Main App Component for Story Generator
 * This component handles image uploads, story generation, and displaying
 * the generated stories with audio narration.
 */
import React, { useState, useRef, useEffect, useCallback } from "react";
import CollapsibleStory from "./components/CollapsibleStory";
import AudioPlayer from "./components/AudioPlayer";
import { Analytics } from "@vercel/analytics/react";
import { X } from "lucide-react";
import api from "./services/api";

const GENRES = [
  "Fantasy",
  "Adventure",
  "Romance",
  "Horror",
  "Mystery",
  "Moral Story",
];
const STORY_LENGTHS = [
  { label: "Short (200 words)", value: 200 },
  { label: "Medium (500 words)", value: 500 },
  { label: "Long (1000 words)", value: 1000 },
];

const VOICE_TYPES = [
  { label: "US English", value: "com" },
  { label: "UK English", value: "co.uk" },
  { label: "Indian English", value: "co.in" },
  { label: "Australian English", value: "com.au" },
];

// Update the BACKEND_URL constant
// const BACKEND_URL =
//   process.env.NODE_ENV === "development"
//     ? "http://localhost:5000"
//     : process.env.REACT_APP_API_URL;

const App = () => {
  const [images, setImages] = useState([]);
  const [imagePreview, setImagePreview] = useState("");
  const [imagePreviews, setImagePreviews] = useState([]);
  const [genre, setGenre] = useState(GENRES[0]);
  const [length, setLength] = useState(STORY_LENGTHS[0].value);
  const [story, setStory] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [voiceSettings, setVoiceSettings] = useState({
    accent: VOICE_TYPES[0].value,
    speed: "normal",
  });
  const [storyDuration, setStoryDuration] = useState(0);
  const [currentNarrationTime, setCurrentNarrationTime] = useState(0);
  const [generationCompleted, setGenerationCompleted] = useState(false);
  const [audioSrc, setAudioSrc] = useState(null);

  const handleImageUpload = (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    // Display previews of all selected images
    setImages((prevImages) => [...prevImages, ...files]);

    // Create previews for all images
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreviews((prev) => [...prev, reader.result]);

        // Also set the first image as the main preview for the StopMotion component
        if (imagePreviews.length === 0) {
          setImagePreview(reader.result);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index) => {
    setImages((prevImages) => prevImages.filter((_, i) => i !== index));
    setImagePreviews((prevPreviews) =>
      prevPreviews.filter((_, i) => i !== index)
    );

    // Update the main preview if needed
    if (index === 0 && imagePreviews.length > 1) {
      setImagePreview(imagePreviews[1]);
    } else if (imagePreviews.length === 1) {
      setImagePreview("");
    }
  };
  const generateStory = async () => {
    if (imagePreviews.length === 0) {
      setError("Please upload at least one image");
      return;
    }

    setLoading(true);
    setError("");
    setGenerationCompleted(false);
    setStory(null);
    setAudioSrc(null);

    try {
      // Convert all images to base64
      const base64Images = imagePreviews.map(
        (preview) => preview.split(",")[1]
      );

      const storyResponse = await api.generateStory(
        base64Images,
        genre,
        length
      );

      setStory(storyResponse.story);
      setAudioSrc(storyResponse.audioUrl);
      setGenerationCompleted(true);
    } catch (err) {
      console.error("Error generating story:", err);
      if (err.name === "AbortError") {
        setError("Request timed out. Please try again.");
      } else if (!navigator.onLine) {
        setError("No internet connection. Please check your network.");
      } else {
        setError(
          err.response?.data?.error ||
            "Failed to generate story. Please try again."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  // Cleanup effects
  useEffect(() => {
    return () => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_50%_50%,var(--tw-gradient-stops))] from-dark-bg via-[#000510] to-[#000510] py-8 px-4 relative">
      <div className="max-w-4xl mx-auto relative z-10">
        <h1
          className="text-5xl font-bold text-center text-white mb-12 text-shadow-neon"
          style={{
            fontFamily: "'Base Neue', 'Eurostile', 'Bank Gothic', sans-serif",
          }}
        >
          Story Generator
        </h1>
        {/* Settings Panel */}
        <div className="bg-[rgba(10,10,31,0.8)] border border-neon-blue/10 rounded-lg p-6 mb-8 backdrop-blur-md shadow-neon">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <select
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
            >
              {GENRES.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>

            <select
              value={length}
              onChange={(e) => setLength(Number(e.target.value))}
              className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
            >
              {STORY_LENGTHS.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>{" "}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <select
              value={voiceSettings.accent}
              onChange={(e) =>
                setVoiceSettings((prev) => ({
                  ...prev,
                  accent: e.target.value,
                }))
              }
              className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
            >
              {VOICE_TYPES.map((v) => (
                <option key={v.value} value={v.value}>
                  {v.label}
                </option>
              ))}
            </select>

            <select
              value={voiceSettings.speed}
              onChange={(e) =>
                setVoiceSettings((prev) => ({ ...prev, speed: e.target.value }))
              }
              className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
            >
              <option value="slow">Slow</option>
              <option value="normal">Normal</option>
              <option value="fast">Fast</option>
            </select>
          </div>
        </div>
        {/* Image Upload */}
        <div className="mb-8">
          <input
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
            id="image-upload"
            multiple
          />
          <label
            htmlFor="image-upload"
            className="block w-full p-6 border-2 border-dashed border-neon-blue/30 rounded-lg text-center text-white cursor-pointer hover:border-neon-blue/50 transition-all bg-dark-bg/30 backdrop-blur-sm"
          >
            {" "}
            {imagePreviews.length > 0 ? (
              <div className="space-y-4">
                <div className="relative">
                  <div
                    className="flex overflow-x-auto pb-2 gap-3 hide-scrollbar px-1 py-1 scroll-smooth"
                    style={{ maxWidth: "100%" }}
                  >
                    {imagePreviews.map((preview, index) => (
                      <div key={index} className="relative group flex-shrink-0">
                        <img
                          src={preview}
                          alt={`Preview ${index + 1}`}
                          className="h-16 w-24 object-cover rounded-md shadow-neon border border-neon-blue/20"
                        />
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            removeImage(index);
                          }}
                          className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-0.5 opacity-70 hover:opacity-100 transition-opacity"
                        >
                          <X size={8} />
                        </button>
                      </div>
                    ))}
                  </div>
                  {imagePreviews.length > 3 && (
                    <div className="absolute right-0 top-0 bottom-0 w-10 bg-gradient-to-l from-dark-bg/80 to-transparent pointer-events-none flex items-center justify-end" />
                  )}
                </div>
                <p className="text-neon-blue/70 text-sm">
                  Click to add more images
                </p>
              </div>
            ) : (
              <div className="py-8">
                <p className="text-lg mb-2">Click to upload images</p>
                <p className="text-sm text-neon-blue/70">
                  You can select multiple images
                </p>
              </div>
            )}
          </label>
        </div>
        {/* Error Message */}
        {error && (
          <div className="text-red-400 text-center mb-4 bg-red-900/20 border border-red-500/20 rounded-lg p-3">
            {error}
          </div>
        )}
        {/* Generate Button */}
        <button
          onClick={generateStory}
          disabled={loading}
          className="glass-button w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="loading-spinner" />
              <span>Generating...</span>
            </>
          ) : (
            "Generate Story"
          )}
        </button>{" "}
        {/* Story Display */}
        {story && (
          <div className="story-container mt-8 animate-fadeIn">
            <AudioPlayer
              story={story}
              voiceSettings={voiceSettings}
              onTimeUpdate={setCurrentNarrationTime}
              initialTime={currentNarrationTime}
            />
            <CollapsibleStory story={story} />
          </div>
        )}
      </div>
      <Analytics />
      <div className="fixed bottom-0 left-0 w-full pointer-events-none">
        {/* Subtle white core glow */}
        <div className="absolute bottom-0 w-full h-[10px] bg-gradient-to-t from-white to-transparent blur-[6px]" />

        {/* Layered soft blue glows */}
        <div className="absolute bottom-0 w-full h-[30px] bg-gradient-to-t from-neon-blue/25 via-neon-blue/10 to-transparent blur-[10px]" />
        <div className="absolute bottom-0 w-full h-[60px] bg-gradient-to-t from-neon-blue/20 via-neon-blue/8 to-transparent blur-[20px]" />
        <div className="absolute bottom-0 w-full h-[100px] bg-gradient-to-t from-neon-blue/15 via-neon-blue/5 to-transparent blur-[30px]" />
        <div className="absolute bottom-0 w-full h-[200px] bg-gradient-to-t from-neon-blue/10 via-neon-blue/3 to-transparent blur-[50px]" />

        {/* Ultra-soft ambient glow */}
        <div className="absolute bottom-0 w-full h-[250px] bg-gradient-to-t from-neon-blue/5 via-neon-blue/2 to-transparent blur-[80px]" />
      </div>
    </div>
  );
};

export default App;
