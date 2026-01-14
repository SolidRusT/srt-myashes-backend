"""
MyAshes.ai Backend API

Product-specific backend services for the Ashes of Creation game assistant.
Provides build persistence, voting, feedback collection, and analytics.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from prometheus_fastapi_instrumentator import Instrumentator
import logging

from app.api.v1 import api_router
from app.core.config import settings
from app.core.errors import APIError, api_error_handler, ValidationError
from app.core.session import SessionMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for MyAshes.ai - Ashes of Creation game assistant",
    version="2.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    debug=settings.DEBUG
)

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
        expose_headers=["X-Session-ID"],
    )


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


@app.get("/")
def root():
    """Root endpoint - basic info."""
    return {
        "name": settings.APP_NAME,
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs" if settings.DEBUG else "disabled in production",
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Application startup handler."""
    logger.info(f"Starting {settings.APP_NAME} API")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"CORS origins: {settings.BACKEND_CORS_ORIGINS}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown handler."""
    logger.info(f"Shutting down {settings.APP_NAME} API")
