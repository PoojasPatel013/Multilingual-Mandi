"""
Authentication endpoints.

This module provides authentication endpoints for user registration,
login, token refresh, and password management.
"""

from datetime import timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_password_reset_token,
    verify_password_reset_token
)
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    UserUpdate,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    VendorProfileCreate,
    VendorProfileResponse
)
from app.services.user_service import get_user_service

router = APIRouter()
settings = get_settings()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register new user account.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user information
        
    Raises:
        HTTPException: If email already exists or registration fails
    """
    user_service = get_user_service(db)
    
    try:
        user = await user_service.create_user(user_data)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Authenticate user and return access tokens.
    
    Args:
        login_data: User login credentials
        db: Database session
        
    Returns:
        JWT access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    user_service = get_user_service(db)
    
    user = await user_service.authenticate_user(
        login_data.email, 
        login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token.
    
    Args:
        token_data: Refresh token data
        db: Database session
        
    Returns:
        New JWT access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    payload = verify_token(token_data.refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists and is active
    user_service = get_user_service(db)
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await user_service.get_user_by_id(user_uuid)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(
        subject=str(user.id),
        expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update current user profile.
    
    Args:
        user_update: User update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If update fails
    """
    user_service = get_user_service(db)
    
    # Convert to dict and filter None values
    update_data = user_update.dict(exclude_unset=True)
    
    updated_user = await user_service.update_user_profile(
        current_user.id,
        update_data
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user profile"
        )
    
    return UserResponse.from_orm(updated_user)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Change user password.
    
    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If password change fails
    """
    user_service = get_user_service(db)
    
    success = await user_service.change_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password. Check your current password."
        )
    
    return {"message": "Password changed successfully"}


@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Request password reset token.
    
    Args:
        reset_data: Password reset request data
        db: Database session
        
    Returns:
        Success message (always returns success for security)
    """
    user_service = get_user_service(db)
    
    # Check if user exists (but don't reveal this information)
    user = await user_service.get_user_by_email(reset_data.email)
    
    if user and user.is_active:
        # Generate reset token
        reset_token = generate_password_reset_token(reset_data.email)
        
        # TODO: Send email with reset token
        # For now, we'll just log it (in production, send email)
        print(f"Password reset token for {reset_data.email}: {reset_token}")
    
    # Always return success message for security
    return {
        "message": "If the email exists, a password reset link has been sent"
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Confirm password reset with token.
    
    Args:
        reset_data: Password reset confirmation data
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If token is invalid or reset fails
    """
    # Verify reset token
    email = verify_password_reset_token(reset_data.token)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user_service = get_user_service(db)
    
    # Reset password
    success = await user_service.reset_password(email, reset_data.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reset password"
        )
    
    return {"message": "Password reset successfully"}


@router.post("/vendor-profile", response_model=VendorProfileResponse)
async def create_vendor_profile(
    profile_data: VendorProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create vendor profile for current user.
    
    Args:
        profile_data: Vendor profile data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created vendor profile
        
    Raises:
        HTTPException: If user is not a vendor or profile creation fails
    """
    from app.models.user import UserRole
    
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can create vendor profiles"
        )
    
    user_service = get_user_service(db)
    
    vendor_profile = await user_service.create_vendor_profile(
        current_user.id,
        profile_data
    )
    
    if not vendor_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create vendor profile"
        )
    
    return VendorProfileResponse.from_orm(vendor_profile)


@router.get("/vendor-profile", response_model=VendorProfileResponse)
async def get_vendor_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get vendor profile for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Vendor profile
        
    Raises:
        HTTPException: If user is not a vendor or profile not found
    """
    from app.models.user import UserRole
    
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can access vendor profiles"
        )
    
    user_service = get_user_service(db)
    
    vendor_profile = await user_service.get_vendor_profile(current_user.id)
    
    if not vendor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor profile not found"
        )
    
    return VendorProfileResponse.from_orm(vendor_profile)