"""
MyAshes.ai Backend API

Product-specific backend services for the Ashes of Creation game assistant.
Provides build persistence, voting, feedback collection, and analytics.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import ValidationError as PydanticValidationError
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
import asyncio
import logging
import time

from app.api.v1 import api_router
from app.core.config import settings
from app.core.errors import APIError, api_error_handler, ValidationError
from app.core.session import SessionMiddleware
from app.core.cache import check_redis_health, close_redis, get_redis
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.business_metrics import metrics_update_loop
from app.core.db_monitoring import setup_db_monitoring
from app.db.session import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Application version - single source of truth
APP_VERSION = "2.3.0"

# Track application start time for uptime calculation
_app_start_time: float = 0.0

# Health check cache to avoid overhead on rapid K8s probe requests
_health_cache: dict = {}
_health_cache_ttl: float = 1.0  # 1 second cache TTL
_health_cache_time: float = 0.0

# OpenAPI documentation description with session header info
API_DESCRIPTION = """
## MyAshes.ai Backend API

Product-specific backend for the Ashes of Creation game assistant.
Provides build sharing, voting, feedback, and analytics.

### Authentication

**Session-Based (Anonymous)**
- Include `X-Session-ID` header for session tracking
- Format: `sess_` + 24 hex characters
- If not provided, server generates one and returns in response header

**Steam Login (Authenticated)**
- Login via PAM Platform at console.solidrust.ai
- Include `Authorization: Bearer <token>` header
- Authenticated users have persistent ownership of builds

### Rate Limiting

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Seconds until limit resets
- `Retry-After`: Seconds to wait (only when rate limited)

### Error Responses

All errors follow this format:
```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "status": 404
}
```

Common error codes:
- `not_found`: Resource does not exist
- `unauthorized`: Missing or invalid authentication
- `forbidden`: Not allowed to perform action
- `validation_error`: Invalid request data
- `rate_limited`: Too many requests
"""

app = FastAPI(
    title=settings.APP_NAME,
    description=API_DESCRIPTION,
    version=APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DOCS_ENABLED else None,
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    debug=settings.DEBUG,
    contact={
        "name": "SolidRusT Networks",
        "url": "https://myashes.ai",
        "email": "support@solidrust.net",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add rate limiter to app state
app.state.limiter = limiter

# Register rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Initialize Prometheus metrics instrumentator
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
    inprogress_name="myashes_http_requests_inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# Add session middleware (must be added before CORS)
app.add_middleware(SessionMiddleware)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*", "X-Session-ID"],
        expose_headers=["X-Session-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"],
    )


# Custom OpenAPI schema with X-Session-ID header documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
    )
    
    # Add X-Session-ID header as a global parameter
    openapi_schema["components"]["securitySchemes"] = {
        "sessionId": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Session-ID",
            "description": "Session ID for anonymous user tracking. Format: sess_ + 24 hex chars. Auto-generated if not provided."
        },
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "PAM Platform authentication token (from Steam login)"
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [
        {"sessionId": []},
        {"bearerAuth": []}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Register custom exception handlers
@app.exception_handler(APIError)
async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors with consistent JSON format."""
    return await api_error_handler(request, exc)


@app.exception_handler(PydanticValidationError)
async def handle_pydantic_validation_error(request: Request, exc: PydanticValidationError) -> JSONResponse:
    """Convert Pydantic validation errors to our API error format."""
    errors = exc.errors()
    message = "; ".join([f"{e['loc'][-1]}: {e['msg']}" for e in errors])
    api_error = ValidationError(message=message, details={"errors": errors})
    return await api_error_handler(request, api_error)


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["status"])
def root():
    """Root endpoint - basic info and links."""
    return {
        "name": settings.APP_NAME,
        "version": APP_VERSION,
        "status": "operational",
        "docs": "/docs" if settings.DOCS_ENABLED else "disabled",
        "redoc": "/redoc" if settings.DOCS_ENABLED else "disabled",
        "health": "/health",
        "features": {
            "rate_limiting": True,
            "authentication": True,
            "templates": True,
            "search": True,
            "business_metrics": True,
            "db_monitoring": True,
        }
    }


async def _perform_health_checks() -> dict:
    """
    Perform actual health checks with latency measurements.
    
    Returns a dict with status, version, dependencies, and uptime.
    """
    health_status = {
        "status": "healthy",
        "version": APP_VERSION,
        "dependencies": {
            "postgres": {"status": "unknown", "latency_ms": None},
            "valkey": {"status": "unknown", "latency_ms": None}
        },
        "uptime_seconds": int(time.time() - _app_start_time) if _app_start_time > 0 else 0
    }
    
    has_critical_failure = False
    has_degradation = False
    
    # Check PostgreSQL connectivity (critical) with latency measurement
    try:
        start = time.perf_counter()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        health_status["dependencies"]["postgres"] = {
            "status": "healthy",
            "latency_ms": latency_ms
        }
    except Exception as e:
        has_critical_failure = True
        error_msg = str(e)[:100] if str(e) else "connection failed"
        health_status["dependencies"]["postgres"] = {
            "status": "unhealthy",
            "latency_ms": None,
            "error": error_msg
        }
        logger.warning(f"Database health check failed: {e}")
    
    # Check Valkey/Redis connectivity (non-critical) with latency measurement
    try:
        start = time.perf_counter()
        is_healthy, status_msg = await check_redis_health()
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        
        if is_healthy:
            health_status["dependencies"]["valkey"] = {
                "status": "healthy",
                "latency_ms": latency_ms
            }
        else:
            has_degradation = True
            health_status["dependencies"]["valkey"] = {
                "status": "degraded",
                "latency_ms": latency_ms,
                "error": status_msg
            }
            logger.debug(f"Valkey health check: {status_msg}")
    except Exception as e:
        has_degradation = True
        error_msg = str(e)[:100] if str(e) else "connection failed"
        health_status["dependencies"]["valkey"] = {
            "status": "degraded",
            "latency_ms": None,
            "error": error_msg
        }
        logger.debug(f"Valkey health check failed: {e}")
    
    # Determine overall status
    if has_critical_failure:
        health_status["status"] = "unhealthy"
    elif has_degradation:
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/health", tags=["status"])
async def health_check():
    """
    Health check endpoint with dependency status for Kubernetes probes.
    
    Returns detailed status including:
    - Overall status: healthy | degraded | unhealthy
    - Version: Current application version
    - Dependencies: PostgreSQL and Valkey status with latency
    - Uptime: Seconds since application started
    
    Results are cached for 1 second to avoid overhead from rapid K8s probe requests.
    
    Status levels:
    - healthy: All dependencies operational
    - degraded: Some non-critical dependencies unavailable (e.g., Valkey cache)
    - unhealthy: Critical dependencies unavailable (e.g., PostgreSQL)
    """
    global _health_cache, _health_cache_time
    
    current_time = time.time()
    
    # Return cached result if within TTL
    if _health_cache and (current_time - _health_cache_time) < _health_cache_ttl:
        return _health_cache
    
    # Perform health checks
    health_status = await _perform_health_checks()
    
    # Cache the result
    _health_cache = health_status
    _health_cache_time = current_time
    
    return health_status


@app.on_event("startup")
async def startup_event():
    """Application startup handler."""
    global _app_start_time
    _app_start_time = time.time()
    
    logger.info(f"Starting {settings.APP_NAME} API v{APP_VERSION}")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"OpenAPI docs: {'enabled' if settings.DOCS_ENABLED else 'disabled'}")
    logger.info(f"CORS origins: {settings.BACKEND_CORS_ORIGINS}")
    logger.info(f"Rate limiting: enabled")
    logger.info(f"Business metrics: enabled (5min update interval)")
    
    # Initialize database monitoring
    setup_db_monitoring(engine)
    logger.info("Database monitoring initialized (slow query threshold: 100ms)")
    
    # Verify database connectivity at startup
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified successfully")
    except Exception as e:
        logger.error(f"Database connection failed at startup: {e}")
        # Don't crash - let health checks handle it
    
    # Verify Redis connectivity at startup (non-blocking)
    try:
        client = await get_redis()
        if client:
            logger.info(f"Redis connection verified: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            logger.info("Rate limiting will use Redis backend (distributed)")
        else:
            logger.warning("Redis not available at startup - rate limiting will use in-memory storage")
    except Exception as e:
        logger.warning(f"Redis connection failed at startup: {e} - rate limiting will use in-memory storage")
    
    # Start business metrics background task
    asyncio.create_task(metrics_update_loop(interval_seconds=300))
    logger.info("Business metrics background task started")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown handler."""
    logger.info(f"Shutting down {settings.APP_NAME} API")
    
    # Close Redis connection gracefully
    await close_redis()
