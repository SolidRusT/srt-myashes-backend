"""
Database session configuration with production-ready connection pooling.

Pool settings are sized for 6 replicas with KEDA autoscaling (0-10).
With pool_size=10 and max_overflow=20, each replica can handle up to 30 concurrent
connections, providing adequate headroom for traffic spikes.

See Issue #10 for rationale.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.core.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    poolclass=QueuePool,
    # Base pool size per replica - increased from default 5
    pool_size=settings.DB_POOL_SIZE,
    # Allow up to pool_size + max_overflow connections during spikes
    max_overflow=settings.DB_MAX_OVERFLOW,
    # Wait up to 30s for connection before failing (prevents indefinite hangs)
    pool_timeout=settings.DB_POOL_TIMEOUT,
    # Recycle connections after 1 hour to prevent stale connections
    pool_recycle=settings.DB_POOL_RECYCLE,
    # Verify connections before using (handles dropped connections gracefully)
    pool_pre_ping=True,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get DB session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
