"""
Product and inventory models.

This module defines product, category, and inventory-related models for
the Multilingual Mandi platform.
"""

from enum import Enum

from sqlalchemy import (
    Boolean, Column, Enum as SQLEnum, Float, ForeignKey, Integer,
    JSON, String, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class AvailabilityStatus(str, Enum):
    """Product availability status enumeration."""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"


class TranslationSource(str, Enum):
    """Translation source enumeration."""
    AI = "ai"
    HUMAN = "human"


class Product(Base, UUIDMixin, TimestampMixin):
    """Product model for marketplace items."""
    
    __tablename__ = "products"
    
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    
    # Basic product information
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    sku = Column(String(100), unique=True, index=True)
    
    # Pricing
    base_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    
    # Inventory
    quantity_available = Column(Integer, default=0, nullable=False)
    minimum_quantity = Column(Integer, default=1, nullable=False)
    availability = Column(
        SQLEnum(AvailabilityStatus),
        default=AvailabilityStatus.IN_STOCK,
        nullable=False,
        index=True
    )
    
    # Media and specifications
    images = Column(JSON)  # List of image URLs
    specifications = Column(JSON)  # Product specifications
    tags = Column(JSON)  # Product tags for search
    
    # Translations
    translations = Column(JSON)  # Multilingual content
    
    # Metrics
    view_count = Column(Integer, default=0, nullable=False)
    favorite_count = Column(Integer, default=0, nullable=False)
    average_rating = Column(Float, default=0.0, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    vendor = relationship("User")
    category = relationship("Category", back_populates="products")
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, price={self.current_price})>"


class Category(Base, UUIDMixin, TimestampMixin):
    """Product category model."""
    
    __tablename__ = "categories"
    
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    
    # Category information
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    
    # Translations
    translations = Column(JSON)  # Multilingual category names
    
    # Hierarchy and ordering
    level = Column(Integer, default=0, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    parent = relationship("Category", remote_side="Category.id")
    products = relationship("Product", back_populates="category")
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"


class ProductTranslation(Base, UUIDMixin, TimestampMixin):
    """Product translation model for multilingual content."""
    
    __tablename__ = "product_translations"
    
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Translation details
    language = Column(String(10), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Translation metadata
    translated_by = Column(
        SQLEnum(TranslationSource),
        default=TranslationSource.AI,
        nullable=False
    )
    confidence = Column(Float, default=0.0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    product = relationship("Product")
    
    def __repr__(self) -> str:
        return f"<ProductTranslation(product_id={self.product_id}, language={self.language})>"


class ProductReview(Base, UUIDMixin, TimestampMixin):
    """Product review and rating model."""
    
    __tablename__ = "product_reviews"
    
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(200))
    comment = Column(Text)
    
    # Review metadata
    is_verified_purchase = Column(Boolean, default=False, nullable=False)
    helpful_votes = Column(Integer, default=0, nullable=False)
    
    # Relationships
    product = relationship("Product")
    user = relationship("User")
    
    def __repr__(self) -> str:
        return f"<ProductReview(product_id={self.product_id}, rating={self.rating})>"