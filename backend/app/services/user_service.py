"""
User service for user management operations.

This module provides service functions for user registration, authentication,
profile management, and related database operations.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.auth import get_password_hash, verify_password
from app.models.user import (
    User, VendorProfile, CustomerProfile, PaymentMethod, 
    UserRole, VerificationStatus
)
from app.schemas.auth import UserRegister, VendorProfileCreate
from app.schemas.profile import (
    UserProfileUpdate, VendorProfileUpdate, PaymentMethodCreate,
    UserVerificationUpdate, GeographicLocationSchema, CulturalContextSchema
)


class UserService:
    """Service class for user management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, user_data: UserRegister) -> User:
        """
        Create new user account.
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user
            
        Raises:
            ValueError: If email already exists
        """
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            phone_number=user_data.phone_number,
            preferred_language=user_data.preferred_language,
            country=user_data.country,
            region=user_data.region,
            city=user_data.city,
            timezone=user_data.timezone,
            currency=user_data.currency,
            verification_status=VerificationStatus.PENDING,
            is_active=True,
            is_superuser=False,
            login_count=0
        )
        
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Email already registered")
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Update login count and last active
        user.login_count += 1
        user.last_active = datetime.utcnow()
        
        try:
            await self.db.commit()
            await self.db.refresh(user)
        except Exception:
            await self.db.rollback()
        
        return user
    
    async def update_user_profile(
        self, 
        user_id: UUID, 
        update_data: UserProfileUpdate
    ) -> Optional[User]:
        """
        Update user profile information with enhanced cultural and geographic data.
        
        Args:
            user_id: User ID
            update_data: UserProfileUpdate schema with comprehensive profile data
            
        Returns:
            Updated user or None if not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Update basic profile fields
        if update_data.first_name is not None:
            user.first_name = update_data.first_name
        if update_data.last_name is not None:
            user.last_name = update_data.last_name
        if update_data.phone_number is not None:
            user.phone_number = update_data.phone_number
        if update_data.preferred_language is not None:
            user.preferred_language = update_data.preferred_language
        
        # Update geographic information
        if update_data.geographic_location is not None:
            geo = update_data.geographic_location
            user.country = geo.country
            user.region = geo.region
            user.city = geo.city
            user.timezone = geo.timezone
            user.currency = geo.currency
            user.coordinates = geo.coordinates
        
        # Update cultural context
        if update_data.cultural_context is not None:
            user.cultural_profile = update_data.cultural_context.dict()
        
        # Update verification documents (admin only)
        if update_data.verification_documents is not None:
            user.verification_documents = update_data.verification_documents
        
        try:
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception:
            await self.db.rollback()
            return None
    
    async def change_password(
        self, 
        user_id: UUID, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully, False otherwise
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            return False
        
        # Hash new password
        user.hashed_password = get_password_hash(new_password)
        
        try:
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            return False
    
    async def reset_password(self, email: str, new_password: str) -> bool:
        """
        Reset user password (for password reset flow).
        
        Args:
            email: User email
            new_password: New password
            
        Returns:
            True if password reset successfully, False otherwise
        """
        user = await self.get_user_by_email(email)
        if not user:
            return False
        
        # Hash new password
        user.hashed_password = get_password_hash(new_password)
        
        try:
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            return False
    
    async def deactivate_user(self, user_id: UUID) -> bool:
        """
        Deactivate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            True if user deactivated successfully, False otherwise
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        
        try:
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            return False
    
    async def activate_user(self, user_id: UUID) -> bool:
        """
        Activate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            True if user activated successfully, False otherwise
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = True
        
        try:
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            return False
    
    async def create_vendor_profile(
        self, 
        user_id: UUID, 
        profile_data: VendorProfileCreate
    ) -> Optional[VendorProfile]:
        """
        Create vendor profile for user.
        
        Args:
            user_id: User ID
            profile_data: Vendor profile data
            
        Returns:
            Created vendor profile or None if failed
        """
        # Check if user exists and is a vendor
        user = await self.get_user_by_id(user_id)
        if not user or user.role != UserRole.VENDOR:
            return None
        
        # Check if vendor profile already exists
        result = await self.db.execute(
            select(VendorProfile).where(VendorProfile.user_id == user_id)
        )
        existing_profile = result.scalar_one_or_none()
        if existing_profile:
            return existing_profile
        
        # Create vendor profile
        vendor_profile = VendorProfile(
            user_id=user_id,
            business_name=profile_data.business_name,
            business_type=profile_data.business_type,
            business_description=profile_data.business_description,
            market_stall=profile_data.market_stall,
            languages=profile_data.languages,
            communication_preferences=profile_data.communication_preferences,
            payment_methods=profile_data.payment_methods,
            business_hours=profile_data.business_hours,
            average_rating=0.0,
            total_sales=0,
            total_reviews=0,
            is_available=True
        )
        
        try:
            self.db.add(vendor_profile)
            await self.db.commit()
            await self.db.refresh(vendor_profile)
            return vendor_profile
        except Exception:
            await self.db.rollback()
            return None
    
    async def get_vendor_profile(self, user_id: UUID) -> Optional[VendorProfile]:
        """
        Get vendor profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Vendor profile or None if not found
        """
        result = await self.db.execute(
            select(VendorProfile).where(VendorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_vendor_profile(
        self, 
        user_id: UUID, 
        update_data: VendorProfileUpdate
    ) -> Optional[VendorProfile]:
        """
        Update vendor profile information.
        
        Args:
            user_id: User ID
            update_data: VendorProfileUpdate schema
            
        Returns:
            Updated vendor profile or None if not found
        """
        vendor_profile = await self.get_vendor_profile(user_id)
        if not vendor_profile:
            return None
        
        # Update fields that are not None
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(vendor_profile, field):
                setattr(vendor_profile, field, value)
        
        try:
            await self.db.commit()
            await self.db.refresh(vendor_profile)
            return vendor_profile
        except Exception:
            await self.db.rollback()
            return None
    
    async def create_customer_profile(self, user_id: UUID) -> Optional[CustomerProfile]:
        """
        Create customer profile for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Created customer profile or None if failed
        """
        # Check if user exists and is a customer
        user = await self.get_user_by_id(user_id)
        if not user or user.role != UserRole.CUSTOMER:
            return None
        
        # Check if customer profile already exists
        result = await self.db.execute(
            select(CustomerProfile).where(CustomerProfile.user_id == user_id)
        )
        existing_profile = result.scalar_one_or_none()
        if existing_profile:
            return existing_profile
        
        # Create customer profile
        customer_profile = CustomerProfile(
            user_id=user_id,
            preferred_categories=[],
            price_range_preferences={},
            total_purchases=0,
            total_spent=0.0,
            average_rating_given=0.0,
            wishlist_items=[],
            favorite_vendors=[],
            notification_preferences={}
        )
        
        try:
            self.db.add(customer_profile)
            await self.db.commit()
            await self.db.refresh(customer_profile)
            return customer_profile
        except Exception:
            await self.db.rollback()
            return None
    
    async def get_customer_profile(self, user_id: UUID) -> Optional[CustomerProfile]:
        """
        Get customer profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Customer profile or None if not found
        """
        result = await self.db.execute(
            select(CustomerProfile).where(CustomerProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_customer_profile(
        self, 
        user_id: UUID, 
        update_data: Dict
    ) -> Optional[CustomerProfile]:
        """
        Update customer profile information.
        
        Args:
            user_id: User ID
            update_data: Dictionary of fields to update
            
        Returns:
            Updated customer profile or None if not found
        """
        customer_profile = await self.get_customer_profile(user_id)
        if not customer_profile:
            return None
        
        # Update allowed fields
        allowed_fields = {
            'preferred_categories', 'price_range_preferences', 
            'wishlist_items', 'favorite_vendors', 'notification_preferences'
        }
        
        for field, value in update_data.items():
            if field in allowed_fields and value is not None:
                setattr(customer_profile, field, value)
        
        try:
            await self.db.commit()
            await self.db.refresh(customer_profile)
            return customer_profile
        except Exception:
            await self.db.rollback()
            return None
    
    async def add_payment_method(
        self, 
        user_id: UUID, 
        payment_data: PaymentMethodCreate
    ) -> Optional[PaymentMethod]:
        """
        Add payment method for user.
        
        Args:
            user_id: User ID
            payment_data: Payment method data
            
        Returns:
            Created payment method or None if failed
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # If this is set as default, unset other default methods
        if payment_data.is_default:
            await self.db.execute(
                update(PaymentMethod)
                .where(PaymentMethod.user_id == user_id)
                .values(is_default=False)
            )
        
        payment_method = PaymentMethod(
            user_id=user_id,
            method_type=payment_data.method_type,
            provider=payment_data.provider,
            details=payment_data.details,
            is_default=payment_data.is_default,
            is_active=True
        )
        
        try:
            self.db.add(payment_method)
            await self.db.commit()
            await self.db.refresh(payment_method)
            return payment_method
        except Exception:
            await self.db.rollback()
            return None
    
    async def get_user_payment_methods(self, user_id: UUID) -> List[PaymentMethod]:
        """
        Get all payment methods for user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of payment methods
        """
        result = await self.db.execute(
            select(PaymentMethod)
            .where(PaymentMethod.user_id == user_id)
            .where(PaymentMethod.is_active == True)
            .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
        )
        return result.scalars().all()
    
    async def delete_payment_method(self, user_id: UUID, payment_method_id: UUID) -> bool:
        """
        Delete (deactivate) payment method.
        
        Args:
            user_id: User ID
            payment_method_id: Payment method ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        result = await self.db.execute(
            select(PaymentMethod)
            .where(PaymentMethod.id == payment_method_id)
            .where(PaymentMethod.user_id == user_id)
        )
        payment_method = result.scalar_one_or_none()
        
        if not payment_method:
            return False
        
        payment_method.is_active = False
        
        try:
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            return False
    
    async def update_user_verification(
        self, 
        user_id: UUID, 
        verification_data: UserVerificationUpdate
    ) -> Optional[User]:
        """
        Update user verification status (admin only).
        
        Args:
            user_id: User ID
            verification_data: Verification update data
            
        Returns:
            Updated user or None if not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.verification_status = verification_data.verification_status
        
        if verification_data.verification_documents is not None:
            user.verification_documents = verification_data.verification_documents
        
        try:
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception:
            await self.db.rollback()
            return None
    
    async def get_user_with_profiles(self, user_id: UUID) -> Optional[User]:
        """
        Get user with all associated profiles loaded.
        
        Args:
            user_id: User ID
            
        Returns:
            User with profiles or None if not found
        """
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.vendor_profile),
                selectinload(User.customer_profile)
            )
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()


def get_user_service(db: AsyncSession) -> UserService:
    """
    Get user service instance.
    
    Args:
        db: Database session
        
    Returns:
        UserService instance
    """
    return UserService(db)