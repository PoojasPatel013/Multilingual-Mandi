"""
Negotiation schemas for request/response validation.

This module defines Pydantic models for negotiation-related API endpoints
including negotiation management, messaging, and cultural context.
"""

from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, validator

from app.models.negotiation import (
    NegotiationStatus, MessageType, NegotiationEventType
)


class NegotiationCreate(BaseModel):
    """Schema for negotiation creation request."""
    
    product_id: UUID = Field(..., description="Product being negotiated")
    vendor_id: UUID = Field(..., description="Vendor user ID")
    initial_price: float = Field(..., gt=0, description="Initial asking price")
    quantity: int = Field(default=1, ge=1, description="Quantity being negotiated")
    expires_at: Optional[datetime] = Field(None, description="Negotiation expiration")
    cultural_context: Optional[Dict] = Field(default_factory=dict)
    language_pair: Optional[Dict] = Field(default_factory=dict)
    
    @validator("language_pair")
    def validate_language_pair(cls, v):
        """Validate language pair format."""
        if v:
            if "vendor" not in v or "customer" not in v:
                raise ValueError("Language pair must include 'vendor' and 'customer' keys")
            for lang in v.values():
                if not isinstance(lang, str) or len(lang) < 2:
                    raise ValueError("Language codes must be valid strings")
        return v


class NegotiationUpdate(BaseModel):
    """Schema for negotiation update request."""
    
    status: Optional[NegotiationStatus] = None
    current_offer: Optional[float] = Field(None, gt=0)
    final_price: Optional[float] = Field(None, gt=0)
    expires_at: Optional[datetime] = None
    cultural_context: Optional[Dict] = None


class NegotiationResponse(BaseModel):
    """Schema for negotiation response."""
    
    id: UUID
    product_id: UUID
    vendor_id: UUID
    customer_id: UUID
    
    # Negotiation details
    initial_price: float
    current_offer: float
    final_price: Optional[float] = None
    quantity: int
    
    # Status and timeline
    status: NegotiationStatus
    expires_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Cultural context
    cultural_context: Optional[Dict] = None
    language_pair: Optional[Dict] = None
    
    # Metrics
    total_messages: int
    total_offers: int
    duration_minutes: int
    ai_suggestions_used: int
    cultural_tips_provided: int
    
    # Timestamps
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class NegotiationMessageCreate(BaseModel):
    """Schema for negotiation message creation."""
    
    negotiation_id: UUID = Field(..., description="Negotiation ID")
    original_text: str = Field(..., min_length=1, description="Message text")
    message_type: MessageType = Field(default=MessageType.TEXT)
    original_language: Optional[str] = Field(None, max_length=10)
    target_language: Optional[str] = Field(None, max_length=10)
    cultural_context: Optional[Dict] = Field(default_factory=dict)
    
    @validator("original_text")
    def validate_message_text(cls, v):
        """Validate message text."""
        if len(v.strip()) == 0:
            raise ValueError("Message text cannot be empty")
        if len(v) > 2000:
            raise ValueError("Message text cannot exceed 2000 characters")
        return v.strip()


class NegotiationMessageResponse(BaseModel):
    """Schema for negotiation message response."""
    
    id: UUID
    negotiation_id: UUID
    sender_id: UUID
    
    # Message content
    original_text: str
    translated_text: Optional[str] = None
    original_language: Optional[str] = None
    target_language: Optional[str] = None
    
    # Message metadata
    message_type: MessageType
    is_read: bool
    read_at: Optional[str] = None
    
    # Translation metadata
    translation_confidence: Optional[float] = None
    translation_alternatives: Optional[List[str]] = None
    
    # Cultural context
    cultural_context: Optional[Dict] = None
    
    # Timestamps
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class NegotiationEventCreate(BaseModel):
    """Schema for negotiation event creation."""
    
    negotiation_id: UUID = Field(..., description="Negotiation ID")
    event_type: NegotiationEventType = Field(..., description="Event type")
    amount: Optional[float] = Field(None, gt=0, description="Offer amount")
    previous_amount: Optional[float] = Field(None, gt=0, description="Previous amount")
    terms: Optional[str] = Field(None, description="Event terms")
    cultural_context: Optional[Dict] = Field(default_factory=dict)
    ai_suggested: bool = Field(default=False, description="AI suggested action")
    
    @validator("amount")
    def validate_amount_for_offer_events(cls, v, values):
        """Validate amount is provided for offer/counteroffer events."""
        if "event_type" in values:
            offer_events = [NegotiationEventType.OFFER, NegotiationEventType.COUNTEROFFER]
            if values["event_type"] in offer_events and v is None:
                raise ValueError("Amount is required for offer and counteroffer events")
        return v


class NegotiationEventResponse(BaseModel):
    """Schema for negotiation event response."""
    
    id: UUID
    negotiation_id: UUID
    user_id: UUID
    
    # Event details
    event_type: NegotiationEventType
    amount: Optional[float] = None
    previous_amount: Optional[float] = None
    
    # Event metadata
    terms: Optional[str] = None
    cultural_context: Optional[Dict] = None
    ai_suggested: bool
    
    # Timestamps
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class CulturalProfileCreate(BaseModel):
    """Schema for cultural profile creation."""
    
    user_id: UUID = Field(..., description="User ID")
    region: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    cultural_group: Optional[str] = Field(None, max_length=100)
    
    # Communication preferences
    negotiation_style: Optional[str] = Field(None, max_length=50)
    time_orientation: Optional[str] = Field(None, max_length=50)
    communication_preferences: Optional[List[str]] = Field(default_factory=list)
    
    # Business etiquette
    business_etiquette: Optional[List[str]] = Field(default_factory=list)
    greeting_customs: Optional[List[str]] = Field(default_factory=list)
    gift_giving_customs: Optional[List[str]] = Field(default_factory=list)
    
    # Calendar and events
    holidays_and_events: Optional[List[str]] = Field(default_factory=list)
    business_hours_culture: Optional[Dict] = Field(default_factory=dict)
    
    # Language preferences
    preferred_languages: Optional[List[str]] = Field(default_factory=list)
    formality_preferences: Optional[Dict] = Field(default_factory=dict)
    
    @validator("negotiation_style")
    def validate_negotiation_style(cls, v):
        """Validate negotiation style."""
        if v is not None:
            allowed_styles = ["direct", "indirect", "relationship_based"]
            if v not in allowed_styles:
                raise ValueError(f"Negotiation style must be one of: {allowed_styles}")
        return v
    
    @validator("time_orientation")
    def validate_time_orientation(cls, v):
        """Validate time orientation."""
        if v is not None:
            allowed_orientations = ["punctual", "flexible"]
            if v not in allowed_orientations:
                raise ValueError(f"Time orientation must be one of: {allowed_orientations}")
        return v


class CulturalProfileResponse(BaseModel):
    """Schema for cultural profile response."""
    
    id: UUID
    user_id: UUID
    region: str
    country: str
    cultural_group: Optional[str] = None
    
    # Communication preferences
    negotiation_style: Optional[str] = None
    time_orientation: Optional[str] = None
    communication_preferences: Optional[List[str]] = None
    
    # Business etiquette
    business_etiquette: Optional[List[str]] = None
    greeting_customs: Optional[List[str]] = None
    gift_giving_customs: Optional[List[str]] = None
    
    # Calendar and events
    holidays_and_events: Optional[List[str]] = None
    business_hours_culture: Optional[Dict] = None
    
    # Language preferences
    preferred_languages: Optional[List[str]] = None
    formality_preferences: Optional[Dict] = None
    
    # Timestamps
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class TranslationCacheResponse(BaseModel):
    """Schema for translation cache response."""
    
    id: UUID
    source_text: str
    source_language: str
    target_language: str
    translated_text: str
    context: Optional[str] = None
    confidence: float
    provider: Optional[str] = None
    usage_count: int
    last_used: str
    is_verified: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class NegotiationListResponse(BaseModel):
    """Schema for negotiation list response with pagination."""
    
    negotiations: List[NegotiationResponse]
    total: int
    page: int
    size: int
    pages: int


class NegotiationSearchRequest(BaseModel):
    """Schema for negotiation search request."""
    
    status: Optional[NegotiationStatus] = None
    product_id: Optional[UUID] = None
    vendor_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: Optional[str] = Field(default="created_at", pattern="^(created_at|current_offer|status)$")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    
    @validator("max_price")
    def validate_price_range(cls, v, values):
        """Validate price range."""
        if v is not None and "min_price" in values and values["min_price"] is not None:
            if v < values["min_price"]:
                raise ValueError("Maximum price must be greater than minimum price")
        return v
    
    @validator("date_to")
    def validate_date_range(cls, v, values):
        """Validate date range."""
        if v is not None and "date_from" in values and values["date_from"] is not None:
            if v < values["date_from"]:
                raise ValueError("End date must be after start date")
        return v


class NegotiationAdviceRequest(BaseModel):
    """Schema for negotiation advice request."""
    
    negotiation_id: UUID = Field(..., description="Negotiation ID")
    current_context: Optional[Dict] = Field(default_factory=dict)
    request_type: str = Field(..., description="Type of advice requested")
    
    @validator("request_type")
    def validate_request_type(cls, v):
        """Validate advice request type."""
        allowed_types = [
            "opening_suggestion", "counteroffer_advice", "cultural_tip",
            "fairness_evaluation", "compromise_suggestion"
        ]
        if v not in allowed_types:
            raise ValueError(f"Request type must be one of: {allowed_types}")
        return v


class NegotiationAdviceResponse(BaseModel):
    """Schema for negotiation advice response."""
    
    negotiation_id: UUID
    advice_type: str
    suggested_response: Optional[str] = None
    cultural_tips: Optional[List[str]] = None
    fairness_score: Optional[float] = None
    alternative_offers: Optional[List[float]] = None
    reasoning: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    class Config:
        from_attributes = True