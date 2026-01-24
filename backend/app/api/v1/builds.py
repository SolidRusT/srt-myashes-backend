"""Build management API endpoints.

Provides CRUD operations for build persistence, voting, and sharing.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging

from app.core.config import settings
from app.core.errors import NotFoundError, UnauthorizedError, ValidationError
from app.core.business_metrics import (
    increment_build_counter,
    increment_vote_counter,
    increment_build_share_counter
)
from app.db.session import get_db
from app.models.build import Build, BuildVote
from app.schemas.builds import (
    BuildCreate,
    BuildUpdate,
    BuildResponse,
    BuildListResponse,
    BuildVoteCreate,
    BuildVoteResponse,
)
from app.services.auth import get_current_user_optional, User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/builds", response_model=BuildResponse, status_code=status.HTTP_201_CREATED)
async def create_build(
    build_in: BuildCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Create a new build.
    
    - Authenticated users: Build is tied to their user_id
    - Anonymous users: Build is tied to session_id only
    """
    session_id = request.headers.get("X-Session-ID")
    
    # Create build
    build = Build(
        **build_in.model_dump(),
        user_id=current_user.user_id if current_user else None,
        session_id=session_id,
    )
    
    db.add(build)
    await db.commit()
    await db.refresh(build)
    
    # Increment business metrics
    increment_build_counter()
    
    logger.info(f"Build created: {build.id} by {'user ' + current_user.user_id if current_user else 'session ' + session_id}")
    
    return build


@router.get("/builds", response_model=BuildListResponse)
async def list_builds(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    primary_class: Optional[str] = None,
    primary_archetype: Optional[str] = None,
    race: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|name|vote_count|avg_rating)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """List builds with pagination and filtering.
    
    Filtering:
    - primary_class: Filter by primary class
    - primary_archetype: Filter by archetype
    - race: Filter by race
    - search: Search in name and description
    
    Sorting:
    - sort_by: created_at, updated_at, name, vote_count, avg_rating
    - sort_order: asc, desc
    """
    # Base query
    query = select(Build)
    count_query = select(func.count(Build.id))
    
    # Apply filters
    filters = []
    
    if primary_class:
        filters.append(Build.primary_class == primary_class)
    
    if primary_archetype:
        filters.append(Build.primary_archetype == primary_archetype)
    
    if race:
        filters.append(Build.race == race)
    
    if search:
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                Build.name.ilike(search_pattern),
                Build.description.ilike(search_pattern),
            )
        )
    
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply sorting
    sort_column = getattr(Build, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    builds = result.scalars().all()
    
    return BuildListResponse(
        builds=builds,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/builds/{build_id}", response_model=BuildResponse)
async def get_build(
    build_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific build by ID."""
    result = await db.execute(
        select(Build).where(Build.id == build_id)
    )
    build = result.scalar_one_or_none()
    
    if not build:
        raise NotFoundError(resource="Build", resource_id=build_id)
    
    # Increment share counter (view count proxy)
    increment_build_share_counter()
    
    return build


@router.patch("/builds/{build_id}", response_model=BuildResponse)
async def update_build(
    build_id: str,
    build_update: BuildUpdate,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Update a build.
    
    Only the build owner (user_id or session_id) can update it.
    """
    session_id = request.headers.get("X-Session-ID")
    
    # Get existing build
    result = await db.execute(
        select(Build).where(Build.id == build_id)
    )
    build = result.scalar_one_or_none()
    
    if not build:
        raise NotFoundError(resource="Build", resource_id=build_id)
    
    # Check ownership
    is_owner = False
    if current_user and build.user_id == current_user.user_id:
        is_owner = True
    elif not current_user and build.session_id == session_id:
        is_owner = True
    
    if not is_owner:
        raise UnauthorizedError(message="You can only update your own builds")
    
    # Update fields
    update_data = build_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(build, field, value)
    
    await db.commit()
    await db.refresh(build)
    
    logger.info(f"Build updated: {build_id}")
    
    return build


@router.delete("/builds/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_build(
    build_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Delete a build.
    
    Only the build owner (user_id or session_id) can delete it.
    """
    session_id = request.headers.get("X-Session-ID")
    
    # Get existing build
    result = await db.execute(
        select(Build).where(Build.id == build_id)
    )
    build = result.scalar_one_or_none()
    
    if not build:
        raise NotFoundError(resource="Build", resource_id=build_id)
    
    # Check ownership
    is_owner = False
    if current_user and build.user_id == current_user.user_id:
        is_owner = True
    elif not current_user and build.session_id == session_id:
        is_owner = True
    
    if not is_owner:
        raise UnauthorizedError(message="You can only delete your own builds")
    
    await db.delete(build)
    await db.commit()
    
    logger.info(f"Build deleted: {build_id}")


@router.post("/builds/{build_id}/vote", response_model=BuildVoteResponse)
async def vote_on_build(
    build_id: str,
    vote_in: BuildVoteCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Vote on a build (1-5 stars).
    
    - Users can vote multiple times (overwrites previous vote)
    - Votes are tracked by user_id (authenticated) or session_id (anonymous)
    """
    session_id = request.headers.get("X-Session-ID")
    
    # Check if build exists
    build_result = await db.execute(
        select(Build).where(Build.id == build_id)
    )
    build = build_result.scalar_one_or_none()
    
    if not build:
        raise NotFoundError(resource="Build", resource_id=build_id)
    
    # Check for existing vote
    vote_query = select(BuildVote).where(BuildVote.build_id == build_id)
    
    if current_user:
        vote_query = vote_query.where(BuildVote.user_id == current_user.user_id)
    else:
        vote_query = vote_query.where(BuildVote.session_id == session_id)
    
    existing_vote_result = await db.execute(vote_query)
    existing_vote = existing_vote_result.scalar_one_or_none()
    
    if existing_vote:
        # Update existing vote
        existing_vote.rating = vote_in.rating
        await db.commit()
        await db.refresh(existing_vote)
        logger.info(f"Vote updated on build {build_id}: {vote_in.rating}")
        vote = existing_vote
    else:
        # Create new vote
        vote = BuildVote(
            build_id=build_id,
            rating=vote_in.rating,
            user_id=current_user.user_id if current_user else None,
            session_id=session_id,
        )
        db.add(vote)
        await db.commit()
        await db.refresh(vote)
        
        # Increment business metrics (only for new votes)
        increment_vote_counter()
        
        logger.info(f"Vote created on build {build_id}: {vote_in.rating}")
    
    # Update build's cached vote stats
    await _update_build_vote_stats(db, build_id)
    
    return vote


async def _update_build_vote_stats(db: AsyncSession, build_id: str):
    """Update cached vote count and average rating for a build."""
    # Get vote stats
    stats_result = await db.execute(
        select(
            func.count(BuildVote.id).label('count'),
            func.avg(BuildVote.rating).label('avg_rating'),
        ).where(BuildVote.build_id == build_id)
    )
    stats = stats_result.one()
    
    # Update build
    await db.execute(
        update(Build)
        .where(Build.id == build_id)
        .values(
            vote_count=stats.count,
            avg_rating=float(stats.avg_rating) if stats.avg_rating else 0.0,
        )
    )
    await db.commit()
