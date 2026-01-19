"""
Redis/Valkey cache client with graceful degradation.

Provides caching functionality that continues working even if Redis is unavailable.
Used for PAM token caching and rate limiting.
"""
from typing import Optional
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


# Global connection pool for connection reuse
_connection_pool: Optional[ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None
_redis_available: bool = True  # Track if Redis is reachable


def _get_connection_pool() -> ConnectionPool:
    """Get or create Redis connection pool."""
    global _connection_pool
    
    if _connection_pool is None:
        _connection_pool = ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            max_connections=10,
            retry_on_timeout=True,
        )
    
    return _connection_pool


async def get_redis() -> Optional[redis.Redis]:
    """
    Get Redis client with graceful degradation.
    
    Returns None if Redis is unavailable, allowing the application
    to continue without caching rather than crashing.
    """
    global _redis_client, _redis_available
    
    # If Redis was previously unavailable, attempt reconnection
    # but don't spam connection attempts
    if not _redis_available:
        return None
    
    if _redis_client is None:
        try:
            pool = _get_connection_pool()
            _redis_client = redis.Redis(connection_pool=pool)
            # Test connection
            await _redis_client.ping()
            logger.info(f"Redis connection established: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Continuing without cache.")
            _redis_available = False
            _redis_client = None
            return None
    
    return _redis_client


async def reset_redis_connection():
    """
    Reset Redis connection state to allow reconnection attempt.
    
    Call this periodically (e.g., from health check) to retry
    Redis connection if it was previously unavailable.
    """
    global _redis_client, _redis_available, _connection_pool
    
    if _redis_client:
        try:
            await _redis_client.close()
        except Exception:
            pass
    
    _redis_client = None
    _redis_available = True
    _connection_pool = None


async def check_redis_health() -> tuple[bool, str]:
    """
    Check Redis connectivity for health endpoint.
    
    Returns:
        Tuple of (is_healthy: bool, status_message: str)
    """
    global _redis_available
    
    try:
        # Try to get or establish connection
        _redis_available = True  # Allow reconnection attempt
        client = await get_redis()
        
        if client is None:
            return False, "connection failed"
        
        # Ping to verify connection
        await client.ping()
        return True, "ok"
        
    except Exception as e:
        error_msg = str(e)[:100] if str(e) else "unknown error"
        logger.warning(f"Redis health check failed: {e}")
        return False, f"error: {error_msg}"


async def cache_get(key: str) -> Optional[str]:
    """
    Get value from cache with graceful degradation.
    
    Args:
        key: Cache key to retrieve
        
    Returns:
        Cached value or None if not found or Redis unavailable
    """
    client = await get_redis()
    if client is None:
        return None
    
    try:
        return await client.get(key)
    except Exception as e:
        logger.warning(f"Redis GET failed for key '{key}': {e}")
        return None


async def cache_set(key: str, value: str, ttl: int = 300) -> bool:
    """
    Set value in cache with graceful degradation.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time-to-live in seconds (default 5 minutes)
        
    Returns:
        True if cached successfully, False otherwise
    """
    client = await get_redis()
    if client is None:
        return False
    
    try:
        await client.setex(key, ttl, value)
        return True
    except Exception as e:
        logger.warning(f"Redis SET failed for key '{key}': {e}")
        return False


async def cache_delete(key: str) -> bool:
    """
    Delete value from cache with graceful degradation.
    
    Args:
        key: Cache key to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    client = await get_redis()
    if client is None:
        return False
    
    try:
        await client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Redis DELETE failed for key '{key}': {e}")
        return False


async def cache_exists(key: str) -> bool:
    """
    Check if key exists in cache.
    
    Args:
        key: Cache key to check
        
    Returns:
        True if key exists, False otherwise (or if Redis unavailable)
    """
    client = await get_redis()
    if client is None:
        return False
    
    try:
        return await client.exists(key) > 0
    except Exception as e:
        logger.warning(f"Redis EXISTS failed for key '{key}': {e}")
        return False


async def close_redis():
    """Close Redis connection gracefully."""
    global _redis_client, _connection_pool
    
    if _redis_client:
        try:
            await _redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")
        finally:
            _redis_client = None
    
    if _connection_pool:
        try:
            await _connection_pool.disconnect()
        except Exception:
            pass
        finally:
            _connection_pool = None
