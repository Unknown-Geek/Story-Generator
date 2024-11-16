import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

export const StopMotionPlayer = ({ story, currentNarrationTime, totalDuration }) => {
  const [frames, setFrames] = useState([]);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [error, setError] = useState(null);
  const [useStopMotion, setUseStopMotion] = useState(true);

  useEffect(() => {
    const generateFrame = async (prompt) => {
      try {
        const response = await fetch(`${BACKEND_URL}/generate_frame`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt })
        });
        
        const data = await response.json();
        
        if (!data.success) {
          if (data.disable_stop_motion) {
            setUseStopMotion(false);
            setError("Stop motion feature is currently unavailable due to API limitations.");
            return null;
          }
          throw new Error(data.error);
        }
        
        return data.image;
      } catch (error) {
        console.error('Frame generation failed:', error);
        return null;
      }
    };

    // Frame generation logic
    const updateFrame = () => {
      if (!story || !totalDuration) return;

      const progress = currentNarrationTime / totalDuration;
      const sentences = story.match(/[^.!?]+[.!?]+/g) || [story];
      const currentSentenceIndex = Math.floor(progress * sentences.length);
      const currentSentence = sentences[currentSentenceIndex];

      if (currentSentence && (!frames[currentSentenceIndex] || frames[currentSentenceIndex] === 'pending')) {
        if (!frames[currentSentenceIndex]) {
          setFrames(prev => {
            const newFrames = [...prev];
            newFrames[currentSentenceIndex] = 'pending';
            return newFrames;
          });

          generateFrame(currentSentence).then(frameData => {
            if (frameData) {
              setFrames(prev => {
                const newFrames = [...prev];
                newFrames[currentSentenceIndex] = frameData;
                return newFrames;
              });
            }
          });
        }
      }

      if (frames[currentSentenceIndex] && frames[currentSentenceIndex] !== 'pending') {
        setCurrentFrame(frames[currentSentenceIndex]);
      }
    };

    updateFrame();
  }, [currentNarrationTime, story, totalDuration, frames]);

  if (!useStopMotion || error) {
    return error ? <div className="text-red-500 text-center">{error}</div> : null;
  }

  return (
    <div className="stop-motion-container rounded-lg overflow-hidden mb-8">
      {currentFrame && (
        <img 
          src={currentFrame} 
          alt="Story visualization" 
          className="w-full h-auto"
        />
      )}
    </div>
  );
};