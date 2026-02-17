#!/bin/bash

# Intelligent Document Analyzer - Startup Script

cd "$(dirname "$0")/app"

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Run the Flask app
echo ""
echo "Starting Intelligent Document Analyzer..."
echo "Open your browser and go to: http://127.0.0.1:8000"
echo ""
python3 app.py
