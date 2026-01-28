"""Tests for Feedback API endpoints.

Covers feedback submission and validation.
"""
import pytest
from fastapi.testclient import TestClient


class TestFeedbackSubmission:
    """Tests for feedback submission."""
    
    def test_submit_feedback_success(self, client: TestClient, session_headers: dict, sample_feedback_data: dict):
        """Submitting feedback returns 201 and feedback ID."""
        response = client.post(
            "/api/v1/feedback",
            json=sample_feedback_data,
            headers=session_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "feedback_id" in data
        assert data["feedback_id"].startswith("f_")
        assert "received_at" in data
    
    def test_submit_feedback_minimal(self, client: TestClient, session_headers: dict):
        """Feedback can be submitted with required fields only."""
        minimal_data = {
            "query": "How to craft?",
            "response_snippet": "You need materials...",
            "search_mode": "quick",
            "rating": "down"
        }
        response = client.post(
            "/api/v1/feedback",
            json=minimal_data,
            headers=session_headers
        )
        
        assert response.status_code == 201
    
    def test_submit_feedback_with_comment(self, client: TestClient, session_headers: dict):
        """Feedback can include optional comment."""
        data = {
            "query": "Best tank class?",
            "response_snippet": "The Fighter/Tank is great...",
            "search_mode": "smart",
            "rating": "up",
            "comment": "This was exactly what I needed!"
        }
        response = client.post(
            "/api/v1/feedback",
            json=data,
            headers=session_headers
        )
        
        assert response.status_code == 201


class TestFeedbackValidation:
    """Tests for feedback validation."""
    
    def test_invalid_rating_value(self, client: TestClient, session_headers: dict):
        """Invalid rating values are rejected."""
        data = {
            "query": "Test query",
            "response_snippet": "Test response",
            "search_mode": "quick",
            "rating": "invalid"
        }
        response = client.post(
            "/api/v1/feedback",
            json=data,
            headers=session_headers
        )
        
        assert response.status_code == 422
    
    def test_invalid_search_mode(self, client: TestClient, session_headers: dict):
        """Invalid search mode values are rejected."""
        data = {
            "query": "Test query",
            "response_snippet": "Test response",
            "search_mode": "turbo",  # Invalid mode
            "rating": "up"
        }
        response = client.post(
            "/api/v1/feedback",
            json=data,
            headers=session_headers
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client: TestClient, session_headers: dict):
        """Missing required fields are rejected."""
        # Missing query
        response = client.post(
            "/api/v1/feedback",
            json={
                "response_snippet": "Test",
                "search_mode": "quick",
                "rating": "up"
            },
            headers=session_headers
        )
        assert response.status_code == 422
        
        # Missing rating
        response = client.post(
            "/api/v1/feedback",
            json={
                "query": "Test",
                "response_snippet": "Test",
                "search_mode": "quick"
            },
            headers=session_headers
        )
        assert response.status_code == 422
    
    def test_response_snippet_truncation(self, client: TestClient, session_headers: dict):
        """Long response snippets are accepted (truncated server-side)."""
        long_snippet = "x" * 1000  # Exceeds 500 char limit
        data = {
            "query": "Test query",
            "response_snippet": long_snippet,
            "search_mode": "deep",
            "rating": "down"
        }
        response = client.post(
            "/api/v1/feedback",
            json=data,
            headers=session_headers
        )
        
        # Should succeed - validation truncates to 500
        assert response.status_code == 201


class TestFeedbackSessionTracking:
    """Tests for session tracking in feedback."""
    
    def test_feedback_without_session(self, client: TestClient, sample_feedback_data: dict):
        """Feedback can be submitted without session ID."""
        response = client.post(
            "/api/v1/feedback",
            json=sample_feedback_data
            # No session headers
        )
        
        # Should still work, session_id will be null
        assert response.status_code == 201
