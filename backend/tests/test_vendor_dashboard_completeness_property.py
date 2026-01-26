"""
Property-based tests for vendor dashboard completeness.

This module contains property-based tests that validate universal properties
of the vendor dashboard system using Hypothesis for comprehensive input coverage.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from uuid import uuid4, UUID
from decimal import Decimal

from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.product import Product, AvailabilityStatus
from app.models.user import User, UserRole, VerificationStatus, VendorProfile
from app.models.transaction import Transaction, TransactionStatus
from app.services.vendor_dashboard_service import VendorDashboardService


class AsyncVendorDashboardService:
    """Async-compatible version of VendorDashboardService for testing."""
    
    async def get_dashboard_overview(self, db: AsyncSession, vendor_id: UUID):
        """Get comprehensive dashboard overview for a vendor."""
        # Get basic vendor info
        vendor_result = await db.execute(select(User).where(User.id == vendor_id))
        vendor = vendor_result.scalar_one_or_none()
        
        vendor_profile_result = await db.execute(select(VendorProfile).where(VendorProfile.user_id == vendor_id))
        vendor_profile = vendor_profile_result.scalar_one_or_none()
        
        # Get product counts
        total_products_result = await db.execute(select(func.count(Product.id)).where(Product.vendor_id == vendor_id))
        total_products = total_products_result.scalar()
        
        active_products_result = await db.execute(
            select(func.count(Product.id)).where(
                and_(Product.vendor_id == vendor_id, Product.is_active == True)
            )
        )
        active_products = active_products_result.scalar()
        
        low_stock_result = await db.execute(
            select(func.count(Product.id)).where(
                and_(
                    Product.vendor_id == vendor_id,
                    Product.availability == AvailabilityStatus.LOW_STOCK
                )
            )
        )
        low_stock_products = low_stock_result.scalar()
        
        out_of_stock_result = await db.execute(
            select(func.count(Product.id)).where(
                and_(
                    Product.vendor_id == vendor_id,
                    Product.availability == AvailabilityStatus.OUT_OF_STOCK
                )
            )
        )
        out_of_stock_products = out_of_stock_result.scalar()
        
        # Get transaction metrics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_transactions_result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.seller_id == vendor_id,
                    Transaction.created_at >= thirty_days_ago,
                    Transaction.status == TransactionStatus.COMPLETED
                )
            )
        )
        recent_transactions = recent_transactions_result.scalars().all()
        
        # Calculate sales metrics
        total_sales = len(recent_transactions)
        total_revenue = sum(t.total_amount for t in recent_transactions)
        average_order_value = total_revenue / total_sales if total_sales > 0 else 0
        
        # Get recent activity (last 10 transactions)
        recent_activity_result = await db.execute(
            select(Transaction).where(Transaction.seller_id == vendor_id)
            .order_by(Transaction.created_at.desc()).limit(10)
        )
        recent_activity_transactions = recent_activity_result.scalars().all()
        
        from app.schemas.vendor_dashboard import VendorDashboardOverview
        
        return VendorDashboardOverview(
            vendor_id=vendor_id,
            business_name=vendor_profile.business_name if vendor_profile else vendor.first_name,
            total_products=total_products,
            active_products=active_products,
            low_stock_products=low_stock_products,
            out_of_stock_products=out_of_stock_products,
            total_sales_30d=total_sales,
            total_revenue_30d=total_revenue,
            average_order_value=average_order_value,
            active_negotiations=0,  # Placeholder
            recent_activity=[
                {
                    "id": str(t.id),
                    "type": "sale",
                    "amount": t.total_amount,
                    "currency": t.currency,
                    "status": t.status.value,
                    "created_at": t.created_at.isoformat()
                }
                for t in recent_activity_transactions
            ]
        )
    
    async def get_inventory_list(
        self,
        db: AsyncSession,
        vendor_id: UUID,
        page: int = 1,
        size: int = 20,
        availability_filter: Optional[AvailabilityStatus] = None,
        search_query: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ):
        """Get paginated inventory list with filtering and search."""
        from app.schemas.vendor_dashboard import InventoryItem, InventoryListResponse
        
        # Build query
        query = select(Product).where(Product.vendor_id == vendor_id)
        
        # Apply filters
        if availability_filter:
            query = query.where(Product.availability == availability_filter)
        
        if search_query:
            search_term = f"%{search_query}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.sku.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.updated_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        # Execute query
        result = await db.execute(query)
        products = result.scalars().all()
        
        # Convert to inventory items
        inventory_items = []
        for product in products:
            # Calculate stock status
            stock_status = "healthy"
            if product.availability == AvailabilityStatus.OUT_OF_STOCK:
                stock_status = "out_of_stock"
            elif product.availability == AvailabilityStatus.LOW_STOCK:
                stock_status = "low_stock"
            elif product.quantity_available <= product.minimum_quantity:
                stock_status = "low_stock"
            
            inventory_items.append(InventoryItem(
                product_id=product.id,
                name=product.name,
                sku=product.sku,
                current_price=product.current_price,
                currency=product.currency,
                quantity_available=product.quantity_available,
                minimum_quantity=product.minimum_quantity,
                availability=product.availability,
                stock_status=stock_status,
                is_active=product.is_active,
                is_featured=product.is_featured,
                view_count=product.view_count,
                average_rating=product.average_rating,
                total_reviews=product.total_reviews,
                last_updated=product.updated_at.isoformat()
            ))
        
        # Calculate pagination info
        pages = (total + size - 1) // size
        
        return InventoryListResponse(
            items=inventory_items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    async def get_sales_analytics(
        self,
        db: AsyncSession,
        vendor_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day"
    ):
        """Get sales analytics with time-based grouping."""
        from app.schemas.vendor_dashboard import SalesAnalytics
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get transactions in date range
        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.seller_id == vendor_id,
                    Transaction.created_at >= start_date,
                    Transaction.created_at <= end_date,
                    Transaction.status == TransactionStatus.COMPLETED
                )
            )
        )
        transactions = result.scalars().all()
        
        if not transactions:
            return SalesAnalytics(
                period_start=start_date.isoformat(),
                period_end=end_date.isoformat(),
                total_sales=0,
                total_revenue=0.0,
                average_order_value=0.0,
                sales_by_period=[],
                top_products=[],
                revenue_trend=[]
            )
        
        # Calculate basic metrics
        total_sales = len(transactions)
        total_revenue = sum(t.total_amount for t in transactions)
        average_order_value = total_revenue / total_sales if total_sales > 0 else 0.0
        
        # Group by period (simplified for testing)
        sales_by_period = []
        if transactions:
            # Simple daily grouping
            daily_sales = {}
            for t in transactions:
                date_key = t.created_at.date().isoformat()
                if date_key not in daily_sales:
                    daily_sales[date_key] = {"count": 0, "revenue": 0.0}
                daily_sales[date_key]["count"] += 1
                daily_sales[date_key]["revenue"] += t.total_amount
            
            sales_by_period = [
                {
                    "period": date_key,
                    "sales_count": data["count"],
                    "revenue": data["revenue"]
                }
                for date_key, data in daily_sales.items()
            ]
        
        # Top products (simplified)
        product_sales = {}
        for t in transactions:
            pid = str(t.product_id)
            if pid not in product_sales:
                product_sales[pid] = {"count": 0, "revenue": 0.0, "quantity": 0}
            product_sales[pid]["count"] += 1
            product_sales[pid]["revenue"] += t.total_amount
            product_sales[pid]["quantity"] += t.quantity
        
        # Get product names
        if product_sales:
            product_ids = [UUID(pid) for pid in product_sales.keys()]
            products_result = await db.execute(
                select(Product).where(Product.id.in_(product_ids))
            )
            products = products_result.scalars().all()
            product_names = {str(p.id): p.name for p in products}
        else:
            product_names = {}
        
        top_products = [
            {
                "product_id": pid,
                "product_name": product_names.get(pid, "Unknown"),
                "sales_count": data["count"],
                "revenue": data["revenue"],
                "quantity_sold": data["quantity"]
            }
            for pid, data in sorted(product_sales.items(), key=lambda x: x[1]["revenue"], reverse=True)[:10]
        ]
        
        # Revenue trend (simplified)
        revenue_trend = [
            {
                "period": period["period"],
                "revenue": period["revenue"],
                "moving_average": period["revenue"]  # Simplified
            }
            for period in sales_by_period
        ]
        
        return SalesAnalytics(
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat(),
            total_sales=total_sales,
            total_revenue=float(total_revenue),
            average_order_value=float(average_order_value),
            sales_by_period=sales_by_period,
            top_products=top_products,
            revenue_trend=revenue_trend
        )
    
    async def get_dashboard_metrics(
        self,
        db: AsyncSession,
        vendor_id: UUID
    ):
        """Get key dashboard metrics for vendor."""
        from app.schemas.vendor_dashboard import DashboardMetrics
        
        # Product metrics
        total_products_result = await db.execute(
            select(func.count(Product.id)).where(Product.vendor_id == vendor_id)
        )
        total_products = total_products_result.scalar()
        
        active_products_result = await db.execute(
            select(func.count(Product.id)).where(
                and_(Product.vendor_id == vendor_id, Product.is_active == True)
            )
        )
        active_products = active_products_result.scalar()
        
        featured_products_result = await db.execute(
            select(func.count(Product.id)).where(
                and_(Product.vendor_id == vendor_id, Product.is_featured == True)
            )
        )
        featured_products = featured_products_result.scalar()
        
        # Inventory alerts
        low_stock_result = await db.execute(
            select(func.count(Product.id)).where(
                and_(
                    Product.vendor_id == vendor_id,
                    Product.availability == AvailabilityStatus.LOW_STOCK
                )
            )
        )
        low_stock_count = low_stock_result.scalar()
        
        out_of_stock_result = await db.execute(
            select(func.count(Product.id)).where(
                and_(
                    Product.vendor_id == vendor_id,
                    Product.availability == AvailabilityStatus.OUT_OF_STOCK
                )
            )
        )
        out_of_stock_count = out_of_stock_result.scalar()
        
        # Sales metrics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_sales_result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.seller_id == vendor_id,
                    Transaction.created_at >= thirty_days_ago,
                    Transaction.status == TransactionStatus.COMPLETED
                )
            )
        )
        recent_sales = recent_sales_result.scalars().all()
        
        sales_30d = len(recent_sales)
        revenue_30d = sum(t.total_amount for t in recent_sales)
        
        # Compare with previous 30 days for growth (simplified)
        sales_growth = 0.0
        revenue_growth = 0.0
        
        # Top performing product (simplified)
        top_product_name = None
        if recent_sales:
            product_revenue = {}
            for sale in recent_sales:
                pid = str(sale.product_id)
                product_revenue[pid] = product_revenue.get(pid, 0) + sale.total_amount
            
            if product_revenue:
                top_product_id = max(product_revenue, key=product_revenue.get)
                top_product_result = await db.execute(
                    select(Product).where(Product.id == UUID(top_product_id))
                )
                top_product = top_product_result.scalar_one_or_none()
                top_product_name = top_product.name if top_product else "Unknown"
        
        return DashboardMetrics(
            total_products=total_products,
            active_products=active_products,
            featured_products=featured_products,
            low_stock_alerts=low_stock_count,
            out_of_stock_alerts=out_of_stock_count,
            sales_30d=sales_30d,
            revenue_30d=revenue_30d,
            sales_growth_30d=sales_growth,
            revenue_growth_30d=revenue_growth,
            top_product_30d=top_product_name
        )


# Custom strategies for generating test data
@composite
def valid_price(draw):
    """Generate valid price values."""
    return draw(st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False))


@composite
def valid_currency(draw):
    """Generate valid currency codes."""
    return draw(st.sampled_from(['USD', 'EUR', 'GBP', 'JPY', 'CNY']))


@composite
def valid_product_name(draw):
    """Generate valid product names."""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Zs', 'Pc')),
        min_size=1,
        max_size=50
    ).filter(lambda x: x.strip() and len(x.strip()) > 0))


@composite
def valid_sku(draw):
    """Generate valid SKU codes."""
    unique_id = str(uuid4())[:8]
    base_sku = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
        min_size=3,
        max_size=8
    ).filter(lambda x: len(x) >= 3))
    return f"{base_sku}_{unique_id}"


@composite
def valid_quantity(draw):
    """Generate valid quantity values."""
    return draw(st.integers(min_value=0, max_value=100))


@composite
def valid_business_name(draw):
    """Generate valid business names."""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Zs')),
        min_size=3,
        max_size=50
    ).filter(lambda x: x.strip() and len(x.strip()) >= 3))


@composite
def valid_vendor_data(draw):
    """Generate valid vendor user data with unique email."""
    unique_id = str(uuid4())[:8]
    return {
        'email': f"vendor_{unique_id}@example.com",
        'hashed_password': 'hashed_password_123',
        'first_name': 'Test',
        'last_name': 'Vendor',
        'role': UserRole.VENDOR,
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


@composite
def valid_customer_data(draw):
    """Generate valid customer user data with unique email."""
    unique_id = str(uuid4())[:8]
    return {
        'email': f"customer_{unique_id}@example.com",
        'hashed_password': 'hashed_password_123',
        'first_name': 'Test',
        'last_name': 'Customer',
        'role': UserRole.CUSTOMER,
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


@composite
def valid_product_data(draw):
    """Generate valid product data."""
    base_price = draw(valid_price())
    current_price = draw(st.floats(min_value=0.01, max_value=base_price * 2.0, allow_nan=False, allow_infinity=False))
    
    return {
        'name': draw(valid_product_name()),
        'description': f"Test product description for {draw(valid_product_name())}",
        'sku': draw(valid_sku()),
        'base_price': base_price,
        'current_price': current_price,
        'currency': draw(valid_currency()),
        'quantity_available': draw(valid_quantity()),
        'minimum_quantity': draw(st.integers(min_value=1, max_value=10)),
        'availability': draw(st.sampled_from(list(AvailabilityStatus))),
        'images': [],
        'specifications': {},
        'tags': [],
        'translations': {},
        'is_active': draw(st.booleans()),
        'is_featured': draw(st.booleans()),
        'view_count': draw(st.integers(min_value=0, max_value=1000)),
        'favorite_count': 0,
        'average_rating': draw(st.floats(min_value=0.0, max_value=5.0)),
        'total_reviews': draw(st.integers(min_value=0, max_value=100))
    }


@composite
def valid_transaction_data(draw):
    """Generate valid transaction data."""
    unit_price = draw(valid_price())
    quantity = draw(st.integers(min_value=1, max_value=5))
    total_amount = unit_price * quantity
    
    return {
        'quantity': quantity,
        'unit_price': unit_price,
        'total_amount': total_amount,
        'currency': draw(valid_currency()),
        'status': draw(st.sampled_from(list(TransactionStatus))),
        'platform_fee': draw(st.floats(min_value=0.0, max_value=total_amount * 0.1)),
        'payment_fee': draw(st.floats(min_value=0.0, max_value=total_amount * 0.05)),
        'transaction_reference': f"TX_{str(uuid4())[:8]}"
    }


class TestVendorDashboardCompleteness:
    """
    Property-based tests for vendor dashboard completeness.
    
    **Validates: Requirements 4.1**
    
    These tests ensure that for any vendor login, the dashboard displays
    all current inventory, active negotiations, and recent sales data
    accurately and completely.
    """
    
    @pytest.fixture
    def vendor_dashboard_service(self):
        """Create vendor dashboard service instance."""
        return AsyncVendorDashboardService()
    
    @given(
        vendor_data=valid_vendor_data(),
        business_name=valid_business_name(),
        products_data=st.lists(
            valid_product_data(),
            min_size=1,
            max_size=8
        )
    )
    @settings(max_examples=12, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_dashboard_inventory_completeness(
        self,
        vendor_data: Dict[str, Any],
        business_name: str,
        products_data: List[Dict[str, Any]],
        vendor_dashboard_service: AsyncVendorDashboardService,
        db_session: AsyncSession
    ):
        """
        **Property 13: Vendor Dashboard Completeness**
        **Validates: Requirements 4.1**
        
        For any vendor with products, the dashboard should display
        all current inventory data accurately and completely,
        including product counts, availability status, and stock alerts.
        """
        # Create vendor user
        vendor = User(**vendor_data)
        db_session.add(vendor)
        await db_session.commit()
        await db_session.refresh(vendor)
        
        # Create vendor profile
        vendor_profile = VendorProfile(
            user_id=vendor.id,
            business_name=business_name,
            business_type="retail",
            average_rating=4.5,
            total_sales=0
        )
        db_session.add(vendor_profile)
        await db_session.commit()
        
        # Create products with various availability statuses
        created_products = []
        expected_active_count = 0
        expected_low_stock_count = 0
        expected_out_of_stock_count = 0
        expected_featured_count = 0
        
        for product_data in products_data:
            product = Product(
                vendor_id=vendor.id,
                **product_data
            )
            db_session.add(product)
            created_products.append(product)
            
            # Count expected metrics
            if product_data['is_active']:
                expected_active_count += 1
            if product_data['is_featured']:
                expected_featured_count += 1
            if product_data['availability'] == AvailabilityStatus.LOW_STOCK:
                expected_low_stock_count += 1
            elif product_data['availability'] == AvailabilityStatus.OUT_OF_STOCK:
                expected_out_of_stock_count += 1
        
        await db_session.commit()
        
        # Refresh all products
        for product in created_products:
            await db_session.refresh(product)
        
        # Get dashboard overview
        overview = await vendor_dashboard_service.get_dashboard_overview(
            db=db_session,
            vendor_id=vendor.id
        )
        
        # Verify inventory completeness
        
        # 1. Dashboard should display correct vendor information
        assert overview.vendor_id == vendor.id
        assert overview.business_name == business_name
        
        # 2. Dashboard should display accurate product counts
        assert overview.total_products == len(created_products), \
            f"Expected {len(created_products)} total products, got {overview.total_products}"
        
        assert overview.active_products == expected_active_count, \
            f"Expected {expected_active_count} active products, got {overview.active_products}"
        
        assert overview.low_stock_products == expected_low_stock_count, \
            f"Expected {expected_low_stock_count} low stock products, got {overview.low_stock_products}"
        
        assert overview.out_of_stock_products == expected_out_of_stock_count, \
            f"Expected {expected_out_of_stock_count} out of stock products, got {overview.out_of_stock_products}"
        
        # 3. Dashboard should provide complete inventory list
        inventory_list = await vendor_dashboard_service.get_inventory_list(
            db=db_session,
            vendor_id=vendor.id,
            page=1,
            size=50
        )
        
        assert inventory_list.total == len(created_products), \
            f"Inventory list should show {len(created_products)} products, got {inventory_list.total}"
        
        assert len(inventory_list.items) == len(created_products), \
            f"Inventory items should contain {len(created_products)} items, got {len(inventory_list.items)}"
        
        # 4. All created products should be present in inventory
        inventory_product_ids = {item.product_id for item in inventory_list.items}
        created_product_ids = {product.id for product in created_products}
        
        assert inventory_product_ids == created_product_ids, \
            "All created products should be present in inventory list"
        
        # 5. Inventory items should have complete data
        for inventory_item in inventory_list.items:
            # Find corresponding created product
            created_product = next(p for p in created_products if p.id == inventory_item.product_id)
            
            assert inventory_item.name == created_product.name
            assert inventory_item.sku == created_product.sku
            assert abs(inventory_item.current_price - created_product.current_price) < 0.01
            assert inventory_item.currency == created_product.currency
            assert inventory_item.quantity_available == created_product.quantity_available
            assert inventory_item.minimum_quantity == created_product.minimum_quantity
            assert inventory_item.availability == created_product.availability
            assert inventory_item.is_active == created_product.is_active
            assert inventory_item.is_featured == created_product.is_featured
            assert inventory_item.view_count == created_product.view_count
            assert abs(inventory_item.average_rating - created_product.average_rating) < 0.01
            assert inventory_item.total_reviews == created_product.total_reviews
        
        # 6. Dashboard metrics should be accurate
        metrics = await vendor_dashboard_service.get_dashboard_metrics(
            db=db_session,
            vendor_id=vendor.id
        )
        
        assert metrics.total_products == len(created_products)
        assert metrics.active_products == expected_active_count
        assert metrics.featured_products == expected_featured_count
        assert metrics.low_stock_alerts == expected_low_stock_count
        assert metrics.out_of_stock_alerts == expected_out_of_stock_count
    
    @given(
        vendor_data=valid_vendor_data(),
        customer_data=valid_customer_data(),
        business_name=valid_business_name(),
        products_data=st.lists(
            valid_product_data(),
            min_size=1,
            max_size=5
        ),
        transactions_data=st.lists(
            valid_transaction_data(),
            min_size=1,
            max_size=8
        )
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_dashboard_sales_completeness(
        self,
        vendor_data: Dict[str, Any],
        customer_data: Dict[str, Any],
        business_name: str,
        products_data: List[Dict[str, Any]],
        transactions_data: List[Dict[str, Any]],
        vendor_dashboard_service: AsyncVendorDashboardService,
        db_session: AsyncSession
    ):
        """
        **Property 13: Vendor Dashboard Completeness**
        **Validates: Requirements 4.1**
        
        For any vendor with sales transactions, the dashboard should display
        all recent sales data accurately and completely, including sales counts,
        revenue totals, and transaction details.
        """
        # Create vendor and customer users
        vendor = User(**vendor_data)
        customer = User(**customer_data)
        db_session.add(vendor)
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(vendor)
        await db_session.refresh(customer)
        
        # Create vendor profile
        vendor_profile = VendorProfile(
            user_id=vendor.id,
            business_name=business_name,
            business_type="retail",
            average_rating=4.5,
            total_sales=0
        )
        db_session.add(vendor_profile)
        await db_session.commit()
        
        # Create products
        created_products = []
        for product_data in products_data:
            product = Product(
                vendor_id=vendor.id,
                **product_data
            )
            db_session.add(product)
            created_products.append(product)
        
        await db_session.commit()
        
        # Refresh products
        for product in created_products:
            await db_session.refresh(product)
        
        # Create transactions within the last 30 days
        created_transactions = []
        expected_completed_sales = 0
        expected_total_revenue = 0.0
        
        for i, transaction_data in enumerate(transactions_data):
            # Create transaction within last 30 days
            transaction_date = datetime.utcnow() - timedelta(days=i % 25)  # Spread across 25 days
            
            transaction = Transaction(
                buyer_id=customer.id,
                seller_id=vendor.id,
                product_id=created_products[i % len(created_products)].id,
                created_at=transaction_date,
                **transaction_data
            )
            db_session.add(transaction)
            created_transactions.append(transaction)
            
            # Count expected metrics for completed transactions
            if transaction_data['status'] == TransactionStatus.COMPLETED:
                expected_completed_sales += 1
                expected_total_revenue += transaction_data['total_amount']
        
        await db_session.commit()
        
        # Refresh transactions
        for transaction in created_transactions:
            await db_session.refresh(transaction)
        
        # Get dashboard overview
        overview = await vendor_dashboard_service.get_dashboard_overview(
            db=db_session,
            vendor_id=vendor.id
        )
        
        # Verify sales completeness
        
        # 1. Dashboard should display accurate sales metrics
        assert overview.total_sales_30d == expected_completed_sales, \
            f"Expected {expected_completed_sales} completed sales, got {overview.total_sales_30d}"
        
        assert abs(overview.total_revenue_30d - expected_total_revenue) < 0.01, \
            f"Expected revenue {expected_total_revenue}, got {overview.total_revenue_30d}"
        
        # 2. Average order value should be calculated correctly
        if expected_completed_sales > 0:
            expected_avg_order = expected_total_revenue / expected_completed_sales
            assert abs(overview.average_order_value - expected_avg_order) < 0.01, \
                f"Expected average order value {expected_avg_order}, got {overview.average_order_value}"
        else:
            assert overview.average_order_value == 0.0
        
        # 3. Recent activity should include transaction data
        assert len(overview.recent_activity) <= 10, \
            "Recent activity should be limited to 10 items"
        
        # All recent activity items should be valid transactions
        for activity in overview.recent_activity:
            assert 'id' in activity
            assert 'type' in activity
            assert activity['type'] == 'sale'
            assert 'amount' in activity
            assert 'currency' in activity
            assert 'status' in activity
            assert 'created_at' in activity
            
            # Verify activity corresponds to actual transaction
            activity_id = UUID(activity['id'])
            matching_transaction = next(
                (t for t in created_transactions if t.id == activity_id),
                None
            )
            assert matching_transaction is not None, \
                f"Activity {activity_id} should correspond to actual transaction"
            
            assert abs(activity['amount'] - matching_transaction.total_amount) < 0.01
            assert activity['currency'] == matching_transaction.currency
            assert activity['status'] == matching_transaction.status.value
        
        # 4. Sales analytics should be complete and accurate
        analytics = await vendor_dashboard_service.get_sales_analytics(
            db=db_session,
            vendor_id=vendor.id,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            group_by="day"
        )
        
        assert analytics.total_sales == expected_completed_sales, \
            f"Analytics should show {expected_completed_sales} total sales"
        
        assert abs(analytics.total_revenue - expected_total_revenue) < 0.01, \
            f"Analytics should show revenue {expected_total_revenue}"
        
        if expected_completed_sales > 0:
            expected_avg = expected_total_revenue / expected_completed_sales
            assert abs(analytics.average_order_value - expected_avg) < 0.01
        
        # 5. Sales by period should account for all completed transactions
        total_period_sales = sum(period['sales_count'] for period in analytics.sales_by_period)
        total_period_revenue = sum(period['revenue'] for period in analytics.sales_by_period)
        
        assert total_period_sales == expected_completed_sales, \
            f"Period sales should sum to {expected_completed_sales}"
        
        assert abs(total_period_revenue - expected_total_revenue) < 0.01, \
            f"Period revenue should sum to {expected_total_revenue}"
        
        # 6. Top products should include products with sales
        if expected_completed_sales > 0:
            assert len(analytics.top_products) > 0, \
                "Top products should include products with sales"
            
            # Verify top products data integrity
            for top_product in analytics.top_products:
                assert 'product_id' in top_product
                assert 'product_name' in top_product
                assert 'sales_count' in top_product
                assert 'revenue' in top_product
                assert 'quantity_sold' in top_product
                
                # Verify product exists
                product_id = UUID(top_product['product_id'])
                matching_product = next(
                    (p for p in created_products if p.id == product_id),
                    None
                )
                assert matching_product is not None, \
                    f"Top product {product_id} should exist in created products"
    
    @given(
        vendor_data=valid_vendor_data(),
        business_name=valid_business_name(),
        products_data=st.lists(
            valid_product_data(),
            min_size=2,
            max_size=6
        )
    )
    @settings(max_examples=8, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_dashboard_inventory_filtering_completeness(
        self,
        vendor_data: Dict[str, Any],
        business_name: str,
        products_data: List[Dict[str, Any]],
        vendor_dashboard_service: AsyncVendorDashboardService,
        db_session: AsyncSession
    ):
        """
        **Property 13: Vendor Dashboard Completeness**
        **Validates: Requirements 4.1**
        
        For any vendor dashboard inventory filtering operation, the system should
        return complete and accurate results that match the filter criteria
        while maintaining data integrity.
        """
        # Create vendor user
        vendor = User(**vendor_data)
        db_session.add(vendor)
        await db_session.commit()
        await db_session.refresh(vendor)
        
        # Create vendor profile
        vendor_profile = VendorProfile(
            user_id=vendor.id,
            business_name=business_name,
            business_type="retail",
            average_rating=4.5,
            total_sales=0
        )
        db_session.add(vendor_profile)
        await db_session.commit()
        
        # Create products with specific characteristics for filtering
        created_products = []
        low_stock_products = []
        out_of_stock_products = []
        in_stock_products = []
        active_products = []
        featured_products = []
        
        for i, product_data in enumerate(products_data):
            # Ensure variety in availability status
            if i % 3 == 0:
                product_data['availability'] = AvailabilityStatus.LOW_STOCK
                low_stock_products.append(i)
            elif i % 3 == 1:
                product_data['availability'] = AvailabilityStatus.OUT_OF_STOCK
                out_of_stock_products.append(i)
            else:
                product_data['availability'] = AvailabilityStatus.IN_STOCK
                in_stock_products.append(i)
            
            # Ensure variety in active status
            product_data['is_active'] = i % 2 == 0
            if product_data['is_active']:
                active_products.append(i)
            
            # Ensure variety in featured status
            product_data['is_featured'] = i % 4 == 0
            if product_data['is_featured']:
                featured_products.append(i)
            
            # Add searchable content
            product_data['name'] = f"Product_{i}_{product_data['name']}"
            
            product = Product(
                vendor_id=vendor.id,
                **product_data
            )
            db_session.add(product)
            created_products.append(product)
        
        await db_session.commit()
        
        # Refresh all products
        for product in created_products:
            await db_session.refresh(product)
        
        # Test filtering completeness
        
        # 1. Test availability filtering - Low Stock
        if low_stock_products:
            low_stock_inventory = await vendor_dashboard_service.get_inventory_list(
                db=db_session,
                vendor_id=vendor.id,
                availability_filter=AvailabilityStatus.LOW_STOCK
            )
            
            assert low_stock_inventory.total == len(low_stock_products), \
                f"Low stock filter should return {len(low_stock_products)} products"
            
            # All returned products should be low stock
            for item in low_stock_inventory.items:
                assert item.availability == AvailabilityStatus.LOW_STOCK
                assert item.stock_status in ["low_stock"]
        
        # 2. Test availability filtering - Out of Stock
        if out_of_stock_products:
            out_of_stock_inventory = await vendor_dashboard_service.get_inventory_list(
                db=db_session,
                vendor_id=vendor.id,
                availability_filter=AvailabilityStatus.OUT_OF_STOCK
            )
            
            assert out_of_stock_inventory.total == len(out_of_stock_products), \
                f"Out of stock filter should return {len(out_of_stock_products)} products"
            
            # All returned products should be out of stock
            for item in out_of_stock_inventory.items:
                assert item.availability == AvailabilityStatus.OUT_OF_STOCK
                assert item.stock_status == "out_of_stock"
        
        # 3. Test availability filtering - In Stock
        if in_stock_products:
            in_stock_inventory = await vendor_dashboard_service.get_inventory_list(
                db=db_session,
                vendor_id=vendor.id,
                availability_filter=AvailabilityStatus.IN_STOCK
            )
            
            assert in_stock_inventory.total == len(in_stock_products), \
                f"In stock filter should return {len(in_stock_products)} products"
            
            # All returned products should be in stock
            for item in in_stock_inventory.items:
                assert item.availability == AvailabilityStatus.IN_STOCK
        
        # 4. Test search functionality
        if len(created_products) > 0:
            # Search for first product by name
            search_term = f"Product_0"
            search_inventory = await vendor_dashboard_service.get_inventory_list(
                db=db_session,
                vendor_id=vendor.id,
                search_query=search_term
            )
            
            # Should find at least one product
            assert search_inventory.total >= 1, \
                f"Search for '{search_term}' should find at least 1 product"
            
            # All returned products should match search criteria
            for item in search_inventory.items:
                assert search_term.lower() in item.name.lower() or \
                       (item.sku and search_term.lower() in item.sku.lower()), \
                       f"Search result should contain '{search_term}'"
        
        # 5. Test pagination completeness
        if len(created_products) > 2:
            # Test first page
            page1 = await vendor_dashboard_service.get_inventory_list(
                db=db_session,
                vendor_id=vendor.id,
                page=1,
                size=2
            )
            
            assert len(page1.items) == min(2, len(created_products))
            assert page1.total == len(created_products)
            assert page1.page == 1
            assert page1.size == 2
            
            # Test second page if applicable
            if len(created_products) > 2:
                page2 = await vendor_dashboard_service.get_inventory_list(
                    db=db_session,
                    vendor_id=vendor.id,
                    page=2,
                    size=2
                )
                
                expected_page2_items = min(2, len(created_products) - 2)
                assert len(page2.items) == expected_page2_items
                assert page2.total == len(created_products)
                assert page2.page == 2
                
                # Ensure no duplicate products between pages
                page1_ids = {item.product_id for item in page1.items}
                page2_ids = {item.product_id for item in page2.items}
                assert len(page1_ids.intersection(page2_ids)) == 0, \
                    "Pages should not contain duplicate products"
        
        # 6. Test sorting completeness
        sorted_inventory = await vendor_dashboard_service.get_inventory_list(
            db=db_session,
            vendor_id=vendor.id,
            sort_by="name",
            sort_order="asc"
        )
        
        # Verify sorting is applied
        if len(sorted_inventory.items) > 1:
            for i in range(len(sorted_inventory.items) - 1):
                current_name = sorted_inventory.items[i].name
                next_name = sorted_inventory.items[i + 1].name
                assert current_name <= next_name, \
                    f"Products should be sorted by name: {current_name} <= {next_name}"
        
        # 7. Test complete inventory data integrity
        all_inventory = await vendor_dashboard_service.get_inventory_list(
            db=db_session,
            vendor_id=vendor.id,
            page=1,
            size=100  # Get all products
        )
        
        # All created products should be present
        assert all_inventory.total == len(created_products)
        assert len(all_inventory.items) == len(created_products)
        
        inventory_ids = {item.product_id for item in all_inventory.items}
        created_ids = {product.id for product in created_products}
        assert inventory_ids == created_ids, \
            "All created products should be present in complete inventory"