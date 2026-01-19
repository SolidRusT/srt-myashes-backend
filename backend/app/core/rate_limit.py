"""
Rate limiting configuration using slowapi.

Provides configurable rate limits for API endpoints:
- Read operations (GET): Higher limits
- Write operations (POST/PUT/DELETE): Lower limits
- Global fallback limits

Supports both IP-based and session-based rate limiting.
"""
import logging
from typing import Optional, Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_rate_limit_key(request: Request) -> str:
    """
    Get the rate limit key for a request.
    
    Strategy:
    1. If authenticated (has player_id), use player_id
    2. If has session ID, use session_id  
    3. Fall back to IP address
    
    This prevents authenticated users from being blocked due to shared IPs
    while still protecting against anonymous abuse.
    """
    # Try to get player_id from request state (set by auth middleware)
    player_id = getattr(request.state, "player_id", None)
    if player_id:
        return f"player:{player_id}"
    
    # Try to get session_id from request state or header
    session_id = getattr(request.state, "session_id", None) or request.headers.get("X-Session-ID")
    if session_id:
        return f"session:{session_id}"
    
    # Fall back to IP address
    return get_remote_address(request)


def get_ip_key(request: Request) -> str:
    """Get rate limit key based on IP address only."""
    return get_remote_address(request)


# Rate limit configurations
class RateLimitConfig:
    """Rate limit configuration values."""
    
    # Read operations (GET requests)
    # Higher limits since reads are less expensive
    READ_LIMIT: str = "100/minute"
    READ_LIMIT_BUILDS_LIST: str = "60/minute"  # List endpoints can be heavier
    
    # Write operations (POST/PUT/PATCH/DELETE)
    # Lower limits to prevent abuse
    WRITE_LIMIT: str = "30/minute"
    WRITE_LIMIT_CREATE: str = "20/minute"  # Creating new resources
    WRITE_LIMIT_VOTE: str = "60/minute"  # Voting is less heavy
    
    # Global fallback
    DEFAULT_LIMIT: str = "200/minute"
    
    # Burst protection - short window limits
    BURST_LIMIT: str = "10/second"
    
    # Enable/disable rate limiting
    ENABLED: bool = True


# Initialize the limiter
# Uses Redis if available, falls back to in-memory storage
def _get_limiter_storage() -> str:
    """Get the storage URL for rate limiting."""
    if settings.REDIS_HOST and settings.REDIS_HOST != "localhost":
        # Use Redis for distributed rate limiting
        password_part = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
        return f"redis://{password_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    # Fall back to memory (not recommended for production with multiple replicas)
    return "memory://"


# Create the limiter instance
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[RateLimitConfig.DEFAULT_LIMIT],
    storage_uri=_get_limiter_storage(),
    strategy="fixed-window",  # Options: fixed-window, moving-window
    headers_enabled=True,  # Add X-RateLimit-* headers to responses
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    
    Returns a JSON response with:
    - 429 status code
    - Retry-After header
    - User-friendly error message
    """
    # Get retry-after from the exception
    retry_after = getattr(exc, "retry_after", 60)
    
    logger.warning(
        f"Rate limit exceeded for {get_rate_limit_key(request)}: "
        f"limit={exc.detail}, retry_after={retry_after}s"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please slow down.",
            "detail": str(exc.detail),
            "retry_after": retry_after,
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(exc.detail).split("/")[0] if "/" in str(exc.detail) else "unknown",
        },
    )


# Convenience decorators for common rate limits
def limit_reads(limit: str = RateLimitConfig.READ_LIMIT) -> Callable:
    """Decorator for read-heavy endpoints."""
    return limiter.limit(limit)


def limit_writes(limit: str = RateLimitConfig.WRITE_LIMIT) -> Callable:
    """Decorator for write endpoints."""
    return limiter.limit(limit)


def limit_creates(limit: str = RateLimitConfig.WRITE_LIMIT_CREATE) -> Callable:
    """Decorator for resource creation endpoints."""
    return limiter.limit(limit)


def limit_votes(limit: str = RateLimitConfig.WRITE_LIMIT_VOTE) -> Callable:
    """Decorator for voting endpoints."""
    return limiter.limit(limit)
