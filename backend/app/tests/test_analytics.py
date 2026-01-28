"""Tests for Analytics API endpoints.

Covers search analytics recording and retrieval.
"""
import pytest
from fastapi.testclient import TestClient


class TestSearchAnalytics:
    """Tests for search analytics recording."""
    
    def test_record_search_success(self, client: TestClient, session_headers: dict, sample_analytics_data: dict):
        """Recording search analytics returns 201."""
        response = client.post(
            "/api/v1/analytics/search",
            json=sample_analytics_data,
            headers=session_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "analytics_id" in data
        assert "recorded_at" in data
    
    def test_record_search_minimal(self, client: TestClient, session_headers: dict):
        """Search can be recorded with minimal data."""
        minimal_data = {
            "query": "simple query",
            "search_mode": "quick",
            "result_count": 0
        }
        response = client.post(
            "/api/v1/analytics/search",
            json=minimal_data,
            headers=session_headers
        )
        
        assert response.status_code == 201
    
    def test_record_search_zero_results(self, client: TestClient, session_headers: dict):
        """Zero result searches are recorded correctly."""
        data = {
            "query": "gibberish query that returns nothing",
            "search_mode": "deep",
            "result_count": 0
        }
        response = client.post(
            "/api/v1/analytics/search",
            json=data,
            headers=session_headers
        )
        
        assert response.status_code == 201


class TestPopularQueries:
    """Tests for popular queries endpoint."""
    
    def test_popular_queries_empty(self, client: TestClient):
        """Popular queries returns empty list when no data."""
        response = client.get("/api/v1/analytics/popular-queries")
        
        assert response.status_code == 200
        data = response.json()
        assert "queries" in data
        assert data["queries"] == []
    
    def test_popular_queries_sorted(self, client: TestClient, session_headers: dict):
        """Popular queries are sorted by frequency."""
        # Record same query multiple times
        for _ in range(5):
            client.post(
                "/api/v1/analytics/search",
                json={"query": "popular query", "search_mode": "quick", "result_count": 10},
                headers=session_headers
            )
        
        # Record different query fewer times
        for _ in range(2):
            client.post(
                "/api/v1/analytics/search",
                json={"query": "less popular", "search_mode": "quick", "result_count": 5},
                headers=session_headers
            )
        
        response = client.get("/api/v1/analytics/popular-queries")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["queries"]) >= 2
        # Most popular should be first
        assert data["queries"][0]["query"] == "popular query"
        assert data["queries"][0]["count"] == 5
    
    def test_popular_queries_limit(self, client: TestClient, session_headers: dict):
        """Popular queries respects limit parameter."""
        # Create many unique queries
        for i in range(20):
            client.post(
                "/api/v1/analytics/search",
                json={"query": f"query {i}", "search_mode": "quick", "result_count": 1},
                headers=session_headers
            )
        
        response = client.get("/api/v1/analytics/popular-queries?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["queries"]) <= 5


class TestAnalyticsValidation:
    """Tests for analytics validation."""
    
    def test_invalid_search_mode(self, client: TestClient, session_headers: dict):
        """Invalid search mode is rejected."""
        response = client.post(
            "/api/v1/analytics/search",
            json={"query": "test", "search_mode": "invalid", "result_count": 0},
            headers=session_headers
        )
        
        assert response.status_code == 422
    
    def test_negative_result_count(self, client: TestClient, session_headers: dict):
        """Negative result count is rejected."""
        response = client.post(
            "/api/v1/analytics/search",
            json={"query": "test", "search_mode": "quick", "result_count": -5},
            headers=session_headers
        )
        
        assert response.status_code == 422
    
    def test_empty_query(self, client: TestClient, session_headers: dict):
        """Empty query is rejected."""
        response = client.post(
            "/api/v1/analytics/search",
            json={"query": "", "search_mode": "quick", "result_count": 0},
            headers=session_headers
        )
        
        assert response.status_code == 422
