# Story Generator

An AI-powered application that generates stories based on uploaded images using Google's Gemini API.

## Features

- Upload an image and generate a story based on it
- Choose from different story genres
- Adjust story length
- Text-to-speech narration with voice options
- Optional animated image frames
- **NEW: Google Colab Backend Server** - Run the backend on Colab with zero setup!

## Running the Backend

### Option 1: Google Colab (Recommended for quick start)

You can now run the backend server on Google Colab without any local installation:

1. Open the application and click the "Open Colab Notebook" button
2. Follow the instructions in the notebook
3. Copy the generated ngrok URL and paste it in the application
4. Click "Connect" to start using the Colab backend

For detailed instructions, see [Colab Setup Guide](backend/COLAB_SETUP.md).

### Option 2: Local Server

If you prefer to run the backend locally:

1. Navigate to the backend folder: `cd backend`
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see below)
4. Run the server: `python server.py`

## Environment Variables

Create a `.env` file in the root directory with:

```
GOOGLE_API_KEY=your_google_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
```

## Running the Frontend

In the project directory, you can run:

### `npm start`

Runs the app in development mode at [http://localhost:3000](http://localhost:3000)

### `npm run build`

Builds the app for production to the `build` folder

## Deployment

The application is configured for deployment on Vercel. The frontend communicates with the backend API hosted on Render or through the Google Colab notebook.

## Learn More

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app). For more information on React and Create React App, check out the [React documentation](https://reactjs.org/).
