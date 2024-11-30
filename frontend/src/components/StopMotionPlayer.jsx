import React, { useState, useEffect, useCallback, useRef } from "react";

const RETRY_DELAY = 2000; // 2 seconds between retries
const MAX_RETRIES = 3;

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL || "http://localhost:5000";
// Update constants for better performance
const FPS = 12;
const FRAME_TIME = 1000 / FPS;
const MAX_FRAMES = 24; // 2 seconds of animation at 12fps
const BATCH_SIZE = 2; // Process two frames at a time
const BATCH_INTERVAL = 5000; // 5 seconds between batches
const REQUEST_TIMEOUT = 15000; // 15 second timeout for requests

// Add request caching
const frameCache = new Map();

export const StopMotionPlayer = ({
  story,
  currentNarrationTime,
  totalDuration
}) => {
  const [frames, setFrames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [currentFrame, setCurrentFrame] = useState(0);
  const frameQueue = useRef([]);
  const isGenerating = useRef(false);

  const generateFrames = useCallback(async () => {
    if (frameQueue.current.length === 0) return;
    
    try {
      setLoading(true);
      const prompt = frameQueue.current[0];
      
      const response = await fetch(`${BACKEND_URL}/generate_frame`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt: prompt
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setFrames(prev => [...prev, data.image]);
        frameQueue.current.shift();
        if (frameQueue.current.length > 0) {
          setTimeout(() => generateFrames(), BATCH_INTERVAL);
        } else {
          setLoading(false);
        }
      } else {
        throw new Error(data.error || 'Failed to generate image');
      }
    } catch (error) {
      setError(`Failed to generate frame: ${error.message}`);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!story) return;

    const initFrameGeneration = async () => {
      try {
        setLoading(true);
        setError('');
        setFrames([]);

        // Extract key scenes from story
        const sentences = story
          .split(/(?<=[.!?])\s+/)
          .filter(s => s.length > 20)
          .slice(0, MAX_FRAMES);

        // Process sentences into frame prompts
        frameQueue.current = sentences.map(sentence => 
          sentence.replace(/[^\w\s.]/g, '').trim()
        );

        // Start frame generation
        generateFrames();
      } catch (error) {
        console.error('Frame generation initialization error:', error);
        setError('Failed to initialize frame generation');
        setLoading(false);
      }
    };

    initFrameGeneration();
  }, [story, generateFrames]);

  // Smooth frame transition logic
  useEffect(() => {
    if (!frames.length) return;

    const frameIndex = Math.min(
      Math.floor((currentNarrationTime / totalDuration) * frames.length),
      frames.length - 1
    );

    // Add smooth transition between frames
    const transitionTime = FRAME_TIME / 1000; // Convert to seconds
    const transition = setTimeout(() => {
      setCurrentFrame(frameIndex);
    }, transitionTime);

    return () => clearTimeout(transition);
  }, [currentNarrationTime, totalDuration, frames.length]);

  if (loading) {
    return (
      <div className="stop-motion-container p-4 text-center">
        <div className="loading-spinner mx-auto" />
        <p className="mt-2 text-neon-blue">Generating test frames...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="stop-motion-container p-4 text-center text-red-400">
        {error}
      </div>
    );
  }

  if (!frames.length) return null;

  return (
    <div className="stop-motion-container">
      {frames[currentFrame] && (
        <img
          src={frames[currentFrame]}
          alt={`Story frame ${currentFrame + 1}`}
          className="w-full h-auto rounded-lg shadow-neon transition-opacity duration-100"
          style={{ opacity: loading ? 0.7 : 1 }}
        />
      )}
      <div className="text-center mt-2 text-neon-blue">
        Frame {currentFrame + 1} of {frames.length}
        {loading &&
          frameQueue.current.length > 0 &&
          ` (Generating ${frameQueue.current.length} more...)`}
      </div>
    </div>
  );
};
