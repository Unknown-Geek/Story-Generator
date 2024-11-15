import React from 'react';
import { FormControl, InputLabel, Select, MenuItem, Slider } from '@mui/material';

const VoiceSettings = ({ settings, onSettingsChange }) => {
  const voices = {
    'us': 'US English',
    'uk': 'UK English',
    'in': 'Indian English',
    'au': 'Australian English'
  };

  const handleChange = (setting, value) => {
    onSettingsChange({
      ...settings,
      [setting]: value
    });
  };

  return (
    <div className="voice-settings">
      <FormControl fullWidth className="mb-4">
        <InputLabel>Voice Accent</InputLabel>
        <Select
          value={settings.accent}
          onChange={(e) => handleChange('accent', e.target.value)}
        >
          {Object.entries(voices).map(([key, label]) => (
            <MenuItem key={key} value={key}>{label}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl fullWidth>
        <Typography gutterBottom>Speed</Typography>
        <Slider
          value={settings.speed}
          min={0.5}
          max={2}
          step={0.1}
          onChange={(_, value) => handleChange('speed', value)}
          marks={[
            { value: 0.5, label: 'Slow' },
            { value: 1, label: 'Normal' },
            { value: 2, label: 'Fast' }
          ]}
        />
      </FormControl>
    </div>
  );
};

export default VoiceSettings;