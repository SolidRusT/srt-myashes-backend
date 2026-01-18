"""
Authentication utilities for MyAshes.ai backend.

Provides:
- Admin authentication via Steam ID whitelist
- User authentication via PAM Platform token validation
"""
from typing import Optional
import logging
import httpx
from pydantic import BaseModel
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

logger = logging.getLogger(__name__)

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


# =============================================================================
# User Authentication (PAM Platform Token Validation)
# =============================================================================


class AuthenticatedUser(BaseModel):
    """
    Authenticated user data from PAM Platform.

    Represents a validated user session with Steam credentials.
    """
    player_id: str
    steam_id: str
    steam_display_name: Optional[str] = None
    tier: str = "free"

    @property
    def display_name(self) -> str:
        """User's display name for UI."""
        return self.steam_display_name or f"Player {self.player_id[:8]}"

    @property
    def is_authenticated(self) -> bool:
        """Always True for AuthenticatedUser instances."""
        return True


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[AuthenticatedUser]:
    """
    Extract and validate authenticated user from PAM Platform token.

    This dependency validates JWT tokens against PAM Platform's authentication
    service. Authentication is optional - returns None if no token or invalid.

    Flow:
    1. Extract Bearer token from Authorization header
    2. Validate token with PAM Platform GraphQL API
    3. Return AuthenticatedUser if valid, None otherwise

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials (optional)

    Returns:
        AuthenticatedUser if token is valid, None otherwise

    Note:
        Does not raise exceptions. Authentication is optional by default.
        Use in endpoints that optionally support authenticated users.
    """
    # Check for token in header first
    if not credentials:
        # Fallback: Check X-Steam-ID header (set by API gateway after PAM validation)
        steam_id = request.headers.get("X-Steam-ID")
        steam_name = request.headers.get("X-Steam-Display-Name")
        player_id = request.headers.get("X-Player-ID")

        if steam_id and player_id:
            # User was already authenticated by API gateway
            return AuthenticatedUser(
                player_id=player_id,
                steam_id=steam_id,
                steam_display_name=steam_name,
                tier="free",  # Default tier if not provided
            )

        return None

    token = credentials.credentials

    # Validate token with PAM Platform GraphQL API
    try:
        async with httpx.AsyncClient(timeout=float(settings.PAM_PLATFORM_TIMEOUT)) as client:
            response = await client.post(
                f"{settings.PAM_PLATFORM_URL}/graphql",
                json={
                    "query": """
                        query ValidateToken($token: String!) {
                            validateToken(token: $token) {
                                valid
                                playerId
                                steamId
                                steamDisplayName
                                tier
                            }
                        }
                    """,
                    "variables": {"token": token}
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                validation = data.get("data", {}).get("validateToken", {})

                if validation.get("valid"):
                    return AuthenticatedUser(
                        player_id=validation["playerId"],
                        steam_id=validation["steamId"],
                        steam_display_name=validation.get("steamDisplayName"),
                        tier=validation.get("tier", "free"),
                    )
                else:
                    logger.debug("PAM Platform returned invalid token")
            else:
                logger.warning(f"PAM Platform returned status {response.status_code}")

    except httpx.TimeoutException:
        logger.warning("PAM Platform token validation timed out")
    except httpx.HTTPError as e:
        logger.warning(f"PAM Platform HTTP error during token validation: {e}")
    except Exception as e:
        logger.error(f"Unexpected error validating PAM token: {e}", exc_info=True)

    return None
