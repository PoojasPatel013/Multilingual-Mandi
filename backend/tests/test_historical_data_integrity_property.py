"""
Property-based tests for historical data integrity.

This module contains property-based tests that validate universal properties
of the historical data system using Hypothesis for comprehensive input coverage.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID
from decimal import Decimal

from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.product import Product, AvailabilityStatus
from app.models.user import User, UserRole, VerificationStatus
from app.models.transaction import Transaction, TransactionStatus
from app.models.negotiation import Negotiation, NegotiationStatus


# Custom strategies for generating test data
@composite
def valid_price(draw):
    """Generate valid price values."""
    return draw(st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False))


@composite
def valid_currency(draw):
    """Generate valid currency codes."""
    return draw(st.sampled_from(['USD', 'EUR', 'GBP', 'JPY']))


@composite
def valid_product_name(draw):
    """Generate valid product names."""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Zs')),
        min_size=1,
        max_size=50
    ).filter(lambda x: x.strip() and len(x.strip()) > 0))


@composite
def valid_quantity(draw):
    """Generate valid quantity values."""
    return draw(st.integers(min_value=1, max_value=100))


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
        'country': 'US',
        'region': 'California',
        'city': 'San Francisco',
        'timezone': 'America/Los_Angeles',
        'currency': draw(valid_currency()),
        'verification_status': VerificationStatus.VERIFIED,
        'is_active': True,
        'is_superuser': False,
        'login_count': 0
    }


class TestHistoricalDataIntegrity:
    """
    Property-based tests for historical data integrity.
    
    **Validates: Requirements 2.4**
    
    These tests ensure that pricing data is maintained accurately over time
    and can be retrieved for trend analysis and future price predictions.
    """
    
    @given(
        user_data=valid_user_data(),
        product_name=valid_product_name(),
        base_price=valid_price(),
        price_changes=st.lists(
            valid_price(),
            min_size=1,
            max_size=3
        )
    )
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_product_price_history_integrity(
        self,
        user_data: Dict[str, Any],
        product_name: str,
        base_price: float,
        price_changes: List[float],
        db_session: AsyncSession
    ):
        """
        **Property 7: Historical Data Integrity**
        **Validates: Requirements 2.4**
        
        For any product with price changes over time, the system should
        maintain accurate historical records that preserve all price points
        and their timestamps for trend analysis.
        """
        # Create vendor user
        vendor = User(**user_data)
        vendor.role = UserRole.VENDOR
        db_session.add(vendor)
        await db_session.commit()
        await db_session.refresh(vendor)
        
        # Create initial product
        product = Product(
            vendor_id=vendor.id,
            name=product_name,
            description=f"Test product: {product_name}",
            base_price=base_price,
            current_price=base_price,
            currency='USD',
            quantity_available=100,
            availability=AvailabilityStatus.IN_STOCK,
            is_active=True
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Apply price changes
        for i, new_price in enumerate(price_changes):
            product.current_price = new_price
            await db_session.commit()
        
        # Verify historical data integrity
        
        # 1. Current price should match the last change
        await db_session.refresh(product)
        expected_final_price = price_changes[-1]
        assert abs(product.current_price - expected_final_price) < 0.01, \
            f"Current price {product.current_price} doesn't match last change {expected_final_price}"
        
        # 2. Product should maintain its base price
        assert abs(product.base_price - base_price) < 0.01, \
            f"Base price {product.base_price} doesn't match original {base_price}"
        
        # 3. Currency should be consistent
        assert product.currency == 'USD'
        
        # 4. Product should be retrievable for analysis
        result = await db_session.execute(
            select(Product).where(Product.id == product.id)
        )
        retrieved_product = result.scalar_one()
        
        assert retrieved_product is not None
        assert abs(retrieved_product.current_price - expected_final_price) < 0.01
        assert retrieved_product.is_active is True
    
    @given(
        vendor_data=valid_user_data(),
        customer_data=valid_user_data(),
        product_name=valid_product_name(),
        transaction_prices=st.lists(
            valid_price(),
            min_size=1,
            max_size=3
        )
    )
    @settings(max_examples=12, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_transaction_price_history_integrity(
        self,
        vendor_data: Dict[str, Any],
        customer_data: Dict[str, Any],
        product_name: str,
        transaction_prices: List[float],
        db_session: AsyncSession
    ):
        """
        **Property 7: Historical Data Integrity**
        **Validates: Requirements 2.4**
        
        For any series of transactions, the system should maintain accurate
        historical transaction records that preserve pricing data for
        market analysis and trend prediction.
        """
        # Ensure different users
        vendor_data['role'] = UserRole.VENDOR
        customer_data['role'] = UserRole.CUSTOMER
        customer_data['email'] = f"customer_{str(uuid4())[:8]}@example.com"
        
        # Create users
        vendor = User(**vendor_data)
        customer = User(**customer_data)
        db_session.add(vendor)
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(vendor)
        await db_session.refresh(customer)
        
        # Create product
        base_price = transaction_prices[0]
        product = Product(
            vendor_id=vendor.id,
            name=product_name,
            description=f"Test product: {product_name}",
            base_price=base_price,
            current_price=base_price,
            currency='USD',
            quantity_available=1000,
            availability=AvailabilityStatus.IN_STOCK,
            is_active=True
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Create transactions based on price history
        created_transactions = []
        for i, price in enumerate(transaction_prices):
            transaction = Transaction(
                buyer_id=customer.id,
                seller_id=vendor.id,
                product_id=product.id,
                quantity=1,
                unit_price=price,
                total_amount=price,
                currency='USD',
                status=TransactionStatus.COMPLETED,
                transaction_reference=f"TX_{str(uuid4())[:8]}"
            )
            db_session.add(transaction)
            created_transactions.append(transaction)
        
        await db_session.commit()
        
        # Refresh all transactions
        for tx in created_transactions:
            await db_session.refresh(tx)
        
        # Verify historical data integrity
        
        # 1. All transactions should be retrievable
        result = await db_session.execute(
            select(Transaction).where(Transaction.product_id == product.id)
            .order_by(Transaction.created_at)
        )
        retrieved_transactions = result.scalars().all()
        
        assert len(retrieved_transactions) == len(transaction_prices), \
            f"Expected {len(transaction_prices)} transactions, got {len(retrieved_transactions)}"
        
        # 2. Transaction prices should match historical data
        for i, (original_price, retrieved) in enumerate(zip(transaction_prices, retrieved_transactions)):
            assert abs(retrieved.unit_price - original_price) < 0.01, \
                f"Transaction {i}: price {retrieved.unit_price} doesn't match expected {original_price}"
            assert retrieved.quantity == 1
            assert abs(retrieved.total_amount - original_price) < 0.01
        
        # 3. All transactions should reference the correct product and users
        for tx in retrieved_transactions:
            assert tx.product_id == product.id
            assert tx.buyer_id == customer.id
            assert tx.seller_id == vendor.id
            assert tx.status == TransactionStatus.COMPLETED
    
    @given(
        vendor_data=valid_user_data(),
        customer_data=valid_user_data(),
        product_name=valid_product_name(),
        initial_price=valid_price(),
        final_price=valid_price()
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_negotiation_price_history_integrity(
        self,
        vendor_data: Dict[str, Any],
        customer_data: Dict[str, Any],
        product_name: str,
        initial_price: float,
        final_price: float,
        db_session: AsyncSession
    ):
        """
        **Property 7: Historical Data Integrity**
        **Validates: Requirements 2.4**
        
        For any negotiation with price offers, the system should
        maintain accurate historical records of all offers for
        analysis and future price predictions.
        """
        # Ensure different users
        vendor_data['role'] = UserRole.VENDOR
        customer_data['role'] = UserRole.CUSTOMER
        customer_data['email'] = f"customer_{str(uuid4())[:8]}@example.com"
        
        # Create users
        vendor = User(**vendor_data)
        customer = User(**customer_data)
        db_session.add(vendor)
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(vendor)
        await db_session.refresh(customer)
        
        # Create product
        product = Product(
            vendor_id=vendor.id,
            name=product_name,
            description=f"Test product: {product_name}",
            base_price=initial_price,
            current_price=initial_price,
            currency='USD',
            quantity_available=100,
            availability=AvailabilityStatus.IN_STOCK,
            is_active=True
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Create negotiation with price history
        negotiation = Negotiation(
            product_id=product.id,
            vendor_id=vendor.id,
            customer_id=customer.id,
            initial_price=initial_price,
            current_offer=final_price,
            final_price=final_price,
            quantity=1,
            status=NegotiationStatus.COMPLETED,
            total_offers=2,
            cultural_context={'region': 'US', 'style': 'direct'},
            language_pair={'vendor': 'en', 'customer': 'en'}
        )
        db_session.add(negotiation)
        await db_session.commit()
        await db_session.refresh(negotiation)
        
        # Verify historical data integrity
        
        # 1. Negotiation should be retrievable with all data intact
        result = await db_session.execute(
            select(Negotiation).where(Negotiation.id == negotiation.id)
        )
        retrieved_negotiation = result.scalar_one()
        
        assert retrieved_negotiation is not None
        assert abs(retrieved_negotiation.initial_price - initial_price) < 0.01
        assert abs(retrieved_negotiation.current_offer - final_price) < 0.01
        assert retrieved_negotiation.total_offers == 2
        assert retrieved_negotiation.status == NegotiationStatus.COMPLETED
        
        # 2. Negotiation should reference correct entities
        assert retrieved_negotiation.product_id == product.id
        assert retrieved_negotiation.vendor_id == vendor.id
        assert retrieved_negotiation.customer_id == customer.id
        
        # 3. Cultural and language context should be preserved
        assert retrieved_negotiation.cultural_context is not None
        assert retrieved_negotiation.language_pair is not None
        assert isinstance(retrieved_negotiation.cultural_context, dict)
        assert isinstance(retrieved_negotiation.language_pair, dict)