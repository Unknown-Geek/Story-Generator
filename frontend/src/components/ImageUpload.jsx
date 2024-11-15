import React, { useState } from 'react';
import { Button } from '@mui/material';
import { processImage } from '../utils/helpers';

const ImageUpload = ({ onImageSelect }) => {
  const [preview, setPreview] = useState(null);

  const handleImageChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const base64Image = await processImage(file);
      setPreview(base64Image);
      onImageSelect(base64Image);
    } catch (error) {
      console.error('Error processing image:', error);
    }
  };

  return (
    <div className="image-upload">
      <input
        type="file"
        accept="image/*"
        onChange={handleImageChange}
        style={{ display: 'none' }}
        id="image-input"
      />
      <label htmlFor="image-input">
        <Button variant="contained" component="span">
          Upload Image
        </Button>
      </label>
      {preview && (
        <div className="preview-container mt-4">
          <img src={preview} alt="Preview" className="max-w-full h-auto" />
        </div>
      )}
    </div>
  );
};

export default ImageUpload;