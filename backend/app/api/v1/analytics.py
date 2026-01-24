"""
Analytics API endpoints.

Tracks search queries to understand user behavior and popular topics.
"""
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.business_metrics import increment_search_counter
from app.db.session import get_db
from app.models.analytics import SearchAnalytics
from app.schemas.analytics import (
    SearchAnalyticsCreate,
    SearchAnalyticsResponse,
    PopularQueriesResponse,
    PopularQueryItem,
)

router = APIRouter(tags=["analytics"])


@router.post("/search", response_model=SearchAnalyticsResponse, status_code=201)
async def record_search(
    request: Request,
    analytics_in: SearchAnalyticsCreate,
    db: Annotated[Session, Depends(get_db)],
) -> SearchAnalyticsResponse:
    """
    Record a search query for analytics.

    Tracks user searches to understand popular topics and search behavior.
    Session ID is extracted from the request (set by middleware).
    """
    session_id = getattr(request.state, "session_id", None)

    # Create analytics record
    analytics = SearchAnalytics(
        query=analytics_in.query,
        search_mode=analytics_in.search_mode,
        result_count=analytics_in.result_count,
        session_id=session_id,
    )

    db.add(analytics)
    db.commit()

    # Increment business metrics
    increment_search_counter(mode=analytics_in.search_mode)

    return SearchAnalyticsResponse(recorded=True)


@router.get("/popular-queries", response_model=PopularQueriesResponse)
async def get_popular_queries(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=90, description="Number of days to look back"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of queries to return"),
) -> PopularQueriesResponse:
    """
    Get popular search queries.

    Returns the most frequently searched queries within the specified time period.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Query for popular queries grouped by query text and search mode
    results = (
        db.query(
            SearchAnalytics.query,
            SearchAnalytics.search_mode,
            func.count(SearchAnalytics.id).label("count"),
        )
        .filter(SearchAnalytics.created_at >= cutoff_date)
        .group_by(SearchAnalytics.query, SearchAnalytics.search_mode)
        .order_by(func.count(SearchAnalytics.id).desc())
        .limit(limit)
        .all()
    )

    queries = [
        PopularQueryItem(query=row.query, search_mode=row.search_mode, count=row.count)
        for row in results
    ]

    return PopularQueriesResponse(queries=queries, period_days=days)
