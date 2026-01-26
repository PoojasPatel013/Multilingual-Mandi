"""
Integration tests for profile management API endpoints.

This module tests the profile management API endpoints to ensure
they work correctly with authentication and database operations.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.models.user import UserRole


class TestProfileAPI:
    """Test profile management API endpoints."""
    
    def test_get_my_profile(self, client: TestClient, auth_headers):
        """Test getting current user profile."""
        response = client.get("/api/v1/profile/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "role" in data
        assert data["email"] == "testauth@example.com"
    
    def test_update_my_profile_basic(self, client: TestClient, auth_headers):
        """Test updating basic profile information."""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "preferred_language": "es"
        }
        
        response = client.put("/api/v1/profile/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["preferred_language"] == "es"
    
    def test_update_my_profile_with_cultural_context(self, client: TestClient, auth_headers):
        """Test updating profile with cultural context."""
        update_data = {
            "first_name": "Cultural",
            "last_name": "User",
            "cultural_context": {
                "region": "South Asia",
                "negotiation_style": "relationship_based",
                "time_orientation": "flexible",
                "communication_preferences": ["indirect", "respectful"],
                "business_etiquette": ["greeting_important"],
                "holidays_and_events": ["Diwali"]
            },
            "geographic_location": {
                "country": "India",
                "region": "Maharashtra",
                "city": "Mumbai",
                "coordinates": {"lat": 19.0760, "lng": 72.8777},
                "timezone": "Asia/Kolkata",
                "currency": "INR"
            }
        }
        
        response = client.put("/api/v1/profile/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Cultural"
        assert data["country"] == "India"
        assert data["city"] == "Mumbai"
        assert data["currency"] == "INR"
        assert data["cultural_profile"] is not None
        assert data["cultural_profile"]["region"] == "South Asia"
        assert data["cultural_profile"]["negotiation_style"] == "relationship_based"
    
    def test_add_payment_method(self, client: TestClient, auth_headers):
        """Test adding payment method."""
        payment_data = {
            "method_type": "card",
            "provider": "stripe",
            "details": {
                "last_four": "1234",
                "brand": "visa"
            },
            "is_default": True
        }
        
        response = client.post("/api/v1/profile/payment-methods", json=payment_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["method_type"] == "card"
        assert data["provider"] == "stripe"
        assert data["is_default"] is True
        assert data["is_active"] is True
        # Details should not be returned for security
        assert "details" not in data
    
    def test_get_payment_methods(self, client: TestClient, auth_headers):
        """Test getting user payment methods."""
        # First add a payment method
        payment_data = {
            "method_type": "bank",
            "provider": "plaid",
            "details": {"account_last_four": "5678"},
            "is_default": False
        }
        
        client.post("/api/v1/profile/payment-methods", json=payment_data, headers=auth_headers)
        
        # Get payment methods
        response = client.get("/api/v1/profile/payment-methods", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check the payment method we just added
        bank_method = next((pm for pm in data if pm["method_type"] == "bank"), None)
        assert bank_method is not None
        assert bank_method["provider"] == "plaid"
        assert bank_method["is_active"] is True
    
    def test_delete_payment_method(self, client: TestClient, auth_headers):
        """Test deleting payment method."""
        # First add a payment method
        payment_data = {
            "method_type": "mobile",
            "provider": "paypal",
            "details": {"email": "test@example.com"},
            "is_default": False
        }
        
        add_response = client.post("/api/v1/profile/payment-methods", json=payment_data, headers=auth_headers)
        payment_method_id = add_response.json()["id"]
        
        # Delete the payment method
        response = client.delete(f"/api/v1/profile/payment-methods/{payment_method_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted successfully" in data["message"]
        
        # Verify it's no longer in the list
        get_response = client.get("/api/v1/profile/payment-methods", headers=auth_headers)
        payment_methods = get_response.json()
        
        # Should not find the deleted payment method
        deleted_method = next((pm for pm in payment_methods if pm["id"] == payment_method_id), None)
        assert deleted_method is None
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        response = client.get("/api/v1/profile/me")
        assert response.status_code == 401
        
        response = client.put("/api/v1/profile/me", json={"first_name": "Test"})
        assert response.status_code == 401
        
        response = client.get("/api/v1/profile/payment-methods")
        assert response.status_code == 401


class TestVendorProfileAPI:
    """Test vendor-specific profile API endpoints."""
    
    @pytest.fixture
    def vendor_auth_headers(self, client: TestClient):
        """Create authentication headers for a vendor user."""
        # Create a vendor user
        vendor_data = {
            "email": "vendor@example.com",
            "password": "testpass123",
            "first_name": "Vendor",
            "last_name": "User",
            "role": "vendor"
        }
        
        # Register vendor
        client.post("/api/v1/auth/register", json=vendor_data)
        
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": vendor_data["email"],
            "password": vendor_data["password"]
        })
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        return {"Authorization": f"Bearer {access_token}"}
    
    def test_create_vendor_profile(self, client: TestClient, vendor_auth_headers):
        """Test creating vendor profile."""
        # First create the vendor profile via auth endpoint
        profile_data = {
            "business_name": "Test Business",
            "business_type": "Retail",
            "business_description": "A test business",
            "languages": ["en", "es"],
            "payment_methods": [{"type": "card", "provider": "stripe"}]
        }
        
        response = client.post("/api/v1/auth/vendor-profile", json=profile_data, headers=vendor_auth_headers)
        assert response.status_code == 200
    
    def test_update_vendor_profile(self, client: TestClient, vendor_auth_headers):
        """Test updating vendor profile."""
        # First create the vendor profile
        profile_data = {
            "business_name": "Initial Business",
            "business_type": "Retail"
        }
        
        client.post("/api/v1/auth/vendor-profile", json=profile_data, headers=vendor_auth_headers)
        
        # Update the vendor profile
        update_data = {
            "business_name": "Updated Business Name",
            "business_description": "Updated description",
            "languages": ["en", "hi", "mr"],
            "is_available": True
        }
        
        response = client.put("/api/v1/profile/vendor", json=update_data, headers=vendor_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # The response should be the full user profile with vendor info
        assert "id" in data
        assert "email" in data
    
    def test_customer_cannot_access_vendor_endpoints(self, client: TestClient, auth_headers):
        """Test that customers cannot access vendor-specific endpoints."""
        update_data = {
            "business_name": "Should Fail"
        }
        
        response = client.put("/api/v1/profile/vendor", json=update_data, headers=auth_headers)
        assert response.status_code == 403


class TestCustomerProfileAPI:
    """Test customer-specific profile API endpoints."""
    
    def test_create_customer_profile(self, client: TestClient, auth_headers):
        """Test creating customer profile."""
        response = client.post("/api/v1/profile/customer", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_purchases"] == 0
        assert data["total_spent"] == 0.0
        assert data["preferred_categories"] == []
        assert data["wishlist_items"] == []
    
    def test_get_customer_profile(self, client: TestClient, auth_headers):
        """Test getting customer profile."""
        # First create the profile
        client.post("/api/v1/profile/customer", headers=auth_headers)
        
        # Get the profile
        response = client.get("/api/v1/profile/customer", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "user_id" in data
        assert "total_purchases" in data
    
    def test_update_customer_profile(self, client: TestClient, auth_headers):
        """Test updating customer profile."""
        # First create the profile
        client.post("/api/v1/profile/customer", headers=auth_headers)
        
        # Update the profile
        update_data = {
            "preferred_categories": ["electronics", "books"],
            "wishlist_items": ["item1", "item2"],
            "favorite_vendors": ["vendor1"]
        }
        
        response = client.put("/api/v1/profile/customer", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["preferred_categories"] == ["electronics", "books"]
        assert len(data["wishlist_items"]) == 2
        assert len(data["favorite_vendors"]) == 1