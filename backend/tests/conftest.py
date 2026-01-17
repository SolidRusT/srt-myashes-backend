"""Pytest fixtures for MyAshes.ai backend tests."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base_class import Base
from app.db.session import get_db
from app.core.auth import AuthenticatedUser, get_current_user


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_authenticated_user():
    """Create a mock authenticated user."""
    return AuthenticatedUser(
        player_id="player_123abc",
        steam_id="76561198012345678",
        steam_display_name="TestPlayer",
        email="test@example.com",
        tier="free",
    )


@pytest.fixture
def authenticated_client(client, mock_authenticated_user):
    """
    Create test client with authenticated user.
    
    Overrides get_current_user to return mock user.
    """
    async def override_get_current_user():
        return mock_authenticated_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.fixture
def sample_build_data():
    """Sample build creation data."""
    return {
        "name": "Test Build",
        "description": "A test build for unit testing",
        "primary_archetype": "fighter",
        "secondary_archetype": "mage",
        "race": "human",
        "is_public": True,
    }


@pytest.fixture
def session_id():
    """Sample session ID."""
    return "sess_abc123def456ghi789jkl012"
