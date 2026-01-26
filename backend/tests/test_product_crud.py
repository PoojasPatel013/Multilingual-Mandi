"""
Tests for product CRUD operations.

This module tests the product management functionality including
creation, reading, updating, deletion, and search operations.
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from app.models.product import Product, Category, AvailabilityStatus
from app.schemas.product import ProductCreate, ProductUpdate, CategoryCreate
from app.services.product_service import ProductService


class TestProductService:
    """Test product service functionality."""
    
    @pytest.fixture
    def product_service(self):
        """Create product service instance."""
        return ProductService()
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()
    
    @pytest.fixture
    def sample_product_data(self):
        """Create sample product data."""
        return ProductCreate(
            name="Test Product",
            description="A test product for testing",
            base_price=100.0,
            current_price=90.0,
            currency="USD",
            quantity_available=10,
            minimum_quantity=1,
            availability=AvailabilityStatus.IN_STOCK,
            images=["http://example.com/image1.jpg"],
            specifications={"color": "red", "size": "large"},
            tags=["test", "sample"],
            is_active=True,
            is_featured=False
        )
    
    @pytest.fixture
    def sample_category_data(self):
        """Create sample category data."""
        return CategoryCreate(
            name="Test Category",
            description="A test category",
            slug="test-category",
            sort_order=1,
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_create_product_basic(self, product_service, mock_db, sample_product_data):
        """Test basic product creation."""
        vendor_id = uuid4()
        
        # Mock database operations
        mock_product = Mock()
        mock_product.id = uuid4()
        mock_product.vendor_id = vendor_id
        mock_product.name = sample_product_data.name
        mock_product.description = sample_product_data.description
        mock_product.base_price = sample_product_data.base_price
        mock_product.current_price = sample_product_data.current_price
        mock_product.currency = sample_product_data.currency
        mock_product.quantity_available = sample_product_data.quantity_available
        mock_product.minimum_quantity = sample_product_data.minimum_quantity
        mock_product.availability = sample_product_data.availability
        mock_product.images = sample_product_data.images
        mock_product.specifications = sample_product_data.specifications
        mock_product.tags = sample_product_data.tags
        mock_product.translations = {}
        mock_product.view_count = 0
        mock_product.favorite_count = 0
        mock_product.average_rating = 0.0
        mock_product.total_reviews = 0
        mock_product.is_active = sample_product_data.is_active
        mock_product.is_featured = sample_product_data.is_featured
        mock_product.created_at = "2024-01-01T00:00:00"
        mock_product.updated_at = "2024-01-01T00:00:00"
        mock_product.category_id = None
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Mock Product constructor
        with patch('app.services.product_service.Product', return_value=mock_product):
            # Test product creation
            result = await product_service.create_product(
                db=mock_db,
                product_data=sample_product_data,
                vendor_id=vendor_id
            )
            
            # Verify database operations were called
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
    
    def test_product_validation(self, sample_product_data):
        """Test product data validation."""
        # Test valid product data
        assert sample_product_data.name == "Test Product"
        assert sample_product_data.base_price == 100.0
        assert sample_product_data.current_price == 90.0
        assert sample_product_data.quantity_available == 10
        assert sample_product_data.availability == AvailabilityStatus.IN_STOCK
        
        # Test price validation
        with pytest.raises(ValueError):
            ProductCreate(
                name="Test Product",
                base_price=-10.0,  # Invalid negative price
                current_price=90.0
            )
        
        with pytest.raises(ValueError):
            ProductCreate(
                name="Test Product",
                base_price=100.0,
                current_price=-5.0  # Invalid negative price
            )
    
    def test_product_update_validation(self):
        """Test product update data validation."""
        # Test valid update data
        update_data = ProductUpdate(
            name="Updated Product",
            current_price=85.0,
            quantity_available=15
        )
        
        assert update_data.name == "Updated Product"
        assert update_data.current_price == 85.0
        assert update_data.quantity_available == 15
        
        # Test partial update
        partial_update = ProductUpdate(name="Partially Updated")
        assert partial_update.name == "Partially Updated"
        assert partial_update.current_price is None
        assert partial_update.quantity_available is None
    
    def test_category_creation(self, sample_category_data):
        """Test category data validation."""
        assert sample_category_data.name == "Test Category"
        assert sample_category_data.slug == "test-category"
        assert sample_category_data.sort_order == 1
        assert sample_category_data.is_active is True
        
        # Test slug validation
        with pytest.raises(ValueError):
            CategoryCreate(
                name="Invalid Category",
                slug="invalid slug with spaces",  # Invalid slug
                sort_order=1
            )
    
    def test_product_search_validation(self):
        """Test product search request validation."""
        from app.schemas.product import ProductSearchRequest
        
        # Test valid search request
        search_request = ProductSearchRequest(
            query="test product",
            min_price=10.0,
            max_price=100.0,
            page=1,
            size=20
        )
        
        assert search_request.query == "test product"
        assert search_request.min_price == 10.0
        assert search_request.max_price == 100.0
        assert search_request.page == 1
        assert search_request.size == 20
        
        # Test price range validation
        with pytest.raises(ValueError):
            ProductSearchRequest(
                min_price=100.0,
                max_price=50.0  # Max price less than min price
            )
    
    def test_product_image_validation(self):
        """Test product image URL validation."""
        # Test valid images
        valid_product = ProductCreate(
            name="Test Product",
            base_price=100.0,
            current_price=90.0,
            images=[
                "http://example.com/image1.jpg",
                "https://example.com/image2.png"
            ]
        )
        
        assert len(valid_product.images) == 2
        
        # Test invalid images
        with pytest.raises(ValueError):
            ProductCreate(
                name="Test Product",
                base_price=100.0,
                current_price=90.0,
                images=["invalid"]  # Too short URL
            )
    
    def test_product_tags_validation(self):
        """Test product tags validation."""
        # Test valid tags
        valid_product = ProductCreate(
            name="Test Product",
            base_price=100.0,
            current_price=90.0,
            tags=["electronics", "gadget", "new"]
        )
        
        assert len(valid_product.tags) == 3
        
        # Test too many tags
        with pytest.raises(ValueError):
            ProductCreate(
                name="Test Product",
                base_price=100.0,
                current_price=90.0,
                tags=[f"tag{i}" for i in range(25)]  # Too many tags
            )
        
        # Test tag length validation
        with pytest.raises(ValueError):
            ProductCreate(
                name="Test Product",
                base_price=100.0,
                current_price=90.0,
                tags=["a" * 60]  # Tag too long
            )


class TestProductModels:
    """Test product model functionality."""
    
    def test_product_model_creation(self):
        """Test product model instantiation."""
        product = Product(
            vendor_id=uuid4(),
            name="Test Product",
            description="Test description",
            base_price=100.0,
            current_price=90.0,
            currency="USD",
            quantity_available=10,
            minimum_quantity=1,
            availability=AvailabilityStatus.IN_STOCK
        )
        
        assert product.name == "Test Product"
        assert product.base_price == 100.0
        assert product.current_price == 90.0
        assert product.availability == AvailabilityStatus.IN_STOCK
    
    def test_category_model_creation(self):
        """Test category model instantiation."""
        category = Category(
            name="Test Category",
            slug="test-category",
            description="Test category description",
            level=0,
            sort_order=1,
            is_active=True
        )
        
        assert category.name == "Test Category"
        assert category.slug == "test-category"
        assert category.level == 0
        assert category.is_active is True
    
    def test_availability_status_enum(self):
        """Test availability status enumeration."""
        assert AvailabilityStatus.IN_STOCK == "in_stock"
        assert AvailabilityStatus.LOW_STOCK == "low_stock"
        assert AvailabilityStatus.OUT_OF_STOCK == "out_of_stock"
        
        # Test enum values
        statuses = [status.value for status in AvailabilityStatus]
        assert "in_stock" in statuses
        assert "low_stock" in statuses
        assert "out_of_stock" in statuses


class TestFileService:
    """Test file service functionality."""
    
    def test_file_service_initialization(self):
        """Test file service initialization."""
        from app.services.file_service import FileService
        
        file_service = FileService()
        
        assert file_service.max_file_size == 10 * 1024 * 1024  # 10MB
        assert "image/jpeg" in file_service.allowed_image_types
        assert "image/png" in file_service.allowed_image_types
        assert "thumbnail" in file_service.image_sizes
        assert "medium" in file_service.image_sizes
        assert "large" in file_service.image_sizes
    
    def test_get_file_extension(self):
        """Test file extension extraction."""
        from app.services.file_service import FileService
        
        file_service = FileService()
        
        assert file_service._get_file_extension("test.jpg") == ".jpg"
        assert file_service._get_file_extension("test.PNG") == ".png"
        assert file_service._get_file_extension("test") == ".jpg"  # Default
        assert file_service._get_file_extension(None) == ".jpg"  # Default
    
    def test_image_url_generation(self):
        """Test image URL generation."""
        from app.services.file_service import FileService
        
        file_service = FileService()
        
        filename = "test-image.jpg"
        
        # Test single size URL
        url = file_service.get_image_url(filename, "large")
        assert url == "/uploads/products/large/test-image.jpg"
        
        # Test all sizes URLs
        all_urls = file_service.get_all_image_urls(filename)
        assert "thumbnail" in all_urls
        assert "medium" in all_urls
        assert "large" in all_urls
        assert all_urls["large"] == "/uploads/products/large/test-image.jpg"