# Makefile for AI Legal Aid System

.PHONY: help install install-dev test test-unit test-property test-integration lint format type-check clean build docs run

# Default target
help:
	@echo "AI Legal Aid System - Available commands:"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run all tests"
	@echo "  test-unit    Run unit tests only"
	@echo "  test-property Run property-based tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-coverage Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         Run linting (flake8)"
	@echo "  format       Format code (black + isort)"
	@echo "  type-check   Run type checking (mypy)"
	@echo "  quality      Run all quality checks"
	@echo ""
	@echo "Development:"
	@echo "  run          Run the application"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build the package"
	@echo "  docs         Generate documentation"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/ -v -m "unit"

test-property:
	pytest tests/ -v -m "property"

test-integration:
	pytest tests/ -v -m "integration"

test-coverage:
	pytest tests/ --cov=src/ai_legal_aid --cov-report=html --cov-report=term

# Code Quality
lint:
	flake8 src/ tests/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

quality: lint type-check
	@echo "All quality checks passed!"

# Development
run:
	python -m ai_legal_aid.main

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .hypothesis/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

docs:
	cd docs && make html

# Development workflow
dev-setup: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything works."

# CI/CD helpers
ci-test: install-dev test-coverage quality
	@echo "CI tests completed successfully!"

# Docker helpers (for future use)
docker-build:
	docker build -t ai-legal-aid:latest .

docker-run:
	docker run -it --rm ai-legal-aid:latest

# Database helpers (for future use)
db-migrate:
	alembic upgrade head

db-reset:
	alembic downgrade base
	alembic upgrade head