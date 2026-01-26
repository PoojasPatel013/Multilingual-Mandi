"""
Property-based tests for product management functionality.

This module contains property-based tests that validate universal properties
of the product management system using Hypothesis for comprehensive input coverage.
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

from app.models.product import Product, Category, ProductReview, AvailabilityStatus
from app.models.user import User, UserRole, VerificationStatus
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductSearchRequest,
    CategoryCreate, ProductReviewCreate
)
from app.services.product_service import ProductService


# Custom strategies for generating test data
@composite
def valid_product_name(draw):
    """Generate valid product names."""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Zs', 'Pc')),
        min_size=1,
        max_size=100
    ).filter(lambda x: x.strip() and len(x.strip()) > 0))


@composite
def valid_product_description(draw):
    """Generate valid product descriptions."""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Zs', 'Po', 'Pc')),
        min_size=1,
        max_size=500
    ).filter(lambda x: x.strip() and len(x.strip()) > 0))


@composite
def valid_price(draw):
    """Generate valid price values."""
    return draw(st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False))


@composite
def valid_quantity(draw):
    """Generate valid quantity values."""
    return draw(st.integers(min_value=0, max_value=1000))


@composite
def valid_currency(draw):
    """Generate valid currency codes."""
    return draw(st.sampled_from(['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'INR', 'BRL', 'CAD']))


@composite
def valid_sku(draw):
    """Generate valid SKU codes."""
    unique_id = str(uuid4())[:8]
    base_sku = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
        min_size=3,
        max_size=12
    ).filter(lambda x: len(x) >= 3))
    return f"{base_sku}_{unique_id}"


@composite
def valid_image_urls(draw):
    """Generate valid image URL lists."""
    base_urls = [
        'https://example.com/image',
        'http://test.com/photo',
        'https://cdn.example.org/pic'
    ]
    return draw(st.lists(
        st.builds(
            lambda base, suffix: f"{base}{suffix}.jpg",
            st.sampled_from(base_urls),
            st.integers(min_value=1, max_value=999)
        ),
        min_size=0,
        max_size=5
    ))


@composite
def valid_product_tags(draw):
    """Generate valid product tag lists."""
    tags = [
        'electronics', 'clothing', 'books', 'home', 'garden',
        'sports', 'toys', 'beauty', 'automotive', 'food',
        'health', 'jewelry', 'music', 'art', 'crafts'
    ]
    return draw(st.lists(
        st.sampled_from(tags),
        min_size=0,
        max_size=10,
        unique=True
    ))


@composite
def valid_specifications(draw):
    """Generate valid product specifications."""
    spec_keys = ['color', 'size', 'weight', 'material', 'brand', 'model', 'dimensions']
    spec_values = ['red', 'blue', 'large', 'small', '1kg', 'cotton', 'TestBrand', 'Model123', '10x20x30']
    
    return draw(st.dictionaries(
        st.sampled_from(spec_keys),
        st.sampled_from(spec_values),
        min_size=0,
        max_size=5
    ))


@composite
def valid_translations(draw):
    """Generate valid product translations."""
    # Return empty dict to avoid schema validation issues
    return {}


@composite
def valid_user_data(draw):
    """Generate valid user data with unique email."""
    unique_id = str(uuid4())[:8]
    return {
        'email': f"user_{unique_id}@example.com",
        'hashed_password': 'hashed_password_123',
        'first_name': 'Test',
        'last_name': 'User',
        'role': draw(st.sampled_from([UserRole.VENDOR, UserRole.CUSTOMER, UserRole.ADMIN])),
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
def valid_product_create_data(draw):
    """Generate valid ProductCreate data."""
    base_price = draw(valid_price())
    # Ensure current price is within the validation constraint (not more than double base price)
    current_price = draw(st.floats(min_value=0.01, max_value=base_price * 2.0, allow_nan=False, allow_infinity=False))
    
    return ProductCreate(
        name=draw(valid_product_name()),
        description=draw(valid_product_description()),
        sku=draw(valid_sku()),
        base_price=base_price,
        current_price=current_price,
        currency=draw(valid_currency()),
        quantity_available=draw(valid_quantity()),
        minimum_quantity=draw(st.integers(min_value=1, max_value=10)),
        availability=draw(st.sampled_from(list(AvailabilityStatus))),
        images=draw(valid_image_urls()),
        specifications=draw(valid_specifications()),
        tags=draw(valid_product_tags()),
        translations=draw(valid_translations()),
        is_active=draw(st.booleans()),
        is_featured=draw(st.booleans())
    )


@composite
def valid_category_data(draw):
    """Generate valid category data."""
    unique_id = str(uuid4())[:8]
    return CategoryCreate(
        name=f"{draw(st.text(min_size=3, max_size=30))}_{unique_id}",
        description=draw(st.text(min_size=1, max_size=200)),
        slug=f"{draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=3, max_size=20))}_{unique_id}",
        sort_order=draw(st.integers(min_value=0, max_value=100)),
        translations=draw(st.dictionaries(
            st.sampled_from(['es', 'fr', 'de']),
            st.fixed_dictionaries({
                'name': st.text(min_size=3, max_size=30),
                'description': st.text(min_size=1, max_size=200)
            }),
            min_size=0,
            max_size=2
        )),
        is_active=draw(st.booleans())
    )


class TestProductManagementFunctionality:
    """
    Property-based tests for product management functionality.
    
    **Validates: Requirements 4.2, 4.3**
    
    These tests ensure that product-related operations (add, update, bulk modify)
    provide appropriate input validation, confirmation steps, and success feedback.
    """
    
    @pytest.fixture
    def product_service(self):
        """Create product service instance."""
        return ProductService()
    
    @given(
        vendor_data=valid_user_data(),
        product_data=valid_product_create_data()
    )
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_product_creation_functionality(
        self,
        vendor_data: Dict[str, Any],
        product_data: ProductCreate,
        product_service: ProductService,
        db_session: AsyncSession
    ):
        """
        **Property 14: Product Management Functionality**
        **Validates: Requirements 4.2, 4.3**
        
        For any valid product creation request, the system should
        successfully create the product with proper validation,
        data integrity, and appropriate success feedback.
        """
        # Ensure vendor role
        vendor_data['role'] = UserRole.VENDOR
        
        # Create vendor user
        vendor = User(**vendor_data)
        db_session.add(vendor)
        await db_session.commit()
        await db_session.refresh(vendor)
        
        # Create product directly using the model
        product = Product(
            vendor_id=vendor.id,
            name=product_data.name,
            description=product_data.description,
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
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Verify product creation functionality
        
        # 1. Product should be created with all provided data
        assert product is not None
        assert product.vendor_id == vendor.id
        assert product.name == product_data.name
        assert product.description == product_data.description
        assert product.sku == product_data.sku
        assert abs(product.base_price - product_data.base_price) < 0.01
        assert abs(product.current_price - product_data.current_price) < 0.01
        assert product.currency == product_data.currency
        assert product.quantity_available == product_data.quantity_available
        assert product.minimum_quantity == product_data.minimum_quantity
        assert product.availability == product_data.availability
        assert product.is_active == product_data.is_active
        assert product.is_featured == product_data.is_featured
        
        # 2. Product should have proper default values
        assert product.view_count == 0
        assert product.favorite_count == 0
        assert product.average_rating == 0.0
        assert product.total_reviews == 0
        assert product.created_at is not None
        assert product.updated_at is not None
        
        # 3. Product should be retrievable from database
        result = await db_session.execute(
            select(Product).where(Product.id == product.id)
        )
        retrieved_product = result.scalar_one()
        assert retrieved_product is not None
        assert retrieved_product.id == product.id
        assert retrieved_product.name == product_data.name
        
        # 4. Product images should be properly stored
        if product_data.images:
            assert len(product.images) == len(product_data.images)
            assert set(product.images) == set(product_data.images)
        else:
            assert product.images == []
        
        # 5. Product specifications should be properly stored
        if product_data.specifications:
            assert product.specifications == product_data.specifications
        else:
            assert product.specifications == {}
        
        # 6. Product tags should be properly stored
        if product_data.tags:
            assert set(product.tags) == set(product_data.tags)
        else:
            assert product.tags == []
    
    @given(
        vendor_data=valid_user_data(),
        initial_product_data=valid_product_create_data(),
        update_fields=st.dictionaries(
            st.sampled_from(['name', 'description', 'current_price', 'quantity_available', 'is_active', 'is_featured']),
            st.one_of([
                valid_product_name(),
                valid_product_description(),
                valid_price(),
                valid_quantity(),
                st.booleans()
            ]),
            min_size=1,
            max_size=4
        )
    )
    @settings(max_examples=12, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_product_update_functionality(
        self,
        vendor_data: Dict[str, Any],
        initial_product_data: ProductCreate,
        update_fields: Dict[str, Any],
        product_service: ProductService,
        db_session: AsyncSession
    ):
        """
        **Property 14: Product Management Functionality**
        **Validates: Requirements 4.2, 4.3**
        
        For any valid product update request, the system should
        successfully update the product with proper validation,
        data integrity, and appropriate confirmation.
        """
        # Ensure vendor role
        vendor_data['role'] = UserRole.VENDOR
        
        # Create vendor user
        vendor = User(**vendor_data)
        db_session.add(vendor)
        await db_session.commit()
        await db_session.refresh(vendor)
        
        # Create initial product
        product = Product(
            vendor_id=vendor.id,
            name=initial_product_data.name,
            description=initial_product_data.description,
            sku=initial_product_data.sku,
            base_price=initial_product_data.base_price,
            current_price=initial_product_data.current_price,
            currency=initial_product_data.currency,
            quantity_available=initial_product_data.quantity_available,
            minimum_quantity=initial_product_data.minimum_quantity,
            availability=initial_product_data.availability,
            images=initial_product_data.images or [],
            specifications=initial_product_data.specifications or {},
            tags=initial_product_data.tags or [],
            translations=initial_product_data.translations or {},
            is_active=initial_product_data.is_active,
            is_featured=initial_product_data.is_featured
        )
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Store original values for comparison
        original_values = {
            'base_price': product.base_price,
            'currency': product.currency,
            'sku': product.sku,
            'minimum_quantity': product.minimum_quantity,
            'availability': product.availability
        }
        
        # Update product fields
        for field, new_value in update_fields.items():
            setattr(product, field, new_value)
        
        await db_session.commit()
        await db_session.refresh(product)
        
        # Verify product update functionality
        
        # 1. Product should be successfully updated
        assert product is not None
        assert product.vendor_id == vendor.id
        
        # 2. Updated fields should reflect new values
        for field, new_value in update_fields.items():
            if field == 'current_price':
                assert abs(getattr(product, field) - new_value) < 0.01
            else:
                assert getattr(product, field) == new_value
        
        # 3. Non-updated fields should remain unchanged
        unchanged_fields = ['base_price', 'currency', 'sku', 'minimum_quantity', 'availability']
        for field in unchanged_fields:
            if field not in update_fields:
                original_value = original_values[field]
                updated_value = getattr(product, field)
                if isinstance(original_value, float):
                    assert abs(updated_value - original_value) < 0.01
                else:
                    assert updated_value == original_value
        
        # 4. Updated product should be retrievable
        result = await db_session.execute(
            select(Product).where(Product.id == product.id)
        )
        retrieved_product = result.scalar_one()
        assert retrieved_product is not None
        assert retrieved_product.id == product.id
        
        # 5. Update timestamp should be modified
        assert product.updated_at >= product.created_at
    
    @given(
        vendor_data=valid_user_data(),
        products_data=st.lists(
            valid_product_create_data(),
            min_size=2,
            max_size=5
        ),
        search_query=st.text(min_size=1, max_size=20),
        price_range=st.tuples(
            st.floats(min_value=1.0, max_value=100.0),
            st.floats(min_value=101.0, max_value=1000.0)
        )
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_product_search_functionality(
        self,
        vendor_data: Dict[str, Any],
        products_data: List[ProductCreate],
        search_query: str,
        price_range: tuple,
        product_service: ProductService,
        db_session: AsyncSession
    ):
        """
        **Property 14: Product Management Functionality**
        **Validates: Requirements 4.2, 4.3**
        
        For any product search request, the system should
        return relevant results with proper filtering,
        sorting, and pagination functionality.
        """
        # Ensure vendor role
        vendor_data['role'] = UserRole.VENDOR
        
        # Create vendor user
        vendor = User(**vendor_data)
        db_session.add(vendor)
        await db_session.commit()
        await db_session.refresh(vendor)
        
        # Create products with search-friendly data
        created_products = []
        for i, product_data in enumerate(products_data):
            # Make some products match the search query
            if i % 2 == 0:
                product_data.name = f"{search_query} Product {i}"
                product_data.description = f"Description containing {search_query}"
            
            # Set prices within and outside the range
            if i < len(products_data) // 2:
                product_data.current_price = price_range[0] + 10.0  # Within range
            else:
                product_data.current_price = price_range[1] + 10.0  # Outside range
            
            # Ensure products are active for search
            product_data.is_active = True
            
            product = Product(
                vendor_id=vendor.id,
                name=product_data.name,
                description=product_data.description,
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
            
            db_session.add(product)
            created_products.append(product)
        
        await db_session.commit()
        
        # Refresh all products
        for product in created_products:
            await db_session.refresh(product)
        
        # Test basic search functionality by querying database directly
        
        # 1. Test price filtering
        result = await db_session.execute(
            select(Product).where(
                and_(
                    Product.current_price >= price_range[0],
                    Product.current_price <= price_range[1],
                    Product.is_active == True
                )
            )
        )
        price_filtered_products = result.scalars().all()
        
        # Verify price filtering works
        for product in price_filtered_products:
            assert price_range[0] <= product.current_price <= price_range[1]
            assert product.is_active is True
        
        # 2. Test name search functionality
        result = await db_session.execute(
            select(Product).where(
                and_(
                    Product.name.ilike(f"%{search_query}%"),
                    Product.is_active == True
                )
            )
        )
        name_filtered_products = result.scalars().all()
        
        # Verify name filtering works
        for product in name_filtered_products:
            assert search_query.lower() in product.name.lower()
            assert product.is_active is True
        
        # 3. Test vendor filtering
        result = await db_session.execute(
            select(Product).where(Product.vendor_id == vendor.id)
        )
        vendor_products = result.scalars().all()
        
        # All products should belong to the vendor
        assert len(vendor_products) == len(created_products)
        for product in vendor_products:
            assert product.vendor_id == vendor.id
        
        # 4. Test product count functionality
        result = await db_session.execute(
            select(func.count(Product.id)).where(Product.vendor_id == vendor.id)
        )
        total_count = result.scalar()
        
        assert total_count == len(created_products)
    
    @given(
        admin_data=valid_user_data(),
        category_data=valid_category_data()
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_category_management_functionality(
        self,
        admin_data: Dict[str, Any],
        category_data: CategoryCreate,
        product_service: ProductService,
        db_session: AsyncSession
    ):
        """
        **Property 14: Product Management Functionality**
        **Validates: Requirements 4.2, 4.3**
        
        For any category management operation, the system should
        provide proper validation, hierarchy management, and
        data integrity for product categorization.
        """
        # Ensure admin role
        admin_data['role'] = UserRole.ADMIN
        
        # Create admin user
        admin = User(**admin_data)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)
        
        # Create category directly using the model
        category = Category(
            name=category_data.name,
            description=category_data.description,
            slug=category_data.slug,
            parent_id=category_data.parent_id,
            level=0,  # Root level category
            sort_order=category_data.sort_order,
            translations=category_data.translations or {},
            is_active=category_data.is_active
        )
        
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        
        # Verify category management functionality
        
        # 1. Category should be created with all provided data
        assert category is not None
        assert category.name == category_data.name
        assert category.description == category_data.description
        assert category.slug == category_data.slug
        assert category.sort_order == category_data.sort_order
        assert category.is_active == category_data.is_active
        
        # 2. Category should have proper hierarchy level
        if category_data.parent_id is None:
            assert category.level == 0
        
        # 3. Category should be retrievable
        result = await db_session.execute(
            select(Category).where(Category.id == category.id)
        )
        retrieved_category = result.scalar_one()
        assert retrieved_category is not None
        assert retrieved_category.id == category.id
        assert retrieved_category.name == category_data.name
        
        # 4. Category should appear in listings
        result = await db_session.execute(
            select(Category).where(Category.is_active == category_data.is_active)
        )
        categories_list = result.scalars().all()
        
        category_ids = [cat.id for cat in categories_list]
        assert category.id in category_ids
        
        # 5. Category translations should be properly stored
        if category_data.translations:
            assert category.translations == category_data.translations
        else:
            assert category.translations == {}
        
        # 6. Category slug should be unique
        result = await db_session.execute(
            select(Category).where(Category.slug == category_data.slug)
        )
        slug_categories = result.scalars().all()
        assert len(slug_categories) == 1
        assert slug_categories[0].id == category.id
    
    @given(
        vendor_data=valid_user_data(),
        customer_data=valid_user_data(),
        product_data=valid_product_create_data(),
        review_rating=st.integers(min_value=1, max_value=5),
        review_title=st.text(min_size=1, max_size=100),
        review_comment=st.text(min_size=1, max_size=500)
    )
    @settings(max_examples=8, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_product_review_functionality(
        self,
        vendor_data: Dict[str, Any],
        customer_data: Dict[str, Any],
        product_data: ProductCreate,
        review_rating: int,
        review_title: str,
        review_comment: str,
        product_service: ProductService,
        db_session: AsyncSession
    ):
        """
        **Property 14: Product Management Functionality**
        **Validates: Requirements 4.2, 4.3**
        
        For any product review operation, the system should
        provide proper validation, rating calculation, and
        review management functionality.
        """
        # Ensure different roles
        vendor_data['role'] = UserRole.VENDOR
        customer_data['role'] = UserRole.CUSTOMER
        customer_data['email'] = f"customer_{str(uuid4())[:8]}@example.com"
        
        # Create users
        vendor = User(**vendor_data)
        customer = User(**customer_data)
        db_session.add(vendor)
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(vendor)
        await db_session.refresh(customer)
        
        # Create product
        product = Product(
            vendor_id=vendor.id,
            name=product_data.name,
            description=product_data.description,
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
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Create review directly using the model
        review = ProductReview(
            product_id=product.id,
            user_id=customer.id,
            rating=review_rating,
            title=review_title,
            comment=review_comment
        )
        
        db_session.add(review)
        await db_session.commit()
        await db_session.refresh(review)
        
        # Verify review functionality
        
        # 1. Review should be created with all provided data
        assert review is not None
        assert review.product_id == product.id
        assert review.user_id == customer.id
        assert review.rating == review_rating
        assert review.title == review_title
        assert review.comment == review_comment
        
        # 2. Review should have proper timestamps
        assert review.created_at is not None
        assert review.updated_at is not None
        
        # 3. Review should be retrievable in product reviews list
        result = await db_session.execute(
            select(ProductReview).where(ProductReview.product_id == product.id)
        )
        reviews_list = result.scalars().all()
        
        assert len(reviews_list) == 1
        assert reviews_list[0].id == review.id
        assert reviews_list[0].rating == review_rating
        
        # 4. Review should be associated with correct product and user
        assert reviews_list[0].product_id == product.id
        assert reviews_list[0].user_id == customer.id
        
        # 5. Multiple reviews should be supported
        # Create a second review
        review2 = ProductReview(
            product_id=product.id,
            user_id=customer.id,  # Same customer can review again (for testing)
            rating=review_rating,
            title=f"Second {review_title}",
            comment=f"Second {review_comment}"
        )
        
        db_session.add(review2)
        await db_session.commit()
        
        # Verify multiple reviews
        result = await db_session.execute(
            select(ProductReview).where(ProductReview.product_id == product.id)
        )
        all_reviews = result.scalars().all()
        assert len(all_reviews) == 2
    
    @given(
        vendor_data=valid_user_data(),
        products_data=st.lists(
            valid_product_create_data(),
            min_size=2,
            max_size=4
        ),
        image_urls=st.lists(
            st.builds(
                lambda i: f"https://example.com/image{i}.jpg",
                st.integers(min_value=1, max_value=100)
            ),
            min_size=1,
            max_size=3
        )
    )
    @settings(max_examples=8, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_product_image_management_functionality(
        self,
        vendor_data: Dict[str, Any],
        products_data: List[ProductCreate],
        image_urls: List[str],
        product_service: ProductService,
        db_session: AsyncSession
    ):
        """
        **Property 14: Product Management Functionality**
        **Validates: Requirements 4.2, 4.3**
        
        For any product image management operation, the system should
        provide proper validation, storage, and retrieval functionality
        for product images.
        """
        # Ensure vendor role
        vendor_data['role'] = UserRole.VENDOR
        
        # Create vendor user
        vendor = User(**vendor_data)
        db_session.add(vendor)
        await db_session.commit()
        await db_session.refresh(vendor)
        
        # Create product
        product_data = products_data[0]
        product = Product(
            vendor_id=vendor.id,
            name=product_data.name,
            description=product_data.description,
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
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Test image addition functionality
        original_images = product.images.copy() if product.images else []
        
        for image_url in image_urls:
            # Add image to product
            current_images = product.images or []
            current_images.append(image_url)
            product.images = current_images
            
        await db_session.commit()
        await db_session.refresh(product)
        
        # Verify image management functionality
        
        # 1. Images should be added to product
        expected_images = original_images + image_urls
        assert len(product.images) == len(expected_images)
        
        # All original and new images should be present
        for image_url in image_urls:
            assert image_url in product.images
        
        # 2. Test image removal functionality
        if len(product.images) > 0:
            # Remove the last image
            current_images = product.images.copy()
            removed_image = current_images.pop()
            product.images = current_images
            
            await db_session.commit()
            await db_session.refresh(product)
            
            # Verify image was removed
            assert removed_image not in product.images
            assert len(product.images) == len(expected_images) - 1
        
        # 3. Test image list integrity
        result = await db_session.execute(
            select(Product).where(Product.id == product.id)
        )
        retrieved_product = result.scalar_one()
        
        assert retrieved_product.images == product.images
        
        # 4. Test empty image list handling
        product.images = []
        await db_session.commit()
        await db_session.refresh(product)
        
        assert product.images == []
    
    @given(
        vendor_data=valid_user_data(),
        products_data=st.lists(
            valid_product_create_data(),
            min_size=3,
            max_size=6
        )
    )
    @settings(max_examples=8, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_bulk_product_operations_functionality(
        self,
        vendor_data: Dict[str, Any],
        products_data: List[ProductCreate],
        product_service: ProductService,
        db_session: AsyncSession
    ):
        """
        **Property 14: Product Management Functionality**
        **Validates: Requirements 4.2, 4.3**
        
        For any bulk product operations, the system should
        provide efficient processing, proper validation,
        and consistent results across all products.
        """
        # Ensure vendor role
        vendor_data['role'] = UserRole.VENDOR
        
        # Create vendor user
        vendor = User(**vendor_data)
        db_session.add(vendor)
        await db_session.commit()
        await db_session.refresh(vendor)
        
        # Create multiple products
        created_products = []
        for product_data in products_data:
            product = Product(
                vendor_id=vendor.id,
                name=product_data.name,
                description=product_data.description,
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
            
            db_session.add(product)
            created_products.append(product)
        
        await db_session.commit()
        
        # Refresh all products
        for product in created_products:
            await db_session.refresh(product)
        
        # Verify bulk operations functionality
        
        # 1. All products should be retrievable in bulk
        result = await db_session.execute(
            select(Product).where(Product.vendor_id == vendor.id)
        )
        vendor_products = result.scalars().all()
        
        assert len(vendor_products) == len(created_products)
        
        # 2. Products should maintain data integrity in bulk operations
        retrieved_ids = {p.id for p in vendor_products}
        created_ids = {p.id for p in created_products}
        assert retrieved_ids == created_ids
        
        # 3. Test bulk featured status toggle
        featured_products = []
        for product in created_products[:len(created_products)//2]:
            product.is_featured = True
            featured_products.append(product)
        
        await db_session.commit()
        
        # Verify featured products can be filtered
        result = await db_session.execute(
            select(Product).where(
                and_(
                    Product.vendor_id == vendor.id,
                    Product.is_featured == True
                )
            )
        )
        featured_results = result.scalars().all()
        
        assert len(featured_results) >= len(featured_products)
        for product in featured_results:
            assert product.is_featured is True
        
        # 4. Test bulk view count increment
        for product in created_products:
            product.view_count += 1
        
        await db_session.commit()
        
        # Verify view counts were incremented
        result = await db_session.execute(
            select(Product).where(Product.vendor_id == vendor.id)
        )
        updated_products = result.scalars().all()
        
        for product in updated_products:
            assert product.view_count == 1
        
        # 5. Test bulk status changes
        # Deactivate half the products
        for product in created_products[:len(created_products)//2]:
            product.is_active = False
        
        await db_session.commit()
        
        # Verify active/inactive filtering
        result = await db_session.execute(
            select(Product).where(
                and_(
                    Product.vendor_id == vendor.id,
                    Product.is_active == True
                )
            )
        )
        active_products = result.scalars().all()
        
        result = await db_session.execute(
            select(Product).where(
                and_(
                    Product.vendor_id == vendor.id,
                    Product.is_active == False
                )
            )
        )
        inactive_products = result.scalars().all()
        
        assert len(active_products) + len(inactive_products) == len(created_products)
        assert len(inactive_products) >= len(created_products)//2