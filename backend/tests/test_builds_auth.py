"""Tests for builds API authentication integration."""
import pytest
from fastapi import status


class TestBuildCreation:
    """Tests for build creation with authentication."""
    
    def test_create_build_anonymous(self, client, sample_build_data, session_id):
        """Anonymous users can create builds."""
        response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers={"X-Session-ID": session_id},
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_build_data["name"]
        assert data["created_by"] == "anonymous"
        assert data["creator"]["is_authenticated"] is False
    
    def test_create_build_authenticated(self, authenticated_client, sample_build_data, session_id):
        """Authenticated users get Steam identity attached to builds."""
        response = authenticated_client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers={"X-Session-ID": session_id},
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_build_data["name"]
        assert data["created_by"] == "TestPlayer"
        assert data["creator"]["is_authenticated"] is True
        assert data["creator"]["steam_id"] == "76561198012345678"


class TestBuildOwnership:
    """Tests for build ownership checks."""
    
    def test_delete_own_build_anonymous(self, client, sample_build_data, session_id):
        """Anonymous users can delete their own builds."""
        # Create build
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers={"X-Session-ID": session_id},
        )
        build_id = create_response.json()["build_id"]
        
        # Delete build
        delete_response = client.delete(
            f"/api/v1/builds/{build_id}",
            headers={"X-Session-ID": session_id},
        )
        
        assert delete_response.status_code == status.HTTP_200_OK
        assert delete_response.json()["deleted"] is True
    
    def test_delete_other_build_anonymous(self, client, sample_build_data, session_id):
        """Anonymous users cannot delete other users' builds."""
        # Create build with one session
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers={"X-Session-ID": session_id},
        )
        build_id = create_response.json()["build_id"]
        
        # Try to delete with different session
        delete_response = client.delete(
            f"/api/v1/builds/{build_id}",
            headers={"X-Session-ID": "sess_different_session_12345678"},
        )
        
        assert delete_response.status_code == status.HTTP_403_FORBIDDEN
        assert delete_response.json()["error"] == "not_owner"
    
    def test_update_build(self, client, sample_build_data, session_id):
        """Build owners can update their builds."""
        # Create build
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers={"X-Session-ID": session_id},
        )
        build_id = create_response.json()["build_id"]
        
        # Update build
        update_response = client.patch(
            f"/api/v1/builds/{build_id}",
            json={"name": "Updated Build Name"},
            headers={"X-Session-ID": session_id},
        )
        
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["name"] == "Updated Build Name"


class TestAuthStatus:
    """Tests for authentication status endpoint."""
    
    def test_auth_status_anonymous(self, client):
        """Anonymous users get anonymous status."""
        response = client.get("/api/v1/builds/auth/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["authenticated"] is False
        assert data["tier"] == "anonymous"
    
    def test_auth_status_authenticated(self, authenticated_client):
        """Authenticated users get their info."""
        response = authenticated_client.get("/api/v1/builds/auth/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["authenticated"] is True
        assert data["player_id"] == "player_123abc"
        assert data["steam_id"] == "76561198012345678"
        assert data["display_name"] == "TestPlayer"


class TestClaimBuilds:
    """Tests for claiming anonymous builds."""
    
    def test_claim_builds_unauthenticated(self, client):
        """Unauthenticated users cannot claim builds."""
        response = client.post(
            "/api/v1/builds/auth/claim",
            json={"session_id": "sess_abc123def456ghi789jkl012"},
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_claim_builds_authenticated(self, client, authenticated_client, sample_build_data, session_id):
        """Authenticated users can claim anonymous builds."""
        # Create anonymous build first (using regular client)
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers={"X-Session-ID": session_id},
        )
        build_id = create_response.json()["build_id"]
        assert create_response.json()["creator"]["is_authenticated"] is False
        
        # Claim builds with authenticated client
        claim_response = authenticated_client.post(
            "/api/v1/builds/auth/claim",
            json={"session_id": session_id},
        )
        
        assert claim_response.status_code == status.HTTP_200_OK
        data = claim_response.json()
        assert data["claimed_count"] == 1
        assert build_id in data["build_ids"]
        
        # Verify build is now authenticated
        get_response = authenticated_client.get(f"/api/v1/builds/{build_id}")
        assert get_response.json()["creator"]["is_authenticated"] is True
        assert get_response.json()["created_by"] == "TestPlayer"


class TestVoting:
    """Tests for voting with authentication."""
    
    def test_vote_anonymous(self, client, sample_build_data, session_id):
        """Anonymous users can vote."""
        # Create build
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers={"X-Session-ID": session_id},
        )
        build_id = create_response.json()["build_id"]
        
        # Vote on build (different session)
        vote_response = client.post(
            f"/api/v1/builds/{build_id}/vote",
            json={"rating": 5},
            headers={"X-Session-ID": "sess_voter_session_123456789ab"},
        )
        
        assert vote_response.status_code == status.HTTP_200_OK
        assert vote_response.json()["your_rating"] == 5
    
    def test_vote_authenticated(self, client, authenticated_client, sample_build_data, session_id):
        """Authenticated users can vote."""
        # Create anonymous build
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers={"X-Session-ID": session_id},
        )
        build_id = create_response.json()["build_id"]
        
        # Vote as authenticated user
        vote_response = authenticated_client.post(
            f"/api/v1/builds/{build_id}/vote",
            json={"rating": 4},
            headers={"X-Session-ID": "sess_auth_user_session_12345ab"},
        )
        
        assert vote_response.status_code == status.HTTP_200_OK
        assert vote_response.json()["your_rating"] == 4
