"""
Main API router for version 1.

This module aggregates all API endpoints for the Multilingual Mandi platform.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, auth, profile

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])

# Additional routers will be added as we implement more features
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(products.router, prefix="/products", tags=["products"])
# api_router.include_router(negotiations.router, prefix="/negotiations", tags=["negotiations"])
# api_router.include_router(translations.router, prefix="/translations", tags=["translations"])