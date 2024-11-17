import React, { memo, useCallback } from 'react';

const GENRES = ["Fantasy", "Adventure", "Romance", "Horror", "Mystery", "Moral Story"];
const STORY_LENGTHS = [
  { label: "Short (200 words)", value: 200 },
  { label: "Medium (500 words)", value: 500 },
  { label: "Long (1000 words)", value: 1000 }
];

const VOICE_TYPES = [
  { label: "US English", value: "com" },
  { label: "UK English", value: "co.uk" },
  { label: "Indian English", value: "co.in" },
  { label: "Australian English", value: "com.au" }
];

const SettingsPanel = memo(({ 
  genre, 
  setGenre, 
  length, 
  setLength, 
  voiceSettings, 
  setVoiceSettings,
  useStopMotion,
  setUseStopMotion 
}) => {
  const handleVoiceSettingsChange = useCallback((key, value) => {
    setVoiceSettings(prev => ({ ...prev, [key]: value }));
  }, [setVoiceSettings]);

  return (
    <div className="bg-[rgba(10,10,31,0.8)] border border-neon-blue/10 rounded-lg p-6 mb-8 backdrop-blur-md shadow-neon">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <select
          value={genre}
          onChange={(e) => setGenre(e.target.value)}
          className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
        >
          {GENRES.map(g => (
            <option key={g} value={g}>{g}</option>
          ))}
        </select>

        <select
          value={length}
          onChange={(e) => setLength(Number(e.target.value))}
          className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
        >
          {STORY_LENGTHS.map(l => (
            <option key={l.value} value={l.value}>{l.label}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <select
          value={voiceSettings.accent}
          onChange={(e) => handleVoiceSettingsChange('accent', e.target.value)}
          className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
        >
          {VOICE_TYPES.map(v => (
            <option key={v.value} value={v.value}>{v.label}</option>
          ))}
        </select>

        <select
          value={voiceSettings.speed}
          onChange={(e) => handleVoiceSettingsChange('speed', e.target.value)}
          className="w-full p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50 transition-all"
        >
          <option value="slow">Slow</option>
          <option value="normal">Normal</option>
          <option value="fast">Fast</option>
        </select>
      </div>

      <div className="mt-4 flex items-center">
        <label className="flex items-center space-x-3 cursor-pointer">
          <input
            type="checkbox"
            checked={useStopMotion}
            onChange={(e) => setUseStopMotion(e.target.checked)}
            className="form-checkbox h-5 w-5 text-neon-blue rounded border-neon-blue/20 focus:ring-neon-blue/50 focus:ring-2 bg-dark-bg/50"
          />
          <span className="text-white">Enable Stop Motion Animation (Uses more resources)</span>
        </label>
      </div>
    </div>
  );
});

export default SettingsPanel;
