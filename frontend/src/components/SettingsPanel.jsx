import React, { memo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { ChevronDown } from 'lucide-react';

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

const CustomSelect = ({ value, onChange, options, label }) => (
  <div className="relative group">
    <select
      value={value}
      onChange={onChange}
      className="w-full p-4 pl-6 pr-12 rounded-lg appearance-none
                 bg-gradient-to-br from-[rgba(10,10,31,0.6)] to-[rgba(0,5,16,0.7)]
                 border border-neon-blue/20 text-white/90
                 focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50
                 transition-all duration-300 text-lg
                 hover:border-neon-blue/40 hover:shadow-neon
                 cursor-pointer backdrop-blur-sm"
    >
      {options.map(opt => (
        <option 
          key={typeof opt === 'string' ? opt : opt.value} 
          value={typeof opt === 'string' ? opt : opt.value}
          className="bg-dark-bg text-white"
        >
          {typeof opt === 'string' ? opt : opt.label}
        </option>
      ))}
    </select>
    <motion.div 
      className="absolute right-4 top-1/2 -translate-y-1/2 text-neon-blue/70 pointer-events-none"
      animate={{ rotate: 0 }}
      whileTap={{ rotate: 180 }}
    >
      <ChevronDown size={24} />
    </motion.div>
    {label && (
      <motion.span 
        className="absolute -top-3 left-4 px-2 text-sm text-neon-blue/80 bg-dark-bg rounded"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {label}
      </motion.span>
    )}
  </div>
);

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
    <motion.div 
      className="bg-[rgba(10,10,31,0.8)] border border-neon-blue/10 rounded-lg p-8 mb-8 backdrop-blur-md shadow-neon"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <CustomSelect
          value={genre}
          onChange={(e) => setGenre(e.target.value)}
          options={GENRES}
          label="Story Genre"
        />

        <CustomSelect
          value={length}
          onChange={(e) => setLength(Number(e.target.value))}
          options={STORY_LENGTHS}
          label="Story Length"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <CustomSelect
          value={voiceSettings.accent}
          onChange={(e) => handleVoiceSettingsChange('accent', e.target.value)}
          options={VOICE_TYPES}
          label="Voice Accent"
        />

        <CustomSelect
          value={voiceSettings.speed}
          onChange={(e) => handleVoiceSettingsChange('speed', e.target.value)}
          options={[
            { label: "Slow", value: "slow" },
            { label: "Normal", value: "normal" },
            { label: "Fast", value: "fast" }
          ]}
          label="Narration Speed"
        />
      </div>

      <motion.div 
        className="mt-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <label className="flex items-center space-x-3 cursor-pointer group">
          <input
            type="checkbox"
            checked={useStopMotion}
            onChange={(e) => setUseStopMotion(e.target.checked)}
            className="form-checkbox h-5 w-5 text-neon-blue rounded border-neon-blue/20 
                      focus:ring-neon-blue/50 focus:ring-2 bg-dark-bg/50
                      transition-all duration-300 cursor-pointer"
          />
          <span className="text-white/90 group-hover:text-white transition-colors duration-300">
            Enable Stop Motion Animation (Uses more resources)
          </span>
        </label>
      </motion.div>
    </motion.div>
  );
});

export default SettingsPanel;
