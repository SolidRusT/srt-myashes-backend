"""Tests for Build API endpoints.

Covers CRUD operations and voting functionality.
"""
import pytest
from fastapi.testclient import TestClient


class TestBuildCreate:
    """Tests for build creation."""
    
    def test_create_build_success(self, client: TestClient, session_headers: dict, sample_build_data: dict):
        """Creating a build returns 201 and valid build ID."""
        response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers=session_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "build_id" in data
        assert data["build_id"].startswith("b_")
        assert data["name"] == sample_build_data["name"]
        assert data["primary_archetype"] == sample_build_data["primary_archetype"]
    
    def test_create_build_minimal(self, client: TestClient, session_headers: dict):
        """Build can be created with minimal required fields."""
        minimal_data = {
            "name": "Minimal Build",
            "primary_archetype": "Mage",
        }
        response = client.post(
            "/api/v1/builds",
            json=minimal_data,
            headers=session_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Build"
    
    def test_create_build_missing_name(self, client: TestClient, session_headers: dict):
        """Build creation fails without required name field."""
        response = client.post(
            "/api/v1/builds",
            json={"primary_archetype": "Tank"},
            headers=session_headers
        )
        
        assert response.status_code == 422


class TestBuildRead:
    """Tests for reading builds."""
    
    def test_list_builds_empty(self, client: TestClient):
        """List builds returns empty list when no builds exist."""
        response = client.get("/api/v1/builds")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["items"] == []
        assert data["total"] == 0
    
    def test_list_builds_with_data(self, client: TestClient, session_headers: dict, sample_build_data: dict):
        """List builds returns created builds."""
        # Create a build first
        client.post("/api/v1/builds", json=sample_build_data, headers=session_headers)
        
        response = client.get("/api/v1/builds")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == sample_build_data["name"]
    
    def test_list_builds_pagination(self, client: TestClient, session_headers: dict):
        """List builds respects pagination parameters."""
        # Create multiple builds
        for i in range(5):
            client.post(
                "/api/v1/builds",
                json={"name": f"Build {i}", "primary_archetype": "Tank"},
                headers=session_headers
            )
        
        # Test pagination
        response = client.get("/api/v1/builds?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
    
    def test_get_build_by_id(self, client: TestClient, session_headers: dict, sample_build_data: dict):
        """Get build by ID returns correct build."""
        # Create a build
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers=session_headers
        )
        build_id = create_response.json()["build_id"]
        
        # Get by ID
        response = client.get(f"/api/v1/builds/{build_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["build_id"] == build_id
        assert data["name"] == sample_build_data["name"]
    
    def test_get_build_not_found(self, client: TestClient):
        """Get non-existent build returns 404."""
        response = client.get("/api/v1/builds/b_nonexistent")
        
        assert response.status_code == 404


class TestBuildUpdate:
    """Tests for updating builds."""
    
    def test_update_build_success(self, client: TestClient, session_headers: dict, sample_build_data: dict):
        """Owner can update their build."""
        # Create a build
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers=session_headers
        )
        build_id = create_response.json()["build_id"]
        
        # Update it
        update_data = {"name": "Updated Build Name", "description": "New description"}
        response = client.patch(
            f"/api/v1/builds/{build_id}",
            json=update_data,
            headers=session_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Build Name"
        assert data["description"] == "New description"
    
    def test_update_build_different_session(self, client: TestClient, session_headers: dict, sample_build_data: dict):
        """Non-owner cannot update build (returns 403)."""
        # Create a build with one session
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers=session_headers
        )
        build_id = create_response.json()["build_id"]
        
        # Try to update with different session
        different_session = {"X-Session-ID": "sess_different_session"}
        response = client.patch(
            f"/api/v1/builds/{build_id}",
            json={"name": "Hacked Name"},
            headers=different_session
        )
        
        assert response.status_code == 403


class TestBuildDelete:
    """Tests for deleting builds."""
    
    def test_delete_build_success(self, client: TestClient, session_headers: dict, sample_build_data: dict):
        """Owner can delete their build."""
        # Create a build
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers=session_headers
        )
        build_id = create_response.json()["build_id"]
        
        # Delete it
        response = client.delete(
            f"/api/v1/builds/{build_id}",
            headers=session_headers
        )
        
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f"/api/v1/builds/{build_id}")
        assert get_response.status_code == 404
    
    def test_delete_build_different_session(self, client: TestClient, session_headers: dict, sample_build_data: dict):
        """Non-owner cannot delete build (returns 403)."""
        # Create a build
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers=session_headers
        )
        build_id = create_response.json()["build_id"]
        
        # Try to delete with different session
        different_session = {"X-Session-ID": "sess_attacker_session"}
        response = client.delete(
            f"/api/v1/builds/{build_id}",
            headers=different_session
        )
        
        assert response.status_code == 403


class TestBuildVoting:
    """Tests for build voting."""
    
    def test_vote_on_build(self, client: TestClient, session_headers: dict, sample_build_data: dict):
        """User can vote on a build."""
        # Create a build
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers=session_headers
        )
        build_id = create_response.json()["build_id"]
        
        # Vote on it
        response = client.post(
            f"/api/v1/builds/{build_id}/vote",
            json={"rating": 5},
            headers=session_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["average_rating"] == 5.0
        assert data["vote_count"] == 1
    
    def test_vote_updates_average(self, client: TestClient, sample_build_data: dict):
        """Multiple votes update average rating."""
        session1 = {"X-Session-ID": "sess_user1"}
        session2 = {"X-Session-ID": "sess_user2"}
        
        # Create a build
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers=session1
        )
        build_id = create_response.json()["build_id"]
        
        # Vote with first user
        client.post(
            f"/api/v1/builds/{build_id}/vote",
            json={"rating": 4},
            headers=session1
        )
        
        # Vote with second user
        response = client.post(
            f"/api/v1/builds/{build_id}/vote",
            json={"rating": 2},
            headers=session2
        )
        
        data = response.json()
        assert data["average_rating"] == 3.0  # (4 + 2) / 2
        assert data["vote_count"] == 2
    
    def test_vote_invalid_rating(self, client: TestClient, session_headers: dict, sample_build_data: dict):
        """Invalid rating values are rejected."""
        # Create a build
        create_response = client.post(
            "/api/v1/builds",
            json=sample_build_data,
            headers=session_headers
        )
        build_id = create_response.json()["build_id"]
        
        # Try invalid rating (too high)
        response = client.post(
            f"/api/v1/builds/{build_id}/vote",
            json={"rating": 10},
            headers=session_headers
        )
        
        assert response.status_code == 422
        
        # Try invalid rating (too low)
        response = client.post(
            f"/api/v1/builds/{build_id}/vote",
            json={"rating": 0},
            headers=session_headers
        )
        
        assert response.status_code == 422
