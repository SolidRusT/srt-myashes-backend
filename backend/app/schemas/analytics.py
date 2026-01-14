"""
Pydantic schemas for Analytics API.

Tracks search queries to understand user behavior and popular topics.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class SearchAnalyticsCreate(BaseModel):
    """Request body for recording a search."""

    query: str = Field(..., min_length=1, max_length=500)
    search_mode: Literal["quick", "smart", "deep"] = Field(...)
    result_count: int = Field(..., ge=0)


class SearchAnalyticsResponse(BaseModel):
    """Response after recording a search."""

    recorded: bool = True


class PopularQueryItem(BaseModel):
    """A single popular query with its count."""

    query: str
    count: int
    search_mode: str


class PopularQueriesResponse(BaseModel):
    """Response containing popular queries."""

    queries: list[PopularQueryItem]
    period_days: int
