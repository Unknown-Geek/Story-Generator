
import React from 'react';
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';

const GenreSelector = ({ genre, onGenreChange }) => {
  const genres = [
    'Fantasy',
    'Adventure',
    'Romance',
    'Mystery',
    'Science Fiction',
    'Fairy Tale'
  ];

  return (
    <FormControl fullWidth>
      <InputLabel>Story Genre</InputLabel>
      <Select
        value={genre}
        onChange={(e) => onGenreChange(e.target.value)}
        label="Story Genre"
      >
        {genres.map((g) => (
          <MenuItem key={g} value={g.toLowerCase()}>
            {g}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default GenreSelector;