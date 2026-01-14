import redis.asyncio as redis
from app.core.config import settings
from loguru import logger
from typing import Any, Optional
import json

# Global redis client
_redis_client = None

async def get_cache():
    """Get the Redis cache client."""
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                encoding="utf-8"
            )
            # Test connection
            await _redis_client.ping()
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    return _redis_client

async def set_cache(key: str, value: Any, expire: int = 3600) -> bool:
    """
    Set a value in the cache.
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        expire: Expiration time in seconds (default 1 hour)
        
    Returns:
        True if successful
    """
    cache = await get_cache()
    
    try:
        # Serialize value to JSON if it's not a primitive type
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value)
        
        # Set the value with expiration
        await cache.set(key, value, ex=expire)
        return True
    except Exception as e:
        logger.error(f"Error setting cache key {key}: {e}")
        return False

async def get_cache_value(key: str, default: Any = None) -> Optional[Any]:
    """
    Get a value from the cache.
    
    Args:
        key: Cache key
        default: Default value if key not found
        
    Returns:
        Cached value or default
    """
    cache = await get_cache()
    
    try:
        # Get the value
        value = await cache.get(key)
        
        if value is None:
            return default
        
        # Try to parse as JSON, return raw value if not JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    except Exception as e:
        logger.error(f"Error getting cache key {key}: {e}")
        return default

async def delete_cache(key: str) -> bool:
    """
    Delete a key from the cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if successful
    """
    cache = await get_cache()
    
    try:
        await cache.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error deleting cache key {key}: {e}")
        return False
