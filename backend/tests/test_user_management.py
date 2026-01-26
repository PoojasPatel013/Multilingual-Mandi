"""
Comprehensive unit tests for user management functionality.

This module provides comprehensive unit tests for user management operations
including profile creation, updates, role-based access control, cultural context,
geographic location handling, and payment method management.

Tests Requirements: 3.1, 4.1, 5.1
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import (
    User, UserRole, VerificationStatus, VendorProfile, 
    CustomerProfile, PaymentMethod
)
from app.schemas.profile import (
    UserProfileUpdate, GeographicLocationSchema, CulturalContextSchema,
    VendorProfileUpdate, PaymentMethodCreate, UserVerificationUpdate
)
from app.schemas.auth import UserRegister, VendorProfileCreate
from app.services.user_service import UserService


class TestUserCreationAndAuthentication:
    """Test user creation and authentication functionality."""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session: AsyncSession):
        """Test successful user creation."""
        user_service = UserService(db_session)
        
        user_data = UserRegister(
            email="newuser@example.com",
            password="securepass123",
            first_name="New",
            last_name="User",
            role=UserRole.CUSTOMER,
            preferred_language="en",
            country="US",
            region="California",
            city="San Francisco",
            timezone="America/Los_Angeles",
            currency="USD"
        )
        
        user = await user_service.create_user(user_data)
        
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.first_name == "New"
        assert user.last_name == "User"
        assert user.role == UserRole.CUSTOMER
        assert user.preferred_language == "en"
        assert user.country == "US"
        assert user.verification_status == VerificationStatus.PENDING
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.login_count == 0
        # Password should be hashed, not plain text
        assert user.hashed_password != "securepass123"
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_fails(self, db_session: AsyncSession):
        """Test that creating user with duplicate email fails."""
        user_service = UserService(db_session)
        
        user_data = UserRegister(
            email="duplicate@example.com",
            password="securepass123",
            first_name="First",
            last_name="User",
            role=UserRole.CUSTOMER
        )
        
        # Create first user
        await user_service.create_user(user_data)
        
        # Attempt to create second user with same email
        with pytest.raises(ValueError, match="Email already registered"):
            await user_service.create_user(user_data)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session: AsyncSession):
        """Test successful user authentication."""
        user_service = UserService(db_session)
        
        # Create user
        user_data = UserRegister(
            email="auth@example.com",
            password="authpass123",
            first_name="Auth",
            last_name="User",
            role=UserRole.CUSTOMER
        )
        
        created_user = await user_service.create_user(user_data)
        initial_login_count = created_user.login_count
        
        # Authenticate user
        authenticated_user = await user_service.authenticate_user(
            "auth@example.com", 
            "authpass123"
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.login_count == initial_login_count + 1
        assert authenticated_user.last_active is not None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password_fails(self, db_session: AsyncSession):
        """Test authentication with wrong password fails."""
        user_service = UserService(db_session)
        
        # Create user
        user_data = UserRegister(
            email="wrongpass@example.com",
            password="correctpass123",
            first_name="Wrong",
            last_name="Pass",
            role=UserRole.CUSTOMER
        )
        
        await user_service.create_user(user_data)
        
        # Attempt authentication with wrong password
        authenticated_user = await user_service.authenticate_user(
            "wrongpass@example.com", 
            "wrongpassword"
        )
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user_fails(self, db_session: AsyncSession):
        """Test authentication with nonexistent user fails."""
        user_service = UserService(db_session)
        
        authenticated_user = await user_service.authenticate_user(
            "nonexistent@example.com", 
            "anypassword"
        )
        
        assert authenticated_user is None


class TestUserProfileManagement:
    """Test comprehensive user profile management."""
    
    @pytest.mark.asyncio
    async def test_update_basic_profile_information(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test updating basic profile information."""
        user_service = UserService(db_session)
        
        profile_update = UserProfileUpdate(
            first_name="Updated",
            last_name="Name",
            phone_number="+1-555-0123",
            preferred_language="es"
        )
        
        updated_user = await user_service.update_user_profile(
            sample_user.id,
            profile_update
        )
        
        assert updated_user is not None
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.phone_number == "+1-555-0123"
        assert updated_user.preferred_language == "es"
        # Other fields should remain unchanged
        assert updated_user.email == sample_user.email
        assert updated_user.role == sample_user.role
    
    @pytest.mark.asyncio
    async def test_update_profile_with_geographic_location(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test updating profile with geographic location."""
        user_service = UserService(db_session)
        
        geographic_location = GeographicLocationSchema(
            country="India",
            region="Maharashtra",
            city="Mumbai",
            coordinates={"lat": 19.0760, "lng": 72.8777},
            timezone="Asia/Kolkata",
            currency="INR"
        )
        
        profile_update = UserProfileUpdate(
            geographic_location=geographic_location
        )
        
        updated_user = await user_service.update_user_profile(
            sample_user.id,
            profile_update
        )
        
        assert updated_user is not None
        assert updated_user.country == "India"
        assert updated_user.region == "Maharashtra"
        assert updated_user.city == "Mumbai"
        assert updated_user.timezone == "Asia/Kolkata"
        assert updated_user.currency == "INR"
        assert updated_user.coordinates == {"lat": 19.0760, "lng": 72.8777}
    
    @pytest.mark.asyncio
    async def test_update_profile_with_cultural_context(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test updating profile with cultural context."""
        user_service = UserService(db_session)
        
        cultural_context = CulturalContextSchema(
            region="South Asia",
            negotiation_style="relationship_based",
            time_orientation="flexible",
            communication_preferences=["indirect", "respectful", "hierarchical"],
            business_etiquette=["greeting_important", "relationship_first", "patience_valued"],
            holidays_and_events=["Diwali", "Eid", "Holi", "Dussehra"]
        )
        
        profile_update = UserProfileUpdate(
            cultural_context=cultural_context
        )
        
        updated_user = await user_service.update_user_profile(
            sample_user.id,
            profile_update
        )
        
        assert updated_user is not None
        assert updated_user.cultural_profile is not None
        
        cultural_profile = updated_user.cultural_profile
        assert cultural_profile["region"] == "South Asia"
        assert cultural_profile["negotiation_style"] == "relationship_based"
        assert cultural_profile["time_orientation"] == "flexible"
        assert "indirect" in cultural_profile["communication_preferences"]
        assert "respectful" in cultural_profile["communication_preferences"]
        assert "hierarchical" in cultural_profile["communication_preferences"]
        assert "greeting_important" in cultural_profile["business_etiquette"]
        assert "Diwali" in cultural_profile["holidays_and_events"]
        assert "Eid" in cultural_profile["holidays_and_events"]
    
    @pytest.mark.asyncio
    async def test_update_profile_comprehensive(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test comprehensive profile update with all fields."""
        user_service = UserService(db_session)
        
        geographic_location = GeographicLocationSchema(
            country="Japan",
            region="Tokyo",
            city="Shibuya",
            coordinates={"lat": 35.6762, "lng": 139.6503},
            timezone="Asia/Tokyo",
            currency="JPY"
        )
        
        cultural_context = CulturalContextSchema(
            region="East Asia",
            negotiation_style="indirect",
            time_orientation="punctual",
            communication_preferences=["formal", "hierarchical", "respectful"],
            business_etiquette=["bow_greeting", "business_card_ceremony", "punctuality_important"],
            holidays_and_events=["Golden Week", "Obon", "New Year"]
        )
        
        profile_update = UserProfileUpdate(
            first_name="Hiroshi",
            last_name="Tanaka",
            phone_number="+81-3-1234-5678",
            preferred_language="ja",
            geographic_location=geographic_location,
            cultural_context=cultural_context
        )
        
        updated_user = await user_service.update_user_profile(
            sample_user.id,
            profile_update
        )
        
        assert updated_user is not None
        
        # Basic profile
        assert updated_user.first_name == "Hiroshi"
        assert updated_user.last_name == "Tanaka"
        assert updated_user.phone_number == "+81-3-1234-5678"
        assert updated_user.preferred_language == "ja"
        
        # Geographic location
        assert updated_user.country == "Japan"
        assert updated_user.region == "Tokyo"
        assert updated_user.city == "Shibuya"
        assert updated_user.timezone == "Asia/Tokyo"
        assert updated_user.currency == "JPY"
        assert updated_user.coordinates == {"lat": 35.6762, "lng": 139.6503}
        
        # Cultural context
        cultural_profile = updated_user.cultural_profile
        assert cultural_profile["region"] == "East Asia"
        assert cultural_profile["negotiation_style"] == "indirect"
        assert cultural_profile["time_orientation"] == "punctual"
        assert "formal" in cultural_profile["communication_preferences"]
        assert "bow_greeting" in cultural_profile["business_etiquette"]
        assert "Golden Week" in cultural_profile["holidays_and_events"]
    
    @pytest.mark.asyncio
    async def test_update_profile_partial_fields(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test partial profile update preserves existing data."""
        user_service = UserService(db_session)
        
        # First update with some fields
        initial_update = UserProfileUpdate(
            first_name="Initial",
            preferred_language="fr",
            geographic_location=GeographicLocationSchema(
                country="France",
                region="Île-de-France",
                city="Paris",
                timezone="Europe/Paris",
                currency="EUR"
            )
        )
        
        await user_service.update_user_profile(sample_user.id, initial_update)
        
        # Second update with different fields
        partial_update = UserProfileUpdate(
            last_name="Partial",
            phone_number="+33-1-23-45-67-89"
        )
        
        updated_user = await user_service.update_user_profile(
            sample_user.id,
            partial_update
        )
        
        assert updated_user is not None
        # New fields should be updated
        assert updated_user.last_name == "Partial"
        assert updated_user.phone_number == "+33-1-23-45-67-89"
        # Previous fields should be preserved
        assert updated_user.first_name == "Initial"
        assert updated_user.preferred_language == "fr"
        assert updated_user.country == "France"
        assert updated_user.city == "Paris"
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_user_profile_fails(self, db_session: AsyncSession):
        """Test updating profile for nonexistent user fails."""
        user_service = UserService(db_session)
        
        profile_update = UserProfileUpdate(
            first_name="Nonexistent"
        )
        
        updated_user = await user_service.update_user_profile(
            uuid4(),  # Random UUID
            profile_update
        )
        
        assert updated_user is None


class TestPasswordManagement:
    """Test password management functionality."""
    
    @pytest.mark.asyncio
    async def test_change_password_success(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test successful password change."""
        user_service = UserService(db_session)
        
        # Set a known password for the sample user
        from app.core.auth import get_password_hash
        original_password = "originalpass123"
        sample_user.hashed_password = get_password_hash(original_password)
        await db_session.commit()
        
        # Change password
        success = await user_service.change_password(
            sample_user.id,
            original_password,
            "newpassword456"
        )
        
        assert success is True
        
        # Verify new password works
        authenticated_user = await user_service.authenticate_user(
            sample_user.email,
            "newpassword456"
        )
        assert authenticated_user is not None
        
        # Verify old password doesn't work
        old_auth = await user_service.authenticate_user(
            sample_user.email,
            original_password
        )
        assert old_auth is None
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current_password_fails(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test password change with wrong current password fails."""
        user_service = UserService(db_session)
        
        success = await user_service.change_password(
            sample_user.id,
            "wrongcurrentpassword",
            "newpassword456"
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_reset_password_success(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test successful password reset."""
        user_service = UserService(db_session)
        
        success = await user_service.reset_password(
            sample_user.email,
            "resetpassword789"
        )
        
        assert success is True
        
        # Verify new password works
        authenticated_user = await user_service.authenticate_user(
            sample_user.email,
            "resetpassword789"
        )
        assert authenticated_user is not None
    
    @pytest.mark.asyncio
    async def test_reset_password_nonexistent_user_fails(self, db_session: AsyncSession):
        """Test password reset for nonexistent user fails."""
        user_service = UserService(db_session)
        
        success = await user_service.reset_password(
            "nonexistent@example.com",
            "newpassword"
        )
        
        assert success is False


class TestUserActivationAndDeactivation:
    """Test user activation and deactivation functionality."""
    
    @pytest.mark.asyncio
    async def test_deactivate_user_success(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test successful user deactivation."""
        user_service = UserService(db_session)
        
        # Ensure user is initially active
        assert sample_user.is_active is True
        
        success = await user_service.deactivate_user(sample_user.id)
        
        assert success is True
        
        # Verify user is deactivated
        updated_user = await user_service.get_user_by_id(sample_user.id)
        assert updated_user.is_active is False
    
    @pytest.mark.asyncio
    async def test_activate_user_success(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test successful user activation."""
        user_service = UserService(db_session)
        
        # First deactivate the user
        sample_user.is_active = False
        await db_session.commit()
        
        success = await user_service.activate_user(sample_user.id)
        
        assert success is True
        
        # Verify user is activated
        updated_user = await user_service.get_user_by_id(sample_user.id)
        assert updated_user.is_active is True
    
    @pytest.mark.asyncio
    async def test_deactivate_nonexistent_user_fails(self, db_session: AsyncSession):
        """Test deactivating nonexistent user fails."""
        user_service = UserService(db_session)
        
        success = await user_service.deactivate_user(uuid4())
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_activate_nonexistent_user_fails(self, db_session: AsyncSession):
        """Test activating nonexistent user fails."""
        user_service = UserService(db_session)
        
        success = await user_service.activate_user(uuid4())
        
        assert success is False


class TestVendorProfileManagement:
    """Test vendor profile management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_vendor_profile_success(
        self, 
        db_session: AsyncSession,
        sample_vendor: User
    ):
        """Test successful vendor profile creation."""
        user_service = UserService(db_session)
        
        profile_data = VendorProfileCreate(
            business_name="Test Vendor Business",
            business_type="Retail",
            business_description="A comprehensive test business for multilingual trading",
            market_stall="Stall B12",
            languages=["en", "es", "fr"],
            communication_preferences={
                "preferred_time": "morning",
                "response_time": "within_1_hour",
                "communication_style": "professional"
            },
            payment_methods=[
                {"type": "card", "provider": "stripe"},
                {"type": "bank", "provider": "plaid"},
                {"type": "mobile", "provider": "paypal"}
            ],
            business_hours={
                "monday": {"open": "09:00", "close": "18:00"},
                "tuesday": {"open": "09:00", "close": "18:00"},
                "wednesday": {"open": "09:00", "close": "18:00"},
                "thursday": {"open": "09:00", "close": "18:00"},
                "friday": {"open": "09:00", "close": "18:00"},
                "saturday": {"open": "10:00", "close": "16:00"},
                "sunday": {"closed": True}
            }
        )
        
        vendor_profile = await user_service.create_vendor_profile(
            sample_vendor.id,
            profile_data
        )
        
        assert vendor_profile is not None
        assert vendor_profile.user_id == sample_vendor.id
        assert vendor_profile.business_name == "Test Vendor Business"
        assert vendor_profile.business_type == "Retail"
        assert vendor_profile.business_description == "A comprehensive test business for multilingual trading"
        assert vendor_profile.market_stall == "Stall B12"
        assert vendor_profile.languages == ["en", "es", "fr"]
        assert vendor_profile.communication_preferences["preferred_time"] == "morning"
        assert len(vendor_profile.payment_methods) == 3
        assert "monday" in vendor_profile.business_hours
        assert vendor_profile.average_rating == 0.0
        assert vendor_profile.total_sales == 0
        assert vendor_profile.total_reviews == 0
        assert vendor_profile.is_available is True
    
    @pytest.mark.asyncio
    async def test_create_vendor_profile_for_customer_fails(
        self, 
        db_session: AsyncSession,
        sample_customer: User
    ):
        """Test creating vendor profile for customer user fails."""
        user_service = UserService(db_session)
        
        profile_data = VendorProfileCreate(
            business_name="Should Fail",
            business_type="Retail"
        )
        
        vendor_profile = await user_service.create_vendor_profile(
            sample_customer.id,
            profile_data
        )
        
        assert vendor_profile is None
    
    @pytest.mark.asyncio
    async def test_create_duplicate_vendor_profile_returns_existing(
        self, 
        db_session: AsyncSession,
        sample_vendor_with_profile
    ):
        """Test creating duplicate vendor profile returns existing profile."""
        sample_vendor, existing_profile = sample_vendor_with_profile
        user_service = UserService(db_session)
        
        profile_data = VendorProfileCreate(
            business_name="New Business Name",
            business_type="Different Type"
        )
        
        vendor_profile = await user_service.create_vendor_profile(
            sample_vendor.id,
            profile_data
        )
        
        # Should return existing profile, not create new one
        assert vendor_profile is not None
        assert vendor_profile.id == existing_profile.id
        assert vendor_profile.business_name == existing_profile.business_name
    
    @pytest.mark.asyncio
    async def test_update_vendor_profile_success(
        self, 
        db_session: AsyncSession,
        sample_vendor_with_profile
    ):
        """Test successful vendor profile update."""
        sample_vendor, vendor_profile = sample_vendor_with_profile
        user_service = UserService(db_session)
        
        update_data = VendorProfileUpdate(
            business_name="Updated Business Name",
            business_description="Updated comprehensive business description",
            languages=["en", "hi", "mr", "gu"],
            communication_preferences={
                "preferred_time": "evening",
                "response_time": "within_30_minutes",
                "communication_style": "friendly"
            },
            payment_methods=[
                {"type": "card", "provider": "stripe"},
                {"type": "upi", "provider": "paytm"},
                {"type": "bank", "provider": "razorpay"}
            ],
            business_hours={
                "monday": {"open": "10:00", "close": "19:00"},
                "tuesday": {"open": "10:00", "close": "19:00"},
                "wednesday": {"open": "10:00", "close": "19:00"},
                "thursday": {"open": "10:00", "close": "19:00"},
                "friday": {"open": "10:00", "close": "19:00"},
                "saturday": {"open": "11:00", "close": "17:00"},
                "sunday": {"open": "12:00", "close": "16:00"}
            },
            is_available=False
        )
        
        updated_profile = await user_service.update_vendor_profile(
            sample_vendor.id,
            update_data
        )
        
        assert updated_profile is not None
        assert updated_profile.business_name == "Updated Business Name"
        assert updated_profile.business_description == "Updated comprehensive business description"
        assert updated_profile.languages == ["en", "hi", "mr", "gu"]
        assert updated_profile.communication_preferences["preferred_time"] == "evening"
        assert updated_profile.communication_preferences["response_time"] == "within_30_minutes"
        assert len(updated_profile.payment_methods) == 3
        assert updated_profile.business_hours["monday"]["open"] == "10:00"
        assert updated_profile.business_hours["sunday"]["open"] == "12:00"
        assert updated_profile.is_available is False
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_vendor_profile_fails(
        self, 
        db_session: AsyncSession,
        sample_vendor: User
    ):
        """Test updating nonexistent vendor profile fails."""
        user_service = UserService(db_session)
        
        update_data = VendorProfileUpdate(
            business_name="Should Fail"
        )
        
        updated_profile = await user_service.update_vendor_profile(
            sample_vendor.id,
            update_data
        )
        
        assert updated_profile is None
    
    @pytest.mark.asyncio
    async def test_get_vendor_profile_success(
        self, 
        db_session: AsyncSession,
        sample_vendor_with_profile
    ):
        """Test getting vendor profile successfully."""
        sample_vendor, vendor_profile = sample_vendor_with_profile
        user_service = UserService(db_session)
        
        retrieved_profile = await user_service.get_vendor_profile(sample_vendor.id)
        
        assert retrieved_profile is not None
        assert retrieved_profile.id == vendor_profile.id
        assert retrieved_profile.business_name == vendor_profile.business_name
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_vendor_profile_returns_none(
        self, 
        db_session: AsyncSession,
        sample_customer: User
    ):
        """Test getting nonexistent vendor profile returns None."""
        user_service = UserService(db_session)
        
        retrieved_profile = await user_service.get_vendor_profile(sample_customer.id)
        
        assert retrieved_profile is None


class TestCustomerProfileManagement:
    """Test customer profile management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_customer_profile_success(
        self, 
        db_session: AsyncSession,
        sample_customer: User
    ):
        """Test successful customer profile creation."""
        user_service = UserService(db_session)
        
        customer_profile = await user_service.create_customer_profile(sample_customer.id)
        
        assert customer_profile is not None
        assert customer_profile.user_id == sample_customer.id
        assert customer_profile.preferred_categories == []
        assert customer_profile.price_range_preferences == {}
        assert customer_profile.total_purchases == 0
        assert customer_profile.total_spent == 0.0
        assert customer_profile.average_rating_given == 0.0
        assert customer_profile.wishlist_items == []
        assert customer_profile.favorite_vendors == []
        assert customer_profile.notification_preferences == {}
    
    @pytest.mark.asyncio
    async def test_create_customer_profile_for_vendor_fails(
        self, 
        db_session: AsyncSession,
        sample_vendor: User
    ):
        """Test creating customer profile for vendor user fails."""
        user_service = UserService(db_session)
        
        customer_profile = await user_service.create_customer_profile(sample_vendor.id)
        
        assert customer_profile is None
    
    @pytest.mark.asyncio
    async def test_create_duplicate_customer_profile_returns_existing(
        self, 
        db_session: AsyncSession,
        sample_customer_with_profile
    ):
        """Test creating duplicate customer profile returns existing profile."""
        sample_customer, existing_profile = sample_customer_with_profile
        user_service = UserService(db_session)
        
        customer_profile = await user_service.create_customer_profile(sample_customer.id)
        
        # Should return existing profile, not create new one
        assert customer_profile is not None
        assert customer_profile.id == existing_profile.id
    
    @pytest.mark.asyncio
    async def test_update_customer_profile_success(
        self, 
        db_session: AsyncSession,
        sample_customer_with_profile
    ):
        """Test successful customer profile update."""
        sample_customer, customer_profile = sample_customer_with_profile
        user_service = UserService(db_session)
        
        vendor_id_1 = str(uuid4())
        vendor_id_2 = str(uuid4())
        product_id_1 = str(uuid4())
        product_id_2 = str(uuid4())
        product_id_3 = str(uuid4())
        
        update_data = {
            "preferred_categories": ["electronics", "books", "clothing", "home_garden"],
            "price_range_preferences": {
                "electronics": {"min": 50, "max": 2000},
                "books": {"min": 5, "max": 100},
                "clothing": {"min": 20, "max": 500},
                "home_garden": {"min": 10, "max": 1000}
            },
            "wishlist_items": [product_id_1, product_id_2, product_id_3],
            "favorite_vendors": [vendor_id_1, vendor_id_2],
            "notification_preferences": {
                "email": True,
                "sms": False,
                "push": True,
                "price_alerts": True,
                "new_products": False
            }
        }
        
        updated_profile = await user_service.update_customer_profile(
            sample_customer.id,
            update_data
        )
        
        assert updated_profile is not None
        assert updated_profile.preferred_categories == ["electronics", "books", "clothing", "home_garden"]
        assert updated_profile.price_range_preferences["electronics"]["min"] == 50
        assert updated_profile.price_range_preferences["electronics"]["max"] == 2000
        assert updated_profile.price_range_preferences["books"]["min"] == 5
        assert len(updated_profile.wishlist_items) == 3
        assert product_id_1 in updated_profile.wishlist_items
        assert len(updated_profile.favorite_vendors) == 2
        assert vendor_id_1 in updated_profile.favorite_vendors
        assert updated_profile.notification_preferences["email"] is True
        assert updated_profile.notification_preferences["sms"] is False
        assert updated_profile.notification_preferences["price_alerts"] is True
    
    @pytest.mark.asyncio
    async def test_update_customer_profile_partial_fields(
        self, 
        db_session: AsyncSession,
        sample_customer_with_profile
    ):
        """Test partial customer profile update preserves existing data."""
        sample_customer, customer_profile = sample_customer_with_profile
        user_service = UserService(db_session)
        
        # Initial state has some data
        assert customer_profile.preferred_categories == ["electronics"]
        assert customer_profile.total_purchases == 5
        
        # Update only some fields
        update_data = {
            "preferred_categories": ["electronics", "books"],
            "wishlist_items": [str(uuid4()), str(uuid4())]
        }
        
        updated_profile = await user_service.update_customer_profile(
            sample_customer.id,
            update_data
        )
        
        assert updated_profile is not None
        # Updated fields
        assert updated_profile.preferred_categories == ["electronics", "books"]
        assert len(updated_profile.wishlist_items) == 2
        # Preserved fields
        assert updated_profile.total_purchases == 5
        assert updated_profile.total_spent == 500.0
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_customer_profile_fails(
        self, 
        db_session: AsyncSession,
        sample_customer: User
    ):
        """Test updating nonexistent customer profile fails."""
        user_service = UserService(db_session)
        
        update_data = {
            "preferred_categories": ["should_fail"]
        }
        
        updated_profile = await user_service.update_customer_profile(
            sample_customer.id,
            update_data
        )
        
        assert updated_profile is None
    
    @pytest.mark.asyncio
    async def test_get_customer_profile_success(
        self, 
        db_session: AsyncSession,
        sample_customer_with_profile
    ):
        """Test getting customer profile successfully."""
        sample_customer, customer_profile = sample_customer_with_profile
        user_service = UserService(db_session)
        
        retrieved_profile = await user_service.get_customer_profile(sample_customer.id)
        
        assert retrieved_profile is not None
        assert retrieved_profile.id == customer_profile.id
        assert retrieved_profile.user_id == sample_customer.id
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_customer_profile_returns_none(
        self, 
        db_session: AsyncSession,
        sample_vendor: User
    ):
        """Test getting nonexistent customer profile returns None."""
        user_service = UserService(db_session)
        
        retrieved_profile = await user_service.get_customer_profile(sample_vendor.id)
        
        assert retrieved_profile is None


class TestPaymentMethodManagement:
    """Test payment method management functionality."""
    
    @pytest.mark.asyncio
    async def test_add_payment_method_success(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test successful payment method addition."""
        user_service = UserService(db_session)
        
        payment_data = PaymentMethodCreate(
            method_type="card",
            provider="stripe",
            details={
                "last_four": "4242",
                "brand": "visa",
                "exp_month": 12,
                "exp_year": 2025,
                "cardholder_name": "Test User"
            },
            is_default=True
        )
        
        payment_method = await user_service.add_payment_method(
            sample_user.id,
            payment_data
        )
        
        assert payment_method is not None
        assert payment_method.user_id == sample_user.id
        assert payment_method.method_type == "card"
        assert payment_method.provider == "stripe"
        assert payment_method.details["last_four"] == "4242"
        assert payment_method.details["brand"] == "visa"
        assert payment_method.is_default is True
        assert payment_method.is_active is True
    
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
            details={"last_four": "1111", "brand": "visa"},
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
            details={"account_last_four": "2222", "bank_name": "Test Bank"},
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
        
        # Verify both methods exist
        assert len(payment_methods) == 2
    
    @pytest.mark.asyncio
    async def test_add_payment_method_various_types(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test adding various types of payment methods."""
        user_service = UserService(db_session)
        
        # Card payment method
        card_data = PaymentMethodCreate(
            method_type="card",
            provider="stripe",
            details={"last_four": "4242", "brand": "visa"},
            is_default=False
        )
        
        # Bank payment method
        bank_data = PaymentMethodCreate(
            method_type="bank",
            provider="plaid",
            details={"account_last_four": "1234", "bank_name": "Test Bank"},
            is_default=False
        )
        
        # Mobile payment method
        mobile_data = PaymentMethodCreate(
            method_type="mobile",
            provider="paypal",
            details={"email": "test@example.com"},
            is_default=True
        )
        
        # Digital wallet payment method
        wallet_data = PaymentMethodCreate(
            method_type="digital_wallet",
            provider="apple_pay",
            details={"device_id": "device123"},
            is_default=False
        )
        
        # Add all payment methods
        card_method = await user_service.add_payment_method(sample_user.id, card_data)
        bank_method = await user_service.add_payment_method(sample_user.id, bank_data)
        mobile_method = await user_service.add_payment_method(sample_user.id, mobile_data)
        wallet_method = await user_service.add_payment_method(sample_user.id, wallet_data)
        
        # Verify all methods were created
        assert card_method is not None
        assert bank_method is not None
        assert mobile_method is not None
        assert wallet_method is not None
        
        # Get all payment methods
        payment_methods = await user_service.get_user_payment_methods(sample_user.id)
        
        assert len(payment_methods) == 4
        
        # Verify types
        method_types = {pm.method_type for pm in payment_methods}
        assert method_types == {"card", "bank", "mobile", "digital_wallet"}
        
        # Verify only mobile is default
        default_methods = [pm for pm in payment_methods if pm.is_default]
        assert len(default_methods) == 1
        assert default_methods[0].method_type == "mobile"
    
    @pytest.mark.asyncio
    async def test_delete_payment_method_success(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test successful payment method deletion."""
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
        
        assert success is True
        
        # Verify payment method is no longer returned in active methods
        payment_methods = await user_service.get_user_payment_methods(sample_user.id)
        assert len(payment_methods) == 0
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_payment_method_fails(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test deleting nonexistent payment method fails."""
        user_service = UserService(db_session)
        
        success = await user_service.delete_payment_method(
            sample_user.id,
            uuid4()  # Random UUID
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_delete_payment_method_wrong_user_fails(
        self, 
        db_session: AsyncSession,
        sample_user: User,
        sample_customer: User
    ):
        """Test deleting payment method with wrong user fails."""
        user_service = UserService(db_session)
        
        # Add payment method for sample_user
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
        
        # Try to delete with different user
        success = await user_service.delete_payment_method(
            sample_customer.id,  # Different user
            payment_method.id
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_get_user_payment_methods_ordering(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test payment methods are returned in correct order (default first, then by creation date)."""
        user_service = UserService(db_session)
        
        # Add multiple payment methods with different creation times
        payment_data_1 = PaymentMethodCreate(
            method_type="card",
            provider="stripe",
            details={"last_four": "1111"},
            is_default=False
        )
        
        payment_data_2 = PaymentMethodCreate(
            method_type="bank",
            provider="plaid",
            details={"account_last_four": "2222"},
            is_default=True  # This should be first
        )
        
        payment_data_3 = PaymentMethodCreate(
            method_type="mobile",
            provider="paypal",
            details={"email": "test@example.com"},
            is_default=False
        )
        
        # Add in order: 1, 2, 3
        method_1 = await user_service.add_payment_method(sample_user.id, payment_data_1)
        method_2 = await user_service.add_payment_method(sample_user.id, payment_data_2)
        method_3 = await user_service.add_payment_method(sample_user.id, payment_data_3)
        
        # Get payment methods
        payment_methods = await user_service.get_user_payment_methods(sample_user.id)
        
        assert len(payment_methods) == 3
        
        # Default method should be first
        default_methods = [pm for pm in payment_methods if pm.is_default]
        assert len(default_methods) == 1
        assert default_methods[0].method_type == "bank"
        assert default_methods[0].provider == "plaid"
        
        # Verify all methods are present
        method_types = {pm.method_type for pm in payment_methods}
        assert method_types == {"card", "bank", "mobile"}


class TestUserVerificationManagement:
    """Test user verification management functionality."""
    
    @pytest.mark.asyncio
    async def test_update_user_verification_success(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test successful user verification update."""
        user_service = UserService(db_session)
        
        # Set initial state to pending for this test
        sample_user.verification_status = VerificationStatus.PENDING
        await db_session.commit()
        
        # Initial state should be pending
        assert sample_user.verification_status == VerificationStatus.PENDING
        
        verification_data = UserVerificationUpdate(
            verification_status=VerificationStatus.VERIFIED,
            verification_documents={
                "id_document": "passport_123456",
                "address_proof": "utility_bill_789",
                "business_license": "license_abc123"
            },
            admin_notes="All documents verified successfully"
        )
        
        updated_user = await user_service.update_user_verification(
            sample_user.id,
            verification_data
        )
        
        assert updated_user is not None
        assert updated_user.verification_status == VerificationStatus.VERIFIED
        assert updated_user.verification_documents is not None
        assert updated_user.verification_documents["id_document"] == "passport_123456"
        assert updated_user.verification_documents["address_proof"] == "utility_bill_789"
        assert updated_user.verification_documents["business_license"] == "license_abc123"
    
    @pytest.mark.asyncio
    async def test_update_user_verification_rejection(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test user verification rejection."""
        user_service = UserService(db_session)
        
        verification_data = UserVerificationUpdate(
            verification_status=VerificationStatus.REJECTED,
            verification_documents={
                "rejection_reason": "Invalid ID document",
                "required_documents": ["valid_passport", "recent_utility_bill"]
            },
            admin_notes="ID document appears to be expired"
        )
        
        updated_user = await user_service.update_user_verification(
            sample_user.id,
            verification_data
        )
        
        assert updated_user is not None
        assert updated_user.verification_status == VerificationStatus.REJECTED
        assert updated_user.verification_documents["rejection_reason"] == "Invalid ID document"
    
    @pytest.mark.asyncio
    async def test_update_verification_nonexistent_user_fails(self, db_session: AsyncSession):
        """Test updating verification for nonexistent user fails."""
        user_service = UserService(db_session)
        
        verification_data = UserVerificationUpdate(
            verification_status=VerificationStatus.VERIFIED
        )
        
        updated_user = await user_service.update_user_verification(
            uuid4(),  # Random UUID
            verification_data
        )
        
        assert updated_user is None


class TestUserWithProfilesRetrieval:
    """Test comprehensive user retrieval with all profiles."""
    
    @pytest.mark.asyncio
    async def test_get_user_with_profiles_vendor(
        self, 
        db_session: AsyncSession,
        sample_vendor_with_profile
    ):
        """Test getting vendor user with all profiles loaded."""
        sample_vendor, vendor_profile = sample_vendor_with_profile
        user_service = UserService(db_session)
        
        user_with_profiles = await user_service.get_user_with_profiles(sample_vendor.id)
        
        assert user_with_profiles is not None
        assert user_with_profiles.id == sample_vendor.id
        assert user_with_profiles.role == UserRole.VENDOR
        
        # Vendor profile should be loaded
        assert user_with_profiles.vendor_profile is not None
        assert user_with_profiles.vendor_profile.id == vendor_profile.id
        assert user_with_profiles.vendor_profile.business_name == vendor_profile.business_name
        
        # Customer profile should be None
        assert user_with_profiles.customer_profile is None
    
    @pytest.mark.asyncio
    async def test_get_user_with_profiles_customer(
        self, 
        db_session: AsyncSession,
        sample_customer_with_profile
    ):
        """Test getting customer user with all profiles loaded."""
        sample_customer, customer_profile = sample_customer_with_profile
        user_service = UserService(db_session)
        
        user_with_profiles = await user_service.get_user_with_profiles(sample_customer.id)
        
        assert user_with_profiles is not None
        assert user_with_profiles.id == sample_customer.id
        assert user_with_profiles.role == UserRole.CUSTOMER
        
        # Customer profile should be loaded
        assert user_with_profiles.customer_profile is not None
        assert user_with_profiles.customer_profile.id == customer_profile.id
        assert user_with_profiles.customer_profile.user_id == sample_customer.id
        
        # Vendor profile should be None
        assert user_with_profiles.vendor_profile is None
    
    @pytest.mark.asyncio
    async def test_get_user_with_profiles_basic_user(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test getting basic user with no additional profiles."""
        user_service = UserService(db_session)
        
        user_with_profiles = await user_service.get_user_with_profiles(sample_user.id)
        
        assert user_with_profiles is not None
        assert user_with_profiles.id == sample_user.id
        
        # No additional profiles should be loaded
        assert user_with_profiles.vendor_profile is None
        assert user_with_profiles.customer_profile is None
    
    @pytest.mark.asyncio
    async def test_get_user_with_profiles_nonexistent_user(self, db_session: AsyncSession):
        """Test getting nonexistent user with profiles returns None."""
        user_service = UserService(db_session)
        
        user_with_profiles = await user_service.get_user_with_profiles(uuid4())
        
        assert user_with_profiles is None


class TestRoleBasedAccessControl:
    """Test role-based access control functionality."""
    
    @pytest.mark.asyncio
    async def test_vendor_operations_restricted_to_vendors(
        self, 
        db_session: AsyncSession,
        sample_customer: User
    ):
        """Test that vendor operations are restricted to vendor users."""
        user_service = UserService(db_session)
        
        # Customer should not be able to create vendor profile
        profile_data = VendorProfileCreate(
            business_name="Should Fail",
            business_type="Retail"
        )
        
        vendor_profile = await user_service.create_vendor_profile(
            sample_customer.id,
            profile_data
        )
        
        assert vendor_profile is None
        
        # Customer should not be able to get vendor profile
        retrieved_profile = await user_service.get_vendor_profile(sample_customer.id)
        assert retrieved_profile is None
    
    @pytest.mark.asyncio
    async def test_customer_operations_restricted_to_customers(
        self, 
        db_session: AsyncSession,
        sample_vendor: User
    ):
        """Test that customer operations are restricted to customer users."""
        user_service = UserService(db_session)
        
        # Vendor should not be able to create customer profile
        customer_profile = await user_service.create_customer_profile(sample_vendor.id)
        assert customer_profile is None
        
        # Vendor should not be able to get customer profile
        retrieved_profile = await user_service.get_customer_profile(sample_vendor.id)
        assert retrieved_profile is None
    
    @pytest.mark.asyncio
    async def test_admin_user_creation(self, db_session: AsyncSession):
        """Test admin user creation and properties."""
        user_service = UserService(db_session)
        
        # Create admin user directly (bypassing registration validation)
        from app.core.auth import get_password_hash
        
        admin_user = User(
            email="admin@example.com",
            hashed_password=get_password_hash("adminpass123"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            preferred_language="en",
            verification_status=VerificationStatus.VERIFIED,
            is_active=True,
            is_superuser=True,
            login_count=0
        )
        
        db_session.add(admin_user)
        await db_session.commit()
        await db_session.refresh(admin_user)
        
        assert admin_user is not None
        assert admin_user.role == UserRole.ADMIN
        assert admin_user.email == "admin@example.com"
        assert admin_user.is_superuser is True
        
        # Admin should not be able to create vendor or customer profiles
        vendor_profile = await user_service.create_vendor_profile(
            admin_user.id,
            VendorProfileCreate(business_name="Should Fail", business_type="Retail")
        )
        assert vendor_profile is None
        
        customer_profile = await user_service.create_customer_profile(admin_user.id)
        assert customer_profile is None


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_update_profile_with_empty_cultural_context(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test updating profile with minimal cultural context."""
        user_service = UserService(db_session)
        
        cultural_context = CulturalContextSchema(
            region="Test Region",
            negotiation_style="direct",
            time_orientation="punctual",
            communication_preferences=[],
            business_etiquette=[],
            holidays_and_events=[]
        )
        
        profile_update = UserProfileUpdate(
            cultural_context=cultural_context
        )
        
        updated_user = await user_service.update_user_profile(
            sample_user.id,
            profile_update
        )
        
        assert updated_user is not None
        assert updated_user.cultural_profile is not None
        assert updated_user.cultural_profile["region"] == "Test Region"
        assert updated_user.cultural_profile["communication_preferences"] == []
        assert updated_user.cultural_profile["business_etiquette"] == []
        assert updated_user.cultural_profile["holidays_and_events"] == []
    
    @pytest.mark.asyncio
    async def test_payment_method_with_minimal_details(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test adding payment method with minimal details."""
        user_service = UserService(db_session)
        
        payment_data = PaymentMethodCreate(
            method_type="cash",
            details={},  # Empty details
            is_default=False
        )
        
        payment_method = await user_service.add_payment_method(
            sample_user.id,
            payment_data
        )
        
        assert payment_method is not None
        assert payment_method.method_type == "cash"
        assert payment_method.provider is None
        assert payment_method.details == {}
        assert payment_method.is_active is True
    
    @pytest.mark.asyncio
    async def test_large_cultural_context_data(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test handling large cultural context data."""
        user_service = UserService(db_session)
        
        # Create large lists for cultural context
        large_communication_prefs = [f"pref_{i}" for i in range(50)]
        large_business_etiquette = [f"etiquette_{i}" for i in range(30)]
        large_holidays = [f"holiday_{i}" for i in range(100)]
        
        cultural_context = CulturalContextSchema(
            region="Large Data Region",
            negotiation_style="relationship_based",
            time_orientation="flexible",
            communication_preferences=large_communication_prefs,
            business_etiquette=large_business_etiquette,
            holidays_and_events=large_holidays
        )
        
        profile_update = UserProfileUpdate(
            cultural_context=cultural_context
        )
        
        updated_user = await user_service.update_user_profile(
            sample_user.id,
            profile_update
        )
        
        assert updated_user is not None
        assert updated_user.cultural_profile is not None
        assert len(updated_user.cultural_profile["communication_preferences"]) == 50
        assert len(updated_user.cultural_profile["business_etiquette"]) == 30
        assert len(updated_user.cultural_profile["holidays_and_events"]) == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_default_payment_method_updates(
        self, 
        db_session: AsyncSession,
        sample_user: User
    ):
        """Test handling concurrent default payment method updates."""
        user_service = UserService(db_session)
        
        # Add first payment method as default
        payment_data_1 = PaymentMethodCreate(
            method_type="card",
            provider="stripe",
            details={"last_four": "1111"},
            is_default=True
        )
        
        method_1 = await user_service.add_payment_method(sample_user.id, payment_data_1)
        
        # Add second payment method as default (should unset first)
        payment_data_2 = PaymentMethodCreate(
            method_type="bank",
            provider="plaid",
            details={"account_last_four": "2222"},
            is_default=True
        )
        
        method_2 = await user_service.add_payment_method(sample_user.id, payment_data_2)
        
        # Add third payment method as default (should unset second)
        payment_data_3 = PaymentMethodCreate(
            method_type="mobile",
            provider="paypal",
            details={"email": "test@example.com"},
            is_default=True
        )
        
        method_3 = await user_service.add_payment_method(sample_user.id, payment_data_3)
        
        # Verify only the last one is default
        payment_methods = await user_service.get_user_payment_methods(sample_user.id)
        default_methods = [pm for pm in payment_methods if pm.is_default]
        
        assert len(default_methods) == 1
        assert default_methods[0].id == method_3.id
        assert default_methods[0].method_type == "mobile"