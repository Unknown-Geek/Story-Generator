
export const validateUrl = (url) => {
  if (!url) return null;
  url = url.trim();
  if (url.startsWith('file://')) {
    url = url.substring(7);
  }
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = `https://${url}`;
  }
  return url.split('/generate_story')[0];
};

export const formatStory = (story) => {
  const sentences = story.split('.');
  const paragraphs = [];
  let currentPara = [];

  sentences.forEach(sentence => {
    if (!sentence.trim()) return;
    currentPara.push(sentence.trim() + '.');
    if (currentPara.length >= 3) {
      paragraphs.push(currentPara.join(' '));
      currentPara = [];
    }
  });

  if (currentPara.length > 0) {
    paragraphs.push(currentPara.join(' '));
  }

  return paragraphs.join('\n\n');
};

export const processImage = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const maxSize = 1024;
        let width = img.width;
        let height = img.height;

        if (width > maxSize || height > maxSize) {
          const ratio = Math.min(maxSize / width, maxSize / height);
          width *= ratio;
          height *= ratio;
        }

        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL('image/jpeg', 0.85));
      };
      img.onerror = reject;
      img.src = event.target.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};