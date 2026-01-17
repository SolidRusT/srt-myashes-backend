"""
Pydantic schemas for Admin API.

Schemas for the AI Data Quality Dashboard admin endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# ============================================================================
# Feedback Admin Schemas
# ============================================================================

class FeedbackListParams(BaseModel):
    """Query parameters for listing feedback."""
    
    rating: Optional[Literal["up", "down"]] = Field(
        None,
        description="Filter by rating (up/down)"
    )
    search_mode: Optional[Literal["quick", "smart", "deep"]] = Field(
        None,
        description="Filter by search mode"
    )
    date_from: Optional[datetime] = Field(
        None,
        description="Filter feedback created after this date"
    )
    date_to: Optional[datetime] = Field(
        None,
        description="Filter feedback created before this date"
    )
    reviewed: Optional[bool] = Field(
        None,
        description="Filter by review status (True=reviewed, False=unreviewed)"
    )
    flagged: Optional[bool] = Field(
        None,
        description="Filter by flagged status"
    )
    query_search: Optional[str] = Field(
        None,
        max_length=200,
        description="Search in query text"
    )
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")


class FeedbackDetail(BaseModel):
    """Detailed feedback record for admin view."""
    
    id: int
    feedback_id: str
    query: str
    response_snippet: str
    search_mode: str
    rating: str
    comment: Optional[str]
    session_id: Optional[str]
    user_id: Optional[str]
    created_at: datetime
    
    # Admin review fields
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    flagged_for_cleanup: bool
    cleanup_issue_url: Optional[str]
    
    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    """Paginated list of feedback for admin."""
    
    items: List[FeedbackDetail]
    total: int
    page: int
    limit: int
    pages: int


class FeedbackUpdateRequest(BaseModel):
    """Request body for updating feedback review status."""
    
    reviewed: bool = Field(
        ...,
        description="Mark as reviewed (True) or unreviewed (False)"
    )


class FeedbackUpdateResponse(BaseModel):
    """Response after updating feedback."""
    
    feedback_id: str
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    message: str


class FeedbackFlagRequest(BaseModel):
    """Request body for flagging feedback for data layer cleanup."""
    
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for flagging (will be included in GitHub issue)"
    )
    priority: Literal["low", "medium", "high"] = Field(
        "medium",
        description="Priority for the cleanup issue"
    )


class FeedbackFlagResponse(BaseModel):
    """Response after flagging feedback."""
    
    feedback_id: str
    flagged_for_cleanup: bool
    cleanup_issue_url: Optional[str]
    message: str


# ============================================================================
# Statistics Schemas
# ============================================================================

class FeedbackStatsResponse(BaseModel):
    """Aggregate statistics for feedback."""
    
    total_feedback: int
    thumbs_up: int
    thumbs_down: int
    thumbs_up_percentage: float
    
    # By search mode
    by_search_mode: dict  # {"quick": {"up": 10, "down": 5}, ...}
    
    # Review stats
    total_reviewed: int
    total_unreviewed: int
    total_flagged: int
    
    # Time-based stats
    feedback_last_24h: int
    feedback_last_7d: int
    feedback_last_30d: int
