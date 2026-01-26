"""
Product schemas for request/response validation.

This module defines Pydantic models for product-related API endpoints
including product creation, updates, and responses.
"""

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.product import AvailabilityStatus, TranslationSource


class ProductTranslationSchema(BaseModel):
    """Schema for product translation data."""
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    language: str = Field(..., min_length=2, max_length=10)
    translated_by: TranslationSource = Field(default=TranslationSource.AI)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @validator("language")
    def validate_language(cls, v):
        """Validate language code format."""
        if not v.isalpha():
            raise ValueError("Language code must contain only letters")
        return v.lower()


class ProductCreate(BaseModel):
    """Schema for product creation request."""
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    sku: Optional[str] = Field(None, max_length=100)
    
    # Pricing
    base_price: float = Field(..., gt=0, description="Base price must be positive")
    current_price: float = Field(..., gt=0, description="Current price must be positive")
    currency: str = Field(default="USD", max_length=10)
    
    # Inventory
    quantity_available: int = Field(default=0, ge=0)
    minimum_quantity: int = Field(default=1, ge=1)
    availability: AvailabilityStatus = Field(default=AvailabilityStatus.IN_STOCK)
    
    # Media and specifications
    images: Optional[List[str]] = Field(default_factory=list)
    specifications: Optional[Dict] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)
    
    # Translations
    translations: Optional[Dict[str, ProductTranslationSchema]] = Field(default_factory=dict)
    
    # Status
    is_active: bool = Field(default=True)
    is_featured: bool = Field(default=False)
    
    @validator("current_price")
    def validate_current_price(cls, v, values):
        """Validate current price against base price."""
        if "base_price" in values and v > values["base_price"] * 2:
            raise ValueError("Current price cannot be more than double the base price")
        return v
    
    @validator("images")
    def validate_images(cls, v):
        """Validate image URLs."""
        if v:
            for url in v:
                if not isinstance(url, str) or len(url) < 10:
                    raise ValueError("Invalid image URL format")
        return v
    
    @validator("tags")
    def validate_tags(cls, v):
        """Validate product tags."""
        if v:
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            for tag in v:
                if not isinstance(tag, str) or len(tag) > 50:
                    raise ValueError("Tags must be strings with max 50 characters")
        return v


class ProductUpdate(BaseModel):
    """Schema for product update request."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    
    # Pricing
    base_price: Optional[float] = Field(None, gt=0)
    current_price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=10)
    
    # Inventory
    quantity_available: Optional[int] = Field(None, ge=0)
    minimum_quantity: Optional[int] = Field(None, ge=1)
    availability: Optional[AvailabilityStatus] = None
    
    # Media and specifications
    images: Optional[List[str]] = None
    specifications: Optional[Dict] = None
    tags: Optional[List[str]] = None
    
    # Status
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    
    @validator("images")
    def validate_images(cls, v):
        """Validate image URLs."""
        if v is not None:
            for url in v:
                if not isinstance(url, str) or len(url) < 10:
                    raise ValueError("Invalid image URL format")
        return v
    
    @validator("tags")
    def validate_tags(cls, v):
        """Validate product tags."""
        if v is not None:
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            for tag in v:
                if not isinstance(tag, str) or len(tag) > 50:
                    raise ValueError("Tags must be strings with max 50 characters")
        return v


class ProductResponse(BaseModel):
    """Schema for product response."""
    
    id: UUID
    vendor_id: UUID
    category_id: Optional[UUID] = None
    
    # Basic information
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    
    # Pricing
    base_price: float
    current_price: float
    currency: str
    
    # Inventory
    quantity_available: int
    minimum_quantity: int
    availability: AvailabilityStatus
    
    # Media and specifications
    images: Optional[List[str]] = None
    specifications: Optional[Dict] = None
    tags: Optional[List[str]] = None
    
    # Translations
    translations: Optional[Dict] = None
    
    # Metrics
    view_count: int
    favorite_count: int
    average_rating: float
    total_reviews: int
    
    # Status
    is_active: bool
    is_featured: bool
    
    # Timestamps
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for product list response with pagination."""
    
    products: List[ProductResponse]
    total: int
    page: int
    size: int
    pages: int


class CategoryCreate(BaseModel):
    """Schema for category creation request."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    slug: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[UUID] = None
    sort_order: int = Field(default=0)
    translations: Optional[Dict] = Field(default_factory=dict)
    is_active: bool = Field(default=True)
    
    @validator("slug")
    def validate_slug(cls, v):
        """Validate slug format."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Slug must contain only letters, numbers, hyphens, and underscores")
        return v.lower()


class CategoryResponse(BaseModel):
    """Schema for category response."""
    
    id: UUID
    parent_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    slug: str
    level: int
    sort_order: int
    translations: Optional[Dict] = None
    is_active: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ProductReviewCreate(BaseModel):
    """Schema for product review creation."""
    
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    title: Optional[str] = Field(None, max_length=200)
    comment: Optional[str] = None
    
    @validator("title")
    def validate_title(cls, v):
        """Validate review title."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Title cannot be empty")
        return v


class ProductReviewResponse(BaseModel):
    """Schema for product review response."""
    
    id: UUID
    product_id: UUID
    user_id: UUID
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    is_verified_purchase: bool
    helpful_votes: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ProductSearchRequest(BaseModel):
    """Schema for product search request."""
    
    query: Optional[str] = Field(None, max_length=200)
    category_id: Optional[UUID] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    availability: Optional[AvailabilityStatus] = None
    vendor_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    sort_by: Optional[str] = Field(default="created_at", pattern="^(created_at|price|rating|name)$")
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