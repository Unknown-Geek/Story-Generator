import React, { useState, useRef, useEffect } from 'react';
import { StopMotionPlayer } from './components/StopMotionPlayer';
import CollapsibleStory from './components/CollapsibleStory';

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
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

const FRAME_INTERVAL = 2; // seconds between frames

const AudioPlayer = ({ story, voiceSettings, onTimeUpdate, initialTime }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(initialTime || 0);
  const [duration, setDuration] = useState(0);
  const [currentLine, setCurrentLine] = useState('');
  const progressRef = useRef(null);
  const utteranceRef = useRef(null);
  const intervalRef = useRef(null);
  const pausedAtRef = useRef(0);
  const textToSpeakRef = useRef(story);

  // Helper functions
  const calculateDuration = (text) => {
    // Estimate duration based on word count and speech rate
    const wordsPerMinute = voiceSettings.speed === 'slow' ? 100 : 
                          voiceSettings.speed === 'fast' ? 200 : 150;
    const wordCount = text.split(' ').length;
    return (wordCount / wordsPerMinute) * 60;
  };

  const getCurrentSentence = (text, position) => {
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
    const totalLength = text.length;
    const currentPosition = Math.floor((position / duration) * totalLength);
    
    let accumulatedLength = 0;
    for (let sentence of sentences) {
      accumulatedLength += sentence.length;
      if (accumulatedLength >= currentPosition) {
        return sentence.trim();
      }
    }
    return sentences[sentences.length - 1].trim();
  };

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
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

  // Effects
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

  useEffect(() => {
    if (isPlaying) {
      stopPlayback();
      startPlayback(pausedAtRef.current);
    }
  }, [voiceSettings]);

  useEffect(() => {
    setCurrentLine(getCurrentSentence(story, currentTime));
  }, [currentTime, story]);

  // Add frame synchronization
  useEffect(() => {
    if (onTimeUpdate) {
      onTimeUpdate(currentTime);
    }
  }, [currentTime, onTimeUpdate]);

  // Render component
  return (
    <div className="cyber-player">
      <div className="current-line">
        {currentLine}
      </div>
      
      <div className="flex items-center gap-4 mb-4">
        <button 
          className="w-16 h-16 rounded-full bg-gradient-to-r from-neon-blue to-neon-purple 
                     flex items-center justify-center shadow-neon hover:shadow-neon-hover 
                     transition-all duration-300"
          onClick={togglePlay}
        >
          {isPlaying ? (
            <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16"/>
              <rect x="14" y="4" width="4" height="16"/>
            </svg>
          ) : (
            <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5,3 19,12 5,21"/>
            </svg>
          )}
        </button>
        <span className="text-white/80 font-mono text-xl">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>
      </div>

      <div 
        className="relative h-3 bg-dark-bg/50 rounded-full cursor-pointer overflow-hidden"
        ref={progressRef}
        onClick={handleProgressClick}
      >
        <div 
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-neon-blue to-neon-purple shadow-neon"
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
  const [useStopMotion, setUseStopMotion] = useState(false);
  const [currentNarrationTime, setCurrentNarrationTime] = useState(0);
  const [storyDuration, setStoryDuration] = useState(0);

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

  useEffect(() => {
    return () => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_50%_50%,var(--tw-gradient-stops))] from-dark-bg via-[#000510] to-[#000510] py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center text-white mb-12 text-shadow-neon">
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
              <span className="text-white">Enable Stop Motion Animation (Uses more resources)</span>
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
    </div>
  );
};

export default App;
