"""
Database query performance monitoring.

Provides SQLAlchemy event hooks for tracking query execution times,
Prometheus metrics for database operations, and slow query logging.

Usage:
    from app.core.db_monitoring import setup_db_monitoring, get_slow_queries
    
    # At app startup
    setup_db_monitoring(engine)
    
    # Get slow query report
    slow_queries = get_slow_queries(limit=100)
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any

from prometheus_client import Counter, Histogram, Gauge
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Prometheus metrics for database operations
DB_QUERY_DURATION = Histogram(
    "myashes_db_query_duration_seconds",
    "Database query execution time in seconds",
    ["operation", "table"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

DB_SLOW_QUERIES = Counter(
    "myashes_db_slow_queries_total",
    "Total number of slow database queries (>100ms)",
    ["table"],
)

DB_QUERIES_TOTAL = Counter(
    "myashes_db_queries_total",
    "Total number of database queries",
    ["operation"],
)

DB_CONNECTION_POOL_SIZE = Gauge(
    "myashes_db_connection_pool_size",
    "Current number of connections in the pool",
)

DB_CONNECTION_POOL_CHECKED_OUT = Gauge(
    "myashes_db_connection_pool_checked_out",
    "Number of connections currently checked out from pool",
)

# Slow query threshold in seconds
SLOW_QUERY_THRESHOLD = 0.1  # 100ms


@dataclass
class SlowQuery:
    """Record of a slow database query."""
    
    statement: str
    parameters: dict[str, Any] | None
    duration_ms: float
    timestamp: datetime
    table: str = "unknown"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "statement": self.statement[:500],  # Truncate long queries
            "parameters": str(self.parameters)[:200] if self.parameters else None,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp.isoformat(),
            "table": self.table,
        }


class SlowQueryTracker:
    """Thread-safe tracker for slow queries with rolling window."""
    
    def __init__(self, max_size: int = 1000):
        self._queries: deque[SlowQuery] = deque(maxlen=max_size)
        self._lock = Lock()
        self._total_count = 0
        self._total_time_ms = 0.0
    
    def add(self, query: SlowQuery) -> None:
        """Add a slow query to the tracker."""
        with self._lock:
            self._queries.append(query)
            self._total_count += 1
            self._total_time_ms += query.duration_ms
    
    def get_recent(self, limit: int = 100) -> list[dict]:
        """Get most recent slow queries."""
        with self._lock:
            queries = list(self._queries)[-limit:]
            return [q.to_dict() for q in reversed(queries)]
    
    def get_stats(self) -> dict:
        """Get slow query statistics."""
        with self._lock:
            if not self._queries:
                return {
                    "total_slow_queries": 0,
                    "avg_duration_ms": 0,
                    "max_duration_ms": 0,
                    "recent_count": 0,
                }
            
            durations = [q.duration_ms for q in self._queries]
            return {
                "total_slow_queries": self._total_count,
                "avg_duration_ms": round(self._total_time_ms / self._total_count, 2),
                "max_duration_ms": round(max(durations), 2),
                "recent_count": len(self._queries),
            }
    
    def get_by_table(self) -> dict[str, int]:
        """Get slow query counts by table."""
        with self._lock:
            counts: dict[str, int] = {}
            for query in self._queries:
                counts[query.table] = counts.get(query.table, 0) + 1
            return counts


# Global slow query tracker
_slow_query_tracker = SlowQueryTracker()


def extract_table_name(statement: str) -> str:
    """Extract table name from SQL statement."""
    statement = statement.lower().strip()
    
    # Handle common patterns
    patterns = [
        ("from ", " "),    # SELECT ... FROM table
        ("into ", " "),    # INSERT INTO table
        ("update ", " "),  # UPDATE table
        ("delete from ", " "),  # DELETE FROM table
    ]
    
    for pattern, delimiter in patterns:
        if pattern in statement:
            idx = statement.find(pattern) + len(pattern)
            rest = statement[idx:].strip()
            # Get first word (table name)
            table = rest.split()[0] if rest else "unknown"
            # Remove any alias or schema prefix
            table = table.split(".")[-1]
            table = table.split()[0]
            # Remove quotes
            table = table.strip('"\'`')
            return table
    
    return "unknown"


def extract_operation(statement: str) -> str:
    """Extract operation type from SQL statement."""
    statement = statement.lower().strip()
    
    if statement.startswith("select"):
        return "select"
    elif statement.startswith("insert"):
        return "insert"
    elif statement.startswith("update"):
        return "update"
    elif statement.startswith("delete"):
        return "delete"
    elif statement.startswith("begin") or statement.startswith("commit") or statement.startswith("rollback"):
        return "transaction"
    else:
        return "other"


def setup_db_monitoring(engine: Engine) -> None:
    """Set up SQLAlchemy event hooks for database monitoring.
    
    Args:
        engine: SQLAlchemy engine to monitor
    """
    
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        """Record query start time."""
        conn.info.setdefault("query_start_time", []).append(time.time())
    
    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        """Record query completion and track metrics."""
        start_times = conn.info.get("query_start_time", [])
        if not start_times:
            return
        
        start_time = start_times.pop()
        duration = time.time() - start_time
        duration_ms = duration * 1000
        
        # Extract metadata
        operation = extract_operation(statement)
        table = extract_table_name(statement)
        
        # Record Prometheus metrics
        DB_QUERY_DURATION.labels(operation=operation, table=table).observe(duration)
        DB_QUERIES_TOTAL.labels(operation=operation).inc()
        
        # Track slow queries
        if duration > SLOW_QUERY_THRESHOLD:
            DB_SLOW_QUERIES.labels(table=table).inc()
            
            slow_query = SlowQuery(
                statement=statement,
                parameters=parameters if isinstance(parameters, dict) else None,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                table=table,
            )
            _slow_query_tracker.add(slow_query)
            
            logger.warning(
                f"Slow query ({duration_ms:.0f}ms) on {table}: "
                f"{statement[:200]}..."
            )
    
    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        """Track connection pool checkout."""
        pool = engine.pool
        DB_CONNECTION_POOL_SIZE.set(pool.size())
        DB_CONNECTION_POOL_CHECKED_OUT.set(pool.checkedout())
    
    @event.listens_for(engine, "checkin")
    def on_checkin(dbapi_connection, connection_record):
        """Track connection pool checkin."""
        pool = engine.pool
        DB_CONNECTION_POOL_SIZE.set(pool.size())
        DB_CONNECTION_POOL_CHECKED_OUT.set(pool.checkedout())
    
    logger.info("Database monitoring initialized with slow query threshold: 100ms")


def get_slow_queries(limit: int = 100) -> list[dict]:
    """Get recent slow queries.
    
    Args:
        limit: Maximum number of queries to return
        
    Returns:
        List of slow query records
    """
    return _slow_query_tracker.get_recent(limit)


def get_slow_query_stats() -> dict:
    """Get slow query statistics.
    
    Returns:
        Dictionary with query statistics
    """
    return _slow_query_tracker.get_stats()


def get_slow_queries_by_table() -> dict[str, int]:
    """Get slow query counts grouped by table.
    
    Returns:
        Dictionary mapping table names to query counts
    """
    return _slow_query_tracker.get_by_table()
