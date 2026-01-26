"""
Health check endpoints.

This module provides health check endpoints for monitoring the application
and its dependencies.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        dict: Basic health status
    """
    return {
        "status": "healthy",
        "service": "multilingual-mandi-api",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check including database and Redis connectivity.
    
    Args:
        db: Database session
        
    Returns:
        dict: Detailed health status
        
    Raises:
        HTTPException: If any service is unhealthy
    """
    health_status = {
        "status": "healthy",
        "service": "multilingual-mandi-api",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check database connectivity
    try:
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis connectivity
    try:
        redis_client = get_redis()
        await redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status