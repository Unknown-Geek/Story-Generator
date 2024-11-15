import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

export const StopMotionPlayer = ({ story, currentNarrationTime, totalDuration }) => {
    const [frames, setFrames] = useState([]);
    const [currentFrame, setCurrentFrame] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Test with just three frames initially
    useEffect(() => {
        const generateTestFrames = async () => {
            if (!story || frames.length > 0) return;
            setLoading(true);
            setError('');

            try {
                const sentences = story.match(/[^.!?]+[.!?]+/g) || [story];
                // Just generate 3 frames for testing
                const testPrompts = sentences.slice(0, 3).map(sentence => ({
                    prompt: `Create a family-friendly illustration: ${sentence.trim()}`
                }));

                const framePromises = testPrompts.map(async ({ prompt }) => {
                    try {
                        const response = await fetch(`${BACKEND_URL}/generate_frame`, {
                            method: 'POST',
                            headers: { 
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            },
                            mode: 'cors',  // Add this line
                            credentials: 'same-origin',  // Add this line
                            body: JSON.stringify({ prompt })
                        });

                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        
                        const data = await response.json();
                        return data.success ? data.image : null;
                    } catch (error) {
                        console.error('Frame generation error:', error);
                        return null;
                    }
                });

                const generatedFrames = await Promise.all(framePromises);
                const validFrames = generatedFrames.filter(Boolean);
                
                if (validFrames.length > 0) {
                    setFrames(validFrames);
                } else {
                    throw new Error('No frames were generated successfully');
                }
            } catch (err) {
                setError('Failed to generate test frames');
                console.error('Frame generation error:', err);
            } finally {
                setLoading(false);
            }
        };

        generateTestFrames();
    }, [story]);

    // Update current frame based on narration time
    useEffect(() => {
        if (frames.length === 0) return;
        
        const frameIndex = Math.min(
            Math.floor(currentNarrationTime / (totalDuration / frames.length)),
            frames.length - 1
        );
        
        setCurrentFrame(frameIndex);
    }, [currentNarrationTime, frames.length, totalDuration]);

    if (loading) {
        return (
            <div className="stop-motion-container p-4 text-center">
                <div className="loading-spinner mx-auto"/>
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
            <img
                src={frames[currentFrame]}
                alt={`Story frame ${currentFrame + 1}`}
                className="w-full h-auto rounded-lg shadow-neon"
            />
            <div className="text-center mt-2 text-neon-blue">
                Frame {currentFrame + 1} of {frames.length}
            </div>
        </div>
    );
};