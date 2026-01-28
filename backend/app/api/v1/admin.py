"""
Admin endpoints for database monitoring, diagnostics, and AI feedback analysis.

These endpoints provide operational visibility into database performance
and AI response quality. Intended for internal use by operators.

Authentication: X-Admin-Token header required for feedback endpoints.
"""

from datetime import datetime, timedelta
from typing import Any, Annotated, Optional
import os

from fastapi import APIRouter, Query, Depends, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, desc, case
from sqlalchemy.orm import Session
import csv
import io

from app.core.db_monitoring import (
    get_slow_queries,
    get_slow_query_stats,
    get_slow_queries_by_table,
)
from app.db.session import get_db
from app.models.feedback import Feedback

router = APIRouter(tags=["admin"])

# Admin token for feedback endpoints (simple auth, PAM integration can come later)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-admin-token-change-in-production")


# Authentication dependency
async def verify_admin_token(
    x_admin_token: Annotated[Optional[str], Header()] = None
) -> str:
    """Verify admin token from X-Admin-Token header."""
    if not x_admin_token or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required. Provide valid X-Admin-Token header."
        )
    return x_admin_token


# --- Database Monitoring Endpoints (existing) ---


class SlowQueryReport(BaseModel):
    """Slow query report response."""
    
    statistics: dict[str, Any]
    by_table: dict[str, int]
    recent_queries: list[dict[str, Any]]


class HealthDetail(BaseModel):
    """Detailed health information."""
    
    database: dict[str, Any]
    slow_queries: dict[str, Any]


@router.get("/db/slow-queries", response_model=SlowQueryReport)
async def get_slow_query_report(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum queries to return")
) -> SlowQueryReport:
    """Get slow query report with statistics and recent queries.
    
    Returns:
        - statistics: Aggregate metrics (total count, avg/max duration)
        - by_table: Slow query counts grouped by table name
        - recent_queries: List of recent slow queries with details
    
    Slow queries are those exceeding 100ms execution time.
    """
    return SlowQueryReport(
        statistics=get_slow_query_stats(),
        by_table=get_slow_queries_by_table(),
        recent_queries=get_slow_queries(limit=limit),
    )


@router.get("/db/stats")
async def get_db_stats() -> dict[str, Any]:
    """Get database performance statistics.
    
    Returns summary statistics about query performance:
    - total_slow_queries: Total slow queries since startup
    - avg_duration_ms: Average slow query duration
    - max_duration_ms: Maximum query duration seen
    - hot_tables: Tables with most slow queries
    """
    stats = get_slow_query_stats()
    by_table = get_slow_queries_by_table()
    
    # Sort tables by query count
    hot_tables = sorted(by_table.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        **stats,
        "hot_tables": dict(hot_tables),
        "threshold_ms": 100,
    }


# --- AI Data Quality Dashboard Endpoints (Issue #24) ---


class FeedbackSummary(BaseModel):
    """Overall feedback statistics response."""
    
    total_feedback: int
    positive_count: int
    negative_count: int
    positive_rate: float = Field(description="Ratio of positive to total feedback (0.0-1.0)")
    by_search_mode: dict[str, dict[str, int]]
    period_days: int
    queried_at: datetime


class FeedbackItem(BaseModel):
    """Single feedback item for display."""
    
    feedback_id: str
    query: str
    response_snippet: str
    comment: Optional[str]
    search_mode: str
    rating: str
    session_id: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    flagged_for_cleanup: bool = False

    class Config:
        from_attributes = True


class NegativeFeedbackResponse(BaseModel):
    """Paginated negative feedback response."""
    
    items: list[FeedbackItem]
    total: int
    offset: int
    limit: int


class FeedbackPatterns(BaseModel):
    """Common patterns in negative feedback."""
    
    frequent_queries: list[dict[str, Any]] = Field(
        description="Queries with most negative feedback"
    )
    by_search_mode: dict[str, int] = Field(
        description="Negative feedback counts by search mode"
    )
    total_negative: int
    total_unreviewed: int


class TrendPoint(BaseModel):
    """Single data point for trend visualization."""
    
    date: str
    positive: int
    negative: int
    total: int


class FeedbackTrends(BaseModel):
    """Daily feedback trends for sparkline visualization."""
    
    data: list[TrendPoint]
    period_days: int


@router.get(
    "/feedback/summary",
    response_model=FeedbackSummary,
    dependencies=[Depends(verify_admin_token)]
)
async def feedback_summary(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
) -> FeedbackSummary:
    """Get overall feedback statistics.
    
    Returns aggregate feedback metrics for the specified period:
    - Total feedback count
    - Positive/negative breakdown
    - Positive rate (quality indicator)
    - Breakdown by search mode
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Get total counts
    total = db.query(func.count(Feedback.id)).filter(
        Feedback.created_at >= cutoff
    ).scalar() or 0
    
    positive = db.query(func.count(Feedback.id)).filter(
        Feedback.created_at >= cutoff,
        Feedback.rating == "up"
    ).scalar() or 0
    
    negative = total - positive
    
    # Get counts by search mode and rating
    by_mode_raw = db.query(
        Feedback.search_mode,
        Feedback.rating,
        func.count(Feedback.id)
    ).filter(
        Feedback.created_at >= cutoff
    ).group_by(
        Feedback.search_mode,
        Feedback.rating
    ).all()
    
    # Format by_search_mode as {mode: {positive: n, negative: n}}
    by_search_mode: dict[str, dict[str, int]] = {}
    for mode, rating, count in by_mode_raw:
        if mode not in by_search_mode:
            by_search_mode[mode] = {"positive": 0, "negative": 0}
        key = "positive" if rating == "up" else "negative"
        by_search_mode[mode][key] = count
    
    return FeedbackSummary(
        total_feedback=total,
        positive_count=positive,
        negative_count=negative,
        positive_rate=positive / total if total > 0 else 0.0,
        by_search_mode=by_search_mode,
        period_days=days,
        queried_at=datetime.utcnow(),
    )


@router.get(
    "/feedback/negative",
    response_model=NegativeFeedbackResponse,
    dependencies=[Depends(verify_admin_token)]
)
async def negative_feedback(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=500, description="Maximum items to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    unreviewed_only: bool = Query(default=False, description="Only show unreviewed feedback"),
) -> NegativeFeedbackResponse:
    """Get recent negative feedback with queries.
    
    Returns paginated list of negative feedback items for review.
    Use unreviewed_only=true to filter to items needing attention.
    """
    query = db.query(Feedback).filter(Feedback.rating == "down")
    
    if unreviewed_only:
        query = query.filter(Feedback.reviewed_at.is_(None))
    
    # Get total count for pagination
    total = query.count()
    
    # Get paginated results
    items = query.order_by(desc(Feedback.created_at)).offset(offset).limit(limit).all()
    
    return NegativeFeedbackResponse(
        items=[
            FeedbackItem(
                feedback_id=f.feedback_id,
                query=f.query,
                response_snippet=f.response_snippet[:200] + "..." if len(f.response_snippet) > 200 else f.response_snippet,
                comment=f.comment,
                search_mode=f.search_mode,
                rating=f.rating,
                session_id=f.session_id,
                created_at=f.created_at,
                reviewed_at=f.reviewed_at,
                flagged_for_cleanup=f.flagged_for_cleanup,
            )
            for f in items
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/feedback/patterns",
    response_model=FeedbackPatterns,
    dependencies=[Depends(verify_admin_token)]
)
async def feedback_patterns(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
) -> FeedbackPatterns:
    """Identify common patterns in negative feedback.
    
    Helps prioritize which queries/topics need data improvement:
    - Most frequently downvoted queries
    - Search modes with most issues
    - Count of unreviewed items needing attention
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Queries with most negative feedback
    frequent_raw = db.query(
        Feedback.query,
        func.count(Feedback.id).label("count")
    ).filter(
        Feedback.rating == "down",
        Feedback.created_at >= cutoff
    ).group_by(
        Feedback.query
    ).order_by(
        desc("count")
    ).limit(20).all()
    
    frequent_queries = [
        {"query": q, "negative_count": c}
        for q, c in frequent_raw
    ]
    
    # Negative feedback by search mode
    by_mode_raw = db.query(
        Feedback.search_mode,
        func.count(Feedback.id)
    ).filter(
        Feedback.rating == "down",
        Feedback.created_at >= cutoff
    ).group_by(
        Feedback.search_mode
    ).all()
    
    by_search_mode = dict(by_mode_raw)
    
    # Total negative count
    total_negative = db.query(func.count(Feedback.id)).filter(
        Feedback.rating == "down",
        Feedback.created_at >= cutoff
    ).scalar() or 0
    
    # Unreviewed count
    total_unreviewed = db.query(func.count(Feedback.id)).filter(
        Feedback.rating == "down",
        Feedback.reviewed_at.is_(None),
        Feedback.created_at >= cutoff
    ).scalar() or 0
    
    return FeedbackPatterns(
        frequent_queries=frequent_queries,
        by_search_mode=by_search_mode,
        total_negative=total_negative,
        total_unreviewed=total_unreviewed,
    )


@router.get(
    "/feedback/trends",
    response_model=FeedbackTrends,
    dependencies=[Depends(verify_admin_token)]
)
async def feedback_trends(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=90, description="Number of days to include"),
) -> FeedbackTrends:
    """Get daily feedback trends for sparkline visualization.
    
    Returns time-series data suitable for dashboard sparklines:
    - Daily counts of positive/negative feedback
    - Useful for identifying quality degradation over time
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Query daily counts by rating
    raw = db.query(
        func.date(Feedback.created_at).label("date"),
        Feedback.rating,
        func.count(Feedback.id).label("count")
    ).filter(
        Feedback.created_at >= cutoff
    ).group_by(
        "date",
        Feedback.rating
    ).order_by("date").all()
    
    # Organize by date
    date_data: dict[str, dict[str, int]] = {}
    for date, rating, count in raw:
        date_str = date.isoformat() if hasattr(date, 'isoformat') else str(date)
        if date_str not in date_data:
            date_data[date_str] = {"positive": 0, "negative": 0}
        key = "positive" if rating == "up" else "negative"
        date_data[date_str][key] = count
    
    # Convert to list, filling in missing dates
    data: list[TrendPoint] = []
    current = datetime.utcnow().date()
    for i in range(days - 1, -1, -1):
        date = current - timedelta(days=i)
        date_str = date.isoformat()
        counts = date_data.get(date_str, {"positive": 0, "negative": 0})
        data.append(TrendPoint(
            date=date_str,
            positive=counts["positive"],
            negative=counts["negative"],
            total=counts["positive"] + counts["negative"],
        ))
    
    return FeedbackTrends(data=data, period_days=days)


@router.get(
    "/feedback/export",
    dependencies=[Depends(verify_admin_token)]
)
async def export_negative_feedback(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=30, ge=1, le=365, description="Number of days to export"),
) -> StreamingResponse:
    """Export negative feedback as CSV for detailed analysis.
    
    Returns a CSV file containing all negative feedback from the specified period.
    Useful for offline analysis or importing into external tools.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    items = db.query(Feedback).filter(
        Feedback.rating == "down",
        Feedback.created_at >= cutoff
    ).order_by(desc(Feedback.created_at)).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "feedback_id",
        "query",
        "response_snippet",
        "comment",
        "search_mode",
        "session_id",
        "created_at",
        "reviewed_at",
        "flagged_for_cleanup",
    ])
    
    # Data rows
    for f in items:
        writer.writerow([
            f.feedback_id,
            f.query,
            f.response_snippet[:200] if f.response_snippet else "",
            f.comment or "",
            f.search_mode,
            f.session_id or "",
            f.created_at.isoformat(),
            f.reviewed_at.isoformat() if f.reviewed_at else "",
            f.flagged_for_cleanup,
        ])
    
    output.seek(0)
    
    filename = f"negative_feedback_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# --- Admin Review Actions ---


class ReviewFeedbackRequest(BaseModel):
    """Request body for marking feedback as reviewed."""
    
    reviewed_by: str = Field(description="Steam ID of reviewing admin")
    flagged_for_cleanup: bool = Field(default=False, description="Flag for data cleanup")
    cleanup_issue_url: Optional[str] = Field(None, description="GitHub issue URL if filed")


class ReviewFeedbackResponse(BaseModel):
    """Response after reviewing feedback."""
    
    feedback_id: str
    reviewed_at: datetime
    reviewed_by: str
    flagged_for_cleanup: bool


@router.post(
    "/feedback/{feedback_id}/review",
    response_model=ReviewFeedbackResponse,
    dependencies=[Depends(verify_admin_token)]
)
async def review_feedback(
    feedback_id: str,
    review: ReviewFeedbackRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ReviewFeedbackResponse:
    """Mark feedback as reviewed.
    
    Allows admins to track which negative feedback has been analyzed
    and optionally flag items that need data cleanup.
    """
    feedback = db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found")
    
    feedback.reviewed_at = datetime.utcnow()
    feedback.reviewed_by = review.reviewed_by
    feedback.flagged_for_cleanup = review.flagged_for_cleanup
    feedback.cleanup_issue_url = review.cleanup_issue_url
    
    db.commit()
    db.refresh(feedback)
    
    return ReviewFeedbackResponse(
        feedback_id=feedback.feedback_id,
        reviewed_at=feedback.reviewed_at,
        reviewed_by=feedback.reviewed_by,
        flagged_for_cleanup=feedback.flagged_for_cleanup,
    )
