"""
SQLAlchemy models for character builds and voting.
"""
from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, Text, Float,
    ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base


class Build(Base):
    """
    Character build model - stores user-created builds.
    """
    __tablename__ = "builds"

    # Primary key - use integer for internal operations, build_id for external
    id = Column(Integer, primary_key=True, index=True)
    build_id = Column(String(12), unique=True, index=True, nullable=False)  # e.g., "b_abc12345"

    # Build details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    primary_archetype = Column(String(20), nullable=False)
    secondary_archetype = Column(String(20), nullable=False)
    class_name = Column(String(50), nullable=False)  # Computed from matrix
    race = Column(String(20), nullable=False)

    # Visibility
    is_public = Column(Boolean, default=True, nullable=False)

    # Ownership
    session_id = Column(String(64), index=True, nullable=False)  # For anonymous users
    user_id = Column(String(64), index=True, nullable=True)  # For authenticated users (future OAuth)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Voting aggregates (denormalized for performance)
    rating_sum = Column(Float, default=0.0, nullable=False)
    vote_count = Column(Integer, default=0, nullable=False)

    # Relationships
    votes = relationship("BuildVote", back_populates="build", cascade="all, delete-orphan")

    @property
    def avg_rating(self) -> float | None:
        """Calculate average rating from sum and count."""
        if self.vote_count == 0:
            return None
        return round(self.rating_sum / self.vote_count, 1)

    def __repr__(self):
        return f"<Build {self.build_id}: {self.name} ({self.class_name})>"


class BuildVote(Base):
    """
    Vote/rating on a build.

    Each session can vote once per build.
    Rating is 1-5 stars.
    """
    __tablename__ = "build_votes"

    id = Column(Integer, primary_key=True, index=True)
    build_id = Column(String(12), ForeignKey("builds.build_id", ondelete="CASCADE"), nullable=False)

    # Who voted - session_id for anonymous, user_id for authenticated
    session_id = Column(String(64), index=True, nullable=True)
    user_id = Column(String(64), index=True, nullable=True)

    # The rating (1-5)
    rating = Column(Integer, nullable=False)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    build = relationship("Build", back_populates="votes")

    # Constraints
    __table_args__ = (
        # Each session can only vote once per build
        UniqueConstraint("build_id", "session_id", name="uq_build_vote_session"),
        # Each user can only vote once per build (for future OAuth)
        UniqueConstraint("build_id", "user_id", name="uq_build_vote_user"),
        # Rating must be 1-5
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_vote_rating_range"),
    )

    def __repr__(self):
        return f"<BuildVote build={self.build_id} rating={self.rating}>"
