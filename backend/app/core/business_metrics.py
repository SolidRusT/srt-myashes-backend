"""Business metrics for MyAshes.ai product KPIs.

Exposes Prometheus metrics for business intelligence and product decisions.
Metrics are updated via:
1. Real-time counters (incremented during API calls)
2. Background gauges (updated every 5 minutes from PostgreSQL)

All metrics use 'myashes_' prefix for easy filtering in Grafana.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import func, select, and_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.build import Build, BuildVote
from app.models.feedback import Feedback
from app.models.analytics import SearchAnalytics

logger = logging.getLogger(__name__)

# ============================================================================
# BUILD METRICS
# ============================================================================

builds_total = Counter(
    'myashes_builds_total',
    'Total number of builds created'
)

builds_by_class = Gauge(
    'myashes_builds_by_class',
    'Number of builds per class',
    ['class_name']
)

builds_by_archetype = Gauge(
    'myashes_builds_by_archetype',
    'Number of builds per archetype',
    ['archetype']
)

build_votes_total = Counter(
    'myashes_build_votes_total',
    'Total number of votes cast on builds'
)

build_avg_rating = Gauge(
    'myashes_build_avg_rating',
    'Average build rating (1-5 scale)'
)

# ============================================================================
# FEEDBACK METRICS
# ============================================================================

feedback_total = Counter(
    'myashes_feedback_total',
    'Total feedback submissions',
    ['rating']  # 'up' or 'down'
)

feedback_by_mode = Counter(
    'myashes_feedback_by_mode',
    'Feedback submissions by search mode',
    ['mode', 'rating']  # mode: quick/smart/deep, rating: up/down
)

feedback_satisfaction_rate = Gauge(
    'myashes_feedback_satisfaction_rate',
    'Ratio of thumbs up to total feedback (0.0-1.0)'
)

# ============================================================================
# SEARCH ANALYTICS METRICS
# ============================================================================

searches_total = Counter(
    'myashes_searches_total',
    'Total search queries',
    ['mode']  # quick, smart, deep
)

search_avg_results = Gauge(
    'myashes_search_avg_results',
    'Average number of results per search mode',
    ['mode']
)

# ============================================================================
# USER ENGAGEMENT METRICS
# ============================================================================

daily_active_sessions = Gauge(
    'myashes_daily_active_sessions',
    'Unique session IDs in the last 24 hours'
)

build_shares_total = Counter(
    'myashes_build_shares_total',
    'Total build views (share count proxy)'
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def increment_build_counter():
    """Increment build creation counter (call when build is created)."""
    builds_total.inc()


def increment_vote_counter():
    """Increment vote counter (call when vote is cast)."""
    build_votes_total.inc()


def increment_feedback_counter(rating: str, mode: Optional[str] = None):
    """Increment feedback counters.
    
    Args:
        rating: 'up' or 'down'
        mode: 'quick', 'smart', or 'deep' (optional)
    """
    feedback_total.labels(rating=rating).inc()
    if mode:
        feedback_by_mode.labels(mode=mode, rating=rating).inc()


def increment_search_counter(mode: str):
    """Increment search counter.
    
    Args:
        mode: 'quick', 'smart', or 'deep'
    """
    searches_total.labels(mode=mode).inc()


def increment_build_share_counter():
    """Increment build share counter (call when build is viewed)."""
    build_shares_total.inc()


# ============================================================================
# BACKGROUND GAUGE UPDATES
# ============================================================================

async def update_build_metrics(db: AsyncSession):
    """Update build-related gauge metrics from database.
    
    Updates:
    - builds_by_class
    - builds_by_archetype
    - build_avg_rating
    """
    try:
        # Builds by class
        class_counts = await db.execute(
            select(
                Build.primary_class,
                func.count(Build.id).label('count')
            ).group_by(Build.primary_class)
        )
        for row in class_counts:
            if row.primary_class:
                builds_by_class.labels(class_name=row.primary_class).set(row.count)
        
        # Builds by archetype
        archetype_counts = await db.execute(
            select(
                Build.primary_archetype,
                func.count(Build.id).label('count')
            ).group_by(Build.primary_archetype)
        )
        for row in archetype_counts:
            if row.primary_archetype:
                builds_by_archetype.labels(archetype=row.primary_archetype).set(row.count)
        
        # Average build rating
        avg_rating_result = await db.execute(
            select(func.avg(BuildVote.rating))
        )
        avg_rating = avg_rating_result.scalar()
        if avg_rating is not None:
            build_avg_rating.set(float(avg_rating))
        
        logger.debug("Updated build metrics")
    except Exception as e:
        logger.error(f"Failed to update build metrics: {e}")


async def update_feedback_metrics(db: AsyncSession):
    """Update feedback-related gauge metrics from database.
    
    Updates:
    - feedback_satisfaction_rate
    """
    try:
        # Satisfaction rate (thumbs up / total)
        total_feedback = await db.execute(
            select(func.count(Feedback.id))
        )
        total_count = total_feedback.scalar() or 0
        
        if total_count > 0:
            thumbs_up = await db.execute(
                select(func.count(Feedback.id)).where(Feedback.rating == 'up')
            )
            up_count = thumbs_up.scalar() or 0
            satisfaction_rate = up_count / total_count
            feedback_satisfaction_rate.set(satisfaction_rate)
        else:
            feedback_satisfaction_rate.set(0.0)
        
        logger.debug("Updated feedback metrics")
    except Exception as e:
        logger.error(f"Failed to update feedback metrics: {e}")


async def update_search_metrics(db: AsyncSession):
    """Update search analytics gauge metrics from database.
    
    Updates:
    - search_avg_results
    """
    try:
        # Average results per search mode
        for mode in ['quick', 'smart', 'deep']:
            avg_results = await db.execute(
                select(func.avg(SearchAnalytics.result_count))
                .where(SearchAnalytics.search_mode == mode)
            )
            avg = avg_results.scalar()
            if avg is not None:
                search_avg_results.labels(mode=mode).set(float(avg))
        
        logger.debug("Updated search metrics")
    except Exception as e:
        logger.error(f"Failed to update search metrics: {e}")


async def update_engagement_metrics(db: AsyncSession):
    """Update user engagement gauge metrics from database.
    
    Updates:
    - daily_active_sessions
    """
    try:
        # Unique sessions in last 24 hours
        # We'll count from SearchAnalytics as a proxy (builds and feedback also have session_id)
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Count unique session IDs from all tables in last 24 hours
        # Using SearchAnalytics as the most active table
        unique_sessions = await db.execute(
            select(func.count(func.distinct(SearchAnalytics.session_id)))
            .where(SearchAnalytics.created_at >= yesterday)
        )
        session_count = unique_sessions.scalar() or 0
        daily_active_sessions.set(session_count)
        
        logger.debug(f"Updated engagement metrics: {session_count} daily active sessions")
    except Exception as e:
        logger.error(f"Failed to update engagement metrics: {e}")


async def update_all_business_metrics():
    """Update all gauge metrics from database.
    
    Called periodically by background task.
    """
    logger.info("Updating business metrics from database")
    
    async with AsyncSessionLocal() as db:
        await update_build_metrics(db)
        await update_feedback_metrics(db)
        await update_search_metrics(db)
        await update_engagement_metrics(db)
    
    logger.info("Business metrics update complete")


# ============================================================================
# BACKGROUND TASK
# ============================================================================

async def metrics_update_loop(interval_seconds: int = 300):
    """Background task to update gauge metrics periodically.
    
    Args:
        interval_seconds: Update interval in seconds (default: 300 = 5 minutes)
    """
    logger.info(f"Starting business metrics update loop (interval: {interval_seconds}s)")
    
    while True:
        try:
            await update_all_business_metrics()
        except Exception as e:
            logger.error(f"Error in metrics update loop: {e}")
        
        await asyncio.sleep(interval_seconds)
