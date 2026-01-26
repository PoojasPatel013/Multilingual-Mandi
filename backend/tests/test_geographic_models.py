"""
Unit tests for geographic and cultural context models.

This module tests the GeographicLocation, CulturalContext, and RegionConfiguration
models and their functionality for multi-region support.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.models.geographic import (
    GeographicLocation, CulturalContext, RegionConfiguration,
    NegotiationStyle, TimeOrientation, RegionType, CurrencyCode
)


class TestGeographicLocationModel:
    """Test GeographicLocation model functionality."""
    
    def test_geographic_location_creation(self):
        """Test creating a GeographicLocation instance."""
        location_id = uuid4()
        
        location = GeographicLocation(
            id=location_id,
            country="United States",
            region="California",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles",
            currency=CurrencyCode.USD,
            region_type=RegionType.CITY,
            country_code="USA",
            region_code="CA",
            market_active=True,
            supported_languages=["en", "es"],
            local_payment_methods=["card", "bank", "mobile"],
            business_regulations={"min_age": 18, "business_license_required": True},
            tax_configuration={"sales_tax": 0.0875, "vat": 0.0},
            compliance_requirements=["gdpr_compliant", "ccpa_compliant"],
            market_size="large",
            economic_indicators={"gdp_per_capita": 75000, "inflation_rate": 0.03},
            seasonal_patterns={"peak_months": ["11", "12"], "low_months": ["01", "02"]}
        )
        
        assert location.id == location_id
        assert location.country == "United States"
        assert location.region == "California"
        assert location.city == "San Francisco"
        assert location.latitude == 37.7749
        assert location.longitude == -122.4194
        assert location.timezone == "America/Los_Angeles"
        assert location.currency == CurrencyCode.USD
        assert location.region_type == RegionType.CITY
        assert location.country_code == "USA"
        assert location.region_code == "CA"
        assert location.market_active is True
        assert "en" in location.supported_languages
        assert "es" in location.supported_languages
        assert "card" in location.local_payment_methods
        assert location.business_regulations["min_age"] == 18
        assert location.tax_configuration["sales_tax"] == 0.0875
        assert "gdpr_compliant" in location.compliance_requirements
        assert location.market_size == "large"
        assert location.economic_indicators["gdp_per_capita"] == 75000
        assert "11" in location.seasonal_patterns["peak_months"]
    
    def test_geographic_location_minimal_creation(self):
        """Test creating a GeographicLocation with minimal required fields."""
        location = GeographicLocation(
            country="India",
            region="Maharashtra",
            city="Mumbai",
            timezone="Asia/Kolkata",
            currency=CurrencyCode.INR
        )
        
        assert location.country == "India"
        assert location.region == "Maharashtra"
        assert location.city == "Mumbai"
        assert location.timezone == "Asia/Kolkata"
        assert location.currency == CurrencyCode.INR
        # Note: Default values are set at the database level, not in Python objects
    
    def test_geographic_location_unique_constraint(self):
        """Test that the unique constraint on country, region, city works."""
        # This test would need database integration to fully test
        # For now, we just verify the constraint is defined
        location = GeographicLocation(
            country="Japan",
            region="Tokyo",
            city="Tokyo",
            timezone="Asia/Tokyo",
            currency=CurrencyCode.JPY
        )
        
        # Verify the table args include the unique constraint
        assert hasattr(GeographicLocation, '__table_args__')
        table_args = GeographicLocation.__table_args__
        assert any(
            hasattr(arg, 'name') and arg.name == 'unique_location'
            for arg in table_args
            if hasattr(arg, 'name')
        )


class TestCulturalContextModel:
    """Test CulturalContext model functionality."""
    
    def test_cultural_context_creation(self):
        """Test creating a CulturalContext instance."""
        context_id = uuid4()
        location_id = uuid4()
        
        context = CulturalContext(
            id=context_id,
            geographic_location_id=location_id,
            cultural_group="East Asian",
            cultural_subgroup="Japanese Business",
            negotiation_style=NegotiationStyle.INDIRECT,
            time_orientation=TimeOrientation.PUNCTUAL,
            communication_preferences=["formal", "respectful", "patient"],
            formality_level="formal",
            directness_preference="low",
            business_etiquette=["bow_greeting", "business_card_ceremony", "hierarchy_respect"],
            greeting_customs=["bow", "business_card_exchange"],
            meeting_protocols=["punctuality", "formal_dress", "hierarchy_seating"],
            negotiation_pace="slow",
            relationship_importance="high",
            hierarchy_respect="high",
            holidays_and_events=["Golden Week", "Obon", "New Year"],
            business_hours_culture={"start": "09:00", "end": "18:00", "overtime_common": True},
            seasonal_considerations={"summer_vacation": "August", "year_end_busy": "December"},
            preferred_languages=["ja", "en"],
            formality_preferences={"use_honorifics": True, "formal_speech": True},
            translation_sensitivities=["direct_refusal", "personal_questions"],
            gift_giving_customs=["omiyage", "seasonal_gifts"],
            hospitality_expectations=["tea_service", "formal_reception"],
            taboos_and_sensitivities=["pointing", "loud_speaking", "direct_confrontation"],
            bargaining_culture="discouraged",
            payment_preferences=["bank_transfer", "cash", "company_card"],
            contract_formality="high",
            trust_building_methods=["relationship_building", "shared_meals", "gift_exchange"],
            relationship_maintenance=["regular_contact", "seasonal_greetings", "face_to_face_meetings"],
            conflict_resolution_style="mediated"
        )
        
        assert context.id == context_id
        assert context.geographic_location_id == location_id
        assert context.cultural_group == "East Asian"
        assert context.cultural_subgroup == "Japanese Business"
        assert context.negotiation_style == NegotiationStyle.INDIRECT
        assert context.time_orientation == TimeOrientation.PUNCTUAL
        assert "formal" in context.communication_preferences
        assert context.formality_level == "formal"
        assert context.directness_preference == "low"
        assert "bow_greeting" in context.business_etiquette
        assert "bow" in context.greeting_customs
        assert "punctuality" in context.meeting_protocols
        assert context.negotiation_pace == "slow"
        assert context.relationship_importance == "high"
        assert context.hierarchy_respect == "high"
        assert "Golden Week" in context.holidays_and_events
        assert context.business_hours_culture["start"] == "09:00"
        assert context.seasonal_considerations["summer_vacation"] == "August"
        assert "ja" in context.preferred_languages
        assert context.formality_preferences["use_honorifics"] is True
        assert "direct_refusal" in context.translation_sensitivities
        assert "omiyage" in context.gift_giving_customs
        assert "tea_service" in context.hospitality_expectations
        assert "pointing" in context.taboos_and_sensitivities
        assert context.bargaining_culture == "discouraged"
        assert "bank_transfer" in context.payment_preferences
        assert context.contract_formality == "high"
        assert "relationship_building" in context.trust_building_methods
        assert "regular_contact" in context.relationship_maintenance
        assert context.conflict_resolution_style == "mediated"
    
    def test_cultural_context_minimal_creation(self):
        """Test creating a CulturalContext with minimal required fields."""
        location_id = uuid4()
        
        context = CulturalContext(
            geographic_location_id=location_id,
            cultural_group="Western",
            negotiation_style=NegotiationStyle.DIRECT,
            time_orientation=TimeOrientation.PUNCTUAL
        )
        
        assert context.geographic_location_id == location_id
        assert context.cultural_group == "Western"
        assert context.negotiation_style == NegotiationStyle.DIRECT
        assert context.time_orientation == TimeOrientation.PUNCTUAL
    
    def test_cultural_context_different_styles(self):
        """Test creating CulturalContext with different negotiation styles."""
        location_id = uuid4()
        
        # Test direct style
        direct_context = CulturalContext(
            geographic_location_id=location_id,
            cultural_group="Northern European",
            negotiation_style=NegotiationStyle.DIRECT,
            time_orientation=TimeOrientation.PUNCTUAL
        )
        assert direct_context.negotiation_style == NegotiationStyle.DIRECT
        
        # Test indirect style
        indirect_context = CulturalContext(
            geographic_location_id=location_id,
            cultural_group="East Asian",
            negotiation_style=NegotiationStyle.INDIRECT,
            time_orientation=TimeOrientation.PUNCTUAL
        )
        assert indirect_context.negotiation_style == NegotiationStyle.INDIRECT
        
        # Test relationship-based style
        relationship_context = CulturalContext(
            geographic_location_id=location_id,
            cultural_group="Latin American",
            negotiation_style=NegotiationStyle.RELATIONSHIP_BASED,
            time_orientation=TimeOrientation.FLEXIBLE
        )
        assert relationship_context.negotiation_style == NegotiationStyle.RELATIONSHIP_BASED
        assert relationship_context.time_orientation == TimeOrientation.FLEXIBLE


class TestRegionConfigurationModel:
    """Test RegionConfiguration model functionality."""
    
    def test_region_configuration_creation(self):
        """Test creating a RegionConfiguration instance."""
        config_id = uuid4()
        location_id = uuid4()
        
        config = RegionConfiguration(
            id=config_id,
            geographic_location_id=location_id,
            platform_name="Multilingual Mandi USA",
            platform_description="Local marketplace for the United States",
            features_enabled=["translation", "negotiation", "escrow", "analytics"],
            features_disabled=["cryptocurrency"],
            feature_configurations={
                "translation": {"default_languages": ["en", "es"]},
                "negotiation": {"max_duration_hours": 72},
                "escrow": {"threshold_usd": 1000}
            },
            theme_configuration={
                "primary_color": "#1976d2",
                "secondary_color": "#dc004e",
                "font_family": "Roboto"
            },
            language_settings={
                "default_language": "en",
                "supported_languages": ["en", "es", "fr"],
                "rtl_support": False
            },
            currency_display={
                "symbol": "$",
                "position": "before",
                "decimal_places": 2
            },
            minimum_transaction_amount=1.0,
            maximum_transaction_amount=50000.0,
            escrow_threshold=1000.0,
            business_hours={
                "monday": {"start": "09:00", "end": "17:00"},
                "tuesday": {"start": "09:00", "end": "17:00"},
                "sunday": {"closed": True}
            },
            support_contacts={
                "email": "support@multilingualMandi.com",
                "phone": "+1-800-123-4567",
                "hours": "9 AM - 5 PM PST"
            },
            legal_information={
                "terms_url": "https://example.com/terms",
                "privacy_url": "https://example.com/privacy",
                "jurisdiction": "California, USA"
            },
            payment_gateway_config={
                "stripe": {"enabled": True, "public_key": "pk_test_..."},
                "paypal": {"enabled": True, "client_id": "client_..."}
            },
            translation_service_config={
                "provider": "google",
                "api_key": "encrypted_key",
                "fallback_provider": "azure"
            },
            analytics_config={
                "google_analytics": {"tracking_id": "GA-123456"},
                "mixpanel": {"project_token": "token_123"}
            },
            data_retention_policy={
                "user_data_months": 24,
                "transaction_data_years": 7,
                "analytics_data_months": 12
            },
            privacy_policy_config={
                "cookie_consent": True,
                "data_processing_consent": True,
                "marketing_consent": False
            },
            audit_requirements={
                "financial_audit": True,
                "security_audit": True,
                "compliance_audit": True
            },
            rate_limits={
                "api_calls_per_minute": 100,
                "translation_calls_per_hour": 1000,
                "negotiation_messages_per_hour": 500
            },
            caching_strategy={
                "translation_cache_hours": 24,
                "product_cache_minutes": 15,
                "user_session_minutes": 30
            },
            cdn_configuration={
                "provider": "cloudflare",
                "regions": ["us-west", "us-east"],
                "cache_ttl_seconds": 3600
            }
        )
        
        assert config.id == config_id
        assert config.geographic_location_id == location_id
        assert config.platform_name == "Multilingual Mandi USA"
        assert config.platform_description == "Local marketplace for the United States"
        assert "translation" in config.features_enabled
        assert "cryptocurrency" in config.features_disabled
        assert config.feature_configurations["translation"]["default_languages"] == ["en", "es"]
        assert config.theme_configuration["primary_color"] == "#1976d2"
        assert config.language_settings["default_language"] == "en"
        assert config.currency_display["symbol"] == "$"
        assert config.minimum_transaction_amount == 1.0
        assert config.maximum_transaction_amount == 50000.0
        assert config.escrow_threshold == 1000.0
        assert config.business_hours["monday"]["start"] == "09:00"
        assert config.support_contacts["email"] == "support@multilingualMandi.com"
        assert config.legal_information["jurisdiction"] == "California, USA"
        assert config.payment_gateway_config["stripe"]["enabled"] is True
        assert config.translation_service_config["provider"] == "google"
        assert config.analytics_config["google_analytics"]["tracking_id"] == "GA-123456"
        assert config.data_retention_policy["user_data_months"] == 24
        assert config.privacy_policy_config["cookie_consent"] is True
        assert config.audit_requirements["financial_audit"] is True
        assert config.rate_limits["api_calls_per_minute"] == 100
        assert config.caching_strategy["translation_cache_hours"] == 24
        assert config.cdn_configuration["provider"] == "cloudflare"
    
    def test_region_configuration_minimal_creation(self):
        """Test creating a RegionConfiguration with minimal required fields."""
        location_id = uuid4()
        
        config = RegionConfiguration(
            geographic_location_id=location_id
        )
        
        assert config.geographic_location_id == location_id
        # All other fields should be optional


class TestEnumValues:
    """Test enum values are correct."""
    
    def test_negotiation_style_enum(self):
        """Test NegotiationStyle enum values."""
        assert NegotiationStyle.DIRECT == "direct"
        assert NegotiationStyle.INDIRECT == "indirect"
        assert NegotiationStyle.RELATIONSHIP_BASED == "relationship_based"
    
    def test_time_orientation_enum(self):
        """Test TimeOrientation enum values."""
        assert TimeOrientation.PUNCTUAL == "punctual"
        assert TimeOrientation.FLEXIBLE == "flexible"
    
    def test_region_type_enum(self):
        """Test RegionType enum values."""
        assert RegionType.COUNTRY == "country"
        assert RegionType.STATE == "state"
        assert RegionType.PROVINCE == "province"
        assert RegionType.REGION == "region"
        assert RegionType.CITY == "city"
        assert RegionType.DISTRICT == "district"
    
    def test_currency_code_enum(self):
        """Test CurrencyCode enum values."""
        assert CurrencyCode.USD == "USD"
        assert CurrencyCode.EUR == "EUR"
        assert CurrencyCode.GBP == "GBP"
        assert CurrencyCode.JPY == "JPY"
        assert CurrencyCode.CNY == "CNY"
        assert CurrencyCode.INR == "INR"
        assert CurrencyCode.OTHER == "OTHER"
    
    def test_currency_code_comprehensive(self):
        """Test that all major currencies are included."""
        major_currencies = [
            "USD", "EUR", "GBP", "JPY", "CNY", "INR", "BRL", "CAD", 
            "AUD", "MXN", "KRW", "SGD", "HKD", "CHF", "SEK", "NOK"
        ]
        
        for currency in major_currencies:
            assert hasattr(CurrencyCode, currency)
            assert getattr(CurrencyCode, currency) == currency


class TestModelRelationships:
    """Test relationships between geographic models."""
    
    def test_geographic_location_cultural_context_relationship(self):
        """Test the relationship between GeographicLocation and CulturalContext."""
        # This test would need database integration to fully test relationships
        # For now, we verify the relationship attributes exist
        
        # Check that GeographicLocation has cultural_contexts relationship
        assert hasattr(GeographicLocation, 'cultural_contexts')
        
        # Check that CulturalContext has geographic_location relationship
        assert hasattr(CulturalContext, 'geographic_location')
        
        # Check that CulturalContext has geographic_location_id foreign key
        assert hasattr(CulturalContext, 'geographic_location_id')
    
    def test_geographic_location_user_relationship(self):
        """Test the relationship between GeographicLocation and User."""
        # Check that GeographicLocation has users relationship
        assert hasattr(GeographicLocation, 'users')
    
    def test_region_configuration_geographic_location_relationship(self):
        """Test the relationship between RegionConfiguration and GeographicLocation."""
        # Check that RegionConfiguration has geographic_location relationship
        assert hasattr(RegionConfiguration, 'geographic_location')
        
        # Check that RegionConfiguration has geographic_location_id foreign key
        assert hasattr(RegionConfiguration, 'geographic_location_id')


class TestModelRepresentations:
    """Test model string representations."""
    
    def test_geographic_location_repr(self):
        """Test GeographicLocation string representation."""
        location = GeographicLocation(
            country="United States",
            region="California", 
            city="San Francisco",
            timezone="America/Los_Angeles",
            currency=CurrencyCode.USD
        )
        
        repr_str = repr(location)
        assert "GeographicLocation" in repr_str
        assert "United States" in repr_str
        assert "California" in repr_str
        assert "San Francisco" in repr_str
    
    def test_cultural_context_repr(self):
        """Test CulturalContext string representation."""
        location_id = uuid4()
        context = CulturalContext(
            geographic_location_id=location_id,
            cultural_group="Western",
            negotiation_style=NegotiationStyle.DIRECT,
            time_orientation=TimeOrientation.PUNCTUAL
        )
        
        repr_str = repr(context)
        assert "CulturalContext" in repr_str
        assert "Western" in repr_str
        assert "NegotiationStyle.DIRECT" in repr_str
    
    def test_region_configuration_repr(self):
        """Test RegionConfiguration string representation."""
        location_id = uuid4()
        config = RegionConfiguration(
            geographic_location_id=location_id
        )
        
        repr_str = repr(config)
        assert "RegionConfiguration" in repr_str
        assert str(location_id) in repr_str