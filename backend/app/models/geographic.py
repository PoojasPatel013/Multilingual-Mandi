"""
Geographic and cultural context models.

This module defines geographic location and cultural context models for
the Multilingual Mandi platform, supporting multi-region scalability
and cultural awareness in negotiations.
"""

from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import (
    Boolean, Column, Enum as SQLEnum, Float, ForeignKey, Integer,
    JSON, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class NegotiationStyle(str, Enum):
    """Negotiation style enumeration for cultural context."""
    DIRECT = "direct"
    INDIRECT = "indirect"
    RELATIONSHIP_BASED = "relationship_based"


class TimeOrientation(str, Enum):
    """Time orientation enumeration for cultural context."""
    PUNCTUAL = "punctual"
    FLEXIBLE = "flexible"


class RegionType(str, Enum):
    """Region type enumeration for geographic classification."""
    COUNTRY = "country"
    STATE = "state"
    PROVINCE = "province"
    REGION = "region"
    CITY = "city"
    DISTRICT = "district"


class CurrencyCode(str, Enum):
    """Common currency codes for regional support."""
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    JPY = "JPY"  # Japanese Yen
    CNY = "CNY"  # Chinese Yuan
    INR = "INR"  # Indian Rupee
    BRL = "BRL"  # Brazilian Real
    CAD = "CAD"  # Canadian Dollar
    AUD = "AUD"  # Australian Dollar
    MXN = "MXN"  # Mexican Peso
    KRW = "KRW"  # South Korean Won
    SGD = "SGD"  # Singapore Dollar
    HKD = "HKD"  # Hong Kong Dollar
    CHF = "CHF"  # Swiss Franc
    SEK = "SEK"  # Swedish Krona
    NOK = "NOK"  # Norwegian Krone
    DKK = "DKK"  # Danish Krone
    PLN = "PLN"  # Polish Zloty
    CZK = "CZK"  # Czech Koruna
    HUF = "HUF"  # Hungarian Forint
    RUB = "RUB"  # Russian Ruble
    TRY = "TRY"  # Turkish Lira
    ZAR = "ZAR"  # South African Rand
    AED = "AED"  # UAE Dirham
    SAR = "SAR"  # Saudi Riyal
    EGP = "EGP"  # Egyptian Pound
    NGN = "NGN"  # Nigerian Naira
    KES = "KES"  # Kenyan Shilling
    GHS = "GHS"  # Ghanaian Cedi
    MAD = "MAD"  # Moroccan Dirham
    TND = "TND"  # Tunisian Dinar
    OTHER = "OTHER"  # For currencies not listed


class GeographicLocation(Base, UUIDMixin, TimestampMixin):
    """Geographic location model for multi-region support."""
    
    __tablename__ = "geographic_locations"
    
    # Basic location information
    country = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    
    # Geographic coordinates
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Regional configuration
    timezone = Column(String(50), nullable=False)
    currency = Column(SQLEnum(CurrencyCode), nullable=False, index=True)
    
    # Administrative information
    region_type = Column(
        SQLEnum(RegionType),
        default=RegionType.REGION,
        nullable=False
    )
    country_code = Column(String(3), index=True)  # ISO 3166-1 alpha-3
    region_code = Column(String(10), index=True)  # Regional subdivision code
    
    # Market configuration
    market_active = Column(Boolean, default=True, nullable=False)
    supported_languages = Column(JSON)  # List of supported language codes
    local_payment_methods = Column(JSON)  # Supported payment methods
    
    # Business rules and regulations
    business_regulations = Column(JSON)  # Regional business rules
    tax_configuration = Column(JSON)  # Tax rules and rates
    compliance_requirements = Column(JSON)  # Regulatory compliance
    
    # Market characteristics
    market_size = Column(String(20))  # small, medium, large, enterprise
    economic_indicators = Column(JSON)  # Economic data for pricing
    seasonal_patterns = Column(JSON)  # Seasonal business patterns
    
    # Relationships
    users = relationship("User", back_populates="geographic_location")
    cultural_contexts = relationship("CulturalContext", back_populates="geographic_location")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('country', 'region', 'city', name='unique_location'),
    )
    
    def __repr__(self) -> str:
        return f"<GeographicLocation(id={self.id}, country={self.country}, region={self.region}, city={self.city})>"


class CulturalContext(Base, UUIDMixin, TimestampMixin):
    """Cultural context model for culturally-aware negotiations."""
    
    __tablename__ = "cultural_contexts"
    
    # Geographic association
    geographic_location_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("geographic_locations.id"), 
        nullable=False,
        index=True
    )
    
    # Cultural identification
    cultural_group = Column(String(100), nullable=False, index=True)
    cultural_subgroup = Column(String(100))  # More specific cultural identification
    
    # Communication styles
    negotiation_style = Column(
        SQLEnum(NegotiationStyle),
        nullable=False,
        index=True
    )
    time_orientation = Column(
        SQLEnum(TimeOrientation),
        nullable=False
    )
    
    # Communication preferences
    communication_preferences = Column(JSON)  # List of communication styles
    formality_level = Column(String(20))  # formal, semi_formal, informal
    directness_preference = Column(String(20))  # high, medium, low
    
    # Business etiquette
    business_etiquette = Column(JSON)  # Business etiquette guidelines
    greeting_customs = Column(JSON)  # Greeting and introduction customs
    meeting_protocols = Column(JSON)  # Meeting and discussion protocols
    
    # Negotiation characteristics
    negotiation_pace = Column(String(20))  # fast, moderate, slow
    relationship_importance = Column(String(20))  # high, medium, low
    hierarchy_respect = Column(String(20))  # high, medium, low
    
    # Cultural calendar
    holidays_and_events = Column(JSON)  # Important cultural dates
    business_hours_culture = Column(JSON)  # Cultural business hour preferences
    seasonal_considerations = Column(JSON)  # Seasonal cultural factors
    
    # Language and communication
    preferred_languages = Column(JSON)  # Ordered list of preferred languages
    formality_preferences = Column(JSON)  # Language formality preferences
    translation_sensitivities = Column(JSON)  # Words/phrases requiring care
    
    # Gift and hospitality customs
    gift_giving_customs = Column(JSON)  # Gift-giving etiquette
    hospitality_expectations = Column(JSON)  # Hospitality customs
    taboos_and_sensitivities = Column(JSON)  # Cultural taboos to avoid
    
    # Economic and business culture
    bargaining_culture = Column(String(20))  # expected, optional, discouraged
    payment_preferences = Column(JSON)  # Preferred payment methods and timing
    contract_formality = Column(String(20))  # high, medium, low
    
    # Trust and relationship building
    trust_building_methods = Column(JSON)  # Ways to build trust
    relationship_maintenance = Column(JSON)  # Maintaining business relationships
    conflict_resolution_style = Column(String(20))  # direct, mediated, avoidance
    
    # Relationships
    geographic_location = relationship("GeographicLocation", back_populates="cultural_contexts")
    users = relationship("User", back_populates="cultural_context")
    
    def __repr__(self) -> str:
        return f"<CulturalContext(id={self.id}, cultural_group={self.cultural_group}, negotiation_style={self.negotiation_style})>"


class RegionConfiguration(Base, UUIDMixin, TimestampMixin):
    """Region-specific configuration model for platform customization."""
    
    __tablename__ = "region_configurations"
    
    # Geographic association
    geographic_location_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("geographic_locations.id"), 
        nullable=False,
        unique=True,
        index=True
    )
    
    # Platform configuration
    platform_name = Column(String(200))  # Localized platform name
    platform_description = Column(Text)  # Localized description
    
    # Feature availability
    features_enabled = Column(JSON)  # List of enabled features
    features_disabled = Column(JSON)  # List of disabled features
    feature_configurations = Column(JSON)  # Feature-specific settings
    
    # UI/UX customization
    theme_configuration = Column(JSON)  # UI theme and styling
    language_settings = Column(JSON)  # Language and localization settings
    currency_display = Column(JSON)  # Currency formatting preferences
    
    # Business rules
    minimum_transaction_amount = Column(Float)
    maximum_transaction_amount = Column(Float)
    escrow_threshold = Column(Float)  # Amount above which escrow is required
    
    # Operational settings
    business_hours = Column(JSON)  # Regional business hours
    support_contacts = Column(JSON)  # Regional support information
    legal_information = Column(JSON)  # Legal disclaimers and terms
    
    # Integration settings
    payment_gateway_config = Column(JSON)  # Payment gateway configurations
    translation_service_config = Column(JSON)  # Translation service settings
    analytics_config = Column(JSON)  # Analytics and reporting settings
    
    # Compliance and regulatory
    data_retention_policy = Column(JSON)  # Data retention requirements
    privacy_policy_config = Column(JSON)  # Privacy policy configurations
    audit_requirements = Column(JSON)  # Audit and compliance requirements
    
    # Performance and scaling
    rate_limits = Column(JSON)  # API rate limiting configuration
    caching_strategy = Column(JSON)  # Caching configuration
    cdn_configuration = Column(JSON)  # CDN settings
    
    # Relationships
    geographic_location = relationship("GeographicLocation")
    
    def __repr__(self) -> str:
        return f"<RegionConfiguration(id={self.id}, location_id={self.geographic_location_id})>"