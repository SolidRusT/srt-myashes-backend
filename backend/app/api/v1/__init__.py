from fastapi import APIRouter

from app.api.v1.builds import router as builds_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.analytics import router as analytics_router

api_router = APIRouter()

# Include API routers
api_router.include_router(builds_router, prefix="/builds", tags=["builds"])
api_router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
