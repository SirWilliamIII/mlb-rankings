#!/bin/bash

# MLB Probability Tracker - Development Start Script

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found."
fi

# Start PostgreSQL container if not running and DATABASE_URL is not set
if [ -z "$DATABASE_URL" ] && command -v docker &> /dev/null; then
    if ! docker ps --format '{{.Names}}' | grep -q 'mlb-rankings-db'; then
        echo "Starting PostgreSQL container..."
        docker compose up -d db
        echo "Waiting for PostgreSQL to be ready..."
        sleep 3
    else
        echo "PostgreSQL container already running."
    fi

    # Export DATABASE_URL to connect to Dockerized PostgreSQL
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/mlb_stats"
else
    if [ -n "$DATABASE_URL" ]; then
        echo "Using existing DATABASE_URL."
    else
        echo "Docker not found and DATABASE_URL not set. Using SQLite fallback."
    fi
fi

echo ""
echo "Starting MLB Probability Tracker Backend..."
echo "Access the dashboard at http://127.0.0.1:5555"

# Run the Flask application using uv
uv run python -m app.app
