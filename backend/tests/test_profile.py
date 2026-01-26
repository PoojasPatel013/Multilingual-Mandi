"""
Unit tests for user profile management.

This module tests the enhanced user profile management functionality
including cultural context, geographic location, and role-specific profiles.
"""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, VerificationStatus, VendorProfile, CustomerProfile
from app.schemas.profile import (
    UserProfileUpdate, GeographicLocationSchema, CulturalContextSchema,
    VendorProfileUpdate, PaymentMethodCreate
)
from app.services.user_service import UserService


class TestUserProfileManagement:
    """Test user profile management operations."""
    
    @pytest.mark.asyncio
    async def test_update_user_profile_with_cultural_context(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test updating user profile with cultural context."""
        user_service = UserService(db_session)
        
        # Create cultural context
        cultural_context = CulturalContextSchema(
            region="South Asia",
            negotiation_style="relationship_based",
            time_orientation="flexible",
            communication_preferences=["indirect", "respectful"],
            business_etiquette=["greeting_important", "relationship_first"],
            holidays_and_events=["Diwali", "Eid", "Holi"]
        )
        
        # Create geographic location
        geographic_location = GeographicLocationSchema(
            country="India",
            region="Maharashtra",
            city="Mumbai",
            coordinates={"lat": 19.0760, "lng": 72.8777},
            timezone="Asia/Kolkata",
            currency="INR"
        )
        
        # Create profile update
        profile_update = UserProfileUpdate(
            first_name="Rajesh",
            last_name="Sharma",
            phone_number="+91-9876543210",
            preferred_language="hi",
            cultural_context=cultural_context,
            geographic_location=geographic_location
        )
        
        # Update profile
        updated_user = await user_service.update_user_profile(
            sample_user.id,
            profile_update
        )
        
        # Verify updates
        assert updated_user is not None
        assert updated_user.first_name == "Rajesh"
        assert updated_user.last_name == "Sharma"
        assert updated_user.phone_number == "+91-9876543210"
        assert updated_user.preferred_language == "hi"
        assert updated_user.country == "India"
        assert updated_user.region == "Maharashtra"
        assert updated_user.city == "Mumbai"
        assert updated_user.timezone == "Asia/Kolkata"
        assert updated_user.currency == "INR"
        assert updated_user.coordinates == {"lat": 19.0760, "lng": 72.8777}
        
        # Verify cultural profile
        assert updated_user.cultural_profile is not None
        cultural_profile = updated_user.cultural_profile
        assert cultural_profile["region"] == "South Asia"
        assert cultural_profile["negotiation_style"] == "relationship_based"
        assert cultural_profile["time_orientation"] == "flexible"
        assert "indirect" in cultural_profile["communication_preferences"]
        assert "Diwali" in cultural_profile["holidays_and_events"]
    
    @pytest.mark.asyncio
    async def test_update_user_profile_partial(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test partial user profile update."""
        user_service = UserService(db_session)
        
        # Create partial update
        profile_update = UserProfileUpdate(
            first_name="UpdatedName",
            preferred_language="es"
        )
        
        # Update profile
        updated_user = await user_service.update_user_profile(
            sample_user.id,
            profile_update
        )
        
        # Verify updates
        assert updated_user is not None
        assert updated_user.first_name == "UpdatedName"
        assert updated_user.preferred_language == "es"
        # Other fields should remain unchanged
        assert updated_user.last_name == sample_user.last_name
        assert updated_user.email == sample_user.email
    
    @pytest.mark.asyncio
    async def test_create_customer_profile(
        self, 
        db_session: AsyncSession,
        sample_customer: User
    ):
        """Test creating customer profile."""
        user_service = UserService(db_session)
        
        # Create customer profile
        customer_profile = await user_service.create_customer_profile(sample_customer.id)
        
        # Verify profile creation
        assert customer_profile is not None
        assert customer_profile.user_id == sample_customer.id
        assert customer_profile.total_purchases == 0
        assert customer_profile.total_spent == 0.0
        assert customer_profile.average_rating_given == 0.0
        assert customer_profile.preferred_categories == []
        assert customer_profile.wishlist_items == []
        assert customer_profile.favorite_vendors == []
    
    @pytest.mark.asyncio
    async def test_create_customer_profile_for_vendor_fails(
        self, 
        db_session: AsyncSession,
        sample_vendor: User
    ):
        """Test that creating customer profile for vendor fails."""
        user_service = UserService(db_session)
        
        # Attempt to create customer profile for vendor
        customer_profile = await user_service.create_customer_profile(sample_vendor.id)
        
        # Should return None
        assert customer_profile is None
    
    @pytest.mark.asyncio
    async def test_update_customer_profile(
        self, 
        db_session: AsyncSession,
        sample_customer_with_profile: tuple[User, CustomerProfile]
    ):
        """Test updating customer profile."""
        user, customer_profile = sample_customer_with_profile
        user_service = UserService(db_session)
        
        # Update customer profile
        update_data = {
            "preferred_categories": ["electronics", "books"],
            "price_range_preferences": {
                "electronics": {"min": 100, "max": 5000},
                "books": {"min": 10, "max": 500}
            },
            "wishlist_items": [str(uuid4()), str(uuid4())],
            "favorite_vendors": [str(uuid4())]
        }
        
        updated_profile = await user_service.update_customer_profile(
            user.id,
            update_data
        )
        
        # Verify updates
        assert updated_profile is not None
        assert updated_profile.preferred_categories == ["electronics", "books"]
        assert "electronics" in updated_profile.price_range_preferences
        assert len(updated_profile.wishlist_items) == 2
        assert len(updated_profile.favorite_vendors) == 1
    
    @pytest.mark.asyncio
    async def test_update_vendor_profile(
        self, 
        db_session: AsyncSession,
        sample_vendor_with_profile: tuple[User, VendorProfile]
    ):
        """Test updating vendor profile."""
        user, vendor_profile = sample_vendor_with_profile
        user_service = UserService(db_session)
        
        # Create vendor profile update
        vendor_update = VendorProfileUpdate(
            business_name="Updated Business Name",
            business_type="Retail",
            business_description="Updated description",
            languages=["en", "hi", "mr"],
            communication_preferences={"preferred_time": "morning"},
            payment_methods=[
                {"type": "card", "provider": "stripe"},
                {"type": "upi", "provider": "paytm"}
            ],
            business_hours={
                "monday": {"open": "09:00", "close": "18:00"},
                "tuesday": {"open": "09:00", "close": "18:00"}
            },
            is_available=True
        )
        
        # Update vendor profile
        updated_profile = await user_service.update_vendor_profile(
            user.id,
            vendor_update
        )
        
        # Verify updates
        assert updated_profile is not None
        assert updated_profile.business_name == "Updated Business Name"
        assert updated_profile.business_type == "Retail"
        assert updated_profile.business_description == "Updated description"
        assert updated_profile.languages == ["en", "hi", "mr"]
        assert updated_profile.communication_preferences["preferred_time"] == "morning"
        assert len(updated_profile.payment_methods) == 2
        assert "monday" in updated_profile.business_hours
        assert updated_profile.is_available is True
    
    @pytest.mark.asyncio
    async def test_add_payment_method(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test adding payment method."""
        user_service = UserService(db_session)
        
        # Create payment method
        payment_data = PaymentMethodCreate(
            method_type="card",
            provider="stripe",
            details={
                "last_four": "1234",
                "brand": "visa",
                "exp_month": 12,
                "exp_year": 2025
            },
            is_default=True
        )
        
        # Add payment method
        payment_method = await user_service.add_payment_method(
            sample_user.id,
            payment_data
        )
        
        # Verify payment method
        assert payment_method is not None
        assert payment_method.user_id == sample_user.id
        assert payment_method.method_type == "card"
        assert payment_method.provider == "stripe"
        assert payment_method.is_default is True
        assert payment_method.is_active is True
        assert payment_method.details["last_four"] == "1234"
    
    @pytest.mark.asyncio
    async def test_add_multiple_payment_methods_default_handling(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test that adding new default payment method unsets previous default."""
        user_service = UserService(db_session)
        
        # Add first payment method as default
        payment_data_1 = PaymentMethodCreate(
            method_type="card",
            provider="stripe",
            details={"last_four": "1111"},
            is_default=True
        )
        
        payment_method_1 = await user_service.add_payment_method(
            sample_user.id,
            payment_data_1
        )
        
        # Add second payment method as default
        payment_data_2 = PaymentMethodCreate(
            method_type="bank",
            provider="plaid",
            details={"account_last_four": "2222"},
            is_default=True
        )
        
        payment_method_2 = await user_service.add_payment_method(
            sample_user.id,
            payment_data_2
        )
        
        # Get all payment methods
        payment_methods = await user_service.get_user_payment_methods(sample_user.id)
        
        # Verify only one is default
        default_methods = [pm for pm in payment_methods if pm.is_default]
        assert len(default_methods) == 1
        assert default_methods[0].id == payment_method_2.id
    
    @pytest.mark.asyncio
    async def test_delete_payment_method(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test deleting payment method."""
        user_service = UserService(db_session)
        
        # Add payment method
        payment_data = PaymentMethodCreate(
            method_type="card",
            provider="stripe",
            details={"last_four": "1234"},
            is_default=False
        )
        
        payment_method = await user_service.add_payment_method(
            sample_user.id,
            payment_data
        )
        
        # Delete payment method
        success = await user_service.delete_payment_method(
            sample_user.id,
            payment_method.id
        )
        
        # Verify deletion
        assert success is True
        
        # Verify payment method is deactivated
        payment_methods = await user_service.get_user_payment_methods(sample_user.id)
        assert len(payment_methods) == 0  # Should not return inactive methods
    
    @pytest.mark.asyncio
    async def test_get_user_with_profiles(
        self, 
        db_session: AsyncSession,
        sample_vendor_with_profile: tuple[User, VendorProfile]
    ):
        """Test getting user with all profiles loaded."""
        user, vendor_profile = sample_vendor_with_profile
        user_service = UserService(db_session)
        
        # Get user with profiles
        user_with_profiles = await user_service.get_user_with_profiles(user.id)
        
        # Verify user and profiles are loaded
        assert user_with_profiles is not None
        assert user_with_profiles.id == user.id
        assert user_with_profiles.vendor_profile is not None
        assert user_with_profiles.vendor_profile.id == vendor_profile.id


class TestCulturalContextValidation:
    """Test cultural context schema validation."""
    
    def test_valid_cultural_context(self):
        """Test valid cultural context creation."""
        cultural_context = CulturalContextSchema(
            region="East Asia",
            negotiation_style="indirect",
            time_orientation="punctual",
            communication_preferences=["formal", "hierarchical"],
            business_etiquette=["bow_greeting", "business_card_ceremony"],
            holidays_and_events=["Chinese New Year", "Golden Week"]
        )
        
        assert cultural_context.region == "East Asia"
        assert cultural_context.negotiation_style == "indirect"
        assert cultural_context.time_orientation == "punctual"
        assert "formal" in cultural_context.communication_preferences
        assert "Chinese New Year" in cultural_context.holidays_and_events
    
    def test_invalid_negotiation_style(self):
        """Test invalid negotiation style raises validation error."""
        with pytest.raises(ValueError, match="Negotiation style must be one of"):
            CulturalContextSchema(
                region="Test Region",
                negotiation_style="invalid_style",
                time_orientation="punctual"
            )
    
    def test_invalid_time_orientation(self):
        """Test invalid time orientation raises validation error."""
        with pytest.raises(ValueError, match="Time orientation must be one of"):
            CulturalContextSchema(
                region="Test Region",
                negotiation_style="direct",
                time_orientation="invalid_orientation"
            )


class TestGeographicLocationValidation:
    """Test geographic location schema validation."""
    
    def test_valid_geographic_location(self):
        """Test valid geographic location creation."""
        location = GeographicLocationSchema(
            country="United States",
            region="California",
            city="San Francisco",
            coordinates={"lat": 37.7749, "lng": -122.4194},
            timezone="America/Los_Angeles",
            currency="USD"
        )
        
        assert location.country == "United States"
        assert location.coordinates["lat"] == 37.7749
        assert location.coordinates["lng"] == -122.4194
    
    def test_invalid_coordinates_format(self):
        """Test invalid coordinates format raises validation error."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            GeographicLocationSchema(
                country="Test Country",
                region="Test Region",
                city="Test City",
                coordinates="invalid",
                timezone="UTC",
                currency="USD"
            )
    
    def test_invalid_coordinates_keys(self):
        """Test missing coordinate keys raises validation error."""
        with pytest.raises(ValueError, match="Coordinates must contain 'lat' and 'lng' keys"):
            GeographicLocationSchema(
                country="Test Country",
                region="Test Region",
                city="Test City",
                coordinates={"latitude": 0, "longitude": 0},
                timezone="UTC",
                currency="USD"
            )
    
    def test_invalid_latitude_range(self):
        """Test invalid latitude range raises validation error."""
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            GeographicLocationSchema(
                country="Test Country",
                region="Test Region",
                city="Test City",
                coordinates={"lat": 95, "lng": 0},
                timezone="UTC",
                currency="USD"
            )
    
    def test_invalid_longitude_range(self):
        """Test invalid longitude range raises validation error."""
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            GeographicLocationSchema(
                country="Test Country",
                region="Test Region",
                city="Test City",
                coordinates={"lat": 0, "lng": 185},
                timezone="UTC",
                currency="USD"
            )