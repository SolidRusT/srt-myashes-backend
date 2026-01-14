"""
SQLAlchemy model for search analytics.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

from app.db.base_class import Base


class SearchAnalytics(Base):
    """
    Search analytics for tracking user queries.

    Records search queries to understand user behavior and popular topics.
    """
    __tablename__ = "search_analytics"

    id = Column(Integer, primary_key=True, index=True)

    # The search query
    query = Column(Text, nullable=False)
    search_mode = Column(String(10), nullable=False)  # quick, smart, deep
    result_count = Column(Integer, nullable=False, default=0)

    # Who searched
    session_id = Column(String(64), index=True, nullable=True)
    user_id = Column(String(64), index=True, nullable=True)  # Future OAuth

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<SearchAnalytics {self.id}: '{self.query[:30]}...'>"
