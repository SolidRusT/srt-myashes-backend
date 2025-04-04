from .chat import router as chat_router
from .builds import router as build_router
from .servers import router as server_router
from .items import router as items_router
from .locations import router as locations_router
from .crafting import router as crafting_router

__all__ = [
    "chat_router",
    "build_router", 
    "server_router",
    "items_router",
    "locations_router",
    "crafting_router"
]
