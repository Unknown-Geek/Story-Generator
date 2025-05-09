# Setting Up the Story Generator Backend on Google Colab

This guide explains how to run the Story Generator backend server on Google Colab using ngrok for public access.

## Why Use Google Colab?

- **Free GPU Resources**: Access to computational resources for AI operations
- **No Local Setup**: Run the backend without installing anything on your computer
- **Temporary Deployment**: Perfect for demos and testing

## Prerequisites

- Google account (for accessing Google Colab)
- Google AI Gemini API key (get it from [Google AI Studio](https://ai.google.dev/))
- Optional: Hugging Face API key (for image generation features)
- Optional: ngrok account for longer session times (free account available at [ngrok.com](https://ngrok.com))

## Setup Instructions

### Step 1: Open the Colab Notebook

1. Open the following link in your browser:
   ```
   https://colab.research.google.com/github/Unknown-Geek/Story-Generator/blob/main/backend/colab_server.ipynb
   ```
   
   Alternatively, you can click the "Open Colab Notebook" button in the frontend application.

### Step 2: Set Up Your API Keys

You have two options to provide API keys:

#### Option A: Using Colab Secrets (Recommended)

1. In Colab, click on the 🔑 icon in the left sidebar
2. Add the following secrets:
   - `GOOGLE_API_KEY`: Your Google AI Gemini API key
   - `HUGGINGFACE_API_KEY`: Your Hugging Face API key (optional)
   - `NGROK_AUTH_TOKEN`: Your ngrok auth token (optional, extends connection time)

#### Option B: Enter Keys When Prompted

If you don't set up secrets, you'll be prompted to enter the API keys when running the notebook.

### Step 3: Run the Notebook

1. Click "Runtime" → "Run all" or use Ctrl+F9
2. Wait for all cells to execute
3. When execution is complete, you'll see an ngrok URL displayed

### Step 4: Connect to the Frontend

1. Copy the ngrok URL (e.g., `https://a1b2-c3d4-e5f6.ngrok.io`)
2. Paste it into the "Server Connection" field in the Story Generator frontend
3. Click "Connect"
4. The status indicator should turn green if the connection is successful

## Important Notes

- **Session Duration**: Free ngrok connections expire after 2 hours
- **Colab Timeout**: Colab sessions will disconnect after being idle for ~30 minutes
- **Keep Alive**: To prevent disconnection, either interact with the notebook occasionally or use a "keep-alive" script
- **Reconnecting**: If the connection is lost, you'll need to restart the Colab notebook and get a new ngrok URL

## Troubleshooting

- **Connection Error**: Make sure you're using the full URL including `https://`
- **Server Not Healthy**: Check the Colab notebook for error messages
- **Timeout Issues**: Your Colab session may have expired - restart the notebook
- **API Key Errors**: Verify your API keys are correct and have necessary permissions

For more help, please refer to the main project documentation or open an issue on GitHub. 