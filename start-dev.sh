#!/bin/bash

# MLB Probability Tracker - Development Start Script

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found."
fi

echo "Starting MLB Probability Tracker Backend..."
echo "Access the dashboard at http://127.0.0.1:5000"

# Run the Flask application using uv
uv run python -m app.app
