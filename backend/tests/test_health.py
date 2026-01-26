"""
Test health check endpoints.

This module tests the health check functionality to ensure the API
and its dependencies are working correctly.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
@pytest.mark.asyncio
async def test_basic_health_check(client: AsyncClient):
    """
    Test basic health check endpoint.
    
    Args:
        client: Test HTTP client
    """
    response = await client.get("/api/v1/health/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["service"] == "multilingual-mandi-api"
    assert data["version"] == "1.0.0"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detailed_health_check(client: AsyncClient):
    """
    Test detailed health check endpoint.
    
    Args:
        client: Test HTTP client
    """
    response = await client.get("/api/v1/health/detailed")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["service"] == "multilingual-mandi-api"
    assert data["version"] == "1.0.0"
    assert "checks" in data
    
    # Check that database and Redis checks are present
    checks = data["checks"]
    assert "database" in checks
    assert "redis" in checks
    
    # In test environment, these should be healthy
    assert checks["database"] == "healthy"
    assert checks["redis"] == "healthy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_main_health_endpoint(client: AsyncClient):
    """
    Test main health endpoint.
    
    Args:
        client: Test HTTP client
    """
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["service"] == "multilingual-mandi-api"