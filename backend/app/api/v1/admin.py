"""
Admin API endpoints for AI Data Quality Dashboard.

Provides endpoints for reviewing AI response feedback and flagging
bad responses for data layer cleanup.
"""
import os
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.feedback import Feedback
from app.core.auth import require_admin
from app.schemas.admin import (
    FeedbackDetail,
    FeedbackListResponse,
    FeedbackUpdateRequest,
    FeedbackUpdateResponse,
    FeedbackFlagRequest,
    FeedbackFlagResponse,
    FeedbackStatsResponse,
)

router = APIRouter(tags=["admin"])


@router.get("/feedback", response_model=FeedbackListResponse)
async def list_feedback(
    admin_steam_id: Annotated[str, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    rating: Optional[str] = Query(None, regex="^(up|down)$"),
    search_mode: Optional[str] = Query(None, regex="^(quick|smart|deep)$"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    reviewed: Optional[bool] = Query(None),
    flagged: Optional[bool] = Query(None),
    query_search: Optional[str] = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> FeedbackListResponse:
    """
    List feedback with filtering and pagination.
    
    Requires admin authentication via Steam ID.
    """
    # Build query with filters
    query = db.query(Feedback)
    
    if rating:
        query = query.filter(Feedback.rating == rating)
    
    if search_mode:
        query = query.filter(Feedback.search_mode == search_mode)
    
    if date_from:
        query = query.filter(Feedback.created_at >= date_from)
    
    if date_to:
        query = query.filter(Feedback.created_at <= date_to)
    
    if reviewed is not None:
        if reviewed:
            query = query.filter(Feedback.reviewed_at.isnot(None))
        else:
            query = query.filter(Feedback.reviewed_at.is_(None))
    
    if flagged is not None:
        query = query.filter(Feedback.flagged_for_cleanup == flagged)
    
    if query_search:
        search_pattern = f"%{query_search}%"
        query = query.filter(
            or_(
                Feedback.query.ilike(search_pattern),
                Feedback.response_snippet.ilike(search_pattern),
                Feedback.comment.ilike(search_pattern),
            )
        )
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    pages = (total + limit - 1) // limit if total > 0 else 1
    offset = (page - 1) * limit
    
    # Get paginated results, most recent first
    items = query.order_by(Feedback.created_at.desc()).offset(offset).limit(limit).all()
    
    return FeedbackListResponse(
        items=[FeedbackDetail.model_validate(item) for item in items],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/feedback/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    admin_steam_id: Annotated[str, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> FeedbackStatsResponse:
    """
    Get aggregate statistics for all feedback.
    
    Requires admin authentication via Steam ID.
    """
    now = datetime.utcnow()
    
    # Total counts
    total = db.query(func.count(Feedback.id)).scalar() or 0
    thumbs_up = db.query(func.count(Feedback.id)).filter(Feedback.rating == "up").scalar() or 0
    thumbs_down = db.query(func.count(Feedback.id)).filter(Feedback.rating == "down").scalar() or 0
    
    # Calculate percentage
    thumbs_up_pct = (thumbs_up / total * 100) if total > 0 else 0.0
    
    # By search mode
    by_search_mode = {}
    for mode in ["quick", "smart", "deep"]:
        up_count = db.query(func.count(Feedback.id)).filter(
            and_(Feedback.search_mode == mode, Feedback.rating == "up")
        ).scalar() or 0
        down_count = db.query(func.count(Feedback.id)).filter(
            and_(Feedback.search_mode == mode, Feedback.rating == "down")
        ).scalar() or 0
        by_search_mode[mode] = {"up": up_count, "down": down_count}
    
    # Review stats
    reviewed = db.query(func.count(Feedback.id)).filter(
        Feedback.reviewed_at.isnot(None)
    ).scalar() or 0
    unreviewed = total - reviewed
    flagged = db.query(func.count(Feedback.id)).filter(
        Feedback.flagged_for_cleanup == True
    ).scalar() or 0
    
    # Time-based stats
    last_24h = db.query(func.count(Feedback.id)).filter(
        Feedback.created_at >= now - timedelta(hours=24)
    ).scalar() or 0
    last_7d = db.query(func.count(Feedback.id)).filter(
        Feedback.created_at >= now - timedelta(days=7)
    ).scalar() or 0
    last_30d = db.query(func.count(Feedback.id)).filter(
        Feedback.created_at >= now - timedelta(days=30)
    ).scalar() or 0
    
    return FeedbackStatsResponse(
        total_feedback=total,
        thumbs_up=thumbs_up,
        thumbs_down=thumbs_down,
        thumbs_up_percentage=round(thumbs_up_pct, 1),
        by_search_mode=by_search_mode,
        total_reviewed=reviewed,
        total_unreviewed=unreviewed,
        total_flagged=flagged,
        feedback_last_24h=last_24h,
        feedback_last_7d=last_7d,
        feedback_last_30d=last_30d,
    )


@router.get("/feedback/{feedback_id}", response_model=FeedbackDetail)
async def get_feedback(
    feedback_id: str,
    admin_steam_id: Annotated[str, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> FeedbackDetail:
    """
    Get a single feedback record by ID.
    
    Requires admin authentication via Steam ID.
    """
    feedback = db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback {feedback_id} not found",
        )
    
    return FeedbackDetail.model_validate(feedback)


@router.patch("/feedback/{feedback_id}", response_model=FeedbackUpdateResponse)
async def update_feedback(
    feedback_id: str,
    request: FeedbackUpdateRequest,
    admin_steam_id: Annotated[str, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> FeedbackUpdateResponse:
    """
    Update the review status of a feedback record.
    
    Requires admin authentication via Steam ID.
    """
    feedback = db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback {feedback_id} not found",
        )
    
    if request.reviewed:
        feedback.reviewed_at = datetime.utcnow()
        feedback.reviewed_by = admin_steam_id
        message = "Feedback marked as reviewed"
    else:
        feedback.reviewed_at = None
        feedback.reviewed_by = None
        message = "Feedback marked as unreviewed"
    
    db.commit()
    db.refresh(feedback)
    
    return FeedbackUpdateResponse(
        feedback_id=feedback.feedback_id,
        reviewed_at=feedback.reviewed_at,
        reviewed_by=feedback.reviewed_by,
        message=message,
    )


@router.post("/feedback/{feedback_id}/flag", response_model=FeedbackFlagResponse)
async def flag_feedback(
    feedback_id: str,
    request: FeedbackFlagRequest,
    admin_steam_id: Annotated[str, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> FeedbackFlagResponse:
    """
    Flag feedback for data layer cleanup.
    
    This creates a GitHub issue in the srt-data-layer repository
    to track the cleanup of bad training data.
    
    Requires admin authentication via Steam ID.
    """
    feedback = db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback {feedback_id} not found",
        )
    
    if feedback.flagged_for_cleanup and feedback.cleanup_issue_url:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Feedback already flagged. Issue: {feedback.cleanup_issue_url}",
        )
    
    # TODO: Create GitHub issue via MCP or GitHub API
    # For now, mark as flagged and set placeholder URL
    # Phase 4 (srt-pam-platform#16) will add proper GitHub integration
    
    # Mark as flagged
    feedback.flagged_for_cleanup = True
    feedback.reviewed_at = datetime.utcnow()
    feedback.reviewed_by = admin_steam_id
    
    # Placeholder - will be replaced with actual GitHub issue URL
    # Format: https://github.com/SolidRusT/srt-data-layer/issues/XX
    feedback.cleanup_issue_url = None  # Set when GitHub integration is added
    
    db.commit()
    db.refresh(feedback)
    
    return FeedbackFlagResponse(
        feedback_id=feedback.feedback_id,
        flagged_for_cleanup=feedback.flagged_for_cleanup,
        cleanup_issue_url=feedback.cleanup_issue_url,
        message=f"Feedback flagged for cleanup. Reason: {request.reason}. "
                f"Priority: {request.priority}. "
                f"GitHub issue creation pending PAM Platform integration (see srt-pam-platform#16).",
    )
