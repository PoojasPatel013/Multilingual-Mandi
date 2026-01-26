"""
User and profile models.

This module defines the user, vendor profile, and related models for
the Multilingual Mandi platform.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, 
    JSON, String, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class UserRole(str, Enum):
    """User role enumeration."""
    VENDOR = "vendor"
    CUSTOMER = "customer"
    ADMIN = "admin"


class VerificationStatus(str, Enum):
    """User verification status enumeration."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class User(Base, UUIDMixin, TimestampMixin):
    """User model for authentication and basic profile information."""
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, index=True)
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone_number = Column(String(20))
    preferred_language = Column(String(10), default="en", nullable=False)
    
    # Geographic and cultural context (foreign keys to dedicated models)
    geographic_location_id = Column(UUID(as_uuid=True), ForeignKey("geographic_locations.id"))
    cultural_context_id = Column(UUID(as_uuid=True), ForeignKey("cultural_contexts.id"))
    
    # Legacy geographic information (kept for backward compatibility)
    country = Column(String(100))
    region = Column(String(100))
    city = Column(String(100))
    timezone = Column(String(50))
    currency = Column(String(10))
    coordinates = Column(JSON)  # {"lat": float, "lng": float}
    
    # Legacy cultural context (kept for backward compatibility)
    cultural_profile = Column(JSON)  # Cultural preferences and context
    
    # Verification
    verification_status = Column(
        SQLEnum(VerificationStatus),
        default=VerificationStatus.PENDING,
        nullable=False
    )
    verification_documents = Column(JSON)  # Document references
    
    # Activity tracking
    last_active = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    login_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    vendor_profile = relationship(
        "VendorProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    customer_profile = relationship(
        "CustomerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    geographic_location = relationship("GeographicLocation", back_populates="users")
    cultural_context = relationship("CulturalContext", back_populates="users")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class VendorProfile(Base, UUIDMixin, TimestampMixin):
    """Extended profile for vendor users."""
    
    __tablename__ = "vendor_profiles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Business information
    business_name = Column(String(200), nullable=False)
    business_type = Column(String(100))
    business_description = Column(Text)
    market_stall = Column(String(100))  # Physical location reference
    
    # Business metrics
    average_rating = Column(Float, default=0.0, nullable=False)
    total_sales = Column(Integer, default=0, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    
    # Languages and communication
    languages = Column(JSON)  # List of supported languages
    communication_preferences = Column(JSON)
    
    # Payment methods
    payment_methods = Column(JSON)  # Supported payment methods
    
    # Business hours and availability
    business_hours = Column(JSON)  # Operating hours
    is_available = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="vendor_profile")
    
    def __repr__(self) -> str:
        return f"<VendorProfile(id={self.id}, business_name={self.business_name})>"


class CustomerProfile(Base, UUIDMixin, TimestampMixin):
    """Extended profile for customer users."""
    
    __tablename__ = "customer_profiles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Shopping preferences
    preferred_categories = Column(JSON)  # List of preferred product categories
    price_range_preferences = Column(JSON)  # Price range preferences by category
    
    # Purchase history summary
    total_purchases = Column(Integer, default=0, nullable=False)
    total_spent = Column(Float, default=0.0, nullable=False)
    average_rating_given = Column(Float, default=0.0, nullable=False)
    
    # Wishlist and favorites
    wishlist_items = Column(JSON)  # List of product IDs
    favorite_vendors = Column(JSON)  # List of vendor IDs
    
    # Communication preferences
    notification_preferences = Column(JSON)  # Notification settings
    
    # Relationships
    user = relationship("User", back_populates="customer_profile")
    
    def __repr__(self) -> str:
        return f"<CustomerProfile(id={self.id}, user_id={self.user_id})>"


class PaymentMethod(Base, UUIDMixin, TimestampMixin):
    """Payment method model for users."""
    
    __tablename__ = "payment_methods"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Payment method details
    method_type = Column(String(50), nullable=False)  # card, bank, mobile, etc.
    provider = Column(String(100))  # Stripe, PayPal, etc.
    details = Column(JSON)  # Encrypted payment details
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self) -> str:
        return f"<PaymentMethod(id={self.id}, type={self.method_type})>"