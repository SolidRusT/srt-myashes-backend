from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from services.vector_store import query_vector_store
from services.cache_service import set_cache, get_cache_value
from loguru import logger

router = APIRouter()

# Models
class Coordinate(BaseModel):
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    z: Optional[float] = Field(None, description="Z coordinate (elevation)")

class LocationPoint(BaseModel):
    id: str = Field(..., description="Point ID")
    name: str = Field(..., description="Point name")
    type: str = Field(..., description="Point type (Resource, NPC, POI, etc.)")
    coordinates: Coordinate = Field(..., description="Location coordinates")
    zone: str = Field(..., description="Zone/region name")
    description: Optional[str] = Field(None, description="Location description")
    resources: Optional[List[str]] = Field(None, description="Available resources at this location")
    npcs: Optional[List[str]] = Field(None, description="NPCs at this location")
    quests: Optional[List[str]] = Field(None, description="Quests at this location")
    difficulty: Optional[str] = Field(None, description="Area difficulty")
    notes: Optional[str] = Field(None, description="Additional notes")

class Zone(BaseModel):
    id: str = Field(..., description="Zone ID")
    name: str = Field(..., description="Zone name")
    type: str = Field(..., description="Zone type (Forest, Desert, Mountain, etc.)")
    region: str = Field(..., description="Region the zone belongs to")
    level_range: Optional[str] = Field(None, description="Level range for the zone")
    description: Optional[str] = Field(None, description="Zone description")
    points_of_interest: Optional[List[str]] = Field(None, description="Notable locations in the zone")
    resources: Optional[List[str]] = Field(None, description="Resources found in the zone")
    nodes: Optional[List[Dict[str, Any]]] = Field(None, description="Nodes in the zone")

class Region(BaseModel):
    id: str = Field(..., description="Region ID")
    name: str = Field(..., description="Region name")
    description: Optional[str] = Field(None, description="Region description")
    zones: List[str] = Field(..., description="Zones in the region")
    climate: Optional[str] = Field(None, description="Region climate")
    faction: Optional[str] = Field(None, description="Controlling faction if any")

class ResourceNode(BaseModel):
    id: str = Field(..., description="Node ID")
    resource: str = Field(..., description="Resource name")
    type: str = Field(..., description="Resource type")
    locations: List[Dict[str, Any]] = Field(..., description="Where to find this resource")
    level: Optional[str] = Field(None, description="Required gathering level")
    respawn_time: Optional[str] = Field(None, description="Approximate respawn time")
    notes: Optional[str] = Field(None, description="Additional notes")

# Routes
@router.get("/zones", response_model=List[Zone])
async def get_zones():
    """
    Get a list of all zones in the game.
    """
    try:
        # Check cache first
        cache_key = "locations:zones"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return [Zone(**zone) for zone in cached_data]
        
        # Query vector store
        results = query_vector_store("list all zones", limit=50, filters={"type": "location"})
        
        # Group by zone name
        zones_dict = {}
        for doc in results:
            metadata = doc.get("metadata", {})
            
            # Skip if not a zone
            if metadata.get("type", "").lower() != "zone":
                continue
                
            zone_name = metadata.get("name", "Unknown Zone")
            if zone_name not in zones_dict:
                zones_dict[zone_name] = {
                    "id": metadata.get("id", str(uuid.uuid4())),
                    "name": zone_name,
                    "type": metadata.get("type", "Unknown"),
                    "region": metadata.get("zone", "Unknown Region"),
                    "level_range": metadata.get("level_range", None),
                    "description": metadata.get("description", ""),
                    "points_of_interest": [],
                    "resources": [],
                    "nodes": []
                }
                
            # Add points of interest if any
            if "points_of_interest" in metadata:
                for poi in metadata["points_of_interest"]:
                    if poi not in zones_dict[zone_name]["points_of_interest"]:
                        zones_dict[zone_name]["points_of_interest"].append(poi)
                        
            # Add resources if any
            if "resources" in metadata:
                for resource in metadata["resources"]:
                    if resource not in zones_dict[zone_name]["resources"]:
                        zones_dict[zone_name]["resources"].append(resource)
        
        # Convert to list of Zone objects
        zones = [Zone(**zone_data) for zone_data in zones_dict.values()]
        
        # Cache the result
        await set_cache(cache_key, [zone.dict() for zone in zones], expire=86400)  # 1 day
        
        return zones
        
    except Exception as e:
        logger.error(f"Error getting zones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve zones"
        )

@router.get("/zones/{zone_id}", response_model=Zone)
async def get_zone(zone_id: str):
    """
    Get detailed information about a specific zone.
    """
    try:
        # Check cache first
        cache_key = f"locations:zone:{zone_id}"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return Zone(**cached_data)
        
        # Query vector store
        results = query_vector_store(f"zone id:{zone_id}", limit=1, filters={"type": "location"})
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Zone not found"
            )
        
        doc = results[0]
        metadata = doc.get("metadata", {})
        
        # Create Zone object
        zone = Zone(
            id=metadata.get("id", zone_id),
            name=metadata.get("name", "Unknown Zone"),
            type=metadata.get("type", "Unknown"),
            region=metadata.get("zone", "Unknown Region"),
            level_range=metadata.get("level_range", None),
            description=metadata.get("description", ""),
            points_of_interest=metadata.get("points_of_interest", []),
            resources=metadata.get("resources", []),
            nodes=metadata.get("nodes", [])
        )
        
        # Cache the result
        await set_cache(cache_key, zone.dict(), expire=86400)  # 1 day
        
        return zone
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting zone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve zone"
        )

@router.get("/zone-by-name/{zone_name}", response_model=Zone)
async def get_zone_by_name(zone_name: str):
    """
    Get detailed information about a specific zone by name.
    """
    try:
        # Build a safe cache key (remove spaces and special chars)
        safe_name = "".join(c for c in zone_name.lower() if c.isalnum())
        cache_key = f"locations:zone_name:{safe_name}"
        
        # Check cache first
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return Zone(**cached_data)
        
        # Query vector store
        results = query_vector_store(f"zone {zone_name}", limit=5, filters={"type": "location"})
        
        # Find the closest match
        zone_doc = None
        for doc in results:
            metadata = doc.get("metadata", {})
            if metadata.get("name", "").lower() == zone_name.lower():
                zone_doc = doc
                break
                
        if not zone_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Zone not found"
            )
        
        metadata = zone_doc.get("metadata", {})
        
        # Create Zone object
        zone = Zone(
            id=metadata.get("id", str(uuid.uuid4())),
            name=metadata.get("name", "Unknown Zone"),
            type=metadata.get("type", "Unknown"),
            region=metadata.get("zone", "Unknown Region"),
            level_range=metadata.get("level_range", None),
            description=metadata.get("description", ""),
            points_of_interest=metadata.get("points_of_interest", []),
            resources=metadata.get("resources", []),
            nodes=metadata.get("nodes", [])
        )
        
        # Cache the result
        await set_cache(cache_key, zone.dict(), expire=86400)  # 1 day
        
        return zone
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting zone by name: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve zone"
        )

@router.get("/resources", response_model=List[ResourceNode])
async def get_resources(
    resource_type: Optional[str] = None,
    zone: Optional[str] = None,
    level: Optional[str] = None
):
    """
    Get a list of resource nodes with optional filtering.
    """
    try:
        # Build cache key
        cache_params = f"type={resource_type or ''}&zone={zone or ''}&level={level or ''}"
        cache_key = f"locations:resources:{cache_params}"
        
        # Check cache first
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return [ResourceNode(**node) for node in cached_data]
        
        # Build search query
        search_text = "resource nodes"
        
        if resource_type:
            search_text += f" type:{resource_type}"
            
        if zone:
            search_text += f" in {zone}"
            
        if level:
            search_text += f" level:{level}"
        
        # Query vector store
        results = query_vector_store(search_text, limit=30, filters={"type": "location"})
        
        # Group by resource name
        resources_dict = {}
        for doc in results:
            metadata = doc.get("metadata", {})
            
            # Skip if not a resource node
            location_type = metadata.get("type", "").lower()
            if "resource" not in location_type and "node" not in location_type:
                continue
                
            resource_name = metadata.get("resource", metadata.get("name", "Unknown Resource"))
            
            # Apply filters
            if resource_type and resource_type.lower() not in location_type.lower():
                continue
                
            if zone and zone.lower() != metadata.get("zone", "").lower():
                continue
                
            if level and level != metadata.get("level", ""):
                continue
            
            if resource_name not in resources_dict:
                resources_dict[resource_name] = {
                    "id": metadata.get("id", str(uuid.uuid4())),
                    "resource": resource_name,
                    "type": location_type,
                    "locations": [],
                    "level": metadata.get("level", None),
                    "respawn_time": metadata.get("respawn_time", None),
                    "notes": metadata.get("notes", None)
                }
            
            # Add location
            location = {
                "zone": metadata.get("zone", "Unknown"),
                "description": metadata.get("description", "")
            }
            
            # Add coordinates if available
            if "coordinates" in metadata:
                coords = metadata["coordinates"]
                location["coordinates"] = {
                    "x": coords.get("x", 0),
                    "y": coords.get("y", 0),
                    "z": coords.get("z", 0) if "z" in coords else None
                }
                
            resources_dict[resource_name]["locations"].append(location)
        
        # Convert to list of ResourceNode objects
        resources = [ResourceNode(**res_data) for res_data in resources_dict.values()]
        
        # Cache the result
        await set_cache(cache_key, [res.dict() for res in resources], expire=3600)  # 1 hour
        
        return resources
        
    except Exception as e:
        logger.error(f"Error getting resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resources"
        )

@router.get("/resource/{resource_name}", response_model=ResourceNode)
async def get_resource(resource_name: str):
    """
    Get information about where to find a specific resource.
    """
    try:
        # Build a safe cache key (remove spaces and special chars)
        safe_name = "".join(c for c in resource_name.lower() if c.isalnum())
        cache_key = f"locations:resource:{safe_name}"
        
        # Check cache first
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return ResourceNode(**cached_data)
        
        # Query vector store
        results = query_vector_store(f"where to find {resource_name}", limit=20, filters={"type": "location"})
        
        # Process results
        locations = []
        level = None
        respawn_time = None
        notes = None
        
        for doc in results:
            metadata = doc.get("metadata", {})
            
            # Skip if not relevant to this resource
            doc_text = doc.get("text", "").lower()
            metadata_resource = metadata.get("resource", "").lower()
            
            if resource_name.lower() not in doc_text and resource_name.lower() not in metadata_resource:
                continue
            
            # Add location
            location = {
                "zone": metadata.get("zone", "Unknown"),
                "description": metadata.get("description", "")
            }
            
            # Add coordinates if available
            if "coordinates" in metadata:
                coords = metadata["coordinates"]
                location["coordinates"] = {
                    "x": coords.get("x", 0),
                    "y": coords.get("y", 0),
                    "z": coords.get("z", 0) if "z" in coords else None
                }
                
            locations.append(location)
            
            # Update metadata if available
            if not level and "level" in metadata:
                level = metadata["level"]
                
            if not respawn_time and "respawn_time" in metadata:
                respawn_time = metadata["respawn_time"]
                
            if not notes and "notes" in metadata:
                notes = metadata["notes"]
        
        if not locations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource {resource_name} not found"
            )
        
        # Create ResourceNode object
        resource = ResourceNode(
            id=str(uuid.uuid4()),
            resource=resource_name,
            type="Unknown",  # We don't know the exact type
            locations=locations,
            level=level,
            respawn_time=respawn_time,
            notes=notes
        )
        
        # Cache the result
        await set_cache(cache_key, resource.dict(), expire=3600)  # 1 hour
        
        return resource
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resource information"
        )

@router.get("/points-of-interest", response_model=List[LocationPoint])
async def get_points_of_interest(
    poi_type: Optional[str] = None,
    zone: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get points of interest with optional filtering.
    """
    try:
        # Build cache key
        cache_params = f"type={poi_type or ''}&zone={zone or ''}&limit={limit}"
        cache_key = f"locations:pois:{cache_params}"
        
        # Check cache first
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return [LocationPoint(**poi) for poi in cached_data]
        
        # Build search query
        search_text = "points of interest"
        
        if poi_type:
            search_text += f" type:{poi_type}"
            
        if zone:
            search_text += f" in {zone}"
        
        # Query vector store
        results = query_vector_store(search_text, limit=limit, filters={"type": "location"})
        
        # Convert to LocationPoint objects
        pois = []
        for doc in results:
            metadata = doc.get("metadata", {})
            
            # Skip if not a POI
            if metadata.get("type", "").lower() == "zone":
                continue
                
            # Apply filters
            if poi_type and poi_type.lower() not in metadata.get("type", "").lower():
                continue
                
            if zone and zone.lower() != metadata.get("zone", "").lower():
                continue
            
            # Create coordinate object
            coordinate = Coordinate(
                x=0,
                y=0
            )
            
            if "coordinates" in metadata:
                coords = metadata["coordinates"]
                coordinate = Coordinate(
                    x=float(coords.get("x", 0)),
                    y=float(coords.get("y", 0)),
                    z=float(coords.get("z", 0)) if "z" in coords else None
                )
            
            # Create LocationPoint object
            poi = LocationPoint(
                id=metadata.get("id", str(uuid.uuid4())),
                name=metadata.get("name", "Unknown POI"),
                type=metadata.get("type", "POI"),
                coordinates=coordinate,
                zone=metadata.get("zone", "Unknown"),
                description=metadata.get("description", ""),
                resources=metadata.get("resources", None),
                npcs=metadata.get("npcs", None),
                quests=metadata.get("quests", None),
                difficulty=metadata.get("difficulty", None),
                notes=metadata.get("notes", None)
            )
            
            pois.append(poi)
        
        # Cache the result
        await set_cache(cache_key, [poi.dict() for poi in pois], expire=3600)  # 1 hour
        
        return pois
        
    except Exception as e:
        logger.error(f"Error getting points of interest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve points of interest"
        )
