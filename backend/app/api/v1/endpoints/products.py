"""
Product management endpoints.

This module provides FastAPI endpoints for product CRUD operations,
image upload, categorization, and search functionality.
"""

import os
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.product import Category, Product, ProductReview
from app.models.user import User
from app.schemas.product import (
    CategoryCreate, CategoryResponse, ProductCreate, ProductListResponse,
    ProductResponse, ProductReviewCreate, ProductReviewResponse,
    ProductSearchRequest, ProductUpdate
)
from app.services.file_service import FileService
from app.services.product_service import ProductService

router = APIRouter()

# Initialize services
file_service = FileService()
product_service = ProductService()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new product.
    
    Only vendors can create products.
    """
    if current_user.role != "vendor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can create products"
        )
    
    # Create product with vendor_id
    product = await product_service.create_product(
        db=db,
        product_data=product_data,
        vendor_id=current_user.id
    )
    
    return product


@router.get("/", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    vendor_id: Optional[UUID] = Query(None, description="Filter by vendor"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|name|price|rating)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    List products with pagination and filtering.
    """
    return await product_service.list_products(
        db=db,
        page=page,
        size=size,
        category_id=category_id,
        vendor_id=vendor_id,
        is_active=is_active,
        is_featured=is_featured,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/search", response_model=ProductListResponse)
async def search_products(
    search_request: ProductSearchRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    Search products with advanced filtering and sorting.
    """
    return await product_service.search_products(db=db, search_request=search_request)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific product by ID.
    """
    product = await product_service.get_product(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Increment view count
    await product_service.increment_view_count(db=db, product_id=product_id)
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a product.
    
    Only the product owner (vendor) can update their products.
    """
    # Get existing product
    existing_product = await product_service.get_product(db=db, product_id=product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check ownership
    if existing_product.vendor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own products"
        )
    
    # Update product
    updated_product = await product_service.update_product(
        db=db,
        product_id=product_id,
        product_data=product_data
    )
    
    return updated_product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a product.
    
    Only the product owner (vendor) can delete their products.
    """
    # Get existing product
    existing_product = await product_service.get_product(db=db, product_id=product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check ownership
    if existing_product.vendor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own products"
        )
    
    # Delete product
    await product_service.delete_product(db=db, product_id=product_id)


@router.post("/{product_id}/images", response_model=dict)
async def upload_product_image(
    product_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image for a product.
    
    Only the product owner (vendor) can upload images.
    """
    # Get existing product
    existing_product = await product_service.get_product(db=db, product_id=product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check ownership
    if existing_product.vendor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload images for your own products"
        )
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed"
        )
    
    # Upload image
    image_url = await file_service.upload_product_image(
        file=file,
        product_id=product_id
    )
    
    # Add image URL to product
    await product_service.add_product_image(
        db=db,
        product_id=product_id,
        image_url=image_url
    )
    
    return {"image_url": image_url, "message": "Image uploaded successfully"}


@router.delete("/{product_id}/images/{image_index}")
async def delete_product_image(
    product_id: UUID,
    image_index: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a product image by index.
    
    Only the product owner (vendor) can delete images.
    """
    # Get existing product
    existing_product = await product_service.get_product(db=db, product_id=product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check ownership
    if existing_product.vendor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete images from your own products"
        )
    
    # Delete image
    await product_service.remove_product_image(
        db=db,
        product_id=product_id,
        image_index=image_index
    )
    
    return {"message": "Image deleted successfully"}


# Category endpoints
@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new product category.
    
    Only admins can create categories.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    category = await product_service.create_category(db=db, category_data=category_data)
    return category


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    List product categories.
    """
    return await product_service.list_categories(
        db=db,
        parent_id=parent_id,
        is_active=is_active
    )


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific category by ID.
    """
    category = await product_service.get_category(db=db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


# Product reviews endpoints
@router.post("/{product_id}/reviews", response_model=ProductReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_product_review(
    product_id: UUID,
    review_data: ProductReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a review for a product.
    
    Only customers can create reviews.
    """
    if current_user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create reviews"
        )
    
    # Check if product exists
    product = await product_service.get_product(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if user already reviewed this product
    existing_review = db.query(ProductReview).filter(
        and_(
            ProductReview.product_id == product_id,
            ProductReview.user_id == current_user.id
        )
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this product"
        )
    
    # Create review
    review = await product_service.create_product_review(
        db=db,
        product_id=product_id,
        user_id=current_user.id,
        review_data=review_data
    )
    
    return review


@router.get("/{product_id}/reviews", response_model=List[ProductReviewResponse])
async def list_product_reviews(
    product_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List reviews for a product.
    """
    # Check if product exists
    product = await product_service.get_product(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return await product_service.list_product_reviews(
        db=db,
        product_id=product_id,
        page=page,
        size=size
    )


# Vendor-specific endpoints
@router.get("/vendor/my-products", response_model=ProductListResponse)
async def get_my_products(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get products owned by the current vendor.
    """
    if current_user.role != "vendor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can access this endpoint"
        )
    
    return await product_service.list_products(
        db=db,
        page=page,
        size=size,
        vendor_id=current_user.id,
        is_active=is_active,
        sort_by="updated_at",
        sort_order="desc"
    )


@router.post("/{product_id}/toggle-featured")
async def toggle_product_featured(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toggle the featured status of a product.
    
    Only the product owner (vendor) can toggle featured status.
    """
    # Get existing product
    existing_product = await product_service.get_product(db=db, product_id=product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check ownership
    if existing_product.vendor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own products"
        )
    
    # Toggle featured status
    updated_product = await product_service.toggle_featured_status(
        db=db,
        product_id=product_id
    )
    
    return {
        "message": f"Product {'featured' if updated_product.is_featured else 'unfeatured'} successfully",
        "is_featured": updated_product.is_featured
    }