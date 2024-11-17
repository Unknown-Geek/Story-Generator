
import React from 'react';

const GenerateButton = ({ onClick, loading }) => {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="w-full p-4 bg-gradient-to-r from-neon-blue to-neon-purple text-white rounded-lg font-semibold 
                hover:shadow-neon-hover disabled:opacity-50 transition-all duration-300 
                backdrop-blur-sm shadow-neon mb-[50px]"
    >
      {loading ? (
        <div className="loading-spinner inline-block border-t-neon-blue"/>
      ) : (
        "Generate Story"
      )}
    </button>
  );
};

export default GenerateButton;