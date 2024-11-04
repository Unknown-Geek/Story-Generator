#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment"
    exit 1
fi

# Install/upgrade pip and requirements
echo "Installing requirements..."
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install requirements"
    deactivate
    exit 1
fi

echo "Setup completed successfully!"

# Ask to run the application
read -p "Do you want to run the application? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting the application..."
    python app.py
fi

# Deactivate virtual environment
deactivate

echo
echo "You can run the application later using:"
echo "source venv/bin/activate && python app.py"
read -p "Press Enter to exit..."

