"""
Pydantic schemas for Build API.

These schemas define the request/response formats for the builds endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

from app.game_constants.game_data import ARCHETYPES, VALID_RACES


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
    created_by: str = "anonymous"

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

    class Config:
        from_attributes = True


class BuildListResponse(BaseModel):
    """Paginated list of builds."""

    builds: List[BuildListItem]
    total: int
    page: int
    limit: int
    has_more: bool


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
