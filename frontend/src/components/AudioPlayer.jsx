import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, Rewind, FastForward } from 'lucide-react';

const AudioPlayer = ({ story, voiceSettings, onTimeUpdate, initialTime }) => {
  const TEXT_PREVIEW_OFFSET = -0.5;

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
    if (!text || !duration) return '';
    
    // Add preview offset to position
    const previewPosition = Math.max(position + TEXT_PREVIEW_OFFSET, 0);
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
    const totalLength = text.length;
    const currentPosition = Math.floor((previewPosition / duration) * totalLength);
    
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
    <div className="w-full max-w-4xl mx-auto bg-gradient-to-br from-[rgba(10,10,31,0.9)] to-[rgba(10,10,31,0.7)] p-6 rounded-xl border border-neon-blue/20 backdrop-blur-md shadow-neon hover:shadow-neon-hover transition-all duration-300">
      <motion.div 
        className="mb-8 p-8 rounded-xl border border-neon-blue/20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <motion.p 
          key={currentLine} // Add key to trigger animation on line change
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="text-xl md:text-2xl leading-relaxed text-white/90 font-semibold text-center"
        >
          {currentLine || "Ready to start narration..."}
        </motion.p>
      </motion.div>
      
      <div className="flex items-center space-x-4 mb-4">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="w-16 h-16 rounded-full bg-gradient-to-r from-neon-blue/20 to-neon-purple/20 
                   flex items-center justify-center border border-neon-blue/30 shadow-neon"
          onClick={togglePlay}
          aria-label={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? (
            <Pause className="w-8 h-8 text-white/90" />
          ) : (
            <Play className="w-8 h-8 text-white/90" />
          )}
        </motion.button>
        
        <div className="text-lg font-medium text-white/90 font-mono">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>
      </div>

      <div
        className="relative h-12 bg-dark-bg/40 rounded-full cursor-pointer overflow-hidden backdrop-blur-sm group"
        ref={progressRef}
        onClick={handleProgressClick}
        role="slider"
        aria-valuemin={0}
        aria-valuemax={duration}
        aria-valuenow={currentTime}
      >
        <motion.div 
          className="absolute inset-0 flex items-center justify-around"
          initial={{ opacity: 0 }}
          animate={{ opacity: isPlaying ? 1 : 0 }}
        >
          {[...Array(20)].map((_, index) => (
            <motion.div
              key={index}
              className="w-1 bg-neon-blue/40 rounded-full"
              animate={{ 
                height: [8, 24, 8],
                opacity: [0.3, 1, 0.3]
              }}
              transition={{
                repeat: Infinity,
                duration: 1,
                delay: index * 0.05,
                ease: "easeInOut"
              }}
            />
          ))}
        </motion.div>
        
        <motion.div 
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-neon-blue/60 to-neon-purple/60"
          style={{ width: `${(currentTime / duration) * 100}%` }}
          animate={{
            boxShadow: isPlaying ? "0 0 20px rgba(0, 243, 255, 0.3)" : "none"
          }}
        />
        
        <motion.div 
          className="absolute top-1/2 h-6 w-6 rounded-full bg-white shadow-neon cursor-grab"
          style={{ 
            left: `calc(${(currentTime / duration) * 100}%)`,
            transform: 'translate(-50%, -50%)'
          }}
          initial={{ x: '-50%' }}
          whileHover={{ scale: 1.2 }}
          whileTap={{ scale: 0.95 }}
          transformTemplate={({ scale, x }) => 
            `translate(-50%, -50%) ${scale ? `scale(${scale})` : ''}`
          }
        />
      </div>

      <div className="flex justify-center gap-4 mt-4">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => startPlayback(Math.max(0, currentTime - 10))}
          className="p-3 rounded-full bg-gradient-to-r from-neon-blue/10 to-neon-purple/10 
                     border border-neon-blue/20 shadow-neon hover:shadow-neon-hover"
          aria-label="Rewind 10 seconds"
        >
          <Rewind className="w-5 h-5 text-white/90" />
        </motion.button>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => startPlayback(Math.min(duration, currentTime + 10))}
          className="p-3 rounded-full bg-gradient-to-r from-neon-blue/10 to-neon-purple/10 
                     border border-neon-blue/20 shadow-neon hover:shadow-neon-hover"
          aria-label="Forward 10 seconds"
        >
          <FastForward className="w-5 h-5 text-white/90" />
        </motion.button>
      </div>
    </div>
  );
};

export default AudioPlayer;