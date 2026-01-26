"""
Application configuration settings.

This module defines all configuration settings for the Multilingual Mandi
platform using Pydantic settings management.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings configuration."""
    
    # Application settings
    APP_NAME: str = "Multilingual Mandi"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    ALLOWED_HOSTS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="ALLOWED_HOSTS"
    )
    
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/multilingual_mandi",
        env="DATABASE_URL"
    )
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_EXPIRE_TIME: int = Field(default=3600, env="REDIS_EXPIRE_TIME")  # 1 hour
    
    # Security settings
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        env="REFRESH_TOKEN_EXPIRE_DAYS"
    )
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Translation API settings
    TRANSLATION_API_KEY: Optional[str] = Field(default=None, env="TRANSLATION_API_KEY")
    TRANSLATION_API_URL: str = Field(
        default="https://translation.googleapis.com/language/translate/v2",
        env="TRANSLATION_API_URL"
    )
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=["en", "es", "fr", "de", "zh", "hi", "ar", "pt", "ru", "ja"],
        env="SUPPORTED_LANGUAGES"
    )
    
    # WebSocket settings
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(
        default=30,
        env="WEBSOCKET_HEARTBEAT_INTERVAL"
    )
    
    # Celery settings (for background tasks)
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/1",
        env="CELERY_RESULT_BACKEND"
    )
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse ALLOWED_HOSTS from string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("ALLOWED_FILE_TYPES", pre=True)
    def parse_allowed_file_types(cls, v):
        """Parse ALLOWED_FILE_TYPES from string or list."""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    
    @validator("SUPPORTED_LANGUAGES", pre=True)
    def parse_supported_languages(cls, v):
        """Parse SUPPORTED_LANGUAGES from string or list."""
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()