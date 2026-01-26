"""
Vendor dashboard schemas for request/response validation.

This module defines Pydantic models for vendor dashboard-related API endpoints
including inventory management, sales analytics, and bulk operations.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.product import AvailabilityStatus


class InventoryItem(BaseModel):
    """Schema for inventory item in dashboard."""
    
    product_id: UUID
    name: str
    sku: Optional[str] = None
    current_price: float
    currency: str
    quantity_available: int
    minimum_quantity: int
    availability: AvailabilityStatus
    stock_status: str  # "healthy", "low_stock", "out_of_stock"
    is_active: bool
    is_featured: bool
    view_count: int
    average_rating: float
    total_reviews: int
    last_updated: str


class InventoryListResponse(BaseModel):
    """Schema for paginated inventory list response."""
    
    items: List[InventoryItem]
    total: int
    page: int
    size: int
    pages: int


class PriceAdjustment(BaseModel):
    """Schema for bulk price adjustment."""
    
    adjustment_type: str = Field(..., pattern="^(percentage|fixed|absolute)$")
    value: float
    min_price: Optional[float] = Field(None, gt=0)
    max_price: Optional[float] = Field(None, gt=0)
    
    @validator("value")
    def validate_value(cls, v, values):
        """Validate adjustment value based on type."""
        adjustment_type = values.get("adjustment_type")
        if adjustment_type == "percentage" and (v < -100 or v > 1000):
            raise ValueError("Percentage adjustment must be between -100% and 1000%")
        elif adjustment_type in ["fixed", "absolute"] and v < 0:
            raise ValueError("Price values must be positive")
        return v
    
    @validator("max_price")
    def validate_price_range(cls, v, values):
        """Validate price range."""
        if v is not None and "min_price" in values and values["min_price"] is not None:
            if v <= values["min_price"]:
                raise ValueError("Maximum price must be greater than minimum price")
        return v


class ProductUpdateFields(BaseModel):
    """Schema for fields that can be bulk updated."""
    
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    availability: Optional[AvailabilityStatus] = None
    minimum_quantity: Optional[int] = Field(None, ge=1)
    currency: Optional[str] = Field(None, max_length=10)


class BulkProductUpdate(BaseModel):
    """Schema for bulk product update request."""
    
    product_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    updates: ProductUpdateFields
    price_adjustment: Optional[PriceAdjustment] = None
    
    @validator("product_ids")
    def validate_product_ids(cls, v):
        """Validate product IDs list."""
        if len(set(v)) != len(v):
            raise ValueError("Duplicate product IDs are not allowed")
        return v


class DashboardMetrics(BaseModel):
    """Schema for key dashboard metrics."""
    
    total_products: int
    active_products: int
    featured_products: int
    low_stock_alerts: int
    out_of_stock_alerts: int
    sales_30d: int
    revenue_30d: float
    sales_growth_30d: float  # Percentage growth
    revenue_growth_30d: float  # Percentage growth
    top_product_30d: Optional[str] = None


class VendorDashboardOverview(BaseModel):
    """Schema for vendor dashboard overview."""
    
    vendor_id: UUID
    business_name: str
    total_products: int
    active_products: int
    low_stock_products: int
    out_of_stock_products: int
    total_sales_30d: int
    total_revenue_30d: float
    average_order_value: float
    active_negotiations: int
    recent_activity: List[Dict[str, Any]]


class SalesAnalytics(BaseModel):
    """Schema for sales analytics response."""
    
    period_start: str
    period_end: str
    total_sales: int
    total_revenue: float
    average_order_value: float
    sales_by_period: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]
    revenue_trend: List[Dict[str, Any]]


class SalesReport(BaseModel):
    """Schema for comprehensive sales report."""
    
    vendor_id: UUID
    period_start: str
    period_end: str
    total_transactions: int
    completed_transactions: int
    total_revenue: float
    total_fees: float
    net_revenue: float
    transaction_status_breakdown: Dict[str, int]
    product_performance: List[Dict[str, Any]]
    generated_at: str


class InventoryFilterRequest(BaseModel):
    """Schema for inventory filtering request."""
    
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    availability_filter: Optional[AvailabilityStatus] = None
    search_query: Optional[str] = Field(None, max_length=200)
    sort_by: str = Field(default="updated_at", pattern="^(name|sku|price|quantity|updated_at|created_at)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class SalesAnalyticsRequest(BaseModel):
    """Schema for sales analytics request."""
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    group_by: str = Field(default="day", pattern="^(day|week|month)$")
    
    @validator("end_date")
    def validate_date_range(cls, v, values):
        """Validate date range."""
        if v is not None and "start_date" in values and values["start_date"] is not None:
            if v <= values["start_date"]:
                raise ValueError("End date must be after start date")
        return v


class SalesReportRequest(BaseModel):
    """Schema for sales report generation request."""
    
    start_date: datetime
    end_date: datetime
    include_products: bool = Field(default=True)
    include_customers: bool = Field(default=False)
    
    @validator("end_date")
    def validate_date_range(cls, v, values):
        """Validate date range."""
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date")
        return v
    
    @validator("start_date", "end_date")
    def validate_date_not_future(cls, v):
        """Validate dates are not in the future."""
        if v > datetime.utcnow():
            raise ValueError("Date cannot be in the future")
        return v


class BulkUpdateResponse(BaseModel):
    """Schema for bulk update operation response."""
    
    success: bool
    message: str
    updated_count: int
    product_ids: Optional[List[str]] = None
    errors: Optional[List[str]] = None


class InventoryAlert(BaseModel):
    """Schema for inventory alerts."""
    
    product_id: UUID
    product_name: str
    sku: Optional[str] = None
    alert_type: str  # "low_stock", "out_of_stock"
    current_quantity: int
    minimum_quantity: int
    last_updated: str


class InventoryAlertsResponse(BaseModel):
    """Schema for inventory alerts response."""
    
    alerts: List[InventoryAlert]
    total_alerts: int
    low_stock_count: int
    out_of_stock_count: int


class ProductPerformanceMetrics(BaseModel):
    """Schema for individual product performance metrics."""
    
    product_id: UUID
    product_name: str
    sku: Optional[str] = None
    total_sales: int
    total_revenue: float
    average_rating: float
    total_reviews: int
    view_count: int
    conversion_rate: float  # views to sales ratio
    last_sale_date: Optional[str] = None


class TopProductsResponse(BaseModel):
    """Schema for top performing products response."""
    
    products: List[ProductPerformanceMetrics]
    period_start: str
    period_end: str
    sort_by: str  # "revenue", "sales", "rating"