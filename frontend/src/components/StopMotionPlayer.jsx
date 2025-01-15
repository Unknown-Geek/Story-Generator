import React, { useState, useEffect, useCallback, useRef } from "react";

const RETRY_DELAY = 2000; // 2 seconds between retries
const MAX_RETRIES = 3;

const BACKEND_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:5000'
  : process.env.REACT_APP_API_URL;
// Update constants for better performance
const FPS = 12;
const FRAME_TIME = 1000 / FPS;
const MAX_FRAMES = 24; // 2 seconds of animation at 12fps
const BATCH_SIZE = 2; // Process two frames at a time
const BATCH_INTERVAL = 5000; // 5 seconds between batches
const REQUEST_TIMEOUT = 15000; // 15 second timeout for requests

// Add request caching
const frameCache = new Map();

// Add image dimension constants
const IMAGE_DIMENSIONS = {
    width: 512,
    height: 512
};

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

      const data = await response.json();
      
      if (response.status === 429) {
        // Handle rate limit/quota exceeded
        const retryAfter = data.retry_after || 720; // Default to 12 minutes
        setError(`${data.error} Retrying automatically.`);
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        return generateFrames(); // Retry after waiting
      }

      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate image');
      }

      if (data.success) {
        setFrames(prev => [...prev, data.image]);
        frameQueue.current.shift();
        if (frameQueue.current.length > 0) {
          // Add random delay between 5-10 seconds to avoid overwhelming the API
          const delay = Math.random() * 5000 + 5000;
          setTimeout(() => generateFrames(), delay);
        } else {
          setLoading(false);
        }
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
          className="w-full max-w-[512px] h-auto mx-auto rounded-lg shadow-neon transition-opacity duration-100"
          style={{ 
            opacity: loading ? 0.7 : 1,
            aspectRatio: `${IMAGE_DIMENSIONS.width}/${IMAGE_DIMENSIONS.height}`
          }}
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
