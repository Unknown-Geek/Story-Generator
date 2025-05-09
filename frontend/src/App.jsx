import React, { useState, useRef, useEffect, useCallback } from 'react';
import { StopMotionPlayer } from './components/StopMotionPlayer';
import CollapsibleStory from './components/CollapsibleStory';
import AudioPlayer from './components/AudioPlayer';
import ServerConnection from './components/ServerConnection';
import { Analytics } from "@vercel/analytics/react";

const GENRES = ["Fantasy", "Adventure", "Romance", "Horror", "Mystery", "Moral Story"];
const STORY_LENGTHS = [
  { label: "Short (200 words)", value: 200 },
  { label: "Medium (500 words)", value: 500 },
  { label: "Long (1000 words)", value: 1000 }
];

const VOICE_TYPES = [
  { label: "US English", value: "com" },
  { label: "UK English", value: "co.uk" },
  { label: "Indian English", value: "co.in" },
  { label: "Australian English", value: "com.au" }
];

// Default backend URL if not using a custom Colab server
const DEFAULT_BACKEND_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:5000'
  : process.env.REACT_APP_API_URL;

const FRAME_INTERVAL = 2; // seconds between frames

const App = () => {
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [genre, setGenre] = useState(GENRES[0]);
  const [length, setLength] = useState(STORY_LENGTHS[0].value);
  const [story, setStory] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [voiceSettings, setVoiceSettings] = useState({
    accent: VOICE_TYPES[0].value,
    speed: 'normal'
  });
  const [useStopMotion, setUseStopMotion] = useState(false);
  const [currentNarrationTime, setCurrentNarrationTime] = useState(0);
  const [storyDuration, setStoryDuration] = useState(0);
  
  // Server connection state
  const [backendUrl, setBackendUrl] = useState(() => {
    return localStorage.getItem('colabServerUrl') || DEFAULT_BACKEND_URL;
  });
  const [isServerConnected, setIsServerConnected] = useState(false);

  // Check server connection on mount and when backendUrl changes
  useEffect(() => {
    const checkServerConnection = async () => {
      try {
        const response = await fetch(`${backendUrl}/health`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        setIsServerConnected(response.ok);
      } catch (error) {
        setIsServerConnected(false);
      }
    };
    
    checkServerConnection();
    
    // Set up periodic health check (every 30 seconds)
    const intervalId = setInterval(checkServerConnection, 30000);
    
    return () => clearInterval(intervalId);
  }, [backendUrl]);

  const handleServerUrlChange = (newUrl) => {
    setBackendUrl(newUrl);
    // Reset any errors
    setError('');
  };

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImage(file);
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const generateStory = async () => {
    if (!imagePreview) {
      setError('Please upload an image');
      return;
    }

    if (!isServerConnected) {
      setError('Server is not connected. Please check your connection.');
      return;
    }

    setLoading(true);
    setError('');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    try {
      const base64Image = imagePreview.split(',')[1];

      const response = await fetch(`${backendUrl}/generate_story`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image: base64Image,
          genre: genre,
          length: length
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || 
          `Server error (${response.status}). Please try again.`
        );
      }

      const data = await response.json();
      if (data.success) {
        setStory(data.story);
        const wordCount = data.story.split(' ').length;
        const averageWordsPerMinute = 150;
        setStoryDuration((wordCount / averageWordsPerMinute) * 60);
      } else {
        throw new Error(data.error || 'Failed to generate story');
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Request timed out. Please try again.');
      } else if (!navigator.onLine) {
        setError('No internet connection. Please check your network.');
      } else {
        setError(err.message || 'Error connecting to server');
      }
    } finally {
      setLoading(false);
      clearTimeout(timeoutId);
    }
  };

  // Add cleanup effect
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
        <div className="flex justify-between items-center mb-12">
          <h1 className="text-5xl font-bold text-center text-white text-shadow-neon" style={{ fontFamily: "'Base Neue', 'Eurostile', 'Bank Gothic', sans-serif" }}>
            Story Generator
          </h1>
          <div className="flex items-center">
            <div className={`h-3 w-3 rounded-full mr-2 ${isServerConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-300">{isServerConnected ? 'Server Online' : 'Server Offline'}</span>
          </div>
        </div>

        {/* Server Connection Panel */}
        <div className="bg-[rgba(10,10,31,0.8)] border border-neon-blue/10 rounded-lg p-6 mb-8 backdrop-blur-md shadow-neon">
          <ServerConnection 
            onServerUrlChange={handleServerUrlChange}
            serverUrl={backendUrl}
            isConnected={isServerConnected}
          />
        </div>

        {/* Settings Panel */}
        <div className="bg-[rgba(10,10,31,0.8)] border border-neon-blue/10 rounded-lg p-6 mb-8 backdrop-blur-md shadow-neon">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <select
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
            >
              {GENRES.map(g => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>

            <select
              value={length}
              onChange={(e) => setLength(Number(e.target.value))}
              className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
            >
              {STORY_LENGTHS.map(l => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <select
              value={voiceSettings.accent}
              onChange={(e) => setVoiceSettings(prev => ({ ...prev, accent: e.target.value }))}
              className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
            >
              {VOICE_TYPES.map(v => (
                <option key={v.value} value={v.value}>{v.label}</option>
              ))}
            </select>

            <select
              value={voiceSettings.speed}
              onChange={(e) => setVoiceSettings(prev => ({ ...prev, speed: e.target.value }))}
              className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
            >
              <option value="slow">Slow</option>
              <option value="normal">Normal</option>
              <option value="fast">Fast</option>
            </select>
          </div>
          <div className="mt-4 flex items-center">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={useStopMotion}
                onChange={(e) => setUseStopMotion(e.target.checked)}
                className="form-checkbox h-5 w-5 text-neon-blue rounded border-neon-blue/20 
                          focus:ring-neon-blue/50 focus:ring-2 bg-dark-bg/50"
              />
              <span className="text-white">Enable Image Frames</span>
            </label>
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
          />
          <label
            htmlFor="image-upload"
            className="block w-full p-6 border-2 border-dashed border-neon-blue/30 rounded-lg text-center text-white cursor-pointer hover:border-neon-blue/50 transition-all bg-dark-bg/30 backdrop-blur-sm"
          >
            {imagePreview ? (
              <img src={imagePreview} alt="Preview" className="max-h-64 mx-auto rounded shadow-neon" />
            ) : (
              "Click to upload image"
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
          disabled={loading || !isServerConnected}
          className="glass-button w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="loading-spinner" />
              <span>Generating...</span>
            </>
          ) : !isServerConnected ? (
            "Server Not Connected"
          ) : (
            "Generate Story"
          )}
        </button>

        {/* Story Display */}
        {story && (
          <div className="story-container mt-8 animate-fadeIn">
            {useStopMotion && (
              <StopMotionPlayer
                story={story}
                currentNarrationTime={currentNarrationTime}
                totalDuration={storyDuration}
              />
            )}
            <AudioPlayer 
              story={story} 
              voiceSettings={voiceSettings}
              onTimeUpdate={useStopMotion ? setCurrentNarrationTime : undefined}
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
