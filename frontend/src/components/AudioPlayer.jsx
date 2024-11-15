
import React, { useRef, useEffect } from 'react';

const AudioPlayer = ({ audioUrl, onEnded, autoPlay = false }) => {
  const audioRef = useRef(null);

  useEffect(() => {
    if (audioRef.current) {
      if (autoPlay) {
        audioRef.current.play().catch(e => console.error('Auto-play failed:', e));
      }
    }
  }, [audioUrl, autoPlay]);

  return (
    <audio
      ref={audioRef}
      controls
      src={audioUrl}
      onEnded={onEnded}
      className="w-full mt-4"
    />
  );
};

export default AudioPlayer;