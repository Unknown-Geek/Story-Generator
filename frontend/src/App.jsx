import React, { useState, useRef, useEffect } from 'react';
import { StopMotionPlayer } from './components/StopMotionPlayer';
import CollapsibleStory from './components/CollapsibleStory';
import AudioPlayer from './components/AudioPlayer'; // Add this import

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

// Update BACKEND_URL to use environment variable
const BACKEND_URL = process.env.REACT_APP_API_URL || 'https://story-generator-api.onrender.com';

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
  const [sdxlUrl, setSdxlUrl] = useState('');
  const [sdxlStatus, setSdxlStatus] = useState(''); // Add this state

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

    setLoading(true);
    setError('');

    try {
      const base64Image = imagePreview.split(',')[1];

      const response = await fetch(`${BACKEND_URL}/generate_story`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image: base64Image,
          genre: genre,
          length: length
        })
      });

      const data = await response.json();
      if (data.success) {
        setStory(data.story);
        // Calculate approximate duration based on word count
        const wordCount = data.story.split(' ').length;
        const averageWordsPerMinute = 150; // adjust based on your narration speed
        setStoryDuration((wordCount / averageWordsPerMinute) * 60);
      } else {
        setError(data.error || 'Failed to generate story');
      }
    } catch (err) {
      setError('Error connecting to server: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const validateAndConnectSdxl = async (url) => {
    setSdxlStatus('connecting');
    try {
      const cleanUrl = url.trim().replace(/\/$/, '');
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const healthResponse = await fetch(`${cleanUrl}/health`, {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!healthResponse.ok) {
        throw new Error(`Server returned ${healthResponse.status}`);
      }

      const healthData = await healthResponse.json();
      console.log('Health check response:', healthData); // Add debugging
      
      if (!healthData.gpu_available || healthData.service !== 'sdxl' || healthData.status !== 'healthy') {
        throw new Error('Invalid SDXL service response');
      }

      setSdxlStatus('connected');
      setError('');
      return true;
    } catch (err) {
      console.error('SDXL Connection error:', err);
      setSdxlStatus('error');
      setError(`Connection failed: ${err.message}`);
      return false;
    }
  };

  // Add URL input change handler
  const handleSdxlUrlChange = async (e) => {
    const url = e.target.value;
    setSdxlUrl(url);
    if (url) {
      await validateAndConnectSdxl(url);
    } else {
      setSdxlStatus('');
    }
  };

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
        <h1 className="text-5xl font-bold text-center text-white mb-12 text-shadow-neon" style={{ fontFamily: "'Base Neue', 'Eurostile', 'Bank Gothic', sans-serif" }}>
          Story Generator
        </h1>

        {/* Settings Panel */}
        <div className="bg-[rgba(10,10,31,0.8)] border border-neon-blue/10 rounded-lg p-6 mb-8 backdrop-blur-md shadow-neon">
          {/* Add SDXL URL input and Colab button */}
          {useStopMotion && (
            <div className="mb-4 space-y-2">
              <div className="flex gap-4 items-center">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    placeholder="Enter SDXL Server URL (e.g., https://xxxx.trycloudflare.com)"
                    value={sdxlUrl}
                    onChange={handleSdxlUrlChange}
                    className={`w-full p-2 rounded bg-dark-bg/50 border text-white 
                      focus:ring-1 transition-all pr-10
                      ${sdxlStatus === 'connected' ? 'border-green-500 focus:border-green-500 focus:ring-green-500/50' :
                        sdxlStatus === 'error' ? 'border-red-500 focus:border-red-500 focus:ring-red-500/50' :
                        'border-neon-blue/20 focus:border-neon-blue/50 focus:ring-neon-blue/50'}`}
                  />
                  {sdxlStatus && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      {sdxlStatus === 'connecting' && (
                        <div className="loading-spinner w-5 h-5" />
                      )}
                      {sdxlStatus === 'connected' && (
                        <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                      {sdxlStatus === 'error' && (
                        <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )}
                    </div>
                  )}
                </div>
                <a
                  href="https://colab.research.google.com/drive/1hc8G2WY_4P_0Tri-lZ0HmVDdX6MKy5LV?usp=sharing"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="glass-button px-4 py-2 flex items-center gap-2 whitespace-nowrap hover:bg-neon-blue/10"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                  </svg>
                  Open Colab
                </a>
              </div>
              <p className="text-sm italic">
                {sdxlStatus === 'connected' ? (
                  <span className="text-green-400">Connected to SDXL service successfully!</span>
                ) : sdxlStatus === 'error' ? (
                  <span className="text-red-400">Failed to connect. Please check the URL and try again.</span>
                ) : (
                  <span className="text-neon-blue/70">Note: Run the Colab notebook to get your SDXL Server URL</span>
                )}
              </p>
            </div>
          )}
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
              <span className="text-white">Enable Image Frames (Uses more resources)</span>
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
        </button>

        {/* Story Display */}
        {story && (
          <div className="story-container mt-8 animate-fadeIn">
            {useStopMotion && (
              <StopMotionPlayer
                story={story}
                currentNarrationTime={currentNarrationTime}
                totalDuration={storyDuration}
                sdxlUrl={sdxlUrl} // Pass URL to StopMotionPlayer
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
