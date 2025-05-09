import React, { useState, useEffect } from 'react';

const ServerConnection = ({ onServerUrlChange, serverUrl, isConnected }) => {
  const [inputUrl, setInputUrl] = useState(serverUrl || '');
  const [isValidating, setIsValidating] = useState(false);
  const [validationError, setValidationError] = useState('');

  const openColabNotebook = () => {
    window.open('https://colab.research.google.com/github/Unknown-Geek/Story-Generator/blob/main/backend/colab_server.ipynb', '_blank');
  };

  const handleConnect = async () => {
    if (!inputUrl) {
      setValidationError('Please enter the ngrok URL');
      return;
    }

    // Validate URL format
    if (!inputUrl.startsWith('http')) {
      setValidationError('Invalid URL format. It should start with http:// or https://');
      return;
    }

    setIsValidating(true);
    setValidationError('');

    try {
      // Remove trailing slash if present
      const cleanUrl = inputUrl.endsWith('/') ? inputUrl.slice(0, -1) : inputUrl;
      
      // Test the connection
      const response = await fetch(`${cleanUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 5000
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'healthy') {
          onServerUrlChange(cleanUrl);
          setValidationError('');
          // Save the URL to localStorage
          localStorage.setItem('colabServerUrl', cleanUrl);
        } else {
          setValidationError('Server is not healthy. Please check the Colab notebook.');
        }
      } else {
        setValidationError('Could not connect to server. Please check the URL.');
      }
    } catch (error) {
      setValidationError(`Connection error: ${error.message}`);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white text-lg font-medium">Server Connection</h3>
        <div className="flex items-center">
          <div className={`h-3 w-3 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-300">{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>
      
      <div className="flex flex-col md:flex-row gap-3 mb-3">
        <button
          onClick={openColabNotebook}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors font-medium flex items-center justify-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.416 4.608C20.169 4.476 19.875 4.468 19.621 4.587L12.776 8.086C12.599 8.174 12.401 8.174 12.224 8.086L5.379 4.587C5.125 4.468 4.831 4.476 4.584 4.608C4.336 4.741 4.184 5.0 4.184 5.282V15.718C4.184 16.046 4.376 16.338 4.667 16.467L11.667 19.966C11.772 20.011 11.886 20.034 12 20.034C12.114 20.034 12.228 20.011 12.333 19.966L19.333 16.467C19.624 16.338 19.816 16.046 19.816 15.718V5.282C19.816 5.0 19.664 4.741 19.416 4.608ZM18.184 14.981L12 18.052L5.816 14.981V6.019L11.328 9.132C11.752 9.344 12.248 9.344 12.672 9.132L18.184 6.019V14.981Z" />
          </svg>
          Open Colab Notebook
        </button>
        
        <div className="flex-1 flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            placeholder="Paste ngrok URL here (e.g., https://xxxx-xxxx.ngrok.io)"
            className="flex-1 p-2 rounded bg-dark-bg/50 border border-neon-blue/20 text-white focus:border-neon-blue/50 focus:ring-1 focus:ring-neon-blue/50"
          />
          
          <button
            onClick={handleConnect}
            disabled={isValidating}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isValidating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Connecting...
              </>
            ) : (
              'Connect'
            )}
          </button>
        </div>
      </div>
      
      {validationError && (
        <div className="text-red-400 text-sm mb-4 bg-red-900/20 border border-red-500/20 rounded-lg p-2">
          {validationError}
        </div>
      )}
    </div>
  );
};

export default ServerConnection; 