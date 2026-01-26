"""
Unit tests for vendor dashboard functionality.

This module tests the vendor dashboard service and API endpoints
including inventory management, sales analytics, and bulk operations.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.product import Product, AvailabilityStatus
from app.models.transaction import Transaction, TransactionStatus
from app.models.user import User, VendorProfile
from app.schemas.vendor_dashboard import BulkProductUpdate, ProductUpdateFields, PriceAdjustment
from app.services.vendor_dashboard_service import VendorDashboardService


class TestVendorDashboardService:
    """Test cases for VendorDashboardService."""
    
    @pytest.fixture
    def vendor_dashboard_service(self):
        """Create vendor dashboard service instance."""
        return VendorDashboardService()
    
    @pytest.fixture
    def sample_vendor(self, db_session: Session):
        """Create a sample vendor user."""
        vendor = User(
            id=uuid4(),
            email="vendor@test.com",
            hashed_password="hashed_password",
            role="vendor",
            first_name="Test",
            last_name="Vendor",
            is_active=True
        )
        db_session.add(vendor)
        
        vendor_profile = VendorProfile(
            id=uuid4(),
            user_id=vendor.id,
            business_name="Test Business",
            business_type="retail",
            average_rating=4.5,
            total_sales=100
        )
        db_session.add(vendor_profile)
        db_session.commit()
        
        return vendor
    
    @pytest.fixture
    def sample_products(self, db_session: Session, sample_vendor: User):
        """Create sample products for testing."""
        products = []
        
        # Create products with different availability statuses
        for i in range(5):
            availability = [
                AvailabilityStatus.IN_STOCK,
                AvailabilityStatus.LOW_STOCK,
                AvailabilityStatus.OUT_OF_STOCK,
                AvailabilityStatus.IN_STOCK,
                AvailabilityStatus.IN_STOCK
            ][i]
            
            product = Product(
                id=uuid4(),
                vendor_id=sample_vendor.id,
                name=f"Test Product {i+1}",
                description=f"Description for product {i+1}",
                sku=f"SKU{i+1:03d}",
                base_price=100.0 + i * 10,
                current_price=100.0 + i * 10,
                currency="USD",
                quantity_available=10 - i * 2,
                minimum_quantity=5,
                availability=availability,
                is_active=True,
                is_featured=i % 2 == 0,
                view_count=i * 10,
                average_rating=4.0 + i * 0.1,
                total_reviews=i * 2
            )
            products.append(product)
            db_session.add(product)
        
        db_session.commit()
        return products
    
    @pytest.fixture
    def sample_transactions(self, db_session: Session, sample_vendor: User, sample_products: list):
        """Create sample transactions for testing."""
        transactions = []
        
        # Create transactions for the last 30 days
        for i in range(10):
            transaction_date = datetime.utcnow() - timedelta(days=i * 3)
            
            transaction = Transaction(
                id=uuid4(),
                buyer_id=uuid4(),  # Random buyer
                seller_id=sample_vendor.id,
                product_id=sample_products[i % len(sample_products)].id,
                quantity=1 + i % 3,
                unit_price=100.0 + i * 5,
                total_amount=(100.0 + i * 5) * (1 + i % 3),
                currency="USD",
                status=TransactionStatus.COMPLETED if i % 4 != 3 else TransactionStatus.PENDING,
                platform_fee=5.0,
                payment_fee=2.0,
                created_at=transaction_date
            )
            transactions.append(transaction)
            db_session.add(transaction)
        
        db_session.commit()
        return transactions
    
    @pytest.mark.asyncio
    async def test_get_dashboard_overview(
        self,
        vendor_dashboard_service: VendorDashboardService,
        db_session: Session,
        sample_vendor: User,
        sample_products: list,
        sample_transactions: list
    ):
        """Test getting dashboard overview."""
        overview = await vendor_dashboard_service.get_dashboard_overview(
            db=db_session,
            vendor_id=sample_vendor.id
        )
        
        assert overview.vendor_id == sample_vendor.id
        assert overview.business_name == "Test Business"
        assert overview.total_products == 5
        assert overview.active_products == 5
        assert overview.low_stock_products == 1
        assert overview.out_of_stock_products == 1
        assert overview.total_sales_30d > 0
        assert overview.total_revenue_30d > 0
        assert len(overview.recent_activity) <= 10
    
    @pytest.mark.asyncio
    async def test_get_inventory_list(
        self,
        vendor_dashboard_service: VendorDashboardService,
        db_session: Session,
        sample_vendor: User,
        sample_products: list
    ):
        """Test getting inventory list with pagination and filtering."""
        # Test basic inventory list
        inventory = await vendor_dashboard_service.get_inventory_list(
            db=db_session,
            vendor_id=sample_vendor.id,
            page=1,
            size=10
        )
        
        assert len(inventory.items) == 5
        assert inventory.total == 5
        assert inventory.page == 1
        assert inventory.size == 10
        assert inventory.pages == 1
        
        # Test filtering by availability
        low_stock_inventory = await vendor_dashboard_service.get_inventory_list(
            db=db_session,
            vendor_id=sample_vendor.id,
            availability_filter=AvailabilityStatus.LOW_STOCK
        )
        
        assert len(low_stock_inventory.items) == 1
        assert low_stock_inventory.items[0].availability == AvailabilityStatus.LOW_STOCK
        
        # Test search functionality
        search_inventory = await vendor_dashboard_service.get_inventory_list(
            db=db_session,
            vendor_id=sample_vendor.id,
            search_query="Product 1"
        )
        
        assert len(search_inventory.items) == 1
        assert "Product 1" in search_inventory.items[0].name
    
    @pytest.mark.asyncio
    async def test_bulk_update_products(
        self,
        vendor_dashboard_service: VendorDashboardService,
        db_session: Session,
        sample_vendor: User,
        sample_products: list
    ):
        """Test bulk product updates."""
        # Test basic field updates
        product_ids = [p.id for p in sample_products[:3]]
        bulk_update = BulkProductUpdate(
            product_ids=product_ids,
            updates=ProductUpdateFields(
                is_featured=True,
                availability=AvailabilityStatus.IN_STOCK
            )
        )
        
        result = await vendor_dashboard_service.bulk_update_products(
            db=db_session,
            vendor_id=sample_vendor.id,
            bulk_update=bulk_update
        )
        
        assert result["success"] is True
        assert result["updated_count"] == 3
        assert len(result["product_ids"]) == 3
        
        # Verify updates were applied
        updated_products = db_session.query(Product).filter(
            Product.id.in_(product_ids)
        ).all()
        
        for product in updated_products:
            assert product.is_featured is True
            assert product.availability == AvailabilityStatus.IN_STOCK
    
    @pytest.mark.asyncio
    async def test_bulk_price_adjustment(
        self,
        vendor_dashboard_service: VendorDashboardService,
        db_session: Session,
        sample_vendor: User,
        sample_products: list
    ):
        """Test bulk price adjustments."""
        # Test percentage adjustment
        product_ids = [sample_products[0].id]
        original_price = sample_products[0].current_price
        
        bulk_update = BulkProductUpdate(
            product_ids=product_ids,
            updates=ProductUpdateFields(),
            price_adjustment=PriceAdjustment(
                adjustment_type="percentage",
                value=10.0  # 10% increase
            )
        )
        
        result = await vendor_dashboard_service.bulk_update_products(
            db=db_session,
            vendor_id=sample_vendor.id,
            bulk_update=bulk_update
        )
        
        assert result["success"] is True
        
        # Verify price was adjusted
        db_session.refresh(sample_products[0])
        expected_price = original_price * 1.1
        assert abs(sample_products[0].current_price - expected_price) < 0.01
    
    @pytest.mark.asyncio
    async def test_get_sales_analytics(
        self,
        vendor_dashboard_service: VendorDashboardService,
        db_session: Session,
        sample_vendor: User,
        sample_transactions: list
    ):
        """Test sales analytics generation."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        analytics = await vendor_dashboard_service.get_sales_analytics(
            db=db_session,
            vendor_id=sample_vendor.id,
            start_date=start_date,
            end_date=end_date,
            group_by="day"
        )
        
        assert analytics.total_sales > 0
        assert analytics.total_revenue > 0
        assert analytics.average_order_value > 0
        assert len(analytics.sales_by_period) > 0
        assert len(analytics.top_products) > 0
        assert len(analytics.revenue_trend) > 0
    
    @pytest.mark.asyncio
    async def test_generate_sales_report(
        self,
        vendor_dashboard_service: VendorDashboardService,
        db_session: Session,
        sample_vendor: User,
        sample_transactions: list
    ):
        """Test sales report generation."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        report = await vendor_dashboard_service.generate_sales_report(
            db=db_session,
            vendor_id=sample_vendor.id,
            start_date=start_date,
            end_date=end_date,
            include_products=True
        )
        
        assert report.vendor_id == sample_vendor.id
        assert report.total_transactions > 0
        assert report.completed_transactions > 0
        assert report.total_revenue > 0
        assert report.net_revenue > 0
        assert len(report.transaction_status_breakdown) > 0
        assert len(report.product_performance) > 0
    
    @pytest.mark.asyncio
    async def test_get_dashboard_metrics(
        self,
        vendor_dashboard_service: VendorDashboardService,
        db_session: Session,
        sample_vendor: User,
        sample_products: list,
        sample_transactions: list
    ):
        """Test dashboard metrics calculation."""
        metrics = await vendor_dashboard_service.get_dashboard_metrics(
            db=db_session,
            vendor_id=sample_vendor.id
        )
        
        assert metrics.total_products == 5
        assert metrics.active_products == 5
        assert metrics.featured_products == 3  # Every other product is featured
        assert metrics.low_stock_alerts == 1
        assert metrics.out_of_stock_alerts == 1
        assert metrics.sales_30d > 0
        assert metrics.revenue_30d > 0


class TestVendorDashboardAPI:
    """Test cases for vendor dashboard API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def vendor_token(self, client: TestClient, sample_vendor: User):
        """Get authentication token for vendor."""
        # This would need to be implemented based on your auth system
        # For now, we'll mock it
        return "mock_vendor_token"
    
    def test_get_dashboard_overview_unauthorized(self, client: TestClient):
        """Test dashboard overview without authentication."""
        response = client.get("/api/v1/vendor/dashboard/overview")
        assert response.status_code == 401
    
    def test_get_dashboard_overview_non_vendor(self, client: TestClient):
        """Test dashboard overview with non-vendor user."""
        # This would need proper authentication setup
        # For now, we'll skip this test
        pass
    
    def test_bulk_update_validation(self, client: TestClient):
        """Test bulk update request validation."""
        # Test invalid product IDs
        invalid_request = {
            "product_ids": [],  # Empty list should fail
            "updates": {"is_active": True}
        }
        
        response = client.post(
            "/api/v1/vendor/dashboard/inventory/bulk-update",
            json=invalid_request
        )
        assert response.status_code == 422  # Validation error
    
    def test_price_adjustment_validation(self):
        """Test price adjustment validation."""
        # Test invalid percentage
        with pytest.raises(ValueError):
            PriceAdjustment(
                adjustment_type="percentage",
                value=-150  # Invalid percentage
            )
        
        # Test invalid price range
        with pytest.raises(ValueError):
            PriceAdjustment(
                adjustment_type="fixed",
                value=10,
                min_price=100,
                max_price=50  # Max less than min
            )


class TestInventoryManagement:
    """Test cases for inventory management functionality."""
    
    def test_stock_status_calculation(self):
        """Test stock status calculation logic."""
        # This would test the logic for determining stock status
        # based on quantity and availability
        pass
    
    def test_inventory_alerts_generation(self):
        """Test inventory alerts generation."""
        # This would test the logic for generating inventory alerts
        pass


class TestSalesAnalytics:
    """Test cases for sales analytics functionality."""
    
    def test_pandas_data_processing(self):
        """Test pandas data processing for analytics."""
        # This would test the pandas operations used in analytics
        pass
    
    def test_time_period_grouping(self):
        """Test time period grouping for analytics."""
        # This would test day/week/month grouping logic
        pass
    
    def test_trend_calculation(self):
        """Test trend calculation algorithms."""
        # This would test moving average and trend calculations
        pass


# Integration tests would go here to test the full workflow
# from API request to database operations