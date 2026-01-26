"""
Redis configuration and connection management.

This module sets up Redis for caching, session management, and real-time
communication support in the Multilingual Mandi platform.
"""

import json
from typing import Any, Optional, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()

# Global Redis connection
redis_client: Optional[Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_keepalive=True,
        socket_keepalive_options={},
        health_check_interval=30,
    )
    
    # Test connection
    try:
        await redis_client.ping()
        print("✅ Redis connection established")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        raise


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def get_redis() -> Redis:
    """
    Get Redis client instance.
    
    Returns:
        Redis: Redis client instance
        
    Raises:
        RuntimeError: If Redis is not initialized
    """
    if redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client


class RedisCache:
    """Redis cache utility class."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except (json.JSONDecodeError, Exception):
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized_value = json.dumps(value, default=str)
            expire_time = expire or settings.REDIS_EXPIRE_TIME
            return await self.redis.setex(key, expire_time, serialized_value)
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False otherwise
        """
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            return await self.redis.exists(key) > 0
        except Exception:
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value after increment or None if failed
        """
        try:
            return await self.redis.incrby(key, amount)
        except Exception:
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for key.
        
        Args:
            key: Cache key
            seconds: Expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return await self.redis.expire(key, seconds)
        except Exception:
            return False


def get_cache() -> RedisCache:
    """
    Get Redis cache instance.
    
    Returns:
        RedisCache: Redis cache utility instance
    """
    return RedisCache(get_redis())


class SessionManager:
    """Redis-based session management."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.session_prefix = "session:"
    
    async def create_session(
        self,
        session_id: str,
        user_data: dict,
        expire: Optional[int] = None
    ) -> bool:
        """
        Create user session.
        
        Args:
            session_id: Unique session identifier
            user_data: User session data
            expire: Session expiration time in seconds
            
        Returns:
            True if session created successfully
        """
        try:
            key = f"{self.session_prefix}{session_id}"
            serialized_data = json.dumps(user_data, default=str)
            expire_time = expire or settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            return await self.redis.setex(key, expire_time, serialized_data)
        except Exception:
            return False
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get user session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        try:
            key = f"{self.session_prefix}{session_id}"
            data = await self.redis.get(key)
            if data is None:
                return None
            return json.loads(data)
        except (json.JSONDecodeError, Exception):
            return None
    
    async def update_session(
        self,
        session_id: str,
        user_data: dict,
        extend_expiry: bool = True
    ) -> bool:
        """
        Update user session data.
        
        Args:
            session_id: Session identifier
            user_data: Updated user data
            extend_expiry: Whether to extend session expiry
            
        Returns:
            True if session updated successfully
        """
        try:
            key = f"{self.session_prefix}{session_id}"
            serialized_data = json.dumps(user_data, default=str)
            
            if extend_expiry:
                expire_time = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                return await self.redis.setex(key, expire_time, serialized_data)
            else:
                return await self.redis.set(key, serialized_data, keepttl=True)
        except Exception:
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete user session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session deleted successfully
        """
        try:
            key = f"{self.session_prefix}{session_id}"
            result = await self.redis.delete(key)
            return result > 0
        except Exception:
            return False


def get_session_manager() -> SessionManager:
    """
    Get session manager instance.
    
    Returns:
        SessionManager: Session manager instance
    """
    return SessionManager(get_redis())