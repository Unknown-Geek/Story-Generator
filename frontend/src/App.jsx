import React, { useState, useRef, useEffect } from 'react';

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

// Backend URL - update this if your backend runs on a different port
const BACKEND_URL = 'http://localhost:5000';

const AudioPlayer = ({ story, voiceSettings }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const progressRef = useRef(null);
  const utteranceRef = useRef(null);
  const intervalRef = useRef(null);
  const pausedAtRef = useRef(0);
  const textToSpeakRef = useRef(story);

  const calculateDuration = (text) => {
    // Estimate duration based on word count and speech rate
    const wordsPerMinute = voiceSettings.speed === 'slow' ? 100 : 
                          voiceSettings.speed === 'fast' ? 200 : 150;
    const wordCount = text.split(' ').length;
    return (wordCount / wordsPerMinute) * 60;
  };

  const startPlayback = (fromPosition = 0) => {
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }

    // Calculate text to speak based on position
    const words = story.split(' ');
    const wordPosition = Math.floor((words.length * fromPosition) / duration);
    const remainingText = words.slice(wordPosition).join(' ');
    textToSpeakRef.current = remainingText;

    utteranceRef.current = new SpeechSynthesisUtterance(remainingText);
    utteranceRef.current.rate = voiceSettings.speed === 'slow' ? 0.7 : 
                               voiceSettings.speed === 'fast' ? 1.3 : 1;

    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find(v => v.voiceURI.includes(voiceSettings.accent));
    if (voice) utteranceRef.current.voice = voice;

    // Set up event handlers
    utteranceRef.current.onstart = () => {
      setIsPlaying(true);
      if (!duration) {
        setDuration(calculateDuration(story));
      }
      
      if (intervalRef.current) clearInterval(intervalRef.current);
      
      // Start from saved position
      setCurrentTime(fromPosition);
      
      intervalRef.current = setInterval(() => {
        setCurrentTime(prev => {
          const newTime = prev + 0.1;
          pausedAtRef.current = newTime;
          return newTime < duration ? newTime : prev;
        });
      }, 100);
    };

    utteranceRef.current.onend = () => {
      setIsPlaying(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      // Only reset if we finished the complete story
      if (textToSpeakRef.current === story) {
        setCurrentTime(0);
        pausedAtRef.current = 0;
      }
    };

    utteranceRef.current.onpause = () => {
      setIsPlaying(false);
      pausedAtRef.current = currentTime;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };

    window.speechSynthesis.speak(utteranceRef.current);
  };

  const stopPlayback = () => {
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    pausedAtRef.current = currentTime;
    setIsPlaying(false);
  };

  const togglePlay = () => {
    if (isPlaying) {
      stopPlayback();
    } else {
      startPlayback(pausedAtRef.current);
    }
  };

  const handleProgressClick = (e) => {
    if (!progressRef.current) return;

    const bounds = progressRef.current.getBoundingClientRect();
    const percent = (e.clientX - bounds.left) / bounds.width;
    const newTime = percent * duration;
    
    // Stop current playback
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    setCurrentTime(newTime);
    pausedAtRef.current = newTime;

    // If we were playing, start from new position
    if (isPlaying) {
      startPlayback(newTime);
    }
  };

  // Initialize duration on mount
  useEffect(() => {
    setDuration(calculateDuration(story));
    return () => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [story]);

  // Update settings when they change
  useEffect(() => {
    if (isPlaying) {
      stopPlayback();
      startPlayback(pausedAtRef.current);
    }
  }, [voiceSettings]);

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="custom-audio-player bg-white/10 backdrop-blur-md rounded-lg p-4 mt-4">
      <div className="audio-controls flex items-center gap-4">
        <button 
          className="play-button w-12 h-12 rounded-full bg-purple-600 hover:bg-purple-700 flex items-center justify-center"
          onClick={togglePlay}
        >
          {isPlaying ? (
            <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16"/>
              <rect x="14" y="4" width="4" height="16"/>
            </svg>
          ) : (
            <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5,3 19,12 5,21"/>
            </svg>
          )}
        </button>
        <span className="time-info text-white font-mono">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>
      </div>
      <div 
        className="progress-bar mt-4 relative h-2 bg-white/20 rounded-full cursor-pointer"
        ref={progressRef}
        onClick={handleProgressClick}
      >
        <div 
          className="progress-bar-fill absolute top-0 left-0 h-full bg-gradient-to-r from-purple-600 to-blue-600 rounded-full"
          style={{ width: `${(currentTime / duration) * 100}%` }}
        />
      </div>
    </div>
  );
};

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
      } else {
        setError(data.error || 'Failed to generate story');
      }
    } catch (err) {
      setError('Error connecting to server: ' + err.message);
    } finally {
      setLoading(false);
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center text-white mb-12">
          Story Generator
        </h1>

        {/* Settings Panel - removed server URL input */}
        <div className="settings-panel mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <select
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              className="p-2 rounded bg-white/10 text-white"
            >
              {GENRES.map(g => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>

            <select
              value={length}
              onChange={(e) => setLength(Number(e.target.value))}
              className="p-2 rounded bg-white/10 text-white"
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
              className="p-2 rounded bg-white/10 text-white"
            >
              {VOICE_TYPES.map(v => (
                <option key={v.value} value={v.value}>{v.label}</option>
              ))}
            </select>

            <select
              value={voiceSettings.speed}
              onChange={(e) => setVoiceSettings(prev => ({ ...prev, speed: e.target.value }))}
              className="p-2 rounded bg-white/10 text-white"
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
          />
          <label
            htmlFor="image-upload"
            className="block w-full p-4 border-2 border-dashed border-white/30 rounded-lg text-center text-white cursor-pointer hover:border-white/50 transition-colors"
          >
            {imagePreview ? (
              <img src={imagePreview} alt="Preview" className="max-h-64 mx-auto rounded" />
            ) : (
              "Click to upload image"
            )}
          </label>
        </div>

        {/* Error Message */}
        {error && (
          <div className="text-red-400 text-center mb-4">
            {error}
          </div>
        )}

        {/* Generate Button */}
        <button
          onClick={generateStory}
          disabled={loading}
          className="w-full p-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 disabled:bg-purple-400 transition-colors"
        >
          {loading ? (
            <div className="loading-spinner inline-block"/>
          ) : (
            "Generate Story"
          )}
        </button>

        {/* Story Display */}
        {story && (
          <div className="story-container mt-8 animate-fadeIn">
            <p className="sentence">
              {story}
            </p>
            <AudioPlayer 
              story={story} 
              voiceSettings={voiceSettings}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
