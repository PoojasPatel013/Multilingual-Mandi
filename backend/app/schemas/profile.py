"""
User profile schemas for enhanced profile management.

This module defines Pydantic models for user profile management including
cultural context, geographic location, and role-specific profile features.
"""

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.user import UserRole, VerificationStatus


class GeographicLocationSchema(BaseModel):
    """Schema for geographic location information."""
    
    country: str = Field(..., min_length=1, max_length=100)
    region: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    coordinates: Optional[Dict[str, float]] = Field(
        None, 
        description="Geographic coordinates as {'lat': float, 'lng': float}"
    )
    timezone: str = Field(..., min_length=1, max_length=50)
    currency: str = Field(..., min_length=1, max_length=10)
    
    @validator("coordinates")
    def validate_coordinates(cls, v):
        """Validate coordinates format."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Coordinates must be a dictionary")
            if "lat" not in v or "lng" not in v:
                raise ValueError("Coordinates must contain 'lat' and 'lng' keys")
            if not isinstance(v["lat"], (int, float)) or not isinstance(v["lng"], (int, float)):
                raise ValueError("Latitude and longitude must be numbers")
            if not (-90 <= v["lat"] <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= v["lng"] <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        return v


class CulturalContextSchema(BaseModel):
    """Schema for cultural context information."""
    
    region: str = Field(..., min_length=1, max_length=100)
    negotiation_style: str = Field(
        ..., 
        description="Negotiation style: 'direct', 'indirect', or 'relationship_based'"
    )
    time_orientation: str = Field(
        ..., 
        description="Time orientation: 'punctual' or 'flexible'"
    )
    communication_preferences: List[str] = Field(
        default_factory=list,
        description="List of communication preferences"
    )
    business_etiquette: List[str] = Field(
        default_factory=list,
        description="List of business etiquette guidelines"
    )
    holidays_and_events: List[str] = Field(
        default_factory=list,
        description="List of important holidays and cultural events"
    )
    
    @validator("negotiation_style")
    def validate_negotiation_style(cls, v):
        """Validate negotiation style."""
        allowed_styles = ["direct", "indirect", "relationship_based"]
        if v not in allowed_styles:
            raise ValueError(f"Negotiation style must be one of: {allowed_styles}")
        return v
    
    @validator("time_orientation")
    def validate_time_orientation(cls, v):
        """Validate time orientation."""
        allowed_orientations = ["punctual", "flexible"]
        if v not in allowed_orientations:
            raise ValueError(f"Time orientation must be one of: {allowed_orientations}")
        return v


class UserProfileUpdate(BaseModel):
    """Schema for comprehensive user profile updates."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    preferred_language: Optional[str] = Field(None, max_length=10)
    
    # Geographic information
    geographic_location: Optional[GeographicLocationSchema] = None
    
    # Cultural context
    cultural_context: Optional[CulturalContextSchema] = None
    
    # Verification documents (for admin use)
    verification_documents: Optional[Dict] = Field(
        None,
        description="Document references for verification"
    )


class UserProfileResponse(BaseModel):
    """Schema for comprehensive user profile response."""
    
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    phone_number: Optional[str] = None
    preferred_language: str
    
    # Geographic information
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    
    # Cultural context
    cultural_profile: Optional[Dict] = None
    
    # Verification
    verification_status: VerificationStatus
    verification_documents: Optional[Dict] = None
    
    # Activity tracking
    is_active: bool
    created_at: str
    last_active: Optional[str] = None
    login_count: int
    
    class Config:
        from_attributes = True


class VendorProfileUpdate(BaseModel):
    """Schema for vendor profile updates."""
    
    business_name: Optional[str] = Field(None, min_length=1, max_length=200)
    business_type: Optional[str] = Field(None, max_length=100)
    business_description: Optional[str] = None
    market_stall: Optional[str] = Field(None, max_length=100)
    
    # Languages and communication
    languages: Optional[List[str]] = Field(
        None,
        description="List of supported languages (ISO codes)"
    )
    communication_preferences: Optional[Dict] = Field(
        None,
        description="Communication preferences and settings"
    )
    
    # Payment methods
    payment_methods: Optional[List[Dict]] = Field(
        None,
        description="List of supported payment methods"
    )
    
    # Business hours and availability
    business_hours: Optional[Dict] = Field(
        None,
        description="Business operating hours"
    )
    is_available: Optional[bool] = None
    
    @validator("languages")
    def validate_languages(cls, v):
        """Validate language codes."""
        if v is not None:
            # Basic validation for language codes (should be 2-5 characters)
            for lang in v:
                if not isinstance(lang, str) or not (2 <= len(lang) <= 5):
                    raise ValueError("Language codes should be 2-5 character strings")
        return v


class CustomerProfileResponse(BaseModel):
    """Schema for customer-specific profile information."""
    
    id: UUID
    user_id: UUID
    
    # Shopping preferences
    preferred_categories: Optional[List[str]] = Field(
        default_factory=list,
        description="Preferred product categories"
    )
    price_range_preferences: Optional[Dict[str, Dict[str, float]]] = Field(
        default_factory=dict,
        description="Price range preferences by category"
    )
    
    # Purchase history summary
    total_purchases: int = Field(default=0)
    total_spent: float = Field(default=0.0)
    average_rating_given: float = Field(default=0.0)
    
    # Wishlist and favorites
    wishlist_items: Optional[List[UUID]] = Field(
        default_factory=list,
        description="List of product IDs in wishlist"
    )
    favorite_vendors: Optional[List[UUID]] = Field(
        default_factory=list,
        description="List of favorite vendor IDs"
    )
    
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class PaymentMethodCreate(BaseModel):
    """Schema for creating payment methods."""
    
    method_type: str = Field(
        ..., 
        description="Payment method type (card, bank, mobile, etc.)"
    )
    provider: Optional[str] = Field(
        None, 
        max_length=100,
        description="Payment provider (Stripe, PayPal, etc.)"
    )
    details: Dict = Field(
        ...,
        description="Payment method details (encrypted)"
    )
    is_default: bool = Field(default=False)
    
    @validator("method_type")
    def validate_method_type(cls, v):
        """Validate payment method type."""
        allowed_types = [
            "card", "bank", "mobile", "digital_wallet", 
            "cryptocurrency", "cash", "other"
        ]
        if v not in allowed_types:
            raise ValueError(f"Payment method type must be one of: {allowed_types}")
        return v


class PaymentMethodResponse(BaseModel):
    """Schema for payment method response."""
    
    id: UUID
    user_id: UUID
    method_type: str
    provider: Optional[str] = None
    # Note: details are not included in response for security
    is_active: bool
    is_default: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class UserVerificationUpdate(BaseModel):
    """Schema for updating user verification status (admin only)."""
    
    verification_status: VerificationStatus
    verification_documents: Optional[Dict] = Field(
        None,
        description="Document references and verification notes"
    )
    admin_notes: Optional[str] = Field(
        None,
        description="Admin notes about verification decision"
    )