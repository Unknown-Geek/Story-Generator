import React, { useState, useRef, useEffect } from 'react';

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
    <div className="cyber-player p-8 bg-gradient-to-br from-[rgba(10,10,31,0.9)] to-[rgba(10,10,31,0.7)] rounded-xl border border-neon-blue/20 backdrop-blur-md mb-8 shadow-neon hover:shadow-neon-hover transition-all duration-300">
      <div className="current-line mb-8 p-8 bg-gradient-to-br from-[rgba(0,0,0,0.4)] to-[rgba(0,0,0,0.2)] rounded-xl border border-neon-blue/20">
        <p className="text-2xl md:text-3xl leading-relaxed text-white/90 font-light">
          {currentLine || "Ready to start narration..."}
        </p>
      </div>
      
      <div className="flex flex-col md:flex-row items-center gap-8 mb-6">
        <button 
          className="glass-button w-20 h-20 rounded-full flex items-center justify-center group hover:scale-105 transition-all duration-300 bg-gradient-to-br from-neon-blue/20 to-neon-purple/20"
          onClick={togglePlay}
          aria-label={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? (
            <svg className="w-10 h-10 text-white/90 group-hover:text-white" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16"/>
              <rect x="14" y="4" width="4" height="16"/>
            </svg>
          ) : (
            <svg className="w-10 h-10 text-white/90 group-hover:text-white" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5,3 19,12 5,21"/>
            </svg>
          )}
        </button>

        <div className="flex-1 w-full">
          <div className="flex justify-between mb-3">
            <span className="text-white/90 font-mono text-lg">
              {formatTime(currentTime)}
            </span>
            <span className="text-white/90 font-mono text-lg">
              {formatTime(duration)}
            </span>
          </div>

          <div 
            className="relative h-4 bg-dark-bg/40 rounded-full cursor-pointer overflow-hidden backdrop-blur-sm group"
            ref={progressRef}
            onClick={handleProgressClick}
            role="progressbar"
            aria-valuemin="0"
            aria-valuemax={duration}
            aria-valuenow={currentTime}
          >
            <div 
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-neon-blue/60 to-neon-purple/60 group-hover:from-neon-blue/80 group-hover:to-neon-purple/80 transition-all"
              style={{ width: `${(currentTime / duration) * 100}%` }}
            />
            <div 
              className="absolute top-1/2 -translate-y-1/2 h-6 w-6 rounded-full bg-white shadow-neon cursor-grab hover:scale-110 transition-transform duration-200"
              style={{ left: `calc(${(currentTime / duration) * 100}% - 12px)` }}
            />
          </div>
        </div>

        <div className="flex gap-4">
          <button
            onClick={() => startPlayback(Math.max(0, currentTime - 10))}
            className="glass-button p-4 rounded-full hover:scale-110 transition-all duration-300 bg-gradient-to-br from-neon-blue/10 to-neon-purple/10"
            aria-label="Rewind 10 seconds"
          >
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12.5 3L9 7l3.5 4V8c3.3 0 6 2.7 6 6s-2.7 6-6 6-6-2.7-6-6h-2c0 4.4 3.6 8 8 8s8-3.6 8-8-3.6-8-8-8V3z"/>
            </svg>
          </button>
          <button
            onClick={() => startPlayback(Math.min(duration, currentTime + 10))}
            className="glass-button p-4 rounded-full hover:scale-110 transition-all duration-300 bg-gradient-to-br from-neon-blue/10 to-neon-purple/10"
            aria-label="Forward 10 seconds"
          >
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11.5 3l3.5 4-3.5 4V8c-3.3 0-6 2.7-6 6s2.7 6 6 6 6-2.7 6-6h2c0 4.4-3.6 8-8 8s-8-3.6-8-8 3.6-8 8-8V3z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AudioPlayer;