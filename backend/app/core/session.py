"""
Session management for MyAshes.ai backend.

Sessions are anonymous and identified by a session ID:
- Frontend generates: sess_ + 24 hex chars
- Backend generates if missing: sess_ + 24 hex chars
- Passed via X-Session-ID header
"""
import secrets
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import re

SESSION_HEADER = "X-Session-ID"
SESSION_PREFIX = "sess_"
SESSION_PATTERN = re.compile(r"^sess_[a-f0-9]{24}$")


def generate_session_id() -> str:
    """Generate a new session ID matching frontend format."""
    return f"{SESSION_PREFIX}{secrets.token_hex(12)}"


def validate_session_id(session_id: str) -> bool:
    """Validate session ID format."""
    return bool(SESSION_PATTERN.match(session_id))


def get_session_id(request: Request) -> str:
    """
    Get session ID from request.

    Returns the session ID from the request state (set by middleware).
    """
    return getattr(request.state, "session_id", None) or generate_session_id()


class SessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle session ID extraction and generation.

    - Extracts X-Session-ID from request header if present and valid
    - Generates new session ID if missing or invalid
    - Adds session ID to response header
    - Makes session ID available via request.state.session_id
    """

    async def dispatch(self, request: Request, call_next):
        # Extract session ID from header
        session_id = request.headers.get(SESSION_HEADER)

        # Track if we generated a new session
        session_generated = False

        # Validate or generate session ID
        if session_id and validate_session_id(session_id):
            # Valid session ID provided
            pass
        else:
            # Generate new session ID
            session_id = generate_session_id()
            session_generated = True

        # Store in request state for route handlers
        request.state.session_id = session_id
        request.state.session_generated = session_generated

        # Process request
        response: Response = await call_next(request)

        # Always include session ID in response header
        # This allows frontend to capture it if we generated one
        response.headers[SESSION_HEADER] = session_id

        return response
