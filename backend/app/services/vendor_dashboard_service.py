"""
Vendor dashboard service for business logic.

This module provides business logic for vendor dashboard functionality including
inventory management, sales analytics, bulk operations, and dashboard metrics.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.models.product import Product, AvailabilityStatus
from app.models.transaction import Transaction, TransactionStatus
from app.models.user import User, VendorProfile
from app.schemas.vendor_dashboard import (
    BulkProductUpdate, DashboardMetrics, InventoryItem, InventoryListResponse,
    SalesAnalytics, SalesReport, VendorDashboardOverview
)


class VendorDashboardService:
    """Service class for vendor dashboard operations."""
    
    async def get_dashboard_overview(
        self,
        db: Session,
        vendor_id: UUID
    ) -> VendorDashboardOverview:
        """Get comprehensive dashboard overview for a vendor."""
        
        # Get basic vendor info
        vendor = db.query(User).filter(User.id == vendor_id).first()
        vendor_profile = db.query(VendorProfile).filter(VendorProfile.user_id == vendor_id).first()
        
        # Get product counts
        total_products = db.query(Product).filter(Product.vendor_id == vendor_id).count()
        active_products = db.query(Product).filter(
            and_(Product.vendor_id == vendor_id, Product.is_active == True)
        ).count()
        low_stock_products = db.query(Product).filter(
            and_(
                Product.vendor_id == vendor_id,
                Product.availability == AvailabilityStatus.LOW_STOCK
            )
        ).count()
        out_of_stock_products = db.query(Product).filter(
            and_(
                Product.vendor_id == vendor_id,
                Product.availability == AvailabilityStatus.OUT_OF_STOCK
            )
        ).count()
        
        # Get transaction metrics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_transactions = db.query(Transaction).filter(
            and_(
                Transaction.seller_id == vendor_id,
                Transaction.created_at >= thirty_days_ago,
                Transaction.status == TransactionStatus.COMPLETED
            )
        ).all()
        
        # Calculate sales metrics
        total_sales = len(recent_transactions)
        total_revenue = sum(t.total_amount for t in recent_transactions)
        average_order_value = total_revenue / total_sales if total_sales > 0 else 0
        
        # Get active negotiations count (placeholder - will be implemented when negotiation model is ready)
        active_negotiations = 0
        
        # Get recent activity (last 10 transactions)
        recent_activity = db.query(Transaction).filter(
            Transaction.seller_id == vendor_id
        ).order_by(desc(Transaction.created_at)).limit(10).all()
        
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
            active_negotiations=active_negotiations,
            recent_activity=[
                {
                    "id": str(t.id),
                    "type": "sale",
                    "amount": t.total_amount,
                    "currency": t.currency,
                    "status": t.status.value,
                    "created_at": t.created_at.isoformat()
                }
                for t in recent_activity
            ]
        )
    
    async def get_inventory_list(
        self,
        db: Session,
        vendor_id: UUID,
        page: int = 1,
        size: int = 20,
        availability_filter: Optional[AvailabilityStatus] = None,
        search_query: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> InventoryListResponse:
        """Get paginated inventory list with filtering and search."""
        
        query = db.query(Product).filter(Product.vendor_id == vendor_id)
        
        # Apply filters
        if availability_filter:
            query = query.filter(Product.availability == availability_filter)
        
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.sku.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
        
        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.updated_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        products = query.offset(offset).limit(size).all()
        
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
    
    async def bulk_update_products(
        self,
        db: Session,
        vendor_id: UUID,
        bulk_update: BulkProductUpdate
    ) -> Dict[str, Any]:
        """Perform bulk updates on multiple products."""
        
        # Validate that all products belong to the vendor
        products = db.query(Product).filter(
            and_(
                Product.id.in_(bulk_update.product_ids),
                Product.vendor_id == vendor_id
            )
        ).all()
        
        if len(products) != len(bulk_update.product_ids):
            missing_ids = set(bulk_update.product_ids) - {p.id for p in products}
            return {
                "success": False,
                "message": f"Some products not found or not owned by vendor: {missing_ids}",
                "updated_count": 0
            }
        
        # Apply updates
        updated_count = 0
        update_data = bulk_update.updates.dict(exclude_unset=True)
        
        for product in products:
            for field, value in update_data.items():
                if hasattr(product, field):
                    setattr(product, field, value)
                    updated_count += 1
        
        # Handle price adjustments
        if bulk_update.price_adjustment:
            adjustment = bulk_update.price_adjustment
            for product in products:
                if adjustment.adjustment_type == "percentage":
                    new_price = product.current_price * (1 + adjustment.value / 100)
                elif adjustment.adjustment_type == "fixed":
                    new_price = product.current_price + adjustment.value
                else:  # absolute
                    new_price = adjustment.value
                
                # Apply min/max constraints
                if adjustment.min_price and new_price < adjustment.min_price:
                    new_price = adjustment.min_price
                if adjustment.max_price and new_price > adjustment.max_price:
                    new_price = adjustment.max_price
                
                product.current_price = round(new_price, 2)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully updated {len(products)} products",
            "updated_count": len(products),
            "product_ids": [str(p.id) for p in products]
        }
    
    async def get_sales_analytics(
        self,
        db: Session,
        vendor_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day"
    ) -> SalesAnalytics:
        """Get sales analytics with time-based grouping."""
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get transactions in date range
        transactions = db.query(Transaction).filter(
            and_(
                Transaction.seller_id == vendor_id,
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date,
                Transaction.status == TransactionStatus.COMPLETED
            )
        ).all()
        
        # Convert to pandas DataFrame for analysis
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
        
        df = pd.DataFrame([
            {
                "transaction_id": str(t.id),
                "product_id": str(t.product_id),
                "amount": t.total_amount,
                "quantity": t.quantity,
                "currency": t.currency,
                "created_at": t.created_at
            }
            for t in transactions
        ])
        
        # Group by time period
        df['date'] = pd.to_datetime(df['created_at'])
        
        if group_by == "day":
            df['period'] = df['date'].dt.date
        elif group_by == "week":
            df['period'] = df['date'].dt.to_period('W').dt.start_time.dt.date
        elif group_by == "month":
            df['period'] = df['date'].dt.to_period('M').dt.start_time.dt.date
        else:
            df['period'] = df['date'].dt.date
        
        # Calculate metrics
        total_sales = len(df)
        total_revenue = df['amount'].sum()
        average_order_value = df['amount'].mean()
        
        # Sales by period
        sales_by_period = df.groupby('period').agg({
            'transaction_id': 'count',
            'amount': 'sum'
        }).reset_index()
        
        sales_by_period_data = [
            {
                "period": str(row['period']),
                "sales_count": int(row['transaction_id']),
                "revenue": float(row['amount'])
            }
            for _, row in sales_by_period.iterrows()
        ]
        
        # Top products
        top_products = df.groupby('product_id').agg({
            'transaction_id': 'count',
            'amount': 'sum',
            'quantity': 'sum'
        }).reset_index().sort_values('amount', ascending=False).head(10)
        
        # Get product names for top products
        top_product_ids = [UUID(pid) for pid in top_products['product_id'].tolist()]
        products = db.query(Product).filter(Product.id.in_(top_product_ids)).all()
        product_names = {str(p.id): p.name for p in products}
        
        top_products_data = [
            {
                "product_id": row['product_id'],
                "product_name": product_names.get(row['product_id'], "Unknown"),
                "sales_count": int(row['transaction_id']),
                "revenue": float(row['amount']),
                "quantity_sold": int(row['quantity'])
            }
            for _, row in top_products.iterrows()
        ]
        
        # Revenue trend (simple moving average)
        revenue_trend = sales_by_period.copy()
        revenue_trend['moving_avg'] = revenue_trend['amount'].rolling(window=7, min_periods=1).mean()
        
        revenue_trend_data = [
            {
                "period": str(row['period']),
                "revenue": float(row['amount']),
                "moving_average": float(row['moving_avg'])
            }
            for _, row in revenue_trend.iterrows()
        ]
        
        return SalesAnalytics(
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat(),
            total_sales=total_sales,
            total_revenue=float(total_revenue),
            average_order_value=float(average_order_value),
            sales_by_period=sales_by_period_data,
            top_products=top_products_data,
            revenue_trend=revenue_trend_data
        )
    
    async def generate_sales_report(
        self,
        db: Session,
        vendor_id: UUID,
        start_date: datetime,
        end_date: datetime,
        include_products: bool = True,
        include_customers: bool = False
    ) -> SalesReport:
        """Generate comprehensive sales report."""
        
        # Get transactions in date range
        transactions = db.query(Transaction).filter(
            and_(
                Transaction.seller_id == vendor_id,
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date
            )
        ).all()
        
        # Basic metrics
        total_transactions = len(transactions)
        completed_transactions = [t for t in transactions if t.status == TransactionStatus.COMPLETED]
        total_revenue = sum(t.total_amount for t in completed_transactions)
        total_fees = sum(t.platform_fee + t.payment_fee for t in completed_transactions)
        net_revenue = total_revenue - total_fees
        
        # Transaction status breakdown
        status_counts = {}
        for status in TransactionStatus:
            status_counts[status.value] = len([t for t in transactions if t.status == status])
        
        # Product performance (if requested)
        product_performance = []
        if include_products and completed_transactions:
            df = pd.DataFrame([
                {
                    "product_id": str(t.product_id),
                    "quantity": t.quantity,
                    "revenue": t.total_amount
                }
                for t in completed_transactions
            ])
            
            product_stats = df.groupby('product_id').agg({
                'quantity': 'sum',
                'revenue': 'sum'
            }).reset_index()
            
            # Get product names
            product_ids = [UUID(pid) for pid in product_stats['product_id'].tolist()]
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            product_names = {str(p.id): p.name for p in products}
            
            product_performance = [
                {
                    "product_id": row['product_id'],
                    "product_name": product_names.get(row['product_id'], "Unknown"),
                    "quantity_sold": int(row['quantity']),
                    "revenue": float(row['revenue'])
                }
                for _, row in product_stats.iterrows()
            ]
        
        return SalesReport(
            vendor_id=vendor_id,
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat(),
            total_transactions=total_transactions,
            completed_transactions=len(completed_transactions),
            total_revenue=total_revenue,
            total_fees=total_fees,
            net_revenue=net_revenue,
            transaction_status_breakdown=status_counts,
            product_performance=product_performance,
            generated_at=datetime.utcnow().isoformat()
        )
    
    async def get_dashboard_metrics(
        self,
        db: Session,
        vendor_id: UUID
    ) -> DashboardMetrics:
        """Get key dashboard metrics for vendor."""
        
        # Product metrics
        products_query = db.query(Product).filter(Product.vendor_id == vendor_id)
        total_products = products_query.count()
        active_products = products_query.filter(Product.is_active == True).count()
        featured_products = products_query.filter(Product.is_featured == True).count()
        
        # Inventory alerts
        low_stock_count = products_query.filter(
            Product.availability == AvailabilityStatus.LOW_STOCK
        ).count()
        out_of_stock_count = products_query.filter(
            Product.availability == AvailabilityStatus.OUT_OF_STOCK
        ).count()
        
        # Sales metrics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_sales = db.query(Transaction).filter(
            and_(
                Transaction.seller_id == vendor_id,
                Transaction.created_at >= thirty_days_ago,
                Transaction.status == TransactionStatus.COMPLETED
            )
        ).all()
        
        sales_30d = len(recent_sales)
        revenue_30d = sum(t.total_amount for t in recent_sales)
        
        # Compare with previous 30 days for growth
        sixty_days_ago = datetime.utcnow() - timedelta(days=60)
        previous_sales = db.query(Transaction).filter(
            and_(
                Transaction.seller_id == vendor_id,
                Transaction.created_at >= sixty_days_ago,
                Transaction.created_at < thirty_days_ago,
                Transaction.status == TransactionStatus.COMPLETED
            )
        ).all()
        
        prev_sales_count = len(previous_sales)
        prev_revenue = sum(t.total_amount for t in previous_sales)
        
        # Calculate growth rates
        sales_growth = ((sales_30d - prev_sales_count) / prev_sales_count * 100) if prev_sales_count > 0 else 0
        revenue_growth = ((revenue_30d - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        # Top performing product
        if recent_sales:
            product_revenue = {}
            for sale in recent_sales:
                pid = str(sale.product_id)
                product_revenue[pid] = product_revenue.get(pid, 0) + sale.total_amount
            
            top_product_id = max(product_revenue, key=product_revenue.get)
            top_product = db.query(Product).filter(Product.id == UUID(top_product_id)).first()
            top_product_name = top_product.name if top_product else "Unknown"
        else:
            top_product_name = None
        
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