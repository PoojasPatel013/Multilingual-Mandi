"""
Authentication schemas for request/response validation.

This module defines Pydantic models for authentication-related API endpoints
including user registration, login, and token management.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from app.models.user import UserRole, VerificationStatus


class UserRegister(BaseModel):
    """Schema for user registration request."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=100,
        description="User password (minimum 8 characters)"
    )
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = Field(..., description="User role (vendor or customer)")
    phone_number: Optional[str] = Field(None, max_length=20)
    preferred_language: str = Field(default="en", max_length=10)
    
    # Geographic information
    country: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=10)
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one digit
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        
        # Check for at least one letter
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        
        return v
    
    @validator("role")
    def validate_role(cls, v):
        """Validate user role - admin role cannot be set during registration."""
        if v == UserRole.ADMIN:
            raise ValueError("Admin role cannot be assigned during registration")
        return v


class UserLogin(BaseModel):
    """Schema for user login request."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """Schema for authentication token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    
    refresh_token: str = Field(..., description="JWT refresh token")


class UserResponse(BaseModel):
    """Schema for user information response."""
    
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    phone_number: Optional[str] = None
    preferred_language: str
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    verification_status: VerificationStatus
    is_active: bool
    created_at: str
    last_active: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for user profile update request."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    preferred_language: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=10)


class PasswordChange(BaseModel):
    """Schema for password change request."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=100,
        description="New password (minimum 8 characters)"
    )
    
    @validator("new_password")
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one digit
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        
        # Check for at least one letter
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        
        return v


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=100,
        description="New password (minimum 8 characters)"
    )
    
    @validator("new_password")
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one digit
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        
        # Check for at least one letter
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        
        return v


class VendorProfileCreate(BaseModel):
    """Schema for creating vendor profile."""
    
    business_name: str = Field(..., min_length=1, max_length=200)
    business_type: Optional[str] = Field(None, max_length=100)
    business_description: Optional[str] = None
    market_stall: Optional[str] = Field(None, max_length=100)
    languages: Optional[list] = Field(default_factory=list)
    communication_preferences: Optional[dict] = Field(default_factory=dict)
    payment_methods: Optional[list] = Field(default_factory=list)
    business_hours: Optional[dict] = Field(default_factory=dict)


class VendorProfileResponse(BaseModel):
    """Schema for vendor profile response."""
    
    id: UUID
    user_id: UUID
    business_name: str
    business_type: Optional[str] = None
    business_description: Optional[str] = None
    market_stall: Optional[str] = None
    average_rating: float
    total_sales: int
    total_reviews: int
    languages: Optional[list] = None
    communication_preferences: Optional[dict] = None
    payment_methods: Optional[list] = None
    business_hours: Optional[dict] = None
    is_available: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True