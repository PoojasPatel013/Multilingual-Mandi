"""
Product service for business logic.

This module provides business logic for product management including
CRUD operations, search, categorization, and reviews.
"""

import math
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.models.product import Category, Product, ProductReview
from app.schemas.product import (
    CategoryCreate, CategoryResponse, ProductCreate, ProductListResponse,
    ProductResponse, ProductReviewCreate, ProductReviewResponse,
    ProductSearchRequest, ProductUpdate
)


class ProductService:
    """Service class for product-related operations."""
    
    async def create_product(
        self,
        db: Session,
        product_data: ProductCreate,
        vendor_id: UUID
    ) -> ProductResponse:
        """Create a new product."""
        # Create product instance
        product = Product(
            vendor_id=vendor_id,
            name=product_data.name,
            description=product_data.description,
            category_id=product_data.category_id,
            sku=product_data.sku,
            base_price=product_data.base_price,
            current_price=product_data.current_price,
            currency=product_data.currency,
            quantity_available=product_data.quantity_available,
            minimum_quantity=product_data.minimum_quantity,
            availability=product_data.availability,
            images=product_data.images or [],
            specifications=product_data.specifications or {},
            tags=product_data.tags or [],
            translations=product_data.translations or {},
            is_active=product_data.is_active,
            is_featured=product_data.is_featured
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return ProductResponse.from_orm(product)
    
    async def get_product(self, db: Session, product_id: UUID) -> Optional[ProductResponse]:
        """Get a product by ID."""
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            return ProductResponse.from_orm(product)
        return None
    
    async def update_product(
        self,
        db: Session,
        product_id: UUID,
        product_data: ProductUpdate
    ) -> ProductResponse:
        """Update a product."""
        product = db.query(Product).filter(Product.id == product_id).first()
        
        # Update fields that are provided
        update_data = product_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        
        return ProductResponse.from_orm(product)
    
    async def delete_product(self, db: Session, product_id: UUID) -> None:
        """Delete a product."""
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            db.delete(product)
            db.commit()
    
    async def list_products(
        self,
        db: Session,
        page: int = 1,
        size: int = 20,
        category_id: Optional[UUID] = None,
        vendor_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> ProductListResponse:
        """List products with pagination and filtering."""
        query = db.query(Product)
        
        # Apply filters
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if vendor_id:
            query = query.filter(Product.vendor_id == vendor_id)
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        if is_featured is not None:
            query = query.filter(Product.is_featured == is_featured)
        
        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        products = query.offset(offset).limit(size).all()
        
        # Calculate pagination info
        pages = math.ceil(total / size)
        
        return ProductListResponse(
            products=[ProductResponse.from_orm(product) for product in products],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    async def search_products(
        self,
        db: Session,
        search_request: ProductSearchRequest
    ) -> ProductListResponse:
        """Search products with advanced filtering."""
        query = db.query(Product)
        
        # Text search
        if search_request.query:
            search_term = f"%{search_request.query}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.tags.op("@>")(f'["{search_request.query}"]')
                )
            )
        
        # Apply filters
        if search_request.category_id:
            query = query.filter(Product.category_id == search_request.category_id)
        if search_request.vendor_id:
            query = query.filter(Product.vendor_id == search_request.vendor_id)
        if search_request.availability:
            query = query.filter(Product.availability == search_request.availability)
        if search_request.min_price is not None:
            query = query.filter(Product.current_price >= search_request.min_price)
        if search_request.max_price is not None:
            query = query.filter(Product.current_price <= search_request.max_price)
        if search_request.tags:
            for tag in search_request.tags:
                query = query.filter(Product.tags.op("@>")(f'["{tag}"]'))
        
        # Only show active products in search
        query = query.filter(Product.is_active == True)
        
        # Apply sorting
        sort_column = getattr(Product, search_request.sort_by, Product.created_at)
        if search_request.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (search_request.page - 1) * search_request.size
        products = query.offset(offset).limit(search_request.size).all()
        
        # Calculate pagination info
        pages = math.ceil(total / search_request.size)
        
        return ProductListResponse(
            products=[ProductResponse.from_orm(product) for product in products],
            total=total,
            page=search_request.page,
            size=search_request.size,
            pages=pages
        )
    
    async def increment_view_count(self, db: Session, product_id: UUID) -> None:
        """Increment the view count for a product."""
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.view_count += 1
            db.commit()
    
    async def add_product_image(
        self,
        db: Session,
        product_id: UUID,
        image_url: str
    ) -> None:
        """Add an image URL to a product."""
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            images = product.images or []
            images.append(image_url)
            product.images = images
            db.commit()
    
    async def remove_product_image(
        self,
        db: Session,
        product_id: UUID,
        image_index: int
    ) -> None:
        """Remove an image from a product by index."""
        product = db.query(Product).filter(Product.id == product_id).first()
        if product and product.images and 0 <= image_index < len(product.images):
            images = product.images.copy()
            images.pop(image_index)
            product.images = images
            db.commit()
    
    async def toggle_featured_status(
        self,
        db: Session,
        product_id: UUID
    ) -> ProductResponse:
        """Toggle the featured status of a product."""
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.is_featured = not product.is_featured
            db.commit()
            db.refresh(product)
            return ProductResponse.from_orm(product)
    
    # Category methods
    async def create_category(
        self,
        db: Session,
        category_data: CategoryCreate
    ) -> CategoryResponse:
        """Create a new category."""
        # Calculate level based on parent
        level = 0
        if category_data.parent_id:
            parent = db.query(Category).filter(Category.id == category_data.parent_id).first()
            if parent:
                level = parent.level + 1
        
        category = Category(
            name=category_data.name,
            description=category_data.description,
            slug=category_data.slug,
            parent_id=category_data.parent_id,
            level=level,
            sort_order=category_data.sort_order,
            translations=category_data.translations or {},
            is_active=category_data.is_active
        )
        
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return CategoryResponse.from_orm(category)
    
    async def get_category(self, db: Session, category_id: UUID) -> Optional[CategoryResponse]:
        """Get a category by ID."""
        category = db.query(Category).filter(Category.id == category_id).first()
        if category:
            return CategoryResponse.from_orm(category)
        return None
    
    async def list_categories(
        self,
        db: Session,
        parent_id: Optional[UUID] = None,
        is_active: Optional[bool] = None
    ) -> List[CategoryResponse]:
        """List categories with filtering."""
        query = db.query(Category)
        
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)
        
        # Order by level and sort_order
        query = query.order_by(Category.level, Category.sort_order, Category.name)
        
        categories = query.all()
        return [CategoryResponse.from_orm(category) for category in categories]
    
    # Review methods
    async def create_product_review(
        self,
        db: Session,
        product_id: UUID,
        user_id: UUID,
        review_data: ProductReviewCreate
    ) -> ProductReviewResponse:
        """Create a product review."""
        review = ProductReview(
            product_id=product_id,
            user_id=user_id,
            rating=review_data.rating,
            title=review_data.title,
            comment=review_data.comment
        )
        
        db.add(review)
        db.commit()
        db.refresh(review)
        
        # Update product rating statistics
        await self._update_product_rating_stats(db, product_id)
        
        return ProductReviewResponse.from_orm(review)
    
    async def list_product_reviews(
        self,
        db: Session,
        product_id: UUID,
        page: int = 1,
        size: int = 20
    ) -> List[ProductReviewResponse]:
        """List reviews for a product."""
        offset = (page - 1) * size
        reviews = (
            db.query(ProductReview)
            .filter(ProductReview.product_id == product_id)
            .order_by(desc(ProductReview.created_at))
            .offset(offset)
            .limit(size)
            .all()
        )
        
        return [ProductReviewResponse.from_orm(review) for review in reviews]
    
    async def _update_product_rating_stats(self, db: Session, product_id: UUID) -> None:
        """Update product rating statistics after a new review."""
        # Calculate average rating and total reviews
        result = (
            db.query(
                func.avg(ProductReview.rating).label("avg_rating"),
                func.count(ProductReview.id).label("total_reviews")
            )
            .filter(ProductReview.product_id == product_id)
            .first()
        )
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if product and result:
            product.average_rating = float(result.avg_rating or 0)
            product.total_reviews = result.total_reviews or 0
            db.commit()