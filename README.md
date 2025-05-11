# Story Generator

An AI-powered web application that generates unique stories from your images. Upload one or multiple images and get a creative, cohesive story generated based on their content.

![Story Generator](frontend/public/images/story-generator-logo.png)

## Features

- **Multi-Image Upload**: Upload multiple images to generate a story that incorporates elements from all of them
- **Custom Story Settings**: Choose genre, length, and voice preferences
- **Audio Narration**: Listen to your stories with text-to-speech narration
- **Responsive Design**: Works on desktop and mobile devices
- **Visual Highlighting**: See which part of the story is being narrated in real-time

## Tech Stack

### Frontend

- React
- Tailwind CSS
- Axios for API calls
- Framer Motion for animations

### Backend

- Python
- Flask
- Gemini API for image understanding and story generation
- Text-to-speech services

## Installation and Setup

### Prerequisites

- Node.js (v14 or later)
- Python (v3.8 or later)
- Gemini API key

### Backend Setup

1. Clone the repository

   ```bash
   git clone https://github.com/yourusername/Story-Generator.git
   cd Story-Generator/backend
   ```

2. Create a virtual environment and activate it

   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the backend directory with your OpenAI API key

   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. Start the server
   ```bash
   python server.py
   ```

### Frontend Setup

1. Navigate to the frontend directory

   ```bash
   cd ../frontend
   ```

2. Install dependencies

   ```bash
   npm install
   ```

3. Start the development server

   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) to view it in your browser

## Deployment

### Backend

The backend can be deployed to platforms like:

- Render
- Heroku
- AWS Lambda

A Procfile and render.yaml are included for easy deployment.

### Frontend

The frontend can be deployed to:

- Vercel
- Netlify
- GitHub Pages

## Usage

1. Open the application in your browser
2. Upload one or multiple images by clicking on the upload area
3. Select your preferred genre and story length
4. Choose the narration voice and speed
5. Click "Generate Story"
6. View and listen to your generated story
7. Share your story or create a new one

## License

MIT

## Acknowledgements

- OpenAI for providing the image understanding and story generation APIs
- The React and Tailwind CSS communities for their excellent documentation and tools

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
