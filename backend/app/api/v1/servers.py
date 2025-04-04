from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from config import settings
from services.cache_service import set_cache, get_cache_value
from loguru import logger

router = APIRouter()

# Models
class Server(BaseModel):
    name: str = Field(..., description="Server name")
    status: str = Field(..., description="Server status (Online, Offline, Maintenance)")
    population: Optional[str] = Field(None, description="Population level")
    region: Optional[str] = Field(None, description="Server region")

class ServerListResponse(BaseModel):
    servers: List[Server] = Field(..., description="List of game servers")

class ServerStatus(BaseModel):
    server: str = Field(..., description="Server name")
    status: str = Field(..., description="Server status")
    population: Optional[str] = Field(None, description="Population level")
    queue: Optional[int] = Field(None, description="Queue length if any")
    last_updated: str = Field(..., description="Last update timestamp")

# Routes
@router.get("", response_model=ServerListResponse)
async def get_servers():
    """
    Get a list of all game servers.
    """
    try:
        # Check cache first
        cache_key = "servers:list"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return ServerListResponse(**cached_data)
        
        # Use configured server list
        server_list = []
        for server_name in settings.GAME_SERVERS:
            server_list.append(Server(
                name=server_name,
                status="Online",  # Default status
                population=None,
                region=None
            ))
        
        # Create response
        response = ServerListResponse(servers=server_list)
        
        # Cache the result
        await set_cache(cache_key, response.dict(), expire=3600)  # 1 hour
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting servers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve servers"
        )

@router.get("/status/{server_name}", response_model=ServerStatus)
async def get_server_status(server_name: str):
    """
    Get the current status of a specific server.
    """
    try:
        # Check if server exists
        if server_name not in settings.GAME_SERVERS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        # Check cache first
        cache_key = f"servers:status:{server_name}"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return ServerStatus(**cached_data)
        
        # Create default status
        from datetime import datetime
        
        server_status = ServerStatus(
            server=server_name,
            status="Online",  # Default status
            population=None,
            queue=None,
            last_updated=datetime.now().isoformat()
        )
        
        # Cache the result
        await set_cache(cache_key, server_status.dict(), expire=300)  # 5 minutes
        
        return server_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting server status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve server status"
        )

@router.get("/economy/{server_name}", response_model=Dict[str, Any])
async def get_server_economy(server_name: str):
    """
    Get economic data for a specific server.
    """
    try:
        # Check if server exists
        if server_name not in settings.GAME_SERVERS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        # Check cache first
        cache_key = f"servers:economy:{server_name}"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return cached_data
        
        # Create placeholder economy data
        from datetime import datetime
        
        economy_data = {
            "server": server_name,
            "timestamp": datetime.now().isoformat(),
            "currency_value": 100,  # Baseline value
            "hot_items": [
                {"name": "Iron Ore", "avg_price": 10, "volume": 1000},
                {"name": "Health Potion", "avg_price": 25, "volume": 500},
                {"name": "Steel Ingot", "avg_price": 50, "volume": 300}
            ],
            "market_categories": {
                "resources": {"activity": "high", "price_trend": "stable"},
                "weapons": {"activity": "medium", "price_trend": "rising"},
                "armor": {"activity": "medium", "price_trend": "stable"},
                "consumables": {"activity": "high", "price_trend": "falling"}
            }
        }
        
        # Cache the result
        await set_cache(cache_key, economy_data, expire=1800)  # 30 minutes
        
        return economy_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting server economy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve server economy data"
        )

@router.get("/population", response_model=Dict[str, Any])
async def get_population_stats():
    """
    Get population statistics across all servers.
    """
    try:
        # Check cache first
        cache_key = "servers:population"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return cached_data
        
        # Create placeholder population data
        from datetime import datetime
        
        population_data = {
            "timestamp": datetime.now().isoformat(),
            "total_online": 10000,
            "servers": {},
            "faction_distribution": {
                "faction1": 35,
                "faction2": 40,
                "faction3": 25
            },
            "class_distribution": {
                "tank": 15,
                "dps": 50,
                "healer": 20,
                "support": 15
            }
        }
        
        # Add server-specific data
        for server_name in settings.GAME_SERVERS:
            import random
            
            population_data["servers"][server_name] = {
                "population": random.randint(1000, 5000),
                "queue": 0,
                "status": "Online"
            }
        
        # Cache the result
        await set_cache(cache_key, population_data, expire=1800)  # 30 minutes
        
        return population_data
        
    except Exception as e:
        logger.error(f"Error getting population stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve population statistics"
        )
