"""
Authentication module for MyAshes.ai backend.

Provides JWT validation against PAM Platform for Steam-authenticated users.
Supports anonymous access (returns None) for read operations.

Flow:
1. User authenticates via Steam OpenID on PAM Platform (console.solidrust.ai)
2. PAM Platform issues JWT token with player_id and steam_id claims
3. Frontend includes JWT in Authorization header: "Bearer <token>"
4. This module validates JWT against PAM Platform
5. Authenticated users can create/modify builds with their Steam identity

Key design decisions:
- Anonymous access is allowed (get_current_user returns None)
- Use require_auth dependency for write endpoints
- JWT validation is done via PAM Platform API (not local verification)
- Steam ID and display name are extracted from JWT claims
"""
import httpx
import logging
from dataclasses import dataclass
from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from functools import lru_cache
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache for token validation results (TTL: 5 minutes)
_token_cache: dict[str, tuple[float, "AuthenticatedUser"]] = {}
TOKEN_CACHE_TTL = 300  # 5 minutes


@dataclass
class AuthenticatedUser:
    """Represents an authenticated user from PAM Platform."""
    player_id: str  # PAM Platform player ID
    steam_id: Optional[str]  # Steam 64-bit ID
    steam_display_name: Optional[str]  # Steam persona name
    email: Optional[str]  # Email if available
    tier: str = "free"  # Subscription tier (free, pro, enterprise)

    @property
    def display_name(self) -> str:
        """Get the best display name available."""
        if self.steam_display_name:
            return self.steam_display_name
        if self.email:
            return self.email.split('@')[0]
        return f"Player_{self.player_id[:8]}"


def _get_cached_user(token: str) -> Optional[AuthenticatedUser]:
    """Get cached user from token if still valid."""
    if token in _token_cache:
        cached_time, user = _token_cache[token]
        if time.time() - cached_time < TOKEN_CACHE_TTL:
            return user
        else:
            # Expired, remove from cache
            del _token_cache[token]
    return None


def _cache_user(token: str, user: AuthenticatedUser) -> None:
    """Cache authenticated user."""
    # Limit cache size to prevent memory issues
    if len(_token_cache) > 1000:
        # Remove oldest entries
        oldest_tokens = sorted(_token_cache.keys(), key=lambda t: _token_cache[t][0])[:100]
        for t in oldest_tokens:
            del _token_cache[t]
    _token_cache[token] = (time.time(), user)


async def validate_token_with_pam(token: str) -> Optional[AuthenticatedUser]:
    """
    Validate JWT token against PAM Platform.
    
    PAM Platform provides token introspection endpoint that returns:
    - valid: bool
    - player_id: str
    - steam_id: str (optional)
    - steam_display_name: str (optional)
    - email: str (optional)
    - tier: str
    
    Returns AuthenticatedUser if valid, None if invalid.
    """
    # Check cache first
    cached = _get_cached_user(token)
    if cached:
        logger.debug(f"Token cache hit for player {cached.player_id}")
        return cached
    
    # Validate against PAM Platform
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.PAM_PLATFORM_URL}/v1/auth/introspect",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"token": token}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("valid", False):
                    user = AuthenticatedUser(
                        player_id=data.get("player_id", ""),
                        steam_id=data.get("steam_id"),
                        steam_display_name=data.get("steam_display_name"),
                        email=data.get("email"),
                        tier=data.get("tier", "free"),
                    )
                    _cache_user(token, user)
                    logger.info(f"Authenticated user: {user.display_name} (player_id: {user.player_id})")
                    return user
                else:
                    logger.debug("Token validation failed: invalid token")
                    return None
            elif response.status_code == 401:
                logger.debug("Token validation failed: unauthorized")
                return None
            else:
                logger.warning(f"PAM Platform returned unexpected status: {response.status_code}")
                return None
                
    except httpx.TimeoutException:
        logger.error("PAM Platform token validation timed out")
        return None
    except httpx.RequestError as e:
        logger.error(f"PAM Platform request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error validating token: {e}")
        return None


async def get_current_user(request: Request) -> Optional[AuthenticatedUser]:
    """
    Extract and validate JWT from Authorization header.
    
    Returns:
    - AuthenticatedUser if valid token provided
    - None if no token or invalid token (anonymous access)
    
    This dependency allows anonymous access. Use require_auth for
    endpoints that require authentication.
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        return None
    
    # Expect "Bearer <token>" format
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    token = parts[1]
    
    # Validate token with PAM Platform
    return await validate_token_with_pam(token)


async def require_auth(request: Request) -> AuthenticatedUser:
    """
    Dependency that requires authentication.
    
    Raises HTTPException 401 if not authenticated.
    Use this for write endpoints (create, update, delete).
    """
    user = await get_current_user(request)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "authentication_required",
                "message": "Authentication required. Please login with Steam.",
                "status": 401
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


def get_creator_name(user: Optional[AuthenticatedUser]) -> str:
    """
    Get display name for build creator.
    
    Returns:
    - Steam display name if authenticated with Steam
    - "anonymous" if not authenticated
    """
    if user is None:
        return "anonymous"
    return user.display_name
