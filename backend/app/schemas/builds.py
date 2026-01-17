"""
Pydantic schemas for Build API.

These schemas define the request/response formats for the builds endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum

from app.game_constants.game_data import ARCHETYPES, VALID_RACES


class TimePeriod(str, Enum):
    """Time period for popular builds filtering."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    ALL = "all"


class BuildCreate(BaseModel):
    """Request body for creating a new build."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    primary_archetype: str = Field(..., min_length=1, max_length=20)
    secondary_archetype: str = Field(..., min_length=1, max_length=20)
    race: str = Field(..., min_length=1, max_length=20)
    is_public: bool = True

    @field_validator("primary_archetype", "secondary_archetype")
    @classmethod
    def validate_archetype(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in ARCHETYPES:
            raise ValueError(f"Invalid archetype: {v}. Must be one of: {', '.join(sorted(ARCHETYPES))}")
        return v_lower

    @field_validator("race")
    @classmethod
    def validate_race(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in VALID_RACES:
            raise ValueError(f"Invalid race: {v}. Must be one of: {', '.join(sorted(VALID_RACES))}")
        return v_lower


class CreatorInfo(BaseModel):
    """Information about the build creator."""
    display_name: str = "anonymous"
    steam_id: Optional[str] = None
    is_authenticated: bool = False


class BuildResponse(BaseModel):
    """Full build response with all details."""

    build_id: str
    name: str
    description: Optional[str]
    primary_archetype: str
    secondary_archetype: str
    class_name: str
    race: str
    is_public: bool
    share_url: str
    created_at: datetime
    updated_at: datetime
    rating: Optional[float] = None
    vote_count: int = 0
    created_by: str = "anonymous"  # Kept for backward compatibility
    creator: Optional[CreatorInfo] = None  # Detailed creator info

    class Config:
        from_attributes = True


class BuildListItem(BaseModel):
    """Abbreviated build info for list responses."""

    build_id: str
    name: str
    description: Optional[str]
    primary_archetype: str
    secondary_archetype: str
    class_name: str
    race: str
    rating: Optional[float] = None
    vote_count: int = 0
    created_at: datetime
    created_by: str = "anonymous"

    class Config:
        from_attributes = True


class BuildListResponse(BaseModel):
    """Paginated list of builds."""

    builds: List[BuildListItem]
    total: int
    page: int
    limit: int
    has_more: bool


class PopularBuildItem(BaseModel):
    """Build item for popular builds widget."""

    build_id: str
    name: str
    class_name: str
    race: str
    rating: Optional[float] = None
    vote_count: int = 0
    share_url: str
    created_by: str = "anonymous"

    class Config:
        from_attributes = True


class PopularBuildsResponse(BaseModel):
    """Response for popular builds widget."""

    builds: List[PopularBuildItem]
    period: str
    count: int


class VoteRequest(BaseModel):
    """Request body for voting on a build."""

    rating: int = Field(..., ge=1, le=5)


class VoteResponse(BaseModel):
    """Response after voting on a build."""

    build_id: str
    your_rating: int
    avg_rating: float
    vote_count: int


class DeleteResponse(BaseModel):
    """Response after deleting a build."""

    build_id: str
    deleted: bool = True
    message: str = "Build deleted successfully"


class BuildUpdateRequest(BaseModel):
    """Request body for updating a build."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    is_public: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Name cannot be empty")
        return v


class AuthStatusResponse(BaseModel):
    """Response for authentication status check."""
    
    authenticated: bool
    player_id: Optional[str] = None
    steam_id: Optional[str] = None
    display_name: Optional[str] = None
    tier: str = "anonymous"


class ClaimBuildsRequest(BaseModel):
    """Request to claim anonymous builds."""
    
    session_id: str = Field(..., description="Session ID to claim builds from")


class ClaimBuildsResponse(BaseModel):
    """Response after claiming builds."""
    
    claimed_count: int
    build_ids: List[str]
    message: str
