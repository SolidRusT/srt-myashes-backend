"""
Custom error handling for MyAshes.ai backend.

Returns errors in the agreed JSON format:
{
    "error": "error_code",
    "message": "Human readable message",
    "status": 404
}
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Optional


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        error: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[dict] = None
    ):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert to response dict."""
        response = {
            "error": self.error,
            "message": self.message,
            "status": self.status_code
        }
        if self.details:
            response["details"] = self.details
        return response


# Specific error classes
class BuildNotFoundError(APIError):
    """Build does not exist."""

    def __init__(self, build_id: str):
        super().__init__(
            error="build_not_found",
            message=f"Build {build_id} does not exist",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ValidationError(APIError):
    """Request validation failed."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            error="validation_error",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AlreadyVotedError(APIError):
    """User has already voted on this build."""

    def __init__(self, build_id: str):
        super().__init__(
            error="already_voted",
            message=f"You have already voted on build {build_id}",
            status_code=status.HTTP_409_CONFLICT
        )


class NotOwnerError(APIError):
    """User is not the owner of this resource."""

    def __init__(self, resource: str = "build"):
        super().__init__(
            error="not_owner",
            message=f"You do not have permission to modify this {resource}",
            status_code=status.HTTP_403_FORBIDDEN
        )


class RateLimitedError(APIError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            error="rate_limited",
            message=f"Rate limit exceeded. Try again in {retry_after} seconds",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after}
        )


class NotImplementedError(APIError):
    """Feature not yet implemented."""

    def __init__(self, feature: str = "This feature"):
        super().__init__(
            error="not_implemented",
            message=f"{feature} is not yet implemented",
            status_code=status.HTTP_501_NOT_IMPLEMENTED
        )


class InternalError(APIError):
    """Internal server error."""

    def __init__(self, message: str = "An internal error occurred"):
        super().__init__(
            error="internal_error",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions and return JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )
