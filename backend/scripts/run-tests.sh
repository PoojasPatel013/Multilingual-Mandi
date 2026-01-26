#!/bin/bash

# Test runner script for Multilingual Mandi Backend

set -e

echo "🧪 Running Multilingual Mandi Backend Tests"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first."
    exit 1
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
poetry install --with dev

# Set test environment variables
export ENVIRONMENT=testing
export DATABASE_URL=sqlite+aiosqlite:///:memory:
export REDIS_URL=redis://localhost:6379/15

# Run different types of tests based on arguments
case "${1:-all}" in
    "unit")
        echo "🔬 Running unit tests..."
        poetry run pytest tests/ -m "unit" -v --tb=short
        ;;
    "integration")
        echo "🔗 Running integration tests..."
        poetry run pytest tests/ -m "integration" -v --tb=short
        ;;
    "property")
        echo "🎲 Running property-based tests..."
        poetry run pytest tests/ -m "property" -v --tb=short
        ;;
    "coverage")
        echo "📊 Running tests with coverage..."
        poetry run pytest tests/ --cov=app --cov-report=html --cov-report=term-missing -v
        echo "📈 Coverage report generated in htmlcov/index.html"
        ;;
    "fast")
        echo "⚡ Running fast tests only..."
        poetry run pytest tests/ -m "not slow" -v --tb=short
        ;;
    "all"|*)
        echo "🎯 Running all tests..."
        poetry run pytest tests/ -v --tb=short
        ;;
esac

echo "✅ Tests completed!"