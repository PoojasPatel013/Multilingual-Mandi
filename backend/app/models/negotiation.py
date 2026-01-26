"""
Negotiation and communication models.

This module defines negotiation, messaging, and cultural context models for
the Multilingual Mandi platform.
"""

from enum import Enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer,
    JSON, String, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class NegotiationStatus(str, Enum):
    """Negotiation status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class MessageType(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    OFFER = "offer"
    COUNTEROFFER = "counteroffer"
    SYSTEM = "system"
    CULTURAL_TIP = "cultural_tip"


class NegotiationEventType(str, Enum):
    """Negotiation event type enumeration."""
    OFFER = "offer"
    COUNTEROFFER = "counteroffer"
    ACCEPT = "accept"
    REJECT = "reject"
    WITHDRAW = "withdraw"
    EXPIRE = "expire"


class Negotiation(Base, UUIDMixin, TimestampMixin):
    """Negotiation model for product price negotiations."""
    
    __tablename__ = "negotiations"
    
    # Parties involved
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Negotiation details
    initial_price = Column(Float, nullable=False)
    current_offer = Column(Float, nullable=False)
    final_price = Column(Float)
    quantity = Column(Integer, default=1, nullable=False)
    
    # Status and timeline
    status = Column(
        SQLEnum(NegotiationStatus),
        default=NegotiationStatus.ACTIVE,
        nullable=False,
        index=True
    )
    expires_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Cultural context
    cultural_context = Column(JSON)  # Cultural considerations
    language_pair = Column(JSON)  # {"vendor": "en", "customer": "es"}
    
    # Negotiation metrics
    total_messages = Column(Integer, default=0, nullable=False)
    total_offers = Column(Integer, default=0, nullable=False)
    duration_minutes = Column(Integer, default=0, nullable=False)
    
    # AI assistance tracking
    ai_suggestions_used = Column(Integer, default=0, nullable=False)
    cultural_tips_provided = Column(Integer, default=0, nullable=False)
    
    # Relationships
    product = relationship("Product")
    vendor = relationship("User", foreign_keys=[vendor_id])
    customer = relationship("User", foreign_keys=[customer_id])
    messages = relationship("NegotiationMessage", back_populates="negotiation")
    events = relationship("NegotiationEvent", back_populates="negotiation")
    
    def __repr__(self) -> str:
        return f"<Negotiation(id={self.id}, product_id={self.product_id}, status={self.status})>"


class NegotiationMessage(Base, UUIDMixin, TimestampMixin):
    """Message model for negotiation communications."""
    
    __tablename__ = "negotiation_messages"
    
    negotiation_id = Column(UUID(as_uuid=True), ForeignKey("negotiations.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Message content
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text)
    original_language = Column(String(10))
    target_language = Column(String(10))
    
    # Message metadata
    message_type = Column(
        SQLEnum(MessageType),
        default=MessageType.TEXT,
        nullable=False
    )
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True))
    
    # Translation metadata
    translation_confidence = Column(Float)
    translation_alternatives = Column(JSON)
    
    # Cultural context
    cultural_context = Column(JSON)
    
    # Relationships
    negotiation = relationship("Negotiation", back_populates="messages")
    sender = relationship("User")
    
    def __repr__(self) -> str:
        return f"<NegotiationMessage(id={self.id}, type={self.message_type})>"


class NegotiationEvent(Base, UUIDMixin, TimestampMixin):
    """Event model for tracking negotiation actions."""
    
    __tablename__ = "negotiation_events"
    
    negotiation_id = Column(UUID(as_uuid=True), ForeignKey("negotiations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Event details
    event_type = Column(
        SQLEnum(NegotiationEventType),
        nullable=False,
        index=True
    )
    amount = Column(Float)  # For offer/counteroffer events
    previous_amount = Column(Float)
    
    # Event metadata
    terms = Column(Text)
    cultural_context = Column(JSON)
    ai_suggested = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    negotiation = relationship("Negotiation", back_populates="events")
    user = relationship("User")
    
    def __repr__(self) -> str:
        return f"<NegotiationEvent(id={self.id}, type={self.event_type}, amount={self.amount})>"


class CulturalProfile(Base, UUIDMixin, TimestampMixin):
    """Cultural profile model for users."""
    
    __tablename__ = "cultural_profiles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Geographic and cultural information
    region = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    cultural_group = Column(String(100))
    
    # Communication preferences
    negotiation_style = Column(String(50))  # direct, indirect, relationship_based
    time_orientation = Column(String(50))  # punctual, flexible
    communication_preferences = Column(JSON)
    
    # Business etiquette
    business_etiquette = Column(JSON)
    greeting_customs = Column(JSON)
    gift_giving_customs = Column(JSON)
    
    # Calendar and events
    holidays_and_events = Column(JSON)
    business_hours_culture = Column(JSON)
    
    # Language preferences
    preferred_languages = Column(JSON)
    formality_preferences = Column(JSON)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self) -> str:
        return f"<CulturalProfile(id={self.id}, region={self.region})>"


class TranslationCache(Base, UUIDMixin, TimestampMixin):
    """Translation cache model for frequently used translations."""
    
    __tablename__ = "translation_cache"
    
    # Translation details
    source_text = Column(Text, nullable=False, index=True)
    source_language = Column(String(10), nullable=False, index=True)
    target_language = Column(String(10), nullable=False, index=True)
    translated_text = Column(Text, nullable=False)
    
    # Context and quality
    context = Column(String(50))  # negotiation, product_description, etc.
    confidence = Column(Float, nullable=False)
    provider = Column(String(100))  # Translation service provider
    
    # Usage statistics
    usage_count = Column(Integer, default=1, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=False)
    
    # Quality indicators
    is_verified = Column(Boolean, default=False, nullable=False)
    user_feedback = Column(JSON)  # User ratings and feedback
    
    def __repr__(self) -> str:
        return f"<TranslationCache(source={self.source_language}, target={self.target_language})>"