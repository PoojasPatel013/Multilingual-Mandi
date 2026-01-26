"""
Unit tests for authentication functionality.

This module tests user registration, login, JWT token management,
and password operations.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
    verify_password,
    generate_password_reset_token,
    verify_password_reset_token
)
from app.models.user import User, UserRole, VerificationStatus
from app.schemas.auth import UserRegister
from app.services.user_service import UserService


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test password hashing creates different hashes for same password."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        assert len(hash1) > 0
        assert len(hash2) > 0
    
    def test_password_verification(self):
        """Test password verification works correctly."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        # Correct password should verify
        assert verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "test-user-id"
        token = create_access_token(subject=user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        payload = verify_token(token, token_type="access")
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "test-user-id"
        token = create_refresh_token(subject=user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        payload = verify_token(token, token_type="refresh")
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
    
    def test_token_expiration(self):
        """Test token expiration handling."""
        user_id = "test-user-id"
        
        # Create token with very short expiration
        short_expiry = timedelta(seconds=-1)  # Already expired
        token = create_access_token(subject=user_id, expires_delta=short_expiry)
        
        # Verify expired token returns None
        payload = verify_token(token, token_type="access")
        assert payload is None
    
    def test_invalid_token_type(self):
        """Test token type validation."""
        user_id = "test-user-id"
        access_token = create_access_token(subject=user_id)
        
        # Try to verify access token as refresh token
        payload = verify_token(access_token, token_type="refresh")
        assert payload is None
    
    def test_password_reset_token(self):
        """Test password reset token generation and verification."""
        email = "test@example.com"
        
        # Generate reset token
        token = generate_password_reset_token(email)
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify reset token
        verified_email = verify_password_reset_token(token)
        assert verified_email == email
    
    def test_invalid_token(self):
        """Test invalid token handling."""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token, token_type="access")
        assert payload is None
        
        email = verify_password_reset_token(invalid_token)
        assert email is None


@pytest.mark.asyncio
class TestUserService:
    """Test user service operations."""
    
    async def test_create_user(self, db_session: AsyncSession):
        """Test user creation."""
        user_service = UserService(db_session)
        
        user_data = UserRegister(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            role=UserRole.CUSTOMER,
            preferred_language="en"
        )
        
        user = await user_service.create_user(user_data)
        
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.role == UserRole.CUSTOMER
        assert user.is_active is True
        assert user.verification_status == VerificationStatus.PENDING
        assert verify_password("testpass123", user.hashed_password)
    
    async def test_create_duplicate_user(self, db_session: AsyncSession):
        """Test creating user with duplicate email fails."""
        user_service = UserService(db_session)
        
        user_data = UserRegister(
            email="duplicate@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            role=UserRole.CUSTOMER
        )
        
        # Create first user
        await user_service.create_user(user_data)
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="Email already registered"):
            await user_service.create_user(user_data)
    
    async def test_authenticate_user(self, db_session: AsyncSession):
        """Test user authentication."""
        user_service = UserService(db_session)
        
        # Create user
        user_data = UserRegister(
            email="auth@example.com",
            password="testpass123",
            first_name="Auth",
            last_name="User",
            role=UserRole.CUSTOMER
        )
        created_user = await user_service.create_user(user_data)
        
        # Test successful authentication
        authenticated_user = await user_service.authenticate_user(
            "auth@example.com", 
            "testpass123"
        )
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.login_count == 1
        
        # Test failed authentication
        failed_auth = await user_service.authenticate_user(
            "auth@example.com", 
            "wrongpassword"
        )
        assert failed_auth is None
        
        # Test non-existent user
        no_user = await user_service.authenticate_user(
            "nonexistent@example.com", 
            "testpass123"
        )
        assert no_user is None
    
    async def test_get_user_by_email(self, db_session: AsyncSession):
        """Test getting user by email."""
        user_service = UserService(db_session)
        
        # Create user
        user_data = UserRegister(
            email="findme@example.com",
            password="testpass123",
            first_name="Find",
            last_name="Me",
            role=UserRole.VENDOR
        )
        created_user = await user_service.create_user(user_data)
        
        # Find user by email
        found_user = await user_service.get_user_by_email("findme@example.com")
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "findme@example.com"
        
        # Try to find non-existent user
        not_found = await user_service.get_user_by_email("notfound@example.com")
        assert not_found is None
    
    async def test_change_password(self, db_session: AsyncSession):
        """Test password change functionality."""
        user_service = UserService(db_session)
        
        # Create user
        user_data = UserRegister(
            email="changepass@example.com",
            password="oldpass123",
            first_name="Change",
            last_name="Pass",
            role=UserRole.CUSTOMER
        )
        user = await user_service.create_user(user_data)
        
        # Change password successfully
        success = await user_service.change_password(
            user.id,
            "oldpass123",
            "newpass456"
        )
        assert success is True
        
        # Verify old password no longer works
        auth_old = await user_service.authenticate_user(
            "changepass@example.com",
            "oldpass123"
        )
        assert auth_old is None
        
        # Verify new password works
        auth_new = await user_service.authenticate_user(
            "changepass@example.com",
            "newpass456"
        )
        assert auth_new is not None
        
        # Test wrong current password
        fail_change = await user_service.change_password(
            user.id,
            "wrongcurrent",
            "anotherpass"
        )
        assert fail_change is False


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    async def test_register_endpoint(self, client: TestClient):
        """Test user registration endpoint."""
        user_data = {
            "email": "register@example.com",
            "password": "testpass123",
            "first_name": "Register",
            "last_name": "Test",
            "role": "customer",
            "preferred_language": "en"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "register@example.com"
        assert data["first_name"] == "Register"
        assert data["role"] == "customer"
        assert "id" in data
    
    async def test_register_duplicate_email(self, client: TestClient):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": "duplicate@example.com",
            "password": "testpass123",
            "first_name": "First",
            "last_name": "User",
            "role": "customer"
        }
        
        # First registration should succeed
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Second registration should fail
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
    
    async def test_login_endpoint(self, client: TestClient):
        """Test user login endpoint."""
        # First register a user
        user_data = {
            "email": "login@example.com",
            "password": "testpass123",
            "first_name": "Login",
            "last_name": "Test",
            "role": "customer"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Then login
        login_data = {
            "email": "login@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    async def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpass"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    async def test_get_current_user(self, client: TestClient, auth_headers):
        """Test getting current user information."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "role" in data
    
    async def test_unauthorized_access(self, client: TestClient):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401