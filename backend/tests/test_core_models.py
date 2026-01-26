"""
Unit tests for core data models and schemas.

This module tests the Product, Transaction, and Negotiation models
and their corresponding Pydantic schemas.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.models import (
    Product, Category, Transaction, Negotiation, NegotiationMessage,
    AvailabilityStatus, TransactionStatus, NegotiationStatus, MessageType
)
from app.schemas import (
    ProductCreate, ProductUpdate, ProductResponse,
    TransactionCreate, TransactionResponse,
    NegotiationCreate, NegotiationResponse,
    NegotiationMessageCreate
)


class TestProductModel:
    """Test Product model functionality."""
    
    def test_product_creation(self):
        """Test creating a Product instance."""
        product_id = uuid4()
        vendor_id = uuid4()
        category_id = uuid4()
        
        product = Product(
            id=product_id,
            vendor_id=vendor_id,
            category_id=category_id,
            name="Test Product",
            description="A test product",
            base_price=100.0,
            current_price=90.0,
            currency="USD",
            quantity_available=10,
            availability=AvailabilityStatus.IN_STOCK,
            images=["https://example.com/image1.jpg"],
            specifications={"color": "blue", "size": "medium"},
            tags=["test", "electronics"],
            is_active=True
        )
        
        assert product.id == product_id
        assert product.name == "Test Product"
        assert product.base_price == 100.0
        assert product.current_price == 90.0
        assert product.availability == AvailabilityStatus.IN_STOCK
        assert product.is_active is True
        assert len(product.images) == 1
        assert product.specifications["color"] == "blue"
        assert "test" in product.tags
    
    def test_category_creation(self):
        """Test creating a Category instance."""
        category_id = uuid4()
        
        category = Category(
            id=category_id,
            name="Electronics",
            description="Electronic devices",
            slug="electronics",
            level=0,
            is_active=True
        )
        
        assert category.id == category_id
        assert category.name == "Electronics"
        assert category.slug == "electronics"
        assert category.level == 0
        assert category.is_active is True


class TestTransactionModel:
    """Test Transaction model functionality."""
    
    def test_transaction_creation(self):
        """Test creating a Transaction instance."""
        transaction_id = uuid4()
        buyer_id = uuid4()
        seller_id = uuid4()
        product_id = uuid4()
        
        transaction = Transaction(
            id=transaction_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            product_id=product_id,
            quantity=2,
            unit_price=45.0,
            total_amount=90.0,
            currency="USD",
            status=TransactionStatus.PENDING,
            payment_method="card",
            payment_provider="stripe"
        )
        
        assert transaction.id == transaction_id
        assert transaction.buyer_id == buyer_id
        assert transaction.seller_id == seller_id
        assert transaction.quantity == 2
        assert transaction.unit_price == 45.0
        assert transaction.total_amount == 90.0
        assert transaction.status == TransactionStatus.PENDING
        assert transaction.payment_method == "card"


class TestNegotiationModel:
    """Test Negotiation model functionality."""
    
    def test_negotiation_creation(self):
        """Test creating a Negotiation instance."""
        negotiation_id = uuid4()
        product_id = uuid4()
        vendor_id = uuid4()
        customer_id = uuid4()
        
        negotiation = Negotiation(
            id=negotiation_id,
            product_id=product_id,
            vendor_id=vendor_id,
            customer_id=customer_id,
            initial_price=100.0,
            current_offer=80.0,
            quantity=1,
            status=NegotiationStatus.ACTIVE,
            cultural_context={"vendor_style": "direct"},
            language_pair={"vendor": "en", "customer": "es"}
        )
        
        assert negotiation.id == negotiation_id
        assert negotiation.initial_price == 100.0
        assert negotiation.current_offer == 80.0
        assert negotiation.status == NegotiationStatus.ACTIVE
        assert negotiation.cultural_context["vendor_style"] == "direct"
        assert negotiation.language_pair["vendor"] == "en"
    
    def test_negotiation_message_creation(self):
        """Test creating a NegotiationMessage instance."""
        message_id = uuid4()
        negotiation_id = uuid4()
        sender_id = uuid4()
        
        message = NegotiationMessage(
            id=message_id,
            negotiation_id=negotiation_id,
            sender_id=sender_id,
            original_text="Hello, can we negotiate?",
            translated_text="Hola, ¿podemos negociar?",
            original_language="en",
            target_language="es",
            message_type=MessageType.TEXT,
            translation_confidence=0.95
        )
        
        assert message.id == message_id
        assert message.original_text == "Hello, can we negotiate?"
        assert message.translated_text == "Hola, ¿podemos negociar?"
        assert message.message_type == MessageType.TEXT
        assert message.translation_confidence == 0.95


class TestProductSchemas:
    """Test Product Pydantic schemas."""
    
    def test_product_create_schema(self):
        """Test ProductCreate schema validation."""
        product_data = {
            "name": "Test Product",
            "description": "A test product",
            "base_price": 100.0,
            "current_price": 90.0,
            "currency": "USD",
            "quantity_available": 10,
            "availability": "in_stock",
            "images": ["https://example.com/image1.jpg"],
            "specifications": {"color": "blue"},
            "tags": ["test", "electronics"],
            "is_active": True
        }
        
        product_create = ProductCreate(**product_data)
        
        assert product_create.name == "Test Product"
        assert product_create.base_price == 100.0
        assert product_create.current_price == 90.0
        assert product_create.availability == AvailabilityStatus.IN_STOCK
        assert len(product_create.images) == 1
        assert product_create.specifications["color"] == "blue"
        assert "test" in product_create.tags
    
    def test_product_create_validation_errors(self):
        """Test ProductCreate schema validation errors."""
        # Test negative price
        with pytest.raises(ValueError):
            ProductCreate(
                name="Test",
                base_price=-10.0,
                current_price=90.0
            )
        
        # Test empty name
        with pytest.raises(ValueError):
            ProductCreate(
                name="",
                base_price=100.0,
                current_price=90.0
            )
        
        # Test too many tags
        with pytest.raises(ValueError):
            ProductCreate(
                name="Test",
                base_price=100.0,
                current_price=90.0,
                tags=["tag" + str(i) for i in range(25)]  # More than 20 tags
            )
    
    def test_product_update_schema(self):
        """Test ProductUpdate schema validation."""
        update_data = {
            "name": "Updated Product",
            "current_price": 85.0,
            "availability": "low_stock"
        }
        
        product_update = ProductUpdate(**update_data)
        
        assert product_update.name == "Updated Product"
        assert product_update.current_price == 85.0
        assert product_update.availability == AvailabilityStatus.LOW_STOCK


class TestTransactionSchemas:
    """Test Transaction Pydantic schemas."""
    
    def test_transaction_create_schema(self):
        """Test TransactionCreate schema validation."""
        transaction_data = {
            "product_id": str(uuid4()),
            "seller_id": str(uuid4()),
            "quantity": 2,
            "unit_price": 45.0,
            "currency": "USD",
            "payment_method": "card",
            "delivery_address": {
                "street": "123 Main St",
                "city": "San Francisco",
                "country": "USA"
            }
        }
        
        transaction_create = TransactionCreate(**transaction_data)
        
        assert transaction_create.quantity == 2
        assert transaction_create.unit_price == 45.0
        assert transaction_create.payment_method == "card"
        assert transaction_create.delivery_address["street"] == "123 Main St"
    
    def test_transaction_create_validation_errors(self):
        """Test TransactionCreate schema validation errors."""
        # Test invalid payment method
        with pytest.raises(ValueError):
            TransactionCreate(
                product_id=str(uuid4()),
                seller_id=str(uuid4()),
                quantity=1,
                unit_price=100.0,
                payment_method="invalid_method"
            )
        
        # Test zero quantity
        with pytest.raises(ValueError):
            TransactionCreate(
                product_id=str(uuid4()),
                seller_id=str(uuid4()),
                quantity=0,
                unit_price=100.0,
                payment_method="card"
            )
        
        # Test incomplete delivery address
        with pytest.raises(ValueError):
            TransactionCreate(
                product_id=str(uuid4()),
                seller_id=str(uuid4()),
                quantity=1,
                unit_price=100.0,
                payment_method="card",
                delivery_address={"street": "123 Main St"}  # Missing city and country
            )


class TestNegotiationSchemas:
    """Test Negotiation Pydantic schemas."""
    
    def test_negotiation_create_schema(self):
        """Test NegotiationCreate schema validation."""
        negotiation_data = {
            "product_id": str(uuid4()),
            "vendor_id": str(uuid4()),
            "initial_price": 100.0,
            "quantity": 1,
            "language_pair": {"vendor": "en", "customer": "es"}
        }
        
        negotiation_create = NegotiationCreate(**negotiation_data)
        
        assert negotiation_create.initial_price == 100.0
        assert negotiation_create.quantity == 1
        assert negotiation_create.language_pair["vendor"] == "en"
        assert negotiation_create.language_pair["customer"] == "es"
    
    def test_negotiation_message_create_schema(self):
        """Test NegotiationMessageCreate schema validation."""
        message_data = {
            "negotiation_id": str(uuid4()),
            "original_text": "Hello, can we negotiate the price?",
            "message_type": "text",
            "original_language": "en",
            "target_language": "es"
        }
        
        message_create = NegotiationMessageCreate(**message_data)
        
        assert message_create.original_text == "Hello, can we negotiate the price?"
        assert message_create.message_type == MessageType.TEXT
        assert message_create.original_language == "en"
    
    def test_negotiation_message_validation_errors(self):
        """Test NegotiationMessageCreate schema validation errors."""
        # Test empty message text
        with pytest.raises(ValueError):
            NegotiationMessageCreate(
                negotiation_id=str(uuid4()),
                original_text="   ",  # Empty after strip
                message_type="text"
            )
        
        # Test message too long
        with pytest.raises(ValueError):
            NegotiationMessageCreate(
                negotiation_id=str(uuid4()),
                original_text="x" * 2001,  # Exceeds 2000 character limit
                message_type="text"
            )


class TestEnumValues:
    """Test enum values are correct."""
    
    def test_availability_status_enum(self):
        """Test AvailabilityStatus enum values."""
        assert AvailabilityStatus.IN_STOCK == "in_stock"
        assert AvailabilityStatus.LOW_STOCK == "low_stock"
        assert AvailabilityStatus.OUT_OF_STOCK == "out_of_stock"
    
    def test_transaction_status_enum(self):
        """Test TransactionStatus enum values."""
        assert TransactionStatus.PENDING == "pending"
        assert TransactionStatus.PROCESSING == "processing"
        assert TransactionStatus.COMPLETED == "completed"
        assert TransactionStatus.FAILED == "failed"
        assert TransactionStatus.CANCELLED == "cancelled"
        assert TransactionStatus.REFUNDED == "refunded"
    
    def test_negotiation_status_enum(self):
        """Test NegotiationStatus enum values."""
        assert NegotiationStatus.ACTIVE == "active"
        assert NegotiationStatus.COMPLETED == "completed"
        assert NegotiationStatus.CANCELLED == "cancelled"
        assert NegotiationStatus.EXPIRED == "expired"
    
    def test_message_type_enum(self):
        """Test MessageType enum values."""
        assert MessageType.TEXT == "text"
        assert MessageType.OFFER == "offer"
        assert MessageType.COUNTEROFFER == "counteroffer"
        assert MessageType.SYSTEM == "system"
        assert MessageType.CULTURAL_TIP == "cultural_tip"