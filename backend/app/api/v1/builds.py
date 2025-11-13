from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from app.services.vector_store import query_vector_store
from app.services.cache_service import set_cache, get_cache_value
from loguru import logger

router = APIRouter()

# Models
class BuildClass(BaseModel):
    primary: str = Field(..., description="Primary archetype")
    secondary: str = Field(..., description="Secondary archetype")
    classType: str = Field(..., description="Resulting class name")

class BuildSkill(BaseModel):
    id: str = Field(..., description="Skill ID")
    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="Skill description")
    level: int = Field(..., description="Skill level")
    category: str = Field(..., description="Skill category")

class BuildEquipment(BaseModel):
    id: str = Field(..., description="Equipment ID")
    name: str = Field(..., description="Equipment name")
    slot: str = Field(..., description="Equipment slot")
    quality: str = Field(..., description="Item quality")
    stats: Dict[str, Any] = Field(..., description="Item stats")

class CharacterBuild(BaseModel):
    id: str = Field(..., description="Build ID")
    name: str = Field(..., description="Build name")
    description: str = Field(None, description="Build description")
    race: str = Field(..., description="Character race")
    classes: BuildClass = Field(..., description="Character class combination")
    level: int = Field(..., description="Character level")
    skills: List[BuildSkill] = Field([], description="Character skills")
    equipment: List[BuildEquipment] = Field([], description="Character equipment")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user_id: Optional[str] = Field(None, description="User ID (if authenticated)")
    is_public: bool = Field(True, description="Whether the build is public")
    tags: List[str] = Field([], description="Build tags")

class BuildCreate(BaseModel):
    name: str = Field(..., description="Build name")
    description: Optional[str] = Field(None, description="Build description")
    race: str = Field(..., description="Character race")
    classes: BuildClass = Field(..., description="Character class combination")
    level: int = Field(1, ge=1, le=50, description="Character level")
    skills: List[BuildSkill] = Field([], description="Character skills")
    equipment: List[BuildEquipment] = Field([], description="Character equipment")
    is_public: bool = Field(True, description="Whether the build is public")
    tags: List[str] = Field([], description="Build tags")

class BuildUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Build name")
    description: Optional[str] = Field(None, description="Build description")
    race: Optional[str] = Field(None, description="Character race")
    classes: Optional[BuildClass] = Field(None, description="Character class combination")
    level: Optional[int] = Field(None, ge=1, le=50, description="Character level")
    skills: Optional[List[BuildSkill]] = Field(None, description="Character skills")
    equipment: Optional[List[BuildEquipment]] = Field(None, description="Character equipment")
    is_public: Optional[bool] = Field(None, description="Whether the build is public")
    tags: Optional[List[str]] = Field(None, description="Build tags")

class ArchetypeInfo(BaseModel):
    id: str = Field(..., description="Archetype ID")
    name: str = Field(..., description="Archetype name")
    description: str = Field(..., description="Archetype description")

class ClassInfo(BaseModel):
    id: str = Field(..., description="Class ID")
    name: str = Field(..., description="Class name")
    primary: str = Field(..., description="Primary archetype")
    secondary: str = Field(..., description="Secondary archetype")
    description: str = Field(..., description="Class description")

class RaceInfo(BaseModel):
    id: str = Field(..., description="Race ID")
    name: str = Field(..., description="Race name")
    description: str = Field(..., description="Race description")
    racial_traits: List[Dict[str, str]] = Field([], description="Racial traits")

# Routes
@router.get("/archetypes", response_model=List[ArchetypeInfo])
async def get_archetypes():
    """
    Get all available archetypes in the game.
    """
    try:
        # Check cache first
        cache_key = "builds:archetypes"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return cached_data
        
        # Query vector store
        results = query_vector_store("list all archetypes", limit=10, filters={"type": "archetype"})
        
        archetypes = []
        for doc in results:
            metadata = doc.get("metadata", {})
            archetype = ArchetypeInfo(
                id=metadata.get("id", str(uuid.uuid4())),
                name=metadata.get("name", "Unknown"),
                description=metadata.get("description", "")
            )
            archetypes.append(archetype)
        
        # Cache the results
        await set_cache(cache_key, [a.dict() for a in archetypes], expire=86400)  # 1 day
        
        return archetypes
        
    except Exception as e:
        logger.error(f"Error getting archetypes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve archetypes"
        )

@router.get("/classes", response_model=List[ClassInfo])
async def get_classes():
    """
    Get all available classes in the game.
    """
    try:
        # Check cache first
        cache_key = "builds:classes"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return cached_data
        
        # Query vector store
        results = query_vector_store("list all classes", limit=20, filters={"type": "class"})
        
        classes = []
        for doc in results:
            metadata = doc.get("metadata", {})
            class_info = ClassInfo(
                id=metadata.get("id", str(uuid.uuid4())),
                name=metadata.get("name", "Unknown"),
                primary=metadata.get("primary_archetype", "Unknown"),
                secondary=metadata.get("secondary_archetype", "Unknown"),
                description=metadata.get("description", "")
            )
            classes.append(class_info)
        
        # Cache the results
        await set_cache(cache_key, [c.dict() for c in classes], expire=86400)  # 1 day
        
        return classes
        
    except Exception as e:
        logger.error(f"Error getting classes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve classes"
        )

@router.get("/races", response_model=List[RaceInfo])
async def get_races():
    """
    Get all available races in the game.
    """
    try:
        # Check cache first
        cache_key = "builds:races"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return cached_data
        
        # Query vector store
        results = query_vector_store("list all races", limit=10, filters={"type": "race"})
        
        races = []
        for doc in results:
            metadata = doc.get("metadata", {})
            race_info = RaceInfo(
                id=metadata.get("id", str(uuid.uuid4())),
                name=metadata.get("name", "Unknown"),
                description=metadata.get("description", ""),
                racial_traits=metadata.get("racial_traits", [])
            )
            races.append(race_info)
        
        # Cache the results
        await set_cache(cache_key, [r.dict() for r in races], expire=86400)  # 1 day
        
        return races
        
    except Exception as e:
        logger.error(f"Error getting races: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve races"
        )

@router.get("", response_model=List[CharacterBuild])
async def get_builds(
    query: Optional[str] = None,
    class_type: Optional[str] = None,
    race: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get a list of character builds with optional filtering.
    """
    try:
        # Build cache key based on query parameters
        cache_params = f"q={query or ''}&class={class_type or ''}&race={race or ''}&tag={tag or ''}&limit={limit}&offset={offset}"
        cache_key = f"builds:list:{cache_params}"
        
        # Check cache first
        cached_data = await get_cache_value(cache_key)
        if cached_data:
            return cached_data
        
        # Start with a base query
        search_query = "character build"
        if query:
            search_query = query
        
        # Add filters based on parameters
        filters = {"type": "build"}
        
        if class_type or race or tag:
            filter_parts = []
            if class_type:
                filter_parts.append(f"class:{class_type}")
            if race:
                filter_parts.append(f"race:{race}")
            if tag:
                filter_parts.append(f"tag:{tag}")
                
            search_query += " " + " ".join(filter_parts)
        
        # Query vector store
        results = query_vector_store(search_query, limit=limit+offset, filters=filters)
        
        # Convert to response models
        builds = []
        for doc in results[offset:]:
            metadata = doc.get("metadata", {})
            try:
                build = CharacterBuild(
                    id=metadata.get("id", str(uuid.uuid4())),
                    name=metadata.get("name", "Unnamed Build"),
                    description=metadata.get("description", ""),
                    race=metadata.get("race", "Unknown"),
                    classes=metadata.get("classes", {"primary": "Unknown", "secondary": "Unknown", "classType": "Unknown"}),
                    level=metadata.get("level", 1),
                    skills=metadata.get("skills", []),
                    equipment=metadata.get("equipment", []),
                    created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat())),
                    user_id=metadata.get("user_id"),
                    is_public=metadata.get("is_public", True),
                    tags=metadata.get("tags", [])
                )
                builds.append(build)
            except Exception as e:
                logger.error(f"Error parsing build: {e}")
                continue
        
        # Cache the results
        await set_cache(cache_key, [b.dict() for b in builds], expire=3600)  # 1 hour
        
        return builds
        
    except Exception as e:
        logger.error(f"Error getting builds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve builds"
        )

@router.get("/{build_id}", response_model=CharacterBuild)
async def get_build(build_id: str):
    """
    Get a specific character build by ID.
    """
    try:
        # Check cache first
        cache_key = f"builds:detail:{build_id}"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return cached_data
        
        # Query vector store
        results = query_vector_store(f"build id:{build_id}", limit=1, filters={"type": "build"})
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Build not found"
            )
        
        metadata = results[0].get("metadata", {})
        
        try:
            build = CharacterBuild(
                id=metadata.get("id", build_id),
                name=metadata.get("name", "Unnamed Build"),
                description=metadata.get("description", ""),
                race=metadata.get("race", "Unknown"),
                classes=metadata.get("classes", {"primary": "Unknown", "secondary": "Unknown", "classType": "Unknown"}),
                level=metadata.get("level", 1),
                skills=metadata.get("skills", []),
                equipment=metadata.get("equipment", []),
                created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat())),
                user_id=metadata.get("user_id"),
                is_public=metadata.get("is_public", True),
                tags=metadata.get("tags", [])
            )
            
            # Cache the result
            await set_cache(cache_key, build.dict(), expire=3600)  # 1 hour
            
            return build
            
        except Exception as e:
            logger.error(f"Error parsing build: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error parsing build data"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting build: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve build"
        )

@router.post("", response_model=CharacterBuild, status_code=status.HTTP_201_CREATED)
async def create_build(build: BuildCreate = Body(...)):
    """
    Create a new character build.
    """
    try:
        # Generate a new build ID
        build_id = str(uuid.uuid4())
        
        # Create new build
        now = datetime.now()
        new_build = CharacterBuild(
            id=build_id,
            name=build.name,
            description=build.description or "",
            race=build.race,
            classes=build.classes,
            level=build.level,
            skills=build.skills,
            equipment=build.equipment,
            created_at=now,
            updated_at=now,
            user_id=None,  # Would come from authentication
            is_public=build.is_public,
            tags=build.tags
        )
        
        # TODO: Save to database or vector store
        # For now, we'll just cache it
        cache_key = f"builds:detail:{build_id}"
        await set_cache(cache_key, new_build.dict(), expire=86400 * 30)  # 30 days
        
        return new_build
        
    except Exception as e:
        logger.error(f"Error creating build: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create build"
        )

@router.put("/{build_id}", response_model=CharacterBuild)
async def update_build(build_id: str, build_update: BuildUpdate = Body(...)):
    """
    Update an existing character build.
    """
    try:
        # Get existing build
        cache_key = f"builds:detail:{build_id}"
        existing_build = await get_cache_value(cache_key)
        
        if not existing_build:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Build not found"
            )
        
        # Update fields that are provided
        update_data = build_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            existing_build[key] = value
        
        # Update timestamp
        existing_build["updated_at"] = datetime.now().isoformat()
        
        # Save updated build
        await set_cache(cache_key, existing_build, expire=86400 * 30)  # 30 days
        
        # Convert to response model
        return CharacterBuild(**existing_build)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating build: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update build"
        )

@router.delete("/{build_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def delete_build(build_id: str):
    """
    Delete a character build.
    """
    try:
        # Check if build exists
        cache_key = f"builds:detail:{build_id}"
        existing_build = await get_cache_value(cache_key)
        
        if not existing_build:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Build not found"
            )
        
        # Delete from cache
        from services.cache_service import delete_cache
        await delete_cache(cache_key)
        
        # No content in response for successful deletion
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting build: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete build"
        )

@router.get("/recommendations/{archetype}", response_model=List[CharacterBuild])
async def get_build_recommendations(
    archetype: str,
    role: Optional[str] = Query(None, description="Desired role (tank, dps, healer, support)"),
    content_type: Optional[str] = Query(None, description="Content type (pvp, pve, crafting)")
):
    """
    Get recommended builds for a specific archetype and optional role/content type.
    """
    try:
        # Build query based on parameters
        query = f"recommended builds for {archetype}"
        if role:
            query += f" {role} role"
        if content_type:
            query += f" for {content_type}"
        
        # Query vector store
        results = query_vector_store(query, limit=5, filters={"type": "build"})
        
        # Convert to response models
        builds = []
        for doc in results:
            metadata = doc.get("metadata", {})
            try:
                build = CharacterBuild(
                    id=metadata.get("id", str(uuid.uuid4())),
                    name=metadata.get("name", "Recommended Build"),
                    description=metadata.get("description", ""),
                    race=metadata.get("race", "Unknown"),
                    classes=metadata.get("classes", {"primary": "Unknown", "secondary": "Unknown", "classType": "Unknown"}),
                    level=metadata.get("level", 50),
                    skills=metadata.get("skills", []),
                    equipment=metadata.get("equipment", []),
                    created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat())),
                    user_id=metadata.get("user_id"),
                    is_public=metadata.get("is_public", True),
                    tags=metadata.get("tags", [])
                )
                builds.append(build)
            except Exception as e:
                logger.error(f"Error parsing build recommendation: {e}")
                continue
        
        return builds
        
    except Exception as e:
        logger.error(f"Error getting build recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve build recommendations"
        )
