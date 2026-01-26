"""
Transaction schemas for request/response validation.

This module defines Pydantic models for transaction-related API endpoints
including transaction creation, payments, and escrow management.
"""

from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, validator

from app.models.transaction import TransactionStatus, PaymentStatus, EscrowStatus


class TransactionCreate(BaseModel):
    """Schema for transaction creation request."""
    
    product_id: UUID = Field(..., description="Product being purchased")
    seller_id: UUID = Field(..., description="Seller user ID")
    negotiation_id: Optional[UUID] = Field(None, description="Related negotiation ID")
    
    # Transaction details
    quantity: int = Field(..., ge=1, description="Quantity being purchased")
    unit_price: float = Field(..., gt=0, description="Price per unit")
    currency: str = Field(default="USD", max_length=10)
    
    # Payment information
    payment_method: str = Field(..., max_length=50)
    payment_provider: Optional[str] = Field(None, max_length=100)
    
    # Delivery information
    delivery_address: Optional[Dict] = None
    delivery_method: Optional[str] = Field(None, max_length=100)
    
    # Additional data
    notes: Optional[str] = None
    
    @validator("payment_method")
    def validate_payment_method(cls, v):
        """Validate payment method."""
        allowed_methods = [
            "card", "bank_transfer", "mobile_payment", "digital_wallet",
            "cryptocurrency", "cash", "escrow"
        ]
        if v not in allowed_methods:
            raise ValueError(f"Payment method must be one of: {allowed_methods}")
        return v
    
    @validator("delivery_address")
    def validate_delivery_address(cls, v):
        """Validate delivery address format."""
        if v is not None:
            required_fields = ["street", "city", "country"]
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"Delivery address must include {field}")
        return v


class TransactionUpdate(BaseModel):
    """Schema for transaction update request."""
    
    status: Optional[TransactionStatus] = None
    delivery_method: Optional[str] = Field(None, max_length=100)
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    
    id: UUID
    buyer_id: UUID
    seller_id: UUID
    product_id: UUID
    negotiation_id: Optional[UUID] = None
    
    # Transaction details
    quantity: int
    unit_price: float
    total_amount: float
    currency: str
    
    # Status and tracking
    status: TransactionStatus
    transaction_reference: Optional[str] = None
    
    # Payment information
    payment_method: Optional[str] = None
    payment_provider: Optional[str] = None
    payment_reference: Optional[str] = None
    
    # Fees and charges
    platform_fee: float
    payment_fee: float
    tax_amount: float
    
    # Delivery information
    delivery_address: Optional[Dict] = None
    delivery_method: Optional[str] = None
    estimated_delivery: Optional[str] = None
    actual_delivery: Optional[str] = None
    
    # Additional data
    notes: Optional[str] = None
    
    # Timestamps
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    """Schema for payment creation request."""
    
    transaction_id: UUID = Field(..., description="Transaction ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="USD", max_length=10)
    payment_method: str = Field(..., max_length=50)
    provider: str = Field(..., max_length=100)
    provider_reference: Optional[str] = Field(None, max_length=200)
    
    @validator("payment_method")
    def validate_payment_method(cls, v):
        """Validate payment method."""
        allowed_methods = [
            "card", "bank_transfer", "mobile_payment", "digital_wallet",
            "cryptocurrency", "cash"
        ]
        if v not in allowed_methods:
            raise ValueError(f"Payment method must be one of: {allowed_methods}")
        return v


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    
    id: UUID
    transaction_id: UUID
    amount: float
    currency: str
    payment_method: str
    provider: str
    status: PaymentStatus
    provider_reference: Optional[str] = None
    processed_at: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class EscrowCreate(BaseModel):
    """Schema for escrow creation request."""
    
    transaction_id: UUID = Field(..., description="Transaction ID")
    amount: float = Field(..., gt=0, description="Escrow amount")
    currency: str = Field(default="USD", max_length=10)
    release_conditions: List[str] = Field(..., description="Conditions for release")
    release_date: Optional[datetime] = Field(None, description="Automatic release date")
    
    @validator("release_conditions")
    def validate_release_conditions(cls, v):
        """Validate release conditions."""
        if not v or len(v) == 0:
            raise ValueError("At least one release condition must be specified")
        for condition in v:
            if not isinstance(condition, str) or len(condition.strip()) == 0:
                raise ValueError("Release conditions must be non-empty strings")
        return v


class EscrowUpdate(BaseModel):
    """Schema for escrow update request."""
    
    status: Optional[EscrowStatus] = None
    release_date: Optional[datetime] = None
    dispute_reason: Optional[str] = None
    dispute_resolution: Optional[str] = None
    arbitrator_id: Optional[UUID] = None


class EscrowResponse(BaseModel):
    """Schema for escrow response."""
    
    id: UUID
    transaction_id: UUID
    amount: float
    currency: str
    status: EscrowStatus
    release_conditions: List[str]
    funded_at: Optional[str] = None
    release_date: Optional[str] = None
    released_at: Optional[str] = None
    dispute_reason: Optional[str] = None
    dispute_resolution: Optional[str] = None
    arbitrator_id: Optional[UUID] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class RefundCreate(BaseModel):
    """Schema for refund creation request."""
    
    transaction_id: UUID = Field(..., description="Transaction ID")
    payment_id: Optional[UUID] = Field(None, description="Specific payment ID")
    amount: float = Field(..., gt=0, description="Refund amount")
    currency: str = Field(default="USD", max_length=10)
    reason: str = Field(..., max_length=200, description="Refund reason")
    description: Optional[str] = Field(None, description="Detailed description")
    
    @validator("reason")
    def validate_reason(cls, v):
        """Validate refund reason."""
        allowed_reasons = [
            "defective_product", "not_as_described", "damaged_in_shipping",
            "buyer_remorse", "seller_request", "dispute_resolution", "other"
        ]
        if v not in allowed_reasons:
            raise ValueError(f"Refund reason must be one of: {allowed_reasons}")
        return v


class RefundResponse(BaseModel):
    """Schema for refund response."""
    
    id: UUID
    transaction_id: UUID
    payment_id: Optional[UUID] = None
    amount: float
    currency: str
    reason: str
    description: Optional[str] = None
    status: str
    provider_reference: Optional[str] = None
    processed_at: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Schema for transaction list response with pagination."""
    
    transactions: List[TransactionResponse]
    total: int
    page: int
    size: int
    pages: int


class TransactionSearchRequest(BaseModel):
    """Schema for transaction search request."""
    
    status: Optional[TransactionStatus] = None
    buyer_id: Optional[UUID] = None
    seller_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: Optional[str] = Field(default="created_at", pattern="^(created_at|amount|status)$")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    
    @validator("max_amount")
    def validate_amount_range(cls, v, values):
        """Validate amount range."""
        if v is not None and "min_amount" in values and values["min_amount"] is not None:
            if v < values["min_amount"]:
                raise ValueError("Maximum amount must be greater than minimum amount")
        return v
    
    @validator("date_to")
    def validate_date_range(cls, v, values):
        """Validate date range."""
        if v is not None and "date_from" in values and values["date_from"] is not None:
            if v < values["date_from"]:
                raise ValueError("End date must be after start date")
        return v