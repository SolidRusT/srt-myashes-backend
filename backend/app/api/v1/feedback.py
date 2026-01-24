"""
Feedback API endpoints.

Collects thumbs up/down ratings on AI responses to measure quality.
"""
import secrets
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.business_metrics import increment_feedback_counter
from app.db.session import get_db
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(tags=["feedback"])


def generate_feedback_id() -> str:
    """Generate a unique feedback ID like 'f_abc12345'."""
    return f"f_{secrets.token_hex(4)}"


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    request: Request,
    feedback_in: FeedbackCreate,
    db: Annotated[Session, Depends(get_db)],
) -> FeedbackResponse:
    """
    Submit feedback on an AI response.

    Tracks thumbs up/down ratings to measure response quality.
    Session ID is extracted from the request (set by middleware).
    """
    session_id = getattr(request.state, "session_id", None)

    # Generate unique feedback ID
    feedback_id = generate_feedback_id()

    # Ensure uniqueness (unlikely collision but handle it)
    while db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first():
        feedback_id = generate_feedback_id()

    # Create feedback record
    feedback = Feedback(
        feedback_id=feedback_id,
        query=feedback_in.query,
        response_snippet=feedback_in.response_snippet,
        search_mode=feedback_in.search_mode,
        rating=feedback_in.rating,
        comment=feedback_in.comment,
        session_id=session_id,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    # Increment business metrics
    increment_feedback_counter(
        rating=feedback_in.rating,
        mode=feedback_in.search_mode
    )

    return FeedbackResponse(
        feedback_id=feedback.feedback_id,
        received_at=feedback.created_at,
    )
