import React, { useState, useEffect, useCallback, useRef } from "react";

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL || "http://localhost:5000";
// Reduce constants for better performance and less API load
const FPS = 2; // Reduced from 4
const FRAME_TIME = 1000 / FPS;
const MAX_FRAMES = 8; // Reduced from 16
const BATCH_SIZE = 1; // Process one frame at a time
const BATCH_INTERVAL = 10000; // 10 seconds between batches
const REQUEST_TIMEOUT = 15000; // 15 second timeout for requests

// Add request caching
const frameCache = new Map();

export const StopMotionPlayer = ({
  story,
  currentNarrationTime,
  totalDuration,
}) => {
  const [frames, setFrames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [currentFrame, setCurrentFrame] = useState(0);
  const frameQueue = useRef([]);
  const isGenerating = useRef(false);

  const generateFrameBatch = useCallback(async () => {
    if (frameQueue.current.length === 0 || isGenerating.current) return;

    isGenerating.current = true;
    const prompt = frameQueue.current[0]; // Process one at a time

    try {
      const response = await fetch(`${BACKEND_URL}/generate_frame`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });

      const data = await response.json();
      
      if (data.success) {
        setFrames(prev => [...prev, data.image]);
        frameQueue.current = frameQueue.current.slice(1);
      } else {
        console.error('Frame generation failed:', data.error);
      }
    } catch (error) {
      console.error('Frame generation error:', error);
      setError('Failed to generate frame. Retrying...');
    } finally {
      isGenerating.current = false;
    }
  }, []);

  // Modify frame generation initialization
  useEffect(() => {
    if (!story) return;

    setLoading(true);
    setError("");
    setFrames([]);

    // Take fewer key sentences for frames
    const sentences = story
      .split(/(?<=[.!?])\s+/)
      .filter((sentence) => sentence.trim().length > 20) // Only longer, meaningful sentences
      .slice(0, MAX_FRAMES);

    // Take evenly spaced sentences to cover the whole story
    const stride = Math.max(1, Math.floor(sentences.length / MAX_FRAMES));
    frameQueue.current = sentences.filter((_, i) => i % stride === 0);

    const generateFrames = async () => {
      while (frameQueue.current.length > 0) {
        await generateFrameBatch();
        if (frameQueue.current.length > 0) {
          await new Promise((resolve) => setTimeout(resolve, BATCH_INTERVAL));
        }
      }
      setLoading(false);
    };

    generateFrames();

    return () => {
      frameQueue.current = [];
      isGenerating.current = false;
    };
  }, [story, generateFrameBatch]);

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
