"""
User profile management endpoints.

This module provides endpoints for comprehensive user profile management
including cultural context, geographic location, and role-specific profiles.
"""

from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_current_admin
from app.models.user import User, UserRole
from app.schemas.profile import (
    UserProfileUpdate,
    UserProfileResponse,
    VendorProfileUpdate,
    CustomerProfileResponse,
    PaymentMethodCreate,
    PaymentMethodResponse,
    UserVerificationUpdate
)
from app.services.user_service import get_user_service

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current user's comprehensive profile information.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Comprehensive user profile information
    """
    user_service = get_user_service(db)
    user_with_profiles = await user_service.get_user_with_profiles(current_user.id)
    
    if not user_with_profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return UserProfileResponse.from_orm(user_with_profiles)


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update current user's profile with enhanced cultural and geographic data.
    
    Args:
        profile_update: Profile update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user profile information
        
    Raises:
        HTTPException: If update fails
    """
    user_service = get_user_service(db)
    
    updated_user = await user_service.update_user_profile(
        current_user.id,
        profile_update
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user profile"
        )
    
    return UserProfileResponse.from_orm(updated_user)


@router.put("/vendor", response_model=UserProfileResponse)
async def update_vendor_profile(
    vendor_update: VendorProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update vendor profile information.
    
    Args:
        vendor_update: Vendor profile update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user profile with vendor information
        
    Raises:
        HTTPException: If user is not a vendor or update fails
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can update vendor profiles"
        )
    
    user_service = get_user_service(db)
    
    # Ensure vendor profile exists
    vendor_profile = await user_service.get_vendor_profile(current_user.id)
    if not vendor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor profile not found. Please create one first."
        )
    
    updated_profile = await user_service.update_vendor_profile(
        current_user.id,
        vendor_update
    )
    
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update vendor profile"
        )
    
    # Return updated user with profiles
    user_with_profiles = await user_service.get_user_with_profiles(current_user.id)
    return UserProfileResponse.from_orm(user_with_profiles)


@router.post("/customer", response_model=CustomerProfileResponse)
async def create_customer_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create customer profile for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created customer profile
        
    Raises:
        HTTPException: If user is not a customer or profile creation fails
    """
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create customer profiles"
        )
    
    user_service = get_user_service(db)
    
    customer_profile = await user_service.create_customer_profile(current_user.id)
    
    if not customer_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create customer profile"
        )
    
    return CustomerProfileResponse.from_orm(customer_profile)


@router.get("/customer", response_model=CustomerProfileResponse)
async def get_customer_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get customer profile for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Customer profile
        
    Raises:
        HTTPException: If user is not a customer or profile not found
    """
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can access customer profiles"
        )
    
    user_service = get_user_service(db)
    
    customer_profile = await user_service.get_customer_profile(current_user.id)
    
    if not customer_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found"
        )
    
    return CustomerProfileResponse.from_orm(customer_profile)


@router.put("/customer", response_model=CustomerProfileResponse)
async def update_customer_profile(
    update_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update customer profile information.
    
    Args:
        update_data: Customer profile update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated customer profile
        
    Raises:
        HTTPException: If user is not a customer or update fails
    """
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can update customer profiles"
        )
    
    user_service = get_user_service(db)
    
    updated_profile = await user_service.update_customer_profile(
        current_user.id,
        update_data
    )
    
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update customer profile"
        )
    
    return CustomerProfileResponse.from_orm(updated_profile)


@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def add_payment_method(
    payment_data: PaymentMethodCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Add payment method for current user.
    
    Args:
        payment_data: Payment method data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created payment method
        
    Raises:
        HTTPException: If payment method creation fails
    """
    user_service = get_user_service(db)
    
    payment_method = await user_service.add_payment_method(
        current_user.id,
        payment_data
    )
    
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add payment method"
        )
    
    return PaymentMethodResponse.from_orm(payment_method)


@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all payment methods for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of payment methods
    """
    user_service = get_user_service(db)
    
    payment_methods = await user_service.get_user_payment_methods(current_user.id)
    
    return [PaymentMethodResponse.from_orm(pm) for pm in payment_methods]


@router.delete("/payment-methods/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete payment method for current user.
    
    Args:
        payment_method_id: Payment method ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If payment method deletion fails
    """
    user_service = get_user_service(db)
    
    success = await user_service.delete_payment_method(
        current_user.id,
        payment_method_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )
    
    return {"message": "Payment method deleted successfully"}


@router.put("/users/{user_id}/verification", response_model=UserProfileResponse)
async def update_user_verification(
    user_id: UUID,
    verification_data: UserVerificationUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update user verification status (admin only).
    
    Args:
        user_id: User ID to update
        verification_data: Verification update data
        current_admin: Current admin user
        db: Database session
        
    Returns:
        Updated user profile
        
    Raises:
        HTTPException: If user not found or update fails
    """
    user_service = get_user_service(db)
    
    updated_user = await user_service.update_user_verification(
        user_id,
        verification_data
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfileResponse.from_orm(updated_user)


@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get user profile by ID (admin only).
    
    Args:
        user_id: User ID
        current_admin: Current admin user
        db: Database session
        
    Returns:
        User profile information
        
    Raises:
        HTTPException: If user not found
    """
    user_service = get_user_service(db)
    
    user_with_profiles = await user_service.get_user_with_profiles(user_id)
    
    if not user_with_profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfileResponse.from_orm(user_with_profiles)