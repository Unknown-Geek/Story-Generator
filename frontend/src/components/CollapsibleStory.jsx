import React, { useState, useRef, memo } from 'react';

const CollapsibleStory = memo(({ story }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const contentRef = useRef(null);

  const toggleExpand = () => {
    if (!isExpanded) {
      contentRef.current.style.display = 'block';
      requestAnimationFrame(() => setIsExpanded(true));
    } else {
      setIsExpanded(false);
      // Add delay before hiding to allow animation to complete
      setTimeout(() => {
        if (contentRef.current) {
          contentRef.current.style.display = 'none';
        }
      }, 500);
    }
  };

  return (
    <div className="story-collapsible mt-8 overflow-visible">
      <button 
        className="glass-button w-full text-left p-4 rounded-lg hover:scale-[1.02] transition-all duration-300 overflow-visible relative z-10"
        onClick={toggleExpand}
      >
        <div className="flex items-center justify-between gap-4">
          <span className="text-lg font-medium">
            {isExpanded ? 'Hide Story' : 'View Complete Story'}
          </span>
          <svg 
            className={`w-6 h-6 transform transition-transform duration-300 flex-shrink-0 ${
              isExpanded ? 'rotate-180' : ''
            }`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>
      <div 
        ref={contentRef}
        className={`story-collapsible-content mt-4 ${isExpanded ? 'expanded' : ''}`}
        style={{ display: 'none' }}
      >
        <div className="prose prose-invert max-w-none">
          <p className="text-lg leading-relaxed text-gray-100 whitespace-pre-wrap">
            {story}
          </p>
        </div>
      </div>
    </div>
  );
});

export default CollapsibleStory;
