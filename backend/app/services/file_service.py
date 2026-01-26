"""
File service for handling file uploads and storage.

This module provides functionality for uploading, storing, and managing
files including product images and other media assets.
"""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from PIL import Image
import aiofiles


class FileService:
    """Service class for file operations."""
    
    def __init__(self):
        """Initialize file service with configuration."""
        self.upload_dir = Path("uploads")
        self.product_images_dir = self.upload_dir / "products"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_image_types = {
            "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"
        }
        self.image_sizes = {
            "thumbnail": (150, 150),
            "medium": (400, 400),
            "large": (800, 800)
        }
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure upload directories exist."""
        self.upload_dir.mkdir(exist_ok=True)
        self.product_images_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different image sizes
        for size_name in self.image_sizes.keys():
            (self.product_images_dir / size_name).mkdir(exist_ok=True)
    
    async def upload_product_image(
        self,
        file: UploadFile,
        product_id: uuid.UUID
    ) -> str:
        """
        Upload and process a product image.
        
        Returns the URL of the uploaded image.
        """
        # Validate file
        await self._validate_image_file(file)
        
        # Generate unique filename
        file_extension = self._get_file_extension(file.filename)
        filename = f"{product_id}_{uuid.uuid4().hex}{file_extension}"
        
        # Save original file
        original_path = self.product_images_dir / filename
        await self._save_uploaded_file(file, original_path)
        
        # Process and create different sizes
        await self._process_image_sizes(original_path, filename)
        
        # Return the URL for the large image (main display)
        return f"/uploads/products/large/{filename}"
    
    async def _validate_image_file(self, file: UploadFile) -> None:
        """Validate uploaded image file."""
        # Check content type
        if file.content_type not in self.allowed_image_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(self.allowed_image_types)}"
            )
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB"
            )
        
        # Validate that it's actually an image
        try:
            contents = await file.read()
            file.file.seek(0)  # Reset for later use
            
            # Try to open with PIL to validate it's a real image
            with Image.open(file.file) as img:
                img.verify()
            
            file.file.seek(0)  # Reset again
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )
    
    def _get_file_extension(self, filename: Optional[str]) -> str:
        """Get file extension from filename."""
        if not filename:
            return ".jpg"
        
        extension = Path(filename).suffix.lower()
        if not extension:
            return ".jpg"
        
        return extension
    
    async def _save_uploaded_file(self, file: UploadFile, path: Path) -> None:
        """Save uploaded file to disk."""
        try:
            async with aiofiles.open(path, 'wb') as f:
                contents = await file.read()
                await f.write(contents)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
    
    async def _process_image_sizes(self, original_path: Path, filename: str) -> None:
        """Process image into different sizes."""
        try:
            with Image.open(original_path) as img:
                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create different sizes
                for size_name, dimensions in self.image_sizes.items():
                    # Create thumbnail maintaining aspect ratio
                    img_copy = img.copy()
                    img_copy.thumbnail(dimensions, Image.Resampling.LANCZOS)
                    
                    # Create new image with exact dimensions and paste thumbnail centered
                    new_img = Image.new('RGB', dimensions, (255, 255, 255))
                    
                    # Calculate position to center the image
                    x = (dimensions[0] - img_copy.width) // 2
                    y = (dimensions[1] - img_copy.height) // 2
                    
                    new_img.paste(img_copy, (x, y))
                    
                    # Save processed image
                    size_path = self.product_images_dir / size_name / filename
                    new_img.save(size_path, 'JPEG', quality=85, optimize=True)
        
        except Exception as e:
            # Clean up original file if processing fails
            if original_path.exists():
                original_path.unlink()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process image: {str(e)}"
            )
    
    async def delete_product_image(self, image_url: str) -> None:
        """Delete a product image and all its sizes."""
        try:
            # Extract filename from URL
            filename = Path(image_url).name
            
            # Delete all sizes
            for size_name in self.image_sizes.keys():
                size_path = self.product_images_dir / size_name / filename
                if size_path.exists():
                    size_path.unlink()
            
            # Delete original if it exists
            original_path = self.product_images_dir / filename
            if original_path.exists():
                original_path.unlink()
        
        except Exception as e:
            # Log error but don't raise exception
            # (file might already be deleted or not exist)
            print(f"Warning: Failed to delete image {image_url}: {str(e)}")
    
    def get_image_url(self, filename: str, size: str = "large") -> str:
        """Get the URL for an image of a specific size."""
        if size not in self.image_sizes:
            size = "large"
        
        return f"/uploads/products/{size}/{filename}"
    
    def get_all_image_urls(self, filename: str) -> dict:
        """Get URLs for all sizes of an image."""
        return {
            size: f"/uploads/products/{size}/{filename}"
            for size in self.image_sizes.keys()
        }