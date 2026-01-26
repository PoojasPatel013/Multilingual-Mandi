"""
FastAPI dependencies for authentication and authorization.

This module provides dependency functions for JWT token verification,
user authentication, and role-based access control.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth import verify_token
from app.core.database import get_db
from app.models.user import User, UserRole

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    payload = verify_token(credentials.credentials, token_type="access")
    if payload is None:
        raise credentials_exception
    
    # Extract user ID from token
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_vendor(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user if they are a vendor.
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Current vendor user
        
    Raises:
        HTTPException: If user is not a vendor
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Vendor role required."
        )
    return current_user


async def get_current_customer(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user if they are a customer.
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Current customer user
        
    Raises:
        HTTPException: If user is not a customer
    """
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Customer role required."
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user if they are an admin.
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Current admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user if they are a superuser.
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Current superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Superuser role required."
        )
    return current_user


def get_optional_current_user():
    """
    Dependency to get current user optionally (for public endpoints).
    
    Returns:
        Optional[User]: Current user if authenticated, None otherwise
    """
    async def _get_optional_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(
            HTTPBearer(auto_error=False)
        ),
        db: AsyncSession = Depends(get_db)
    ) -> Optional[User]:
        if credentials is None:
            return None
        
        try:
            # Verify token
            payload = verify_token(credentials.credentials, token_type="access")
            if payload is None:
                return None
            
            # Extract user ID from token
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                return None
            
            try:
                user_id = UUID(user_id_str)
            except ValueError:
                return None
            
            # Get user from database
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user is None or not user.is_active:
                return None
            
            return user
            
        except Exception:
            return None
    
    return _get_optional_current_user