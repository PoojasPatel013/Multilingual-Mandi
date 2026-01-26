"""
Transaction and payment models.

This module defines transaction, payment, and escrow-related models for
the Multilingual Mandi platform.
"""

from enum import Enum

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer,
    JSON, String, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class TransactionStatus(str, Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class EscrowStatus(str, Enum):
    """Escrow status enumeration."""
    CREATED = "created"
    FUNDED = "funded"
    RELEASED = "released"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class Transaction(Base, UUIDMixin, TimestampMixin):
    """Transaction model for marketplace purchases."""
    
    __tablename__ = "transactions"
    
    # Parties involved
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    negotiation_id = Column(UUID(as_uuid=True), ForeignKey("negotiations.id"))
    
    # Transaction details
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    
    # Status and tracking
    status = Column(
        SQLEnum(TransactionStatus),
        default=TransactionStatus.PENDING,
        nullable=False,
        index=True
    )
    transaction_reference = Column(String(100), unique=True, index=True)
    
    # Payment information
    payment_method = Column(String(50))
    payment_provider = Column(String(100))
    payment_reference = Column(String(200))
    
    # Fees and charges
    platform_fee = Column(Float, default=0.0, nullable=False)
    payment_fee = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    
    # Delivery and fulfillment
    delivery_address = Column(JSON)
    delivery_method = Column(String(100))
    estimated_delivery = Column(DateTime(timezone=True))
    actual_delivery = Column(DateTime(timezone=True))
    
    # Additional data
    transaction_metadata = Column(JSON)  # Additional transaction data
    notes = Column(Text)
    
    # Relationships
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])
    product = relationship("Product")
    negotiation = relationship("Negotiation")
    payments = relationship("Payment", back_populates="transaction")
    escrow = relationship("Escrow", back_populates="transaction", uselist=False)
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, amount={self.total_amount}, status={self.status})>"


class Payment(Base, UUIDMixin, TimestampMixin):
    """Payment model for transaction payments."""
    
    __tablename__ = "payments"
    
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    payment_method = Column(String(50), nullable=False)
    provider = Column(String(100), nullable=False)
    
    # Status and references
    status = Column(
        SQLEnum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True
    )
    provider_reference = Column(String(200))
    provider_response = Column(JSON)
    
    # Processing details
    processed_at = Column(DateTime(timezone=True))
    failure_reason = Column(Text)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="payments")
    
    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, amount={self.amount}, status={self.status})>"


class Escrow(Base, UUIDMixin, TimestampMixin):
    """Escrow model for high-value transactions."""
    
    __tablename__ = "escrows"
    
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    
    # Escrow details
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    
    # Status and conditions
    status = Column(
        SQLEnum(EscrowStatus),
        default=EscrowStatus.CREATED,
        nullable=False,
        index=True
    )
    release_conditions = Column(JSON)  # Conditions for release
    
    # Timeline
    funded_at = Column(DateTime(timezone=True))
    release_date = Column(DateTime(timezone=True))
    released_at = Column(DateTime(timezone=True))
    
    # Dispute handling
    dispute_reason = Column(Text)
    dispute_resolution = Column(Text)
    arbitrator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    transaction = relationship("Transaction", back_populates="escrow")
    arbitrator = relationship("User")
    
    def __repr__(self) -> str:
        return f"<Escrow(id={self.id}, amount={self.amount}, status={self.status})>"


class Refund(Base, UUIDMixin, TimestampMixin):
    """Refund model for transaction refunds."""
    
    __tablename__ = "refunds"
    
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"))
    
    # Refund details
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    reason = Column(String(200))
    description = Column(Text)
    
    # Status and processing
    status = Column(String(50), default="pending", nullable=False)
    provider_reference = Column(String(200))
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    transaction = relationship("Transaction")
    payment = relationship("Payment")
    
    def __repr__(self) -> str:
        return f"<Refund(id={self.id}, amount={self.amount}, status={self.status})>"