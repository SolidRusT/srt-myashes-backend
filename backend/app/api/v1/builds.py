"""
Builds API Router - Character build persistence and sharing.

Endpoints:
- POST /api/v1/builds - Create a new build
- GET /api/v1/builds/popular - Get popular/trending builds for widget
- GET /api/v1/builds/templates - Get official template builds
- GET /api/v1/builds/{build_id} - Get a specific build
- GET /api/v1/builds - List public builds with filters and search
- PATCH /api/v1/builds/{build_id} - Update a build (owner only, not templates)
- DELETE /api/v1/builds/{build_id} - Delete a build (owner only, not templates)
- POST /api/v1/builds/{build_id}/vote - Vote on a build
- GET /api/v1/builds/auth/status - Check authentication status
- POST /api/v1/builds/auth/claim - Claim anonymous builds

Authentication Strategy:
- Anonymous users can read all public builds
- Anonymous users can create builds (session-based ownership)
- Authenticated users (Steam via PAM) get their Steam identity attached to builds
- Build ownership is checked via session_id OR player_id
- When AUTH_REQUIRED_FOR_WRITES=true, only authenticated users can create/modify
- Template builds are read-only and cannot be modified or deleted
"""
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.db.session import get_db
from app.models.build import Build, BuildVote
from app.schemas.builds import (
    BuildCreate,
    BuildResponse,
    BuildListItem,
    BuildListResponse,
    BuildUpdateRequest,
    VoteRequest,
    VoteResponse,
    DeleteResponse,
    PopularBuildItem,
    PopularBuildsResponse,
    TemplateListResponse,
    TimePeriod,
    CreatorInfo,
    AuthStatusResponse,
    ClaimBuildsRequest,
    ClaimBuildsResponse,
)
from app.core.errors import (
    BuildNotFoundError,
    ValidationError,
    AlreadyVotedError,
    NotOwnerError,
    AuthenticationRequiredError,
)
from app.core.security import generate_build_id
from app.core.session import get_session_id
from app.core.config import settings
from app.core.auth import get_current_user, AuthenticatedUser
from app.game_constants.game_data import get_class_name, validate_archetype, validate_race

logger = logging.getLogger(__name__)

router = APIRouter()


def build_share_url(build_id: str) -> str:
    """Generate the share URL for a build."""
    return f"{settings.WEBSITE_URL}/?build={build_id}"


def build_creator_info(build: Build) -> CreatorInfo:
    """Create CreatorInfo from build model."""
    return CreatorInfo(
        display_name=build.creator_display_name,
        steam_id=build.steam_id,
        is_authenticated=build.is_authenticated,
    )


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
        is_template=build.is_template,
        share_url=build_share_url(build.build_id),
        created_at=build.created_at,
        updated_at=build.updated_at,
        rating=build.avg_rating,
        vote_count=build.vote_count,
        created_by=build.creator_display_name,
        creator=build_creator_info(build),
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
        is_template=build.is_template,
        rating=build.avg_rating,
        vote_count=build.vote_count,
        created_at=build.created_at,
        created_by=build.creator_display_name,
    )


def build_to_popular_item(build: Build) -> PopularBuildItem:
    """Convert a Build model to a PopularBuildItem schema."""
    return PopularBuildItem(
        build_id=build.build_id,
        name=build.name,
        class_name=build.class_name,
        race=build.race,
        is_template=build.is_template,
        rating=build.avg_rating,
        vote_count=build.vote_count,
        share_url=build_share_url(build.build_id),
        created_by=build.creator_display_name,
    )


def check_build_ownership(build: Build, session_id: str, user: Optional[AuthenticatedUser]) -> bool:
    """
    Check if the requester owns the build.
    
    Ownership is determined by:
    1. Matching session_id (anonymous ownership)
    2. Matching player_id (authenticated ownership via PAM)
    
    Note: Template builds are never owned by users.
    """
    # Templates cannot be owned by users
    if build.is_template:
        return False
    
    # Check session-based ownership
    if build.session_id == session_id:
        return True
    
    # Check authenticated ownership
    if user and build.player_id and build.player_id == user.player_id:
        return True
    
    return False


@router.get("/auth/status", response_model=AuthStatusResponse)
async def get_auth_status(
    request: Request,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
):
    """
    Check authentication status.
    
    Returns information about the current user if authenticated,
    or anonymous status if not.
    """
    if user:
        return AuthStatusResponse(
            authenticated=True,
            player_id=user.player_id,
            steam_id=user.steam_id,
            display_name=user.display_name,
            tier=user.tier,
        )
    return AuthStatusResponse(
        authenticated=False,
        tier="anonymous",
    )


@router.post("/auth/claim", response_model=ClaimBuildsResponse)
async def claim_anonymous_builds(
    claim_request: ClaimBuildsRequest,
    request: Request,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Claim anonymous builds created with a session ID.
    
    This allows users who created builds before authenticating
    to link those builds to their Steam account.
    
    Requires authentication.
    """
    if not user:
        raise AuthenticationRequiredError("You must be logged in to claim builds")
    
    # Find all builds with the given session_id that don't have a player_id
    builds_to_claim = db.query(Build).filter(
        Build.session_id == claim_request.session_id,
        Build.player_id == None,  # noqa: E711
        Build.is_template == False,  # Don't claim templates
    ).all()
    
    if not builds_to_claim:
        return ClaimBuildsResponse(
            claimed_count=0,
            build_ids=[],
            message="No anonymous builds found for this session",
        )
    
    # Claim the builds
    claimed_ids = []
    for build in builds_to_claim:
        build.player_id = user.player_id
        build.steam_id = user.steam_id
        build.steam_display_name = user.steam_display_name
        claimed_ids.append(build.build_id)
    
    db.commit()
    
    logger.info(f"User {user.player_id} claimed {len(claimed_ids)} builds from session {claim_request.session_id[:8]}...")
    
    return ClaimBuildsResponse(
        claimed_count=len(claimed_ids),
        build_ids=claimed_ids,
        message=f"Successfully claimed {len(claimed_ids)} builds",
    )


@router.post("", response_model=BuildResponse, status_code=status.HTTP_201_CREATED)
async def create_build(
    build_data: BuildCreate,
    request: Request,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new character build.

    The class_name is computed from primary_archetype + secondary_archetype.
    
    If authenticated (Steam via PAM):
    - Build is linked to player_id and steam_id
    - Creator name shows Steam display name
    
    If anonymous:
    - Build is linked to session_id only
    - Creator name shows "anonymous"
    
    When AUTH_REQUIRED_FOR_WRITES is enabled, authentication is required.
    """
    session_id = get_session_id(request)
    
    # Check if authentication is required for writes
    if settings.AUTH_REQUIRED_FOR_WRITES and not user:
        raise AuthenticationRequiredError("Authentication required to create builds")

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

    # Create build with authentication info if available
    build = Build(
        build_id=build_id,
        name=build_data.name,
        description=build_data.description,
        primary_archetype=build_data.primary_archetype,
        secondary_archetype=build_data.secondary_archetype,
        class_name=class_name,
        race=build_data.race,
        is_public=build_data.is_public,
        is_template=False,  # User-created builds are never templates
        session_id=session_id,
        # Authentication fields (if user is authenticated)
        player_id=user.player_id if user else None,
        steam_id=user.steam_id if user else None,
        steam_display_name=user.steam_display_name if user else None,
    )

    db.add(build)
    db.commit()
    db.refresh(build)

    creator_info = f"by {user.display_name}" if user else f"anonymously (session {session_id[:8]}...)"
    logger.info(f"Created build {build_id} ({class_name}) {creator_info}")

    return build_to_response(build)


@router.get("/templates", response_model=TemplateListResponse)
async def get_template_builds(
    db: Session = Depends(get_db)
):
    """
    Get all official template builds.
    
    Templates are pre-made builds for common archetypes to help
    new users get started. They are read-only and shown prominently
    in the frontend.
    """
    templates = db.query(Build).filter(
        Build.is_template == True
    ).order_by(
        Build.class_name,
        Build.name
    ).all()
    
    return TemplateListResponse(
        templates=[build_to_list_item(t) for t in templates],
        count=len(templates),
    )


@router.get("/popular", response_model=PopularBuildsResponse)
async def get_popular_builds(
    period: TimePeriod = Query(TimePeriod.WEEK, description="Time period to filter by"),
    limit: int = Query(5, ge=1, le=20, description="Number of builds to return"),
    include_templates: bool = Query(False, description="Include template builds"),
    db: Session = Depends(get_db)
):
    """
    Get popular/trending builds for homepage widget display.

    Returns top builds sorted by a combination of rating and vote count,
    optionally filtered by time period.

    Time periods:
    - day: Last 24 hours
    - week: Last 7 days
    - month: Last 30 days
    - all: All time

    The popularity score is calculated as: (avg_rating * vote_count) to balance
    both quality (rating) and engagement (votes).
    """
    # Base query - only public builds with at least 1 vote
    query = db.query(Build).filter(
        Build.is_public == True,
        Build.vote_count > 0
    )
    
    # Exclude templates unless explicitly requested
    if not include_templates:
        query = query.filter(Build.is_template == False)

    # Apply time period filter
    now = datetime.utcnow()
    if period == TimePeriod.DAY:
        cutoff = now - timedelta(days=1)
        query = query.filter(Build.created_at >= cutoff)
    elif period == TimePeriod.WEEK:
        cutoff = now - timedelta(days=7)
        query = query.filter(Build.created_at >= cutoff)
    elif period == TimePeriod.MONTH:
        cutoff = now - timedelta(days=30)
        query = query.filter(Build.created_at >= cutoff)
    # TimePeriod.ALL has no date filter

    # Calculate popularity score: (rating_sum / vote_count) * vote_count = rating_sum
    # But we want to favor builds with more votes, so we use:
    # popularity = avg_rating * sqrt(vote_count) to balance quality and engagement
    # For simplicity, we sort by weighted score: rating_sum (which is avg * count)
    # This naturally balances high ratings with more votes
    query = query.order_by(
        desc(Build.rating_sum),  # Total rating points (quality * quantity)
        desc(Build.vote_count),  # Tiebreaker: more votes
        desc(Build.created_at)   # Tiebreaker: newer
    )

    # Limit results
    builds = query.limit(limit).all()

    return PopularBuildsResponse(
        builds=[build_to_popular_item(b) for b in builds],
        period=period.value,
        count=len(builds),
    )


@router.get("/{build_id}", response_model=BuildResponse)
async def get_build(
    build_id: str,
    request: Request,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific build by ID.

    Public builds are accessible to everyone.
    Private builds are only accessible to the owner.
    Template builds are always accessible.
    """
    session_id = get_session_id(request)

    build = db.query(Build).filter(Build.build_id == build_id).first()

    if not build:
        raise BuildNotFoundError(build_id)

    # Templates are always public, other private builds need ownership check
    if not build.is_public and not build.is_template:
        if not check_build_ownership(build, session_id, user):
            raise BuildNotFoundError(build_id)  # Don't reveal that it exists

    return build_to_response(build)


@router.get("", response_model=BuildListResponse)
async def list_builds(
    request: Request,
    search: Optional[str] = Query(None, min_length=2, max_length=100, description="Search by name or description (partial match)"),
    class_name: Optional[str] = None,
    primary_archetype: Optional[str] = None,
    secondary_archetype: Optional[str] = None,
    race: Optional[str] = None,
    is_template: Optional[bool] = Query(None, description="Filter by template status"),
    sort: str = Query("newest", pattern="^(rating|newest|popular)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List public builds with filtering, search, and pagination.

    Search:
    - search: Text search across build name and description (case-insensitive partial match)

    Filters:
    - class_name: Filter by computed class name (e.g., "Knight")
    - primary_archetype: Filter by primary archetype
    - secondary_archetype: Filter by secondary archetype
    - race: Filter by race
    - is_template: Filter by template status (true/false/null for all)

    Sort options:
    - newest: Most recently created first
    - rating: Highest rated first
    - popular: Most votes first
    
    Search and filters can be combined. For example:
    - ?search=tank&class_name=Guardian - Search for "tank" within Guardian builds
    - ?search=healer&is_template=true - Search for "healer" in template builds only
    """
    # Base query - only public builds
    query = db.query(Build).filter(Build.is_public == True)

    # Apply text search (case-insensitive partial match on name and description)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Build.name.ilike(search_term),
                Build.description.ilike(search_term),
                Build.class_name.ilike(search_term),  # Also search class name for convenience
            )
        )

    # Apply filters
    if class_name:
        query = query.filter(Build.class_name.ilike(f"%{class_name}%"))
    if primary_archetype:
        query = query.filter(Build.primary_archetype == primary_archetype.lower())
    if secondary_archetype:
        query = query.filter(Build.secondary_archetype == secondary_archetype.lower())
    if race:
        query = query.filter(Build.race == race.lower())
    if is_template is not None:
        query = query.filter(Build.is_template == is_template)

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


@router.patch("/{build_id}", response_model=BuildResponse)
async def update_build(
    build_id: str,
    update_data: BuildUpdateRequest,
    request: Request,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a build.

    Only the owner (by session_id or player_id) can update the build.
    Template builds cannot be modified.
    
    Updatable fields:
    - name
    - description
    - is_public
    """
    session_id = get_session_id(request)

    build = db.query(Build).filter(Build.build_id == build_id).first()

    if not build:
        raise BuildNotFoundError(build_id)
    
    # Templates cannot be modified
    if build.is_template:
        raise NotOwnerError("build", "Template builds cannot be modified")

    # Check ownership
    if not check_build_ownership(build, session_id, user):
        raise NotOwnerError("build")

    # Update fields if provided
    if update_data.name is not None:
        build.name = update_data.name
    if update_data.description is not None:
        build.description = update_data.description
    if update_data.is_public is not None:
        build.is_public = update_data.is_public

    db.commit()
    db.refresh(build)

    logger.info(f"Updated build {build_id}")

    return build_to_response(build)


@router.delete("/{build_id}", response_model=DeleteResponse)
async def delete_build(
    build_id: str,
    request: Request,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a build.

    Only the owner (by session_id or player_id) can delete the build.
    Template builds cannot be deleted.
    """
    session_id = get_session_id(request)

    build = db.query(Build).filter(Build.build_id == build_id).first()

    if not build:
        raise BuildNotFoundError(build_id)
    
    # Templates cannot be deleted
    if build.is_template:
        raise NotOwnerError("build", "Template builds cannot be deleted")

    # Check ownership
    if not check_build_ownership(build, session_id, user):
        raise NotOwnerError("build")

    # Delete the build (votes cascade due to relationship)
    db.delete(build)
    db.commit()

    owner_info = f"player {user.player_id}" if user else f"session {session_id[:8]}..."
    logger.info(f"Deleted build {build_id} by {owner_info}")

    return DeleteResponse(build_id=build_id)


@router.post("/{build_id}/vote", response_model=VoteResponse)
async def vote_build(
    build_id: str,
    vote_data: VoteRequest,
    request: Request,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Vote on a build (1-5 stars).

    Each session can only vote once per build.
    Each authenticated player can only vote once per build.
    Voting updates the build's aggregate rating.
    
    You can vote on template builds.
    """
    session_id = get_session_id(request)

    # Get the build
    build = db.query(Build).filter(Build.build_id == build_id).first()

    if not build:
        raise BuildNotFoundError(build_id)

    # Check if already voted - check both session and player
    existing_vote_query = db.query(BuildVote).filter(BuildVote.build_id == build_id)
    
    if user:
        # Check for existing vote by player_id
        existing_vote = existing_vote_query.filter(BuildVote.player_id == user.player_id).first()
        if existing_vote:
            raise AlreadyVotedError(build_id)
    
    # Also check session-based vote
    existing_session_vote = existing_vote_query.filter(BuildVote.session_id == session_id).first()
    if existing_session_vote:
        raise AlreadyVotedError(build_id)

    # Create vote with authentication info if available
    vote = BuildVote(
        build_id=build_id,
        session_id=session_id,
        player_id=user.player_id if user else None,
        steam_id=user.steam_id if user else None,
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

    voter_info = f"player {user.player_id}" if user else f"session {session_id[:8]}..."
    logger.info(f"Vote {vote_data.rating}/5 on build {build_id} by {voter_info}")

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
        "message": "Builds API is fully implemented with Steam authentication, templates, and search",
        "auth_required_for_writes": settings.AUTH_REQUIRED_FOR_WRITES,
        "endpoints": [
            "POST /api/v1/builds - Create build",
            "GET /api/v1/builds/templates - Get template builds",
            "GET /api/v1/builds/popular - Get popular builds",
            "GET /api/v1/builds/{build_id} - Get build",
            "GET /api/v1/builds - List builds (with search)",
            "PATCH /api/v1/builds/{build_id} - Update build",
            "DELETE /api/v1/builds/{build_id} - Delete build",
            "POST /api/v1/builds/{build_id}/vote - Vote on build",
            "GET /api/v1/builds/auth/status - Check auth status",
            "POST /api/v1/builds/auth/claim - Claim anonymous builds",
        ]
    }
