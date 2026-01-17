"""Tests for authentication module."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.core.auth import (
    AuthenticatedUser,
    validate_token_with_pam,
    get_current_user,
    require_auth,
    get_creator_name,
    _token_cache,
)


class TestAuthenticatedUser:
    """Tests for AuthenticatedUser dataclass."""
    
    def test_display_name_with_steam_name(self):
        """Should return Steam display name when available."""
        user = AuthenticatedUser(
            player_id="player_123",
            steam_id="76561198012345678",
            steam_display_name="SteamPlayer",
            email="test@example.com",
        )
        assert user.display_name == "SteamPlayer"
    
    def test_display_name_with_email(self):
        """Should return email prefix when no Steam name."""
        user = AuthenticatedUser(
            player_id="player_123",
            steam_id=None,
            steam_display_name=None,
            email="test@example.com",
        )
        assert user.display_name == "test"
    
    def test_display_name_fallback(self):
        """Should return player ID prefix when no Steam name or email."""
        user = AuthenticatedUser(
            player_id="player_123456789",
            steam_id=None,
            steam_display_name=None,
            email=None,
        )
        assert user.display_name == "Player_player_1"


class TestValidateTokenWithPam:
    """Tests for PAM Platform token validation."""
    
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear token cache before each test."""
        _token_cache.clear()
        yield
        _token_cache.clear()
    
    @pytest.mark.asyncio
    async def test_valid_token(self):
        """Should return AuthenticatedUser for valid token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": True,
            "player_id": "player_123",
            "steam_id": "76561198012345678",
            "steam_display_name": "TestPlayer",
            "email": "test@example.com",
            "tier": "pro",
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance
            
            user = await validate_token_with_pam("valid_token")
            
            assert user is not None
            assert user.player_id == "player_123"
            assert user.steam_id == "76561198012345678"
            assert user.steam_display_name == "TestPlayer"
            assert user.tier == "pro"
    
    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Should return None for invalid token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"valid": False}
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance
            
            user = await validate_token_with_pam("invalid_token")
            
            assert user is None
    
    @pytest.mark.asyncio
    async def test_unauthorized_response(self):
        """Should return None for 401 response."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance
            
            user = await validate_token_with_pam("unauthorized_token")
            
            assert user is None
    
    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Should return None on timeout."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance
            
            user = await validate_token_with_pam("timeout_token")
            
            assert user is None
    
    @pytest.mark.asyncio
    async def test_token_caching(self):
        """Should cache validated tokens."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": True,
            "player_id": "player_cached",
            "steam_id": "76561198012345678",
            "tier": "free",
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance
            
            # First call - should call PAM
            user1 = await validate_token_with_pam("cached_token")
            assert mock_instance.post.call_count == 1
            
            # Second call - should use cache
            user2 = await validate_token_with_pam("cached_token")
            assert mock_instance.post.call_count == 1  # No additional call
            
            assert user1.player_id == user2.player_id


class TestGetCreatorName:
    """Tests for get_creator_name helper."""
    
    def test_anonymous_user(self):
        """Should return 'anonymous' for None user."""
        assert get_creator_name(None) == "anonymous"
    
    def test_authenticated_user(self):
        """Should return display name for authenticated user."""
        user = AuthenticatedUser(
            player_id="player_123",
            steam_id="76561198012345678",
            steam_display_name="SteamPlayer",
            email=None,
        )
        assert get_creator_name(user) == "SteamPlayer"
