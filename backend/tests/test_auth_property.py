"""
Property-based tests for authentication security.

This module contains property-based tests that validate universal properties
of the authentication system using Hypothesis for comprehensive input coverage.
"""

import pytest
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4, UUID

from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
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


# Custom strategies for generating test data
@composite
def valid_user_id(draw):
    """Generate valid UUID strings for user IDs."""
    return str(uuid4())


@composite
def valid_email(draw):
    """Generate valid email addresses."""
    username = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')),
        min_size=1,
        max_size=20
    ).filter(lambda x: x and x[0].isalpha()))
    
    domain = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')),
        min_size=1,
        max_size=15
    ).filter(lambda x: x and x[0].isalpha()))
    
    tld = draw(st.sampled_from(['com', 'org', 'net', 'edu', 'gov']))
    
    return f"{username}@{domain}.{tld}"


@composite
def valid_password(draw):
    """Generate valid passwords that meet security requirements."""
    # Ensure password has at least one letter and one digit
    letters = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu')),
        min_size=1,
        max_size=10
    ))
    digits = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Nd',)),
        min_size=1,
        max_size=5
    ))
    
    # Add some random characters
    extra = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc', 'Pd')),
        min_size=0,
        max_size=10
    ))
    
    # Combine and ensure minimum length
    password = letters + digits + extra
    if len(password) < 8:
        password += 'a' * (8 - len(password))
    
    return password[:100]  # Respect max length


@composite
def valid_user_data(draw):
    """Generate valid user registration data."""
    return UserRegister(
        email=draw(valid_email()),
        password=draw(valid_password()),
        first_name=draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip())),
        last_name=draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip())),
        role=draw(st.sampled_from([UserRole.VENDOR, UserRole.CUSTOMER])),
        phone_number=draw(st.one_of(
            st.none(),
            st.text(min_size=10, max_size=20).filter(lambda x: x.isdigit())
        )),
        preferred_language=draw(st.sampled_from(['en', 'es', 'fr', 'de', 'zh'])),
        country=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        region=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        city=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        timezone=draw(st.one_of(st.none(), st.sampled_from([
            'UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo'
        ]))),
        currency=draw(st.one_of(st.none(), st.sampled_from(['USD', 'EUR', 'GBP', 'JPY'])))
    )


@composite
def token_expiry_delta(draw):
    """Generate valid token expiry deltas."""
    minutes = draw(st.integers(min_value=1, max_value=60))  # Up to 1 hour only
    return timedelta(minutes=minutes)


class TestAuthenticationTokenValidity:
    """
    Property-based tests for authentication token validity.
    
    **Validates: Requirements 4.1, 5.1**
    
    These tests ensure that authentication tokens work correctly across
    all valid inputs and scenarios, validating the universal property
    that valid tokens should always authenticate successfully and invalid
    tokens should always be rejected.
    """
    
    @given(user_id=valid_user_id())
    @settings(max_examples=15, deadline=None)
    def test_access_token_creation_and_verification(self, user_id: str):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any valid user ID, creating an access token should produce
        a token that can be successfully verified and contains the correct
        user information.
        """
        # Create access token
        token = create_access_token(subject=user_id)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        payload = verify_token(token, token_type="access")
        
        # Verification should succeed
        assert payload is not None
        assert isinstance(payload, dict)
        
        # Payload should contain correct information
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        
        # Expiration should be in the future
        exp_timestamp = payload["exp"]
        assert exp_timestamp > datetime.utcnow().timestamp()
    
    @given(user_id=valid_user_id())
    @settings(max_examples=15, deadline=None)
    def test_refresh_token_creation_and_verification(self, user_id: str):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any valid user ID, creating a refresh token should produce
        a token that can be successfully verified as a refresh token.
        """
        # Create refresh token
        token = create_refresh_token(subject=user_id)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token as refresh token
        payload = verify_token(token, token_type="refresh")
        
        # Verification should succeed
        assert payload is not None
        assert isinstance(payload, dict)
        
        # Payload should contain correct information
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload
        
        # Expiration should be in the future
        exp_timestamp = payload["exp"]
        assert exp_timestamp > datetime.utcnow().timestamp()
    
    @given(user_id=valid_user_id())
    @settings(max_examples=15, deadline=None)
    def test_custom_token_expiration(self, user_id: str):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any valid user ID, tokens should be created with proper expiration
        and remain valid until that time.
        """
        # Create token with a short custom expiration (5 minutes)
        expires_delta = timedelta(minutes=5)
        token = create_access_token(subject=user_id, expires_delta=expires_delta)
        
        # Verify token
        payload = verify_token(token, token_type="access")
        assert payload is not None
        
        # Check that the token has an expiration time in the future
        exp_timestamp = payload["exp"]
        current_time = datetime.utcnow().timestamp()
        assert exp_timestamp > current_time
        
        # Check that the expiration is reasonable (within 10 minutes from now)
        max_reasonable_exp = (datetime.utcnow() + timedelta(minutes=10)).timestamp()
        assert exp_timestamp <= max_reasonable_exp
    
    @given(user_id=valid_user_id())
    @settings(max_examples=15, deadline=None)
    def test_token_type_validation(self, user_id: str):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any valid user ID, access tokens should only verify as access tokens
        and refresh tokens should only verify as refresh tokens.
        """
        # Create both token types
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        
        # Access token should verify as access but not refresh
        assert verify_token(access_token, token_type="access") is not None
        assert verify_token(access_token, token_type="refresh") is None
        
        # Refresh token should verify as refresh but not access
        assert verify_token(refresh_token, token_type="refresh") is not None
        assert verify_token(refresh_token, token_type="access") is None
    
    @given(
        user_id=valid_user_id(),
        invalid_token=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=15, deadline=None)
    def test_invalid_token_rejection(self, user_id: str, invalid_token: str):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any invalid token string, verification should always fail
        and return None, ensuring security against token forgery.
        """
        # Assume the invalid token is not a valid JWT format
        assume(not invalid_token.count('.') == 2)
        assume(len(invalid_token) < 200)  # Avoid extremely long strings
        
        # Invalid tokens should always fail verification
        assert verify_token(invalid_token, token_type="access") is None
        assert verify_token(invalid_token, token_type="refresh") is None
    
    @given(user_id=valid_user_id())
    @settings(max_examples=15, deadline=None)
    def test_expired_token_rejection(self, user_id: str):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any user ID, tokens created with past expiration times
        should be rejected during verification.
        """
        # Create token that's already expired
        past_expiry = timedelta(seconds=-1)
        expired_token = create_access_token(subject=user_id, expires_delta=past_expiry)
        
        # Expired token should fail verification
        assert verify_token(expired_token, token_type="access") is None
    
    @given(password=valid_password())
    @settings(max_examples=15, deadline=None)
    def test_password_hashing_consistency(self, password: str):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any valid password, hashing should produce a hash that
        can be verified against the original password, and different
        hashes should be generated for the same password (due to salt).
        """
        # Hash the password twice
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        
        # Both hashes should verify against the original password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
        
        # Hashes should not verify against different passwords
        if len(password) > 1:
            wrong_password = password[:-1] + ('x' if password[-1] != 'x' else 'y')
            assert verify_password(wrong_password, hash1) is False
            assert verify_password(wrong_password, hash2) is False
    
    @given(email=valid_email())
    @settings(max_examples=15, deadline=None)
    def test_password_reset_token_validity(self, email: str):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any valid email, password reset tokens should be generated
        and verified correctly, containing the correct email information.
        """
        # Generate password reset token
        reset_token = generate_password_reset_token(email)
        
        # Token should be a non-empty string
        assert isinstance(reset_token, str)
        assert len(reset_token) > 0
        
        # Verify reset token
        verified_email = verify_password_reset_token(reset_token)
        
        # Verification should succeed and return correct email
        assert verified_email == email
    
    @given(
        email=valid_email(),
        invalid_token=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=15, deadline=None)
    def test_invalid_password_reset_token_rejection(self, email: str, invalid_token: str):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any invalid password reset token, verification should fail
        and return None, ensuring security of the password reset process.
        """
        # Assume the invalid token is not a valid JWT format
        assume(not invalid_token.count('.') == 2)
        assume(len(invalid_token) < 200)
        
        # Invalid reset tokens should always fail verification
        assert verify_password_reset_token(invalid_token) is None


@pytest.mark.asyncio
class TestAuthenticationEndpointSecurity:
    """
    Property-based tests for authentication endpoint security.
    
    **Validates: Requirements 4.1, 5.1**
    
    These tests ensure that authentication endpoints handle all valid
    inputs correctly and reject invalid inputs securely.
    """
    
    @given(user_data=valid_user_data())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_user_registration_token_flow(
        self, 
        user_data: UserRegister,
        db_session: AsyncSession
    ):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any valid user registration data, the complete flow of
        registration and subsequent authentication should work correctly.
        """
        user_service = UserService(db_session)
        
        # Create user
        user = await user_service.create_user(user_data)
        assert user is not None
        assert user.email == user_data.email
        
        # Authenticate user
        authenticated_user = await user_service.authenticate_user(
            user_data.email,
            user_data.password
        )
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        
        # Create tokens for the authenticated user
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        # Verify tokens contain correct user information
        access_payload = verify_token(access_token, token_type="access")
        refresh_payload = verify_token(refresh_token, token_type="refresh")
        
        assert access_payload is not None
        assert refresh_payload is not None
        assert access_payload["sub"] == str(user.id)
        assert refresh_payload["sub"] == str(user.id)
    
    @given(
        user_data=valid_user_data(),
        wrong_password=valid_password()
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_authentication_failure_security(
        self,
        user_data: UserRegister,
        wrong_password: str,
        db_session: AsyncSession
    ):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any valid user and any incorrect password, authentication
        should fail and no tokens should be generated.
        """
        # Ensure wrong password is actually different
        assume(wrong_password != user_data.password)
        
        user_service = UserService(db_session)
        
        # Create user
        user = await user_service.create_user(user_data)
        assert user is not None
        
        # Try to authenticate with wrong password
        authenticated_user = await user_service.authenticate_user(
            user_data.email,
            wrong_password
        )
        
        # Authentication should fail
        assert authenticated_user is None
    
    @given(user_data=valid_user_data())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_token_refresh_security(
        self,
        user_data: UserRegister,
        db_session: AsyncSession
    ):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any valid user, refresh tokens should only be usable for
        token refresh and should generate new valid tokens.
        """
        user_service = UserService(db_session)
        
        # Create and authenticate user
        user = await user_service.create_user(user_data)
        authenticated_user = await user_service.authenticate_user(
            user_data.email,
            user_data.password
        )
        assert authenticated_user is not None
        
        # Create initial tokens
        initial_refresh_token = create_refresh_token(subject=str(user.id))
        
        # Verify refresh token
        refresh_payload = verify_token(initial_refresh_token, token_type="refresh")
        assert refresh_payload is not None
        assert refresh_payload["sub"] == str(user.id)
        
        # Refresh token should not verify as access token
        assert verify_token(initial_refresh_token, token_type="access") is None
        
        # Create new tokens using the refresh token payload
        new_access_token = create_access_token(subject=refresh_payload["sub"])
        new_refresh_token = create_refresh_token(subject=refresh_payload["sub"])
        
        # New tokens should be valid
        new_access_payload = verify_token(new_access_token, token_type="access")
        new_refresh_payload = verify_token(new_refresh_token, token_type="refresh")
        
        assert new_access_payload is not None
        assert new_refresh_payload is not None
        assert new_access_payload["sub"] == str(user.id)
        assert new_refresh_payload["sub"] == str(user.id)


@pytest.mark.asyncio
class TestAuthenticationIntegrationSecurity:
    """
    Integration property-based tests for complete authentication flows.
    
    **Validates: Requirements 4.1, 5.1**
    """
    
    @given(user_data=valid_user_data())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_complete_authentication_flow_security(
        self,
        user_data: UserRegister,
        client: TestClient
    ):
        """
        **Property 1: Authentication token validity**
        **Validates: Requirements 4.1, 5.1**
        
        For any valid user data, the complete authentication flow through
        API endpoints should work correctly and securely.
        """
        # Register user
        register_response = client.post(
            "/api/v1/auth/register",
            json=user_data.dict()
        )
        
        # Registration should succeed
        assert register_response.status_code == 201
        register_data = register_response.json()
        assert register_data["email"] == user_data.email
        
        # Login user
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": user_data.email,
                "password": user_data.password
            }
        )
        
        # Login should succeed
        assert login_response.status_code == 200
        login_data = login_response.json()
        
        # Response should contain valid tokens
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        assert login_data["token_type"] == "bearer"
        assert "expires_in" in login_data
        
        # Tokens should be valid
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        access_payload = verify_token(access_token, token_type="access")
        refresh_payload = verify_token(refresh_token, token_type="refresh")
        
        assert access_payload is not None
        assert refresh_payload is not None
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"
        
        # Use access token to access protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        
        # Protected endpoint should work with valid token
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == user_data.email
        
        # Test token refresh
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        # Token refresh should succeed
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        
        # New tokens should be valid
        new_access_token = refresh_data["access_token"]
        new_refresh_token = refresh_data["refresh_token"]
        
        new_access_payload = verify_token(new_access_token, token_type="access")
        new_refresh_payload = verify_token(new_refresh_token, token_type="refresh")
        
        assert new_access_payload is not None
        assert new_refresh_payload is not None
        
        # New access token should work for protected endpoints
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        new_me_response = client.get("/api/v1/auth/me", headers=new_headers)
        assert new_me_response.status_code == 200