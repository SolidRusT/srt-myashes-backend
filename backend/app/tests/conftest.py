"""Pytest fixtures for MyAshes.ai backend tests.

Provides test database, client, and session fixtures.
"""
import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Set testing environment before imports
os.environ["TESTING"] = "true"
os.environ["ENV"] = "testing"

from app.main import app
from app.db.session import get_db
from app.db.base_class import Base
from app.models import *  # noqa: Import all models for table creation


# Test database URL (in-memory SQLite for speed, or PostgreSQL from CI services)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "sqlite:///:memory:"
)

# Create test engine
if "sqlite" in TEST_DATABASE_URL:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL for CI environment
    engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def session_id() -> str:
    """Generate a test session ID."""
    return "sess_test123456789abc"


@pytest.fixture
def session_headers(session_id: str) -> dict:
    """Headers with session ID."""
    return {"X-Session-ID": session_id}


@pytest.fixture
def sample_build_data() -> dict:
    """Sample build data for testing."""
    return {
        "name": "Test Tank Build",
        "description": "A test build for tanks",
        "primary_archetype": "Tank",
        "secondary_archetype": "Fighter",
        "race": "Orc",
        "build_data": {
            "skills": ["shield_bash", "taunt"],
            "stats": {"strength": 20, "constitution": 18}
        },
        "tags": ["pvp", "endgame"]
    }


@pytest.fixture
def sample_feedback_data() -> dict:
    """Sample feedback data for testing."""
    return {
        "query": "How do I craft epic weapons?",
        "response_snippet": "To craft epic weapons, you need to gather rare materials...",
        "search_mode": "smart",
        "rating": "up",
        "comment": "Very helpful answer!"
    }


@pytest.fixture
def sample_analytics_data() -> dict:
    """Sample search analytics data for testing."""
    return {
        "query": "tank build guide",
        "search_mode": "deep",
        "result_count": 5
    }
