"""
Basic setup test to verify the core infrastructure is working.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)


def test_app_imports():
    """Test that the FastAPI app can be imported successfully."""
    from app.main import app
    assert app is not None
    assert app.title == "Multilingual Mandi API"


def test_health_endpoint():
    """Test the basic health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "multilingual-mandi-api"


def test_api_health_endpoint():
    """Test the API health endpoint."""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "multilingual-mandi-api"
    assert data["version"] == "1.0.0"


def test_app_configuration():
    """Test that the app is configured correctly."""
    from app.core.config import get_settings
    settings = get_settings()
    assert settings.APP_NAME == "Multilingual Mandi"
    assert settings.VERSION == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])