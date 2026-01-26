"""
Property-based tests for multi-region data handling.

This module contains property-based tests that validate universal properties
of the multi-region system using Hypothesis for comprehensive input coverage.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from uuid import uuid4, UUID
from decimal import Decimal

from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.geographic import (
    GeographicLocation, CulturalContext, RegionConfiguration,
    NegotiationStyle, TimeOrientation, RegionType, CurrencyCode
)
from app.models.user import User, UserRole, VerificationStatus
from app.models.product import Product, AvailabilityStatus


# Custom strategies for generating test data
@composite
def valid_country_name(draw):
    """Generate valid country names."""
    countries = [
        'United States', 'Canada', 'Mexico', 'Brazil', 'Argentina',
        'United Kingdom', 'France', 'Germany', 'Spain', 'Italy',
        'Japan', 'China', 'India', 'South Korea', 'Australia',
        'South Africa', 'Nigeria', 'Egypt', 'Morocco', 'Kenya'
    ]
    return draw(st.sampled_from(countries))


@composite
def valid_region_name(draw):
    """Generate valid region names."""
    regions = [
        'California', 'Texas', 'New York', 'Ontario', 'Quebec',
        'Sao Paulo', 'Buenos Aires', 'London', 'Paris', 'Berlin',
        'Tokyo', 'Beijing', 'Mumbai', 'Seoul', 'Sydney',
        'Cape Town', 'Lagos', 'Cairo', 'Casablanca', 'Nairobi'
    ]
    return draw(st.sampled_from(regions))


@composite
def valid_city_name(draw):
    """Generate valid city names."""
    cities = [
        'San Francisco', 'Los Angeles', 'Houston', 'Toronto', 'Montreal',
        'Rio de Janeiro', 'Buenos Aires', 'London', 'Paris', 'Munich',
        'Tokyo', 'Shanghai', 'Delhi', 'Seoul', 'Melbourne',
        'Cape Town', 'Lagos', 'Cairo', 'Rabat', 'Nairobi'
    ]
    return draw(st.sampled_from(cities))


@composite
def valid_timezone(draw):
    """Generate valid timezone strings."""
    timezones = [
        'America/Los_Angeles', 'America/New_York', 'America/Toronto',
        'America/Sao_Paulo', 'Europe/London', 'Europe/Paris',
        'Europe/Berlin', 'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Kolkata',
        'Asia/Seoul', 'Australia/Sydney', 'Africa/Cairo', 'Africa/Lagos'
    ]
    return draw(st.sampled_from(timezones))


@composite
def valid_currency_code(draw):
    """Generate valid currency codes."""
    return draw(st.sampled_from([
        CurrencyCode.USD, CurrencyCode.EUR, CurrencyCode.GBP, CurrencyCode.JPY,
        CurrencyCode.CNY, CurrencyCode.INR, CurrencyCode.BRL, CurrencyCode.CAD,
        CurrencyCode.AUD, CurrencyCode.MXN, CurrencyCode.KRW, CurrencyCode.SGD
    ]))


@composite
def valid_language_codes(draw):
    """Generate valid language code lists."""
    languages = ['en', 'es', 'fr', 'de', 'ja', 'zh', 'hi', 'ko', 'pt', 'ar']
    return draw(st.lists(
        st.sampled_from(languages),
        min_size=1,
        max_size=5,
        unique=True
    ))


@composite
def valid_payment_methods(draw):
    """Generate valid payment method lists."""
    methods = ['card', 'bank_transfer', 'mobile_payment', 'cash', 'digital_wallet']
    return draw(st.lists(
        st.sampled_from(methods),
        min_size=1,
        max_size=4,
        unique=True
    ))


@composite
def valid_business_regulations(draw):
    """Generate valid business regulations."""
    return draw(st.fixed_dictionaries({
        'min_age': st.integers(min_value=16, max_value=21),
        'business_license_required': st.booleans(),
        'tax_registration_required': st.booleans(),
        'max_transaction_amount': st.floats(min_value=1000.0, max_value=100000.0)
    }))


@composite
def valid_geographic_location_data(draw):
    """Generate valid geographic location data."""
    # Generate unique identifier to ensure uniqueness
    unique_id = str(uuid4())[:8]
    
    return {
        'country': draw(valid_country_name()),
        'region': draw(valid_region_name()),
        'city': f"{draw(valid_city_name())}_{unique_id}",  # Ensure unique city names
        'latitude': draw(st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False)),
        'longitude': draw(st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False)),
        'timezone': draw(valid_timezone()),
        'currency': draw(valid_currency_code()),
        'region_type': draw(st.sampled_from(list(RegionType))),
        'country_code': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu',)), min_size=3, max_size=3)),
        'region_code': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Nd')), min_size=2, max_size=5)),
        'market_active': draw(st.booleans()),
        'supported_languages': draw(valid_language_codes()),
        'local_payment_methods': draw(valid_payment_methods()),
        'business_regulations': draw(valid_business_regulations()),
        'market_size': draw(st.sampled_from(['small', 'medium', 'large', 'enterprise']))
    }


@composite
def valid_cultural_context_data(draw):
    """Generate valid cultural context data."""
    unique_id = str(uuid4())[:8]
    
    return {
        'cultural_group': f"{draw(st.sampled_from([
            'Western', 'East Asian', 'South Asian', 'Middle Eastern',
            'Latin American', 'African', 'Nordic', 'Mediterranean'
        ]))}_{unique_id}",  # Ensure unique cultural groups
        'negotiation_style': draw(st.sampled_from(list(NegotiationStyle))),
        'time_orientation': draw(st.sampled_from(list(TimeOrientation))),
        'communication_preferences': draw(st.lists(
            st.sampled_from(['formal', 'informal', 'direct', 'indirect', 'respectful']),
            min_size=1, max_size=3, unique=True
        )),
        'formality_level': draw(st.sampled_from(['formal', 'semi_formal', 'informal'])),
        'directness_preference': draw(st.sampled_from(['high', 'medium', 'low'])),
        'bargaining_culture': draw(st.sampled_from(['expected', 'optional', 'discouraged']))
    }


@composite
def valid_region_configuration_data(draw):
    """Generate valid region configuration data."""
    return {
        'platform_name': draw(st.text(min_size=5, max_size=50)),
        'features_enabled': draw(st.lists(
            st.sampled_from(['translation', 'negotiation', 'escrow', 'analytics', 'voice']),
            min_size=1, max_size=5, unique=True
        )),
        'minimum_transaction_amount': draw(st.floats(min_value=0.01, max_value=10.0)),
        'maximum_transaction_amount': draw(st.floats(min_value=1000.0, max_value=100000.0)),
        'escrow_threshold': draw(st.floats(min_value=100.0, max_value=5000.0)),
        'language_settings': draw(st.fixed_dictionaries({
            'default_language': st.sampled_from(['en', 'es', 'fr', 'de', 'ja']),
            'supported_languages': valid_language_codes(),
            'rtl_support': st.booleans()
        }))
    }


@composite
def valid_user_data(draw):
    """Generate valid user data with unique email."""
    unique_id = str(uuid4())[:8]
    return {
        'email': f"user_{unique_id}@example.com",
        'hashed_password': 'hashed_password_123',
        'first_name': 'Test',
        'last_name': 'User',
        'role': draw(st.sampled_from([UserRole.VENDOR, UserRole.CUSTOMER])),
        'preferred_language': 'en',
        'verification_status': VerificationStatus.VERIFIED,
        'is_active': True,
        'is_superuser': False,
        'login_count': 0
    }


class TestMultiRegionConfiguration:
    """
    Property-based tests for multi-region data handling.
    
    **Validates: Requirements 10.1**
    
    These tests ensure that the system supports independent market configurations
    and local customizations for different regions without affecting other regions.
    """
    
    @given(
        region_data_list=st.lists(
            valid_geographic_location_data(),
            min_size=2,
            max_size=4
        )
    )
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_independent_region_configurations(
        self,
        region_data_list: List[Dict[str, Any]],
        db_session: AsyncSession
    ):
        """
        **Property 34: Multi-Region Configuration**
        **Validates: Requirements 10.1**
        
        For any set of regions added to the platform, each region should
        support independent market configurations and local customizations
        without affecting other regions.
        """
        created_locations = []
        
        # Create multiple geographic locations
        for region_data in region_data_list:
            location = GeographicLocation(**region_data)
            db_session.add(location)
            created_locations.append(location)
        
        await db_session.commit()
        
        # Refresh all locations
        for location in created_locations:
            await db_session.refresh(location)
        
        # Verify independent configurations
        
        # 1. Each region should maintain its unique configuration
        for i, (original_data, location) in enumerate(zip(region_data_list, created_locations)):
            assert location.country == original_data['country']
            assert location.region == original_data['region']
            assert location.city == original_data['city']
            assert location.currency == original_data['currency']
            assert location.timezone == original_data['timezone']
            assert location.market_active == original_data['market_active']
            assert set(location.supported_languages) == set(original_data['supported_languages'])
            assert set(location.local_payment_methods) == set(original_data['local_payment_methods'])
            assert location.business_regulations == original_data['business_regulations']
            assert location.market_size == original_data['market_size']
        
        # 2. Regions should be independently retrievable
        for location in created_locations:
            result = await db_session.execute(
                select(GeographicLocation).where(GeographicLocation.id == location.id)
            )
            retrieved_location = result.scalar_one()
            assert retrieved_location is not None
            assert retrieved_location.id == location.id
        
        # 3. Changes to one region should not affect others
        # Modify the first region
        first_location = created_locations[0]
        original_market_status = first_location.market_active
        first_location.market_active = not original_market_status
        await db_session.commit()
        
        # Verify other regions are unaffected
        for i, location in enumerate(created_locations[1:], 1):
            await db_session.refresh(location)
            original_data = region_data_list[i]
            assert location.market_active == original_data['market_active']
    
    @given(
        location_data=valid_geographic_location_data(),
        cultural_contexts=st.lists(
            valid_cultural_context_data(),
            min_size=1,
            max_size=3
        )
    )
    @settings(max_examples=12, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_region_cultural_context_independence(
        self,
        location_data: Dict[str, Any],
        cultural_contexts: List[Dict[str, Any]],
        db_session: AsyncSession
    ):
        """
        **Property 34: Multi-Region Configuration**
        **Validates: Requirements 10.1**
        
        For any region with multiple cultural contexts, each cultural
        context should be independently configurable without affecting
        other cultural contexts in the same or different regions.
        """
        # Create geographic location
        location = GeographicLocation(**location_data)
        db_session.add(location)
        await db_session.commit()
        await db_session.refresh(location)
        
        # Create multiple cultural contexts for the region
        created_contexts = []
        for context_data in cultural_contexts:
            context = CulturalContext(
                geographic_location_id=location.id,
                **context_data
            )
            db_session.add(context)
            created_contexts.append(context)
        
        await db_session.commit()
        
        # Refresh all contexts
        for context in created_contexts:
            await db_session.refresh(context)
        
        # Verify independent cultural configurations
        
        # 1. Each cultural context should maintain its unique configuration
        for original_data, context in zip(cultural_contexts, created_contexts):
            assert context.geographic_location_id == location.id
            assert context.cultural_group == original_data['cultural_group']
            assert context.negotiation_style == original_data['negotiation_style']
            assert context.time_orientation == original_data['time_orientation']
            assert set(context.communication_preferences) == set(original_data['communication_preferences'])
            assert context.formality_level == original_data['formality_level']
            assert context.directness_preference == original_data['directness_preference']
            assert context.bargaining_culture == original_data['bargaining_culture']
        
        # 2. Cultural contexts should be independently retrievable
        for context in created_contexts:
            result = await db_session.execute(
                select(CulturalContext).where(CulturalContext.id == context.id)
            )
            retrieved_context = result.scalar_one()
            assert retrieved_context is not None
            assert retrieved_context.id == context.id
            assert retrieved_context.geographic_location_id == location.id
        
        # 3. Changes to one cultural context should not affect others
        if len(created_contexts) > 1:
            first_context = created_contexts[0]
            original_style = first_context.negotiation_style
            
            # Change negotiation style
            new_style = (
                NegotiationStyle.DIRECT if original_style != NegotiationStyle.DIRECT
                else NegotiationStyle.INDIRECT
            )
            first_context.negotiation_style = new_style
            await db_session.commit()
            
            # Verify other contexts are unaffected
            for i, context in enumerate(created_contexts[1:], 1):
                await db_session.refresh(context)
                original_data = cultural_contexts[i]
                assert context.negotiation_style == original_data['negotiation_style']
    
    @given(
        location_data=valid_geographic_location_data(),
        config_data=valid_region_configuration_data()
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_region_specific_platform_configuration(
        self,
        location_data: Dict[str, Any],
        config_data: Dict[str, Any],
        db_session: AsyncSession
    ):
        """
        **Property 34: Multi-Region Configuration**
        **Validates: Requirements 10.1**
        
        For any region with platform configuration, the configuration
        should be specific to that region and not affect global or
        other regional settings.
        """
        # Create geographic location
        location = GeographicLocation(**location_data)
        db_session.add(location)
        await db_session.commit()
        await db_session.refresh(location)
        
        # Create region-specific configuration
        config = RegionConfiguration(
            geographic_location_id=location.id,
            **config_data
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)
        
        # Verify region-specific configuration
        
        # 1. Configuration should be linked to the specific region
        assert config.geographic_location_id == location.id
        assert config.platform_name == config_data['platform_name']
        assert set(config.features_enabled) == set(config_data['features_enabled'])
        assert abs(config.minimum_transaction_amount - config_data['minimum_transaction_amount']) < 0.01
        assert abs(config.maximum_transaction_amount - config_data['maximum_transaction_amount']) < 0.01
        assert abs(config.escrow_threshold - config_data['escrow_threshold']) < 0.01
        
        # 2. Language settings should be region-specific
        assert config.language_settings['default_language'] == config_data['language_settings']['default_language']
        assert set(config.language_settings['supported_languages']) == set(config_data['language_settings']['supported_languages'])
        assert config.language_settings['rtl_support'] == config_data['language_settings']['rtl_support']
        
        # 3. Configuration should be retrievable by region
        result = await db_session.execute(
            select(RegionConfiguration).where(
                RegionConfiguration.geographic_location_id == location.id
            )
        )
        retrieved_config = result.scalar_one()
        
        assert retrieved_config is not None
        assert retrieved_config.id == config.id
        assert retrieved_config.geographic_location_id == location.id
        assert retrieved_config.platform_name == config_data['platform_name']
    
    @given(
        regions_data=st.lists(
            st.tuples(
                valid_geographic_location_data(),
                valid_user_data()
            ),
            min_size=2,
            max_size=3
        )
    )
    @settings(max_examples=8, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_user_region_association_independence(
        self,
        regions_data: List[tuple],
        db_session: AsyncSession
    ):
        """
        **Property 34: Multi-Region Configuration**
        **Validates: Requirements 10.1**
        
        For any users associated with different regions, each user should
        be independently associated with their region without affecting
        users in other regions.
        """
        created_locations = []
        created_users = []
        
        # Create regions and users
        for i, (location_data, user_data) in enumerate(regions_data):
            # Create location
            location = GeographicLocation(**location_data)
            db_session.add(location)
            created_locations.append(location)
        
        await db_session.commit()
        
        # Refresh locations and create users
        for i, (location, (_, user_data)) in enumerate(zip(created_locations, regions_data)):
            await db_session.refresh(location)
            
            # Create user associated with this location
            user_data['email'] = f"user_{i}_{str(uuid4())[:8]}@example.com"
            user = User(
                geographic_location_id=location.id,
                country=location.country,
                region=location.region,
                city=location.city,
                timezone=location.timezone,
                currency=location.currency.value,
                **user_data
            )
            db_session.add(user)
            created_users.append(user)
        
        await db_session.commit()
        
        # Refresh all users
        for user in created_users:
            await db_session.refresh(user)
        
        # Verify independent user-region associations
        
        # 1. Each user should be correctly associated with their region
        for user, location in zip(created_users, created_locations):
            assert user.geographic_location_id == location.id
            assert user.country == location.country
            assert user.region == location.region
            assert user.city == location.city
            assert user.timezone == location.timezone
            assert user.currency == location.currency.value
        
        # 2. Users should be retrievable by region
        for location in created_locations:
            result = await db_session.execute(
                select(User).where(User.geographic_location_id == location.id)
            )
            region_users = result.scalars().all()
            
            # Should have exactly one user for this region
            assert len(region_users) == 1
            user = region_users[0]
            assert user.geographic_location_id == location.id
        
        # 3. Changes to one region's users should not affect other regions
        # Deactivate first user
        first_user = created_users[0]
        first_user.is_active = False
        await db_session.commit()
        
        # Verify other users are unaffected
        for user in created_users[1:]:
            await db_session.refresh(user)
            assert user.is_active is True
    
    @given(
        location_data=valid_geographic_location_data(),
        user_data=valid_user_data(),
        product_names=st.lists(
            st.text(min_size=3, max_size=20),
            min_size=1,
            max_size=3
        )
    )
    @settings(max_examples=8, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_region_product_catalog_independence(
        self,
        location_data: Dict[str, Any],
        user_data: Dict[str, Any],
        product_names: List[str],
        db_session: AsyncSession
    ):
        """
        **Property 34: Multi-Region Configuration**
        **Validates: Requirements 10.1**
        
        For any region with products, the product catalog should be
        region-specific and not interfere with product catalogs in
        other regions.
        """
        # Create geographic location
        location = GeographicLocation(**location_data)
        db_session.add(location)
        await db_session.commit()
        await db_session.refresh(location)
        
        # Create vendor user in this region
        user_data['role'] = UserRole.VENDOR
        vendor = User(
            geographic_location_id=location.id,
            country=location.country,
            region=location.region,
            city=location.city,
            timezone=location.timezone,
            currency=location.currency.value,
            **user_data
        )
        db_session.add(vendor)
        await db_session.commit()
        await db_session.refresh(vendor)
        
        # Create products for this region
        created_products = []
        for i, product_name in enumerate(product_names):
            product = Product(
                vendor_id=vendor.id,
                name=f"{product_name}_{i}",
                description=f"Product {product_name} in {location.city}",
                base_price=10.0 + i,
                current_price=10.0 + i,
                currency=location.currency.value,
                quantity_available=100,
                availability=AvailabilityStatus.IN_STOCK,
                is_active=True
            )
            db_session.add(product)
            created_products.append(product)
        
        await db_session.commit()
        
        # Refresh all products
        for product in created_products:
            await db_session.refresh(product)
        
        # Verify region-specific product catalog
        
        # 1. All products should be associated with the region's vendor
        for product in created_products:
            assert product.vendor_id == vendor.id
            assert product.currency == location.currency.value
            assert product.is_active is True
        
        # 2. Products should be retrievable by region (through vendor)
        result = await db_session.execute(
            select(Product).where(Product.vendor_id == vendor.id)
        )
        region_products = result.scalars().all()
        
        assert len(region_products) == len(product_names)
        
        # 3. Product configurations should reflect regional settings
        for product in region_products:
            assert product.currency == location.currency.value
            # Product description should reference the region
            assert location.city in product.description
        
        # 4. Products should maintain regional pricing context
        for i, product in enumerate(region_products):
            expected_price = 10.0 + i
            assert abs(product.base_price - expected_price) < 0.01
            assert abs(product.current_price - expected_price) < 0.01