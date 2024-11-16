import React, { useState, useEffect, useCallback, useRef } from "react";

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL || "http://localhost:5000";
// Reduce FPS and total frames
const FPS = 6; // Reduced from 12
const FRAME_TIME = 1000 / FPS;
const MAX_FRAMES = 24; // Reduced from 48
const BATCH_SIZE = 4; // Reduced from 10
const BATCH_INTERVAL = 5000; // Increased from 2000 to 5000ms
const REQUEST_TIMEOUT = 15000; // 15 second timeout for requests

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
    const batch = frameQueue.current.slice(0, BATCH_SIZE);

    try {
      // Add exponential backoff retry logic
      const fetchWithRetry = async (prompt, retryCount = 0) => {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(
            () => controller.abort(),
            REQUEST_TIMEOUT
          );

          const response = await fetch(`${BACKEND_URL}/generate_frame`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt }),
            signal: controller.signal,
          });

          clearTimeout(timeoutId);

          if (response.status === 429) {
            throw new Error("rate_limit");
          }

          return await response.json();
        } catch (error) {
          if (error.message === "rate_limit" && retryCount < 3) {
            // Exponential backoff
            await new Promise((resolve) =>
              setTimeout(resolve, Math.pow(2, retryCount) * 5000)
            );
            return fetchWithRetry(prompt, retryCount + 1);
          }
          throw error;
        }
      };

      // Process batch with increased delays between requests
      const results = await Promise.all(
        batch.map(
          (prompt, index) =>
            new Promise((resolve) => {
              setTimeout(async () => {
                try {
                  const result = await fetchWithRetry(prompt);
                  resolve({ status: "fulfilled", value: result });
                } catch (error) {
                  resolve({ status: "rejected", reason: error });
                }
              }, index * 1500); // 1.5 second delay between requests
            })
        )
      );

      const successfulFrames = results
        .filter(
          (result) => result.status === "fulfilled" && result.value.success
        )
        .map((result) => result.value.image);

      if (successfulFrames.length > 0) {
        setFrames((prev) => [...prev, ...successfulFrames]);
        frameQueue.current = frameQueue.current.slice(successfulFrames.length);
      }
    } catch (error) {
      console.error("Batch frame generation error:", error);
      setError("Frame generation failed. Retrying...");
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
