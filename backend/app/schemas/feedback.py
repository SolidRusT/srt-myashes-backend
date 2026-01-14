"""
Pydantic schemas for Feedback API.

Feedback is collected on AI responses to track quality.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime


class FeedbackCreate(BaseModel):
    """Request body for submitting feedback."""

    query: str = Field(..., min_length=1, max_length=1000)
    response_snippet: str = Field(..., min_length=1, max_length=500)
    search_mode: Literal["quick", "smart", "deep"] = Field(...)
    rating: Literal["up", "down"] = Field(...)
    comment: Optional[str] = Field(None, max_length=1000)

    @field_validator("response_snippet")
    @classmethod
    def truncate_response(cls, v: str) -> str:
        """Ensure response snippet is max 500 chars."""
        return v[:500] if len(v) > 500 else v


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    feedback_id: str
    received_at: datetime

    class Config:
        from_attributes = True
