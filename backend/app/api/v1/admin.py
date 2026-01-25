"""
Admin endpoints for database monitoring and diagnostics.

These endpoints provide operational visibility into database performance
and are intended for internal use by operators.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Any

from app.core.db_monitoring import (
    get_slow_queries,
    get_slow_query_stats,
    get_slow_queries_by_table,
)

router = APIRouter(tags=["admin"])


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
