"""
SQLAlchemy model for AI response feedback.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime

from app.db.base_class import Base


class Feedback(Base):
    """
    Feedback on AI responses.

    Tracks thumbs up/down ratings on chat responses to measure quality.
    Includes admin review fields for the AI Data Quality Dashboard.
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(12), unique=True, index=True, nullable=False)  # e.g., "f_abc12345"

    # The query and response that was rated
    query = Column(Text, nullable=False)
    response_snippet = Column(Text, nullable=False)  # First 500 chars of response

    # Search context
    search_mode = Column(String(10), nullable=False)  # quick, smart, deep

    # Rating
    rating = Column(String(4), nullable=False)  # up, down
    comment = Column(Text, nullable=True)

    # Who submitted
    session_id = Column(String(64), index=True, nullable=True)
    user_id = Column(String(64), index=True, nullable=True)  # Future OAuth

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Admin review fields (AI Data Quality Dashboard)
    reviewed_at = Column(DateTime, nullable=True, index=True)
    reviewed_by = Column(String(64), nullable=True)  # Steam ID of admin
    flagged_for_cleanup = Column(Boolean, default=False, nullable=False, index=True)
    cleanup_issue_url = Column(String(256), nullable=True)  # GitHub issue URL

    def __repr__(self):
        return f"<Feedback {self.feedback_id}: {self.rating}>"
