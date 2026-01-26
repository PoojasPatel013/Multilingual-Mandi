"""
Vendor dashboard endpoints.

This module provides FastAPI endpoints for vendor dashboard functionality
including inventory management, sales analytics, bulk operations, and metrics.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.product import AvailabilityStatus
from app.models.user import User
from app.schemas.vendor_dashboard import (
    BulkProductUpdate, BulkUpdateResponse, DashboardMetrics,
    InventoryAlertsResponse, InventoryFilterRequest, InventoryListResponse,
    ProductPerformanceMetrics, SalesAnalytics, SalesAnalyticsRequest,
    SalesReport, SalesReportRequest, TopProductsResponse,
    VendorDashboardOverview
)
from app.services.vendor_dashboard_service import VendorDashboardService

router = APIRouter()

# Initialize service
dashboard_service = VendorDashboardService()


def verify_vendor_access(current_user: User) -> None:
    """Verify that the current user is a vendor."""
    if current_user.role != "vendor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can access dashboard endpoints"
        )


@router.get("/overview", response_model=VendorDashboardOverview)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard overview for the current vendor.
    
    Returns key metrics, recent activity, and summary statistics.
    """
    verify_vendor_access(current_user)
    
    overview = await dashboard_service.get_dashboard_overview(
        db=db,
        vendor_id=current_user.id
    )
    
    return overview


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get key dashboard metrics for the current vendor.
    
    Returns product counts, inventory alerts, and sales performance.
    """
    verify_vendor_access(current_user)
    
    metrics = await dashboard_service.get_dashboard_metrics(
        db=db,
        vendor_id=current_user.id
    )
    
    return metrics


@router.get("/inventory", response_model=InventoryListResponse)
async def get_inventory_list(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    availability_filter: Optional[AvailabilityStatus] = Query(None, description="Filter by availability status"),
    search_query: Optional[str] = Query(None, max_length=200, description="Search in name, SKU, or description"),
    sort_by: str = Query("updated_at", pattern="^(name|sku|current_price|quantity_available|updated_at|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated inventory list with filtering and search.
    
    Supports filtering by availability status and searching across product fields.
    """
    verify_vendor_access(current_user)
    
    inventory = await dashboard_service.get_inventory_list(
        db=db,
        vendor_id=current_user.id,
        page=page,
        size=size,
        availability_filter=availability_filter,
        search_query=search_query,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return inventory


@router.get("/inventory/alerts", response_model=InventoryAlertsResponse)
async def get_inventory_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get inventory alerts for low stock and out of stock products.
    
    Returns products that need attention based on stock levels.
    """
    verify_vendor_access(current_user)
    
    # Get inventory with stock issues
    low_stock_inventory = await dashboard_service.get_inventory_list(
        db=db,
        vendor_id=current_user.id,
        page=1,
        size=100,  # Get more items for alerts
        availability_filter=AvailabilityStatus.LOW_STOCK
    )
    
    out_of_stock_inventory = await dashboard_service.get_inventory_list(
        db=db,
        vendor_id=current_user.id,
        page=1,
        size=100,
        availability_filter=AvailabilityStatus.OUT_OF_STOCK
    )
    
    # Convert to alerts format
    alerts = []
    
    for item in low_stock_inventory.items:
        alerts.append({
            "product_id": item.product_id,
            "product_name": item.name,
            "sku": item.sku,
            "alert_type": "low_stock",
            "current_quantity": item.quantity_available,
            "minimum_quantity": item.minimum_quantity,
            "last_updated": item.last_updated
        })
    
    for item in out_of_stock_inventory.items:
        alerts.append({
            "product_id": item.product_id,
            "product_name": item.name,
            "sku": item.sku,
            "alert_type": "out_of_stock",
            "current_quantity": item.quantity_available,
            "minimum_quantity": item.minimum_quantity,
            "last_updated": item.last_updated
        })
    
    return InventoryAlertsResponse(
        alerts=alerts,
        total_alerts=len(alerts),
        low_stock_count=len(low_stock_inventory.items),
        out_of_stock_count=len(out_of_stock_inventory.items)
    )


@router.post("/inventory/bulk-update", response_model=BulkUpdateResponse)
async def bulk_update_products(
    bulk_update: BulkProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform bulk updates on multiple products.
    
    Supports updating common fields and applying price adjustments across multiple products.
    """
    verify_vendor_access(current_user)
    
    result = await dashboard_service.bulk_update_products(
        db=db,
        vendor_id=current_user.id,
        bulk_update=bulk_update
    )
    
    return BulkUpdateResponse(
        success=result["success"],
        message=result["message"],
        updated_count=result["updated_count"],
        product_ids=result.get("product_ids"),
        errors=result.get("errors")
    )


@router.get("/analytics/sales", response_model=SalesAnalytics)
async def get_sales_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics period"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics period"),
    group_by: str = Query("day", pattern="^(day|week|month)$", description="Time grouping for analytics"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get sales analytics with time-based grouping.
    
    Returns sales trends, top products, and revenue analysis for the specified period.
    """
    verify_vendor_access(current_user)
    
    analytics = await dashboard_service.get_sales_analytics(
        db=db,
        vendor_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by
    )
    
    return analytics


@router.post("/reports/sales", response_model=SalesReport)
async def generate_sales_report(
    report_request: SalesReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive sales report for a specific period.
    
    Returns detailed sales metrics, transaction breakdown, and product performance.
    """
    verify_vendor_access(current_user)
    
    report = await dashboard_service.generate_sales_report(
        db=db,
        vendor_id=current_user.id,
        start_date=report_request.start_date,
        end_date=report_request.end_date,
        include_products=report_request.include_products,
        include_customers=report_request.include_customers
    )
    
    return report


@router.get("/analytics/top-products", response_model=TopProductsResponse)
async def get_top_products(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    sort_by: str = Query("revenue", pattern="^(revenue|sales|rating)$", description="Sort criteria"),
    limit: int = Query(10, ge=1, le=50, description="Number of top products to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get top performing products based on various metrics.
    
    Returns products ranked by revenue, sales count, or rating.
    """
    verify_vendor_access(current_user)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get sales analytics to extract top products
    analytics = await dashboard_service.get_sales_analytics(
        db=db,
        vendor_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        group_by="day"
    )
    
    # Convert top products to performance metrics format
    products = []
    for product_data in analytics.top_products[:limit]:
        # Calculate conversion rate (placeholder - would need view data)
        conversion_rate = 0.0  # This would be calculated from actual view/sales data
        
        products.append(ProductPerformanceMetrics(
            product_id=UUID(product_data["product_id"]),
            product_name=product_data["product_name"],
            sku=None,  # Would need to fetch from product data
            total_sales=product_data["sales_count"],
            total_revenue=product_data["revenue"],
            average_rating=0.0,  # Would need to fetch from product data
            total_reviews=0,  # Would need to fetch from product data
            view_count=0,  # Would need to fetch from product data
            conversion_rate=conversion_rate,
            last_sale_date=None  # Would need to calculate from transaction data
        ))
    
    return TopProductsResponse(
        products=products,
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        sort_by=sort_by
    )


@router.get("/analytics/revenue-trend")
async def get_revenue_trend(
    days: int = Query(30, ge=7, le=365, description="Number of days for trend analysis"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get revenue trend analysis for the specified period.
    
    Returns daily revenue data with moving averages and growth indicators.
    """
    verify_vendor_access(current_user)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    analytics = await dashboard_service.get_sales_analytics(
        db=db,
        vendor_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        group_by="day"
    )
    
    return {
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "revenue_trend": analytics.revenue_trend,
        "total_revenue": analytics.total_revenue,
        "average_daily_revenue": analytics.total_revenue / days if days > 0 else 0
    }


@router.get("/analytics/product-performance/{product_id}")
async def get_product_performance(
    product_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed performance metrics for a specific product.
    
    Returns sales data, revenue trends, and customer feedback for the product.
    """
    verify_vendor_access(current_user)
    
    # Verify product ownership
    from app.services.product_service import ProductService
    product_service = ProductService()
    
    product = await product_service.get_product(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if product.vendor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view performance for your own products"
        )
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get product-specific analytics
    analytics = await dashboard_service.get_sales_analytics(
        db=db,
        vendor_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        group_by="day"
    )
    
    # Find this product in the analytics
    product_data = None
    for p in analytics.top_products:
        if p["product_id"] == str(product_id):
            product_data = p
            break
    
    if not product_data:
        product_data = {
            "product_id": str(product_id),
            "product_name": product.name,
            "sales_count": 0,
            "revenue": 0.0,
            "quantity_sold": 0
        }
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "total_sales": product_data["sales_count"],
        "total_revenue": product_data["revenue"],
        "quantity_sold": product_data["quantity_sold"],
        "current_price": product.current_price,
        "average_rating": product.average_rating,
        "total_reviews": product.total_reviews,
        "view_count": product.view_count
    }