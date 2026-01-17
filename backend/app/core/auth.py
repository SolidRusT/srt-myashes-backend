"""
Authentication utilities for MyAshes.ai backend.

Provides admin authentication via Steam ID whitelist.
"""
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

# HTTP Bearer scheme for token extraction
security = HTTPBearer(auto_error=False)


def get_steam_id_from_request(request: Request) -> Optional[str]:
    """
    Extract Steam ID from request.
    
    Checks multiple sources:
    1. X-Steam-ID header (set by PAM Platform after validation)
    2. Request state (set by middleware after PAM token validation)
    
    Returns None if no Steam ID found.
    """
    # Check header first (set by API gateway/PAM after auth)
    steam_id = request.headers.get("X-Steam-ID")
    if steam_id:
        return steam_id
    
    # Check request state (set by auth middleware)
    steam_id = getattr(request.state, "steam_id", None)
    if steam_id:
        return steam_id
    
    return None


def is_admin(steam_id: Optional[str]) -> bool:
    """
    Check if a Steam ID is in the admin whitelist.
    
    Args:
        steam_id: Steam 64-bit ID to check
        
    Returns:
        True if steam_id is in ADMIN_STEAM_IDS, False otherwise
    """
    if not steam_id:
        return False
    
    return steam_id in settings.ADMIN_STEAM_IDS


async def require_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    FastAPI dependency that requires admin access.
    
    Extracts Steam ID from request and verifies it's in the admin whitelist.
    Raises 401 if no Steam ID found, 403 if not an admin.
    
    Returns:
        The admin's Steam ID
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
    """
    steam_id = get_steam_id_from_request(request)
    
    if not steam_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with Steam.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not is_admin(steam_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. Your Steam ID is not authorized.",
        )
    
    return steam_id


async def optional_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    FastAPI dependency that optionally extracts admin Steam ID.
    
    Unlike require_admin, this doesn't raise exceptions.
    Returns the Steam ID if authenticated and admin, None otherwise.
    
    Returns:
        Admin Steam ID or None
    """
    steam_id = get_steam_id_from_request(request)
    
    if steam_id and is_admin(steam_id):
        return steam_id
    
    return None
