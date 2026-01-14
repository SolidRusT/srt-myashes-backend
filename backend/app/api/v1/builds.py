"""
Builds API Router - Character build persistence and sharing.

Endpoints:
- POST /api/v1/builds - Create a new build
- GET /api/v1/builds/{build_id} - Get a specific build
- GET /api/v1/builds - List public builds with filters
- DELETE /api/v1/builds/{build_id} - Delete a build (owner only)
- POST /api/v1/builds/{build_id}/vote - Vote on a build
"""
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from sqlalchemy.exc import IntegrityError
from typing import Optional
import logging

from app.db.session import get_db
from app.models.build import Build, BuildVote
from app.schemas.builds import (
    BuildCreate,
    BuildResponse,
    BuildListItem,
    BuildListResponse,
    VoteRequest,
    VoteResponse,
    DeleteResponse,
)
from app.core.errors import (
    BuildNotFoundError,
    ValidationError,
    AlreadyVotedError,
    NotOwnerError,
)
from app.core.security import generate_build_id
from app.core.session import get_session_id
from app.core.config import settings
from app.game_constants.game_data import get_class_name, validate_archetype, validate_race

logger = logging.getLogger(__name__)

router = APIRouter()


def build_share_url(build_id: str) -> str:
    """Generate the share URL for a build."""
    return f"{settings.WEBSITE_URL}/?build={build_id}"


def build_to_response(build: Build) -> BuildResponse:
    """Convert a Build model to a BuildResponse schema."""
    return BuildResponse(
        build_id=build.build_id,
        name=build.name,
        description=build.description,
        primary_archetype=build.primary_archetype,
        secondary_archetype=build.secondary_archetype,
        class_name=build.class_name,
        race=build.race,
        is_public=build.is_public,
        share_url=build_share_url(build.build_id),
        created_at=build.created_at,
        updated_at=build.updated_at,
        rating=build.avg_rating,
        vote_count=build.vote_count,
        created_by="anonymous",  # Will be username when OAuth is implemented
    )


def build_to_list_item(build: Build) -> BuildListItem:
    """Convert a Build model to a BuildListItem schema."""
    return BuildListItem(
        build_id=build.build_id,
        name=build.name,
        description=build.description,
        primary_archetype=build.primary_archetype,
        secondary_archetype=build.secondary_archetype,
        class_name=build.class_name,
        race=build.race,
        rating=build.avg_rating,
        vote_count=build.vote_count,
        created_at=build.created_at,
    )


@router.post("", response_model=BuildResponse, status_code=status.HTTP_201_CREATED)
async def create_build(
    build_data: BuildCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a new character build.

    The class_name is computed from primary_archetype + secondary_archetype.
    The build is associated with the session ID for ownership.
    """
    session_id = get_session_id(request)

    # Validate archetypes
    if not validate_archetype(build_data.primary_archetype):
        raise ValidationError(f"Invalid primary archetype: {build_data.primary_archetype}")
    if not validate_archetype(build_data.secondary_archetype):
        raise ValidationError(f"Invalid secondary archetype: {build_data.secondary_archetype}")

    # Validate race
    if not validate_race(build_data.race):
        raise ValidationError(f"Invalid race: {build_data.race}")

    # Compute class name from matrix
    class_name = get_class_name(build_data.primary_archetype, build_data.secondary_archetype)
    if not class_name:
        raise ValidationError(
            f"Invalid archetype combination: {build_data.primary_archetype} + {build_data.secondary_archetype}"
        )

    # Generate unique build ID
    build_id = generate_build_id()

    # Create build
    build = Build(
        build_id=build_id,
        name=build_data.name,
        description=build_data.description,
        primary_archetype=build_data.primary_archetype,
        secondary_archetype=build_data.secondary_archetype,
        class_name=class_name,
        race=build_data.race,
        is_public=build_data.is_public,
        session_id=session_id,
    )

    db.add(build)
    db.commit()
    db.refresh(build)

    logger.info(f"Created build {build_id} ({class_name}) for session {session_id[:8]}...")

    return build_to_response(build)


@router.get("/{build_id}", response_model=BuildResponse)
async def get_build(
    build_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get a specific build by ID.

    Public builds are accessible to everyone.
    Private builds are only accessible to the owner.
    """
    session_id = get_session_id(request)

    build = db.query(Build).filter(Build.build_id == build_id).first()

    if not build:
        raise BuildNotFoundError(build_id)

    # Check access for private builds
    if not build.is_public and build.session_id != session_id:
        raise BuildNotFoundError(build_id)  # Don't reveal that it exists

    return build_to_response(build)


@router.get("", response_model=BuildListResponse)
async def list_builds(
    request: Request,
    class_name: Optional[str] = None,
    primary_archetype: Optional[str] = None,
    secondary_archetype: Optional[str] = None,
    race: Optional[str] = None,
    sort: str = Query("newest", pattern="^(rating|newest|popular)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List public builds with filtering and pagination.

    Filters:
    - class_name: Filter by computed class name (e.g., "Knight")
    - primary_archetype: Filter by primary archetype
    - secondary_archetype: Filter by secondary archetype
    - race: Filter by race

    Sort options:
    - newest: Most recently created first
    - rating: Highest rated first
    - popular: Most votes first
    """
    # Base query - only public builds
    query = db.query(Build).filter(Build.is_public == True)

    # Apply filters
    if class_name:
        query = query.filter(Build.class_name.ilike(f"%{class_name}%"))
    if primary_archetype:
        query = query.filter(Build.primary_archetype == primary_archetype.lower())
    if secondary_archetype:
        query = query.filter(Build.secondary_archetype == secondary_archetype.lower())
    if race:
        query = query.filter(Build.race == race.lower())

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    if sort == "newest":
        query = query.order_by(desc(Build.created_at))
    elif sort == "rating":
        # Sort by average rating (computed), nulls last
        query = query.order_by(
            desc(func.coalesce(Build.rating_sum / func.nullif(Build.vote_count, 0), 0)),
            desc(Build.vote_count)
        )
    elif sort == "popular":
        query = query.order_by(desc(Build.vote_count), desc(Build.created_at))

    # Apply pagination
    offset = (page - 1) * limit
    builds = query.offset(offset).limit(limit).all()

    # Calculate has_more
    has_more = (offset + len(builds)) < total

    return BuildListResponse(
        builds=[build_to_list_item(b) for b in builds],
        total=total,
        page=page,
        limit=limit,
        has_more=has_more,
    )


@router.delete("/{build_id}", response_model=DeleteResponse)
async def delete_build(
    build_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Delete a build.

    Only the session that created the build can delete it.
    """
    session_id = get_session_id(request)

    build = db.query(Build).filter(Build.build_id == build_id).first()

    if not build:
        raise BuildNotFoundError(build_id)

    # Check ownership
    if build.session_id != session_id:
        raise NotOwnerError("build")

    # Delete the build (votes cascade due to relationship)
    db.delete(build)
    db.commit()

    logger.info(f"Deleted build {build_id} by session {session_id[:8]}...")

    return DeleteResponse(build_id=build_id)


@router.post("/{build_id}/vote", response_model=VoteResponse)
async def vote_build(
    build_id: str,
    vote_data: VoteRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Vote on a build (1-5 stars).

    Each session can only vote once per build.
    Voting updates the build's aggregate rating.
    """
    session_id = get_session_id(request)

    # Get the build
    build = db.query(Build).filter(Build.build_id == build_id).first()

    if not build:
        raise BuildNotFoundError(build_id)

    # Check if already voted
    existing_vote = db.query(BuildVote).filter(
        BuildVote.build_id == build_id,
        BuildVote.session_id == session_id
    ).first()

    if existing_vote:
        raise AlreadyVotedError(build_id)

    # Create vote
    vote = BuildVote(
        build_id=build_id,
        session_id=session_id,
        rating=vote_data.rating,
    )

    try:
        db.add(vote)

        # Update build aggregates
        build.rating_sum += vote_data.rating
        build.vote_count += 1

        db.commit()
        db.refresh(build)

    except IntegrityError:
        db.rollback()
        raise AlreadyVotedError(build_id)

    logger.info(f"Vote {vote_data.rating}/5 on build {build_id} by session {session_id[:8]}...")

    return VoteResponse(
        build_id=build_id,
        your_rating=vote_data.rating,
        avg_rating=build.avg_rating or 0.0,
        vote_count=build.vote_count,
    )


# Health check endpoint for this router
@router.get("/health/status")
async def builds_health():
    """Health check for builds API."""
    return {
        "status": "operational",
        "message": "Builds API is fully implemented",
        "endpoints": [
            "POST /api/v1/builds - Create build",
            "GET /api/v1/builds/{build_id} - Get build",
            "GET /api/v1/builds - List builds",
            "DELETE /api/v1/builds/{build_id} - Delete build",
            "POST /api/v1/builds/{build_id}/vote - Vote on build",
        ]
    }
