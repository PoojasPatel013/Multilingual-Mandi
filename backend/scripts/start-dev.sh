#!/bin/bash

# Development startup script for Multilingual Mandi Backend

set -e

echo "🚀 Starting Multilingual Mandi Backend Development Environment"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first."
    echo "Visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example"
    cp .env.example .env
    echo "✅ Please update .env file with your configuration"
fi

# Install dependencies
echo "📦 Installing dependencies..."
poetry install

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start database and Redis services
echo "🐘 Starting PostgreSQL and Redis services..."
docker-compose -f ../docker-compose.backend.yml up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run database migrations (when Alembic is set up)
echo "🔄 Running database migrations..."
# poetry run alembic upgrade head

# Start the FastAPI development server
echo "🌟 Starting FastAPI development server..."
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API documentation will be available at: http://localhost:8000/docs"
echo "🔍 Alternative docs at: http://localhost:8000/redoc"

poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload