from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.vector_store import query_vector_store
from app.services.cache_service import set_cache, get_cache_value
from loguru import logger

router = APIRouter()

# Models
class ItemSource(BaseModel):
    type: str = Field(..., description="Source type (drop, craft, vendor, etc.)")
    details: str = Field(..., description="Source details")

class ItemLocation(BaseModel):
    zone: str = Field(..., description="Zone/region name")
    coordinates: Optional[str] = Field(None, description="Coordinates if applicable")
    notes: Optional[str] = Field(None, description="Additional location notes")

class ItemStat(BaseModel):
    name: str = Field(..., description="Stat name")
    value: Any = Field(..., description="Stat value")
    
class CraftingMaterial(BaseModel):
    item_id: str = Field(..., description="Material item ID")
    name: str = Field(..., description="Material name")
    amount: int = Field(..., description="Amount required")

class CraftingRecipe(BaseModel):
    recipe_id: str = Field(..., description="Recipe ID")
    materials: List[CraftingMaterial] = Field(..., description="Required materials")
    skill: str = Field(..., description="Crafting skill required")
    skill_level: str = Field(..., description="Skill level required")

class Item(BaseModel):
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    quality: str = Field(..., description="Item quality (Common, Uncommon, etc.)")
    type: str = Field(..., description="Item type (Weapon, Armor, Resource, etc.)")
    subtype: Optional[str] = Field(None, description="Item subtype (Sword, Chest, Herb, etc.)")
    description: Optional[str] = Field(None, description="Item description")
    stats: Optional[List[ItemStat]] = Field(None, description="Item stats")
    level: Optional[int] = Field(None, description="Item level requirement")
    sources: Optional[List[ItemSource]] = Field(None, description="Where to get the item")
    locations: Optional[List[ItemLocation]] = Field(None, description="Where to find the item")
    recipe: Optional[CraftingRecipe] = Field(None, description="Crafting recipe if craftable")
    used_in: Optional[List[str]] = Field(None, description="Recipes this item is used in")
    icon_url: Optional[str] = Field(None, description="URL to item icon")
    
class ItemSearchResult(BaseModel):
    items: List[Item] = Field(..., description="List of items matching search criteria")
    total: int = Field(..., description="Total number of matching items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")

# Routes
@router.get("", response_model=ItemSearchResult)
async def search_items(
    query: Optional[str] = None,
    type: Optional[str] = None,
    quality: Optional[str] = None,
    level_min: Optional[int] = None,
    level_max: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Search for items with various filters.
    """
    try:
        # Build cache key from parameters
        cache_params = f"q={query or ''}&type={type or ''}&quality={quality or ''}&lvl_min={level_min or ''}&lvl_max={level_max or ''}&page={page}&size={page_size}"
        cache_key = f"items:search:{cache_params}"
        
        # Check cache first
        cached_data = await get_cache_value(cache_key)
        if cached_data:
            return ItemSearchResult(**cached_data)
        
        # Build search query
        if query:
            search_text = query
        else:
            search_text = "items"
            
        # Add type filter if provided
        if type:
            search_text += f" type:{type}"
            
        # Add quality filter if provided
        if quality:
            search_text += f" quality:{quality}"
        
        # Add level filters if provided
        if level_min is not None or level_max is not None:
            level_clause = " level:"
            if level_min is not None:
                level_clause += f"{level_min}"
            if level_max is not None:
                level_clause += f"-{level_max}"
            search_text += level_clause
        
        # Query vector store
        filters = {"type": "item"}
        results = query_vector_store(search_text, limit=page_size * page, filters=filters)
        
        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_results = results[start_idx:end_idx]
        
        # Convert to Item objects
        items = []
        for doc in paged_results:
            metadata = doc.get("metadata", {})
            
            # Extract stats
            stats = []
            if "stats" in metadata and metadata["stats"]:
                for stat_str in metadata["stats"]:
                    parts = stat_str.split(":", 1)
                    if len(parts) == 2:
                        stats.append(ItemStat(name=parts[0].strip(), value=parts[1].strip()))
            
            # Extract sources
            sources = []
            if "sources" in metadata and metadata["sources"]:
                for source_str in metadata["sources"]:
                    sources.append(ItemSource(type="Unknown", details=source_str))
            
            # Extract locations
            locations = []
            if "locations" in metadata and metadata["locations"]:
                for loc_str in metadata["locations"]:
                    locations.append(ItemLocation(zone=loc_str))
            
            # Extract recipe
            recipe = None
            if "recipe" in metadata and metadata["recipe"]:
                recipe_data = metadata["recipe"]
                materials = []
                
                if "materials" in recipe_data:
                    for mat in recipe_data["materials"]:
                        materials.append(CraftingMaterial(
                            item_id="unknown",  # We don't have IDs in the metadata
                            name=mat.get("name", "Unknown"),
                            amount=int(mat.get("amount", "1").split()[0])
                        ))
                
                recipe = CraftingRecipe(
                    recipe_id="unknown",  # We don't have recipe IDs in the metadata
                    materials=materials,
                    skill=recipe_data.get("skill", "Unknown"),
                    skill_level=recipe_data.get("level", "Unknown")
                )
            
            # Create item object
            item = Item(
                id=metadata.get("id", "unknown"),
                name=metadata.get("name", "Unknown Item"),
                quality=metadata.get("quality", "Common"),
                type=metadata.get("type", "Miscellaneous"),
                subtype=metadata.get("subtype"),
                description=metadata.get("description", ""),
                stats=stats,
                level=metadata.get("level"),
                sources=sources,
                locations=locations,
                recipe=recipe,
                used_in=metadata.get("used_in"),
                icon_url=None  # We don't have icon URLs in the metadata
            )
            
            items.append(item)
        
        # Create result object
        result = ItemSearchResult(
            items=items,
            total=len(results),
            page=page,
            page_size=page_size
        )
        
        # Cache the result
        await set_cache(cache_key, result.dict(), expire=3600)  # 1 hour
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search items"
        )

@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: str):
    """
    Get detailed information about a specific item.
    """
    try:
        # Check cache first
        cache_key = f"items:detail:{item_id}"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return Item(**cached_data)
        
        # Query vector store
        results = query_vector_store(f"item id:{item_id}", limit=1, filters={"type": "item"})
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        doc = results[0]
        metadata = doc.get("metadata", {})
        
        # Extract stats
        stats = []
        if "stats" in metadata and metadata["stats"]:
            for stat_str in metadata["stats"]:
                parts = stat_str.split(":", 1)
                if len(parts) == 2:
                    stats.append(ItemStat(name=parts[0].strip(), value=parts[1].strip()))
        
        # Extract sources
        sources = []
        if "sources" in metadata and metadata["sources"]:
            for source_str in metadata["sources"]:
                sources.append(ItemSource(type="Unknown", details=source_str))
        
        # Extract locations
        locations = []
        if "locations" in metadata and metadata["locations"]:
            for loc_str in metadata["locations"]:
                locations.append(ItemLocation(zone=loc_str))
        
        # Extract recipe
        recipe = None
        if "recipe" in metadata and metadata["recipe"]:
            recipe_data = metadata["recipe"]
            materials = []
            
            if "materials" in recipe_data:
                for mat in recipe_data["materials"]:
                    materials.append(CraftingMaterial(
                        item_id="unknown",  # We don't have IDs in the metadata
                        name=mat.get("name", "Unknown"),
                        amount=int(mat.get("amount", "1").split()[0])
                    ))
            
            recipe = CraftingRecipe(
                recipe_id="unknown",  # We don't have recipe IDs in the metadata
                materials=materials,
                skill=recipe_data.get("skill", "Unknown"),
                skill_level=recipe_data.get("level", "Unknown")
            )
        
        # Create item object
        item = Item(
            id=metadata.get("id", item_id),
            name=metadata.get("name", "Unknown Item"),
            quality=metadata.get("quality", "Common"),
            type=metadata.get("type", "Miscellaneous"),
            subtype=metadata.get("subtype"),
            description=metadata.get("description", ""),
            stats=stats,
            level=metadata.get("level"),
            sources=sources,
            locations=locations,
            recipe=recipe,
            used_in=metadata.get("used_in"),
            icon_url=None  # We don't have icon URLs in the metadata
        )
        
        # Cache the result
        await set_cache(cache_key, item.dict(), expire=3600)  # 1 hour
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve item"
        )

@router.get("/by-name/{item_name}", response_model=Item)
async def get_item_by_name(item_name: str):
    """
    Get detailed information about a specific item by its name.
    """
    try:
        # Build a safe cache key (remove spaces and special chars)
        safe_name = "".join(c for c in item_name.lower() if c.isalnum())
        cache_key = f"items:name:{safe_name}"
        
        # Check cache first
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return Item(**cached_data)
        
        # Query vector store
        results = query_vector_store(f"item name:\"{item_name}\"", limit=1, filters={"type": "item"})
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        doc = results[0]
        metadata = doc.get("metadata", {})
        
        # Extract stats
        stats = []
        if "stats" in metadata and metadata["stats"]:
            for stat_str in metadata["stats"]:
                parts = stat_str.split(":", 1)
                if len(parts) == 2:
                    stats.append(ItemStat(name=parts[0].strip(), value=parts[1].strip()))
        
        # Extract sources
        sources = []
        if "sources" in metadata and metadata["sources"]:
            for source_str in metadata["sources"]:
                sources.append(ItemSource(type="Unknown", details=source_str))
        
        # Extract locations
        locations = []
        if "locations" in metadata and metadata["locations"]:
            for loc_str in metadata["locations"]:
                locations.append(ItemLocation(zone=loc_str))
        
        # Extract recipe
        recipe = None
        if "recipe" in metadata and metadata["recipe"]:
            recipe_data = metadata["recipe"]
            materials = []
            
            if "materials" in recipe_data:
                for mat in recipe_data["materials"]:
                    materials.append(CraftingMaterial(
                        item_id="unknown",  # We don't have IDs in the metadata
                        name=mat.get("name", "Unknown"),
                        amount=int(mat.get("amount", "1").split()[0])
                    ))
            
            recipe = CraftingRecipe(
                recipe_id="unknown",  # We don't have recipe IDs in the metadata
                materials=materials,
                skill=recipe_data.get("skill", "Unknown"),
                skill_level=recipe_data.get("level", "Unknown")
            )
        
        # Create item object
        item = Item(
            id=metadata.get("id", "unknown"),
            name=metadata.get("name", "Unknown Item"),
            quality=metadata.get("quality", "Common"),
            type=metadata.get("type", "Miscellaneous"),
            subtype=metadata.get("subtype"),
            description=metadata.get("description", ""),
            stats=stats,
            level=metadata.get("level"),
            sources=sources,
            locations=locations,
            recipe=recipe,
            used_in=metadata.get("used_in"),
            icon_url=None  # We don't have icon URLs in the metadata
        )
        
        # Cache the result
        await set_cache(cache_key, item.dict(), expire=3600)  # 1 hour
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting item by name: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve item"
        )

@router.get("/type/{item_type}", response_model=List[Item])
async def get_items_by_type(
    item_type: str,
    subtype: Optional[str] = None,
    quality: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get a list of items of a specific type.
    """
    try:
        # Build cache key
        cache_params = f"type={item_type}&subtype={subtype or ''}&quality={quality or ''}&limit={limit}"
        cache_key = f"items:type:{cache_params}"
        
        # Check cache first
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return [Item(**item) for item in cached_data]
        
        # Build search query
        search_text = f"items type:{item_type}"
        
        if subtype:
            search_text += f" subtype:{subtype}"
        
        if quality:
            search_text += f" quality:{quality}"
        
        # Query vector store
        filters = {"type": "item"}
        results = query_vector_store(search_text, limit=limit, filters=filters)
        
        # Convert to Item objects
        items = []
        for doc in results:
            metadata = doc.get("metadata", {})
            
            # Check if the type matches exactly (vector search might return similar but not exact matches)
            if metadata.get("type", "").lower() != item_type.lower():
                continue
                
            # Check subtype if provided
            if subtype and metadata.get("subtype", "").lower() != subtype.lower():
                continue
                
            # Check quality if provided
            if quality and metadata.get("quality", "").lower() != quality.lower():
                continue
            
            # Extract stats
            stats = []
            if "stats" in metadata and metadata["stats"]:
                for stat_str in metadata["stats"]:
                    parts = stat_str.split(":", 1)
                    if len(parts) == 2:
                        stats.append(ItemStat(name=parts[0].strip(), value=parts[1].strip()))
            
            # Create item object (simplified for list view)
            item = Item(
                id=metadata.get("id", "unknown"),
                name=metadata.get("name", "Unknown Item"),
                quality=metadata.get("quality", "Common"),
                type=metadata.get("type", "Miscellaneous"),
                subtype=metadata.get("subtype"),
                description=metadata.get("description", ""),
                stats=stats,
                level=metadata.get("level"),
                sources=None,  # Omit detailed data for list view
                locations=None,
                recipe=None,
                used_in=None,
                icon_url=None
            )
            
            items.append(item)
        
        # Cache the result
        await set_cache(cache_key, [item.dict() for item in items], expire=3600)  # 1 hour
        
        return items
        
    except Exception as e:
        logger.error(f"Error getting items by type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve items"
        )

@router.get("/location/{zone_name}", response_model=List[Item])
async def get_items_by_location(
    zone_name: str,
    type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get a list of items found in a specific zone.
    """
    try:
        # Build cache key
        cache_params = f"zone={zone_name}&type={type or ''}&limit={limit}"
        cache_key = f"items:location:{cache_params}"
        
        # Check cache first
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return [Item(**item) for item in cached_data]
        
        # Build search query
        search_text = f"items in {zone_name}"
        
        if type:
            search_text += f" type:{type}"
        
        # Query vector store
        filters = {"type": "item"}
        results = query_vector_store(search_text, limit=limit, filters=filters)
        
        # Convert to Item objects
        items = []
        for doc in results:
            metadata = doc.get("metadata", {})
            
            # Check if the location matches
            locations = metadata.get("locations", [])
            location_match = False
            
            for loc in locations:
                if zone_name.lower() in loc.lower():
                    location_match = True
                    break
                    
            if not location_match:
                continue
                
            # Check type if provided
            if type and metadata.get("type", "").lower() != type.lower():
                continue
            
            # Create item object (simplified for list view)
            item = Item(
                id=metadata.get("id", "unknown"),
                name=metadata.get("name", "Unknown Item"),
                quality=metadata.get("quality", "Common"),
                type=metadata.get("type", "Miscellaneous"),
                subtype=metadata.get("subtype"),
                description=metadata.get("description", ""),
                stats=None,  # Omit detailed data for list view
                level=metadata.get("level"),
                sources=None,
                locations=[ItemLocation(zone=loc) for loc in locations],
                recipe=None,
                used_in=None,
                icon_url=None
            )
            
            items.append(item)
        
        # Cache the result
        await set_cache(cache_key, [item.dict() for item in items], expire=3600)  # 1 hour
        
        return items
        
    except Exception as e:
        logger.error(f"Error getting items by location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve items"
        )
