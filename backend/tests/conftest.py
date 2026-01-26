"""
Pytest configuration and fixtures for the Multilingual Mandi backend tests.

This module provides common test fixtures and configuration for all test modules.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.redis import init_redis, close_redis, get_redis
from app.core.config import get_settings


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
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test HTTP client.
    
    Args:
        db_session: Test database session
        
    Yields:
        AsyncClient: Test HTTP client
    """
    # Override database dependency
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Initialize Redis for tests (using fakeredis in real tests)
    await init_redis()
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Cleanup
    await close_redis()
    app.dependency_overrides.clear()


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


# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.property = pytest.mark.property
pytest.mark.slow = pytest.mark.slow