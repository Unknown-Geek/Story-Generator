import React from 'react';
import { Paper, Typography } from '@mui/material';

const StoryDisplay = ({ story, isLoading }) => {
  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!story) {
    return null;
  }

  return (
    <div className="story-wrapper">
      <Paper elevation={3} className="story-container p-6">
        <Typography variant="body1" component="div" className="story-text">
          {story.split('\n\n').map((paragraph, index) => (
            <p key={index} className="mb-4">
              {paragraph}
            </p>
          ))}
        </Typography>
      </Paper>
    </div>
  );
};

export default StoryDisplay;