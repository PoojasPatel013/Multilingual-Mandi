"""
Pytest configuration and fixtures for the Multilingual Mandi backend tests.

This module provides common test fixtures and configuration for all test modules.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator, Dict
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.redis import init_redis, close_redis, get_redis
from app.core.config import get_settings
from app.core.auth import create_access_token


# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    
    Yields:
        AsyncSession: Test database session
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    """
    Create a test HTTP client.
    
    Args:
        db_session: Test database session
        
    Yields:
        TestClient: Test HTTP client
    """
    # Override database dependency
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock Redis for tests - skip Redis initialization
    try:
        await init_redis()
    except Exception:
        # If Redis fails, continue without it for tests
        pass
    
    with TestClient(app) as client:
        yield client
    
    # Cleanup
    try:
        await close_redis()
    except Exception:
        pass
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: TestClient, db_session: AsyncSession) -> Dict[str, str]:
    """
    Create authentication headers for testing protected endpoints.
    
    Args:
        client: Test HTTP client
        db_session: Test database session
        
    Returns:
        Dict with Authorization header
    """
    # Create a test user
    user_data = {
        "email": "testauth@example.com",
        "password": "testpass123",
        "first_name": "Auth",
        "last_name": "Test",
        "role": "customer"
    }
    
    # Register user
    client.post("/api/v1/auth/register", json=user_data)
    
    # Login to get token
    login_response = client.post("/api/v1/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def settings():
    """Get test settings."""
    return get_settings()


# Property-based testing fixtures
@pytest.fixture
def hypothesis_settings():
    """Configure Hypothesis settings for property-based tests."""
    from hypothesis import settings, Verbosity
    
    return settings(
        max_examples=100,
        verbosity=Verbosity.verbose,
        deadline=None,  # Disable deadline for async tests
    )


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def user_data(role: str = "customer", **kwargs):
        """Create test user data."""
        base_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "role": role,
            "preferred_language": "en",
            "country": "US",
            "region": "California",
            "city": "San Francisco",
            "timezone": "America/Los_Angeles",
            "currency": "USD",
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def product_data(**kwargs):
        """Create test product data."""
        base_data = {
            "name": "Test Product",
            "description": "A test product for testing purposes",
            "base_price": 100.0,
            "current_price": 100.0,
            "currency": "USD",
            "quantity_available": 10,
            "availability": "in_stock",
            "is_active": True,
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def negotiation_data(**kwargs):
        """Create test negotiation data."""
        base_data = {
            "initial_price": 100.0,
            "current_offer": 90.0,
            "quantity": 1,
            "status": "active",
        }
        base_data.update(kwargs)
        return base_data


@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory


# Async test helpers
class AsyncTestHelpers:
    """Helper methods for async tests."""
    
    @staticmethod
    async def create_test_user(db_session: AsyncSession, **kwargs):
        """Create a test user in the database."""
        from app.models.user import User
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user_data = TestDataFactory.user_data(**kwargs)
        hashed_password = pwd_context.hash(user_data.pop("password"))
        
        user = User(
            hashed_password=hashed_password,
            **user_data
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        return user
    
    @staticmethod
    async def create_test_product(db_session: AsyncSession, vendor_id, **kwargs):
        """Create a test product in the database."""
        from app.models.product import Product
        
        product_data = TestDataFactory.product_data(**kwargs)
        product = Product(
            vendor_id=vendor_id,
            **product_data
        )
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        return product


@pytest.fixture
def async_test_helpers():
    """Provide async test helpers."""
    return AsyncTestHelpers


@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession):
    """Create a sample user for testing."""
    from app.models.user import User, UserRole, VerificationStatus
    from app.core.auth import get_password_hash
    
    user = User(
        email="sample@example.com",
        hashed_password=get_password_hash("testpass123"),
        first_name="Sample",
        last_name="User",
        role=UserRole.CUSTOMER,
        preferred_language="en",
        country="US",
        region="California",
        city="San Francisco",
        timezone="America/Los_Angeles",
        currency="USD",
        verification_status=VerificationStatus.VERIFIED,
        is_active=True,
        is_superuser=False,
        login_count=0
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def sample_vendor(db_session: AsyncSession):
    """Create a sample vendor user for testing."""
    from app.models.user import User, UserRole, VerificationStatus
    from app.core.auth import get_password_hash
    
    user = User(
        email="vendor@example.com",
        hashed_password=get_password_hash("testpass123"),
        first_name="Vendor",
        last_name="User",
        role=UserRole.VENDOR,
        preferred_language="en",
        country="US",
        region="California",
        city="San Francisco",
        timezone="America/Los_Angeles",
        currency="USD",
        verification_status=VerificationStatus.VERIFIED,
        is_active=True,
        is_superuser=False,
        login_count=0
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def sample_customer(db_session: AsyncSession):
    """Create a sample customer user for testing."""
    from app.models.user import User, UserRole, VerificationStatus
    from app.core.auth import get_password_hash
    
    user = User(
        email="customer@example.com",
        hashed_password=get_password_hash("testpass123"),
        first_name="Customer",
        last_name="User",
        role=UserRole.CUSTOMER,
        preferred_language="en",
        country="US",
        region="California",
        city="San Francisco",
        timezone="America/Los_Angeles",
        currency="USD",
        verification_status=VerificationStatus.VERIFIED,
        is_active=True,
        is_superuser=False,
        login_count=0
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def sample_vendor_with_profile(db_session: AsyncSession, sample_vendor):
    """Create a sample vendor with vendor profile."""
    from app.models.user import VendorProfile
    
    vendor_profile = VendorProfile(
        user_id=sample_vendor.id,
        business_name="Test Business",
        business_type="Retail",
        business_description="A test business",
        market_stall="Stall A1",
        languages=["en", "es"],
        communication_preferences={"preferred_time": "morning"},
        payment_methods=[{"type": "card", "provider": "stripe"}],
        business_hours={"monday": {"open": "09:00", "close": "17:00"}},
        average_rating=4.5,
        total_sales=100,
        total_reviews=20,
        is_available=True
    )
    
    db_session.add(vendor_profile)
    await db_session.commit()
    await db_session.refresh(vendor_profile)
    
    return sample_vendor, vendor_profile


@pytest_asyncio.fixture
async def sample_customer_with_profile(db_session: AsyncSession, sample_customer):
    """Create a sample customer with customer profile."""
    from app.models.user import CustomerProfile
    
    customer_profile = CustomerProfile(
        user_id=sample_customer.id,
        preferred_categories=["electronics"],
        price_range_preferences={"electronics": {"min": 100, "max": 1000}},
        total_purchases=5,
        total_spent=500.0,
        average_rating_given=4.2,
        wishlist_items=[],
        favorite_vendors=[],
        notification_preferences={"email": True, "sms": False}
    )
    
    db_session.add(customer_profile)
    await db_session.commit()
    await db_session.refresh(customer_profile)
    
    return sample_customer, customer_profile


# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.property = pytest.mark.property
pytest.mark.slow = pytest.mark.slow