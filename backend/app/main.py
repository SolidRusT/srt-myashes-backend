from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import time
from loguru import logger

from config import settings
from services.vector_store import get_vector_store
from services.llm_service import LLMService
from services.cache_service import get_cache
from api.v1 import chat_router, build_router, server_router, items_router, locations_router, crafting_router
from api.discord_bot import start_discord_bot

app = FastAPI(title="Ashes of Creation Assistant API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

# Rate limiting middleware (basic implementation)
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    # Get client IP or user identifier
    client_id = request.client.host
    
    # Get cache
    cache = get_cache()
    
    # Check rate limit (10 requests per minute)
    minute_key = f"rate_limit:{client_id}:{int(time.time() / 60)}"
    current = await cache.incr(minute_key)
    if current == 1:
        await cache.expire(minute_key, 60)
    
    if current > settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Try again in a minute."}
        )
    
    return await call_next(request)

# API health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(build_router, prefix="/api/v1/builds", tags=["builds"])
app.include_router(server_router, prefix="/api/v1/servers", tags=["servers"])
app.include_router(items_router, prefix="/api/v1/items", tags=["items"])
app.include_router(locations_router, prefix="/api/v1/locations", tags=["locations"])
app.include_router(crafting_router, prefix="/api/v1/crafting", tags=["crafting"])

@app.on_event("startup")
async def startup_event():
    # Initialize services
    logger.info("Initializing services...")
    
    # Connect to vector store
    try:
        vector_store = get_vector_store()
        logger.info(f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        raise
    
    # Connect to cache
    try:
        cache = get_cache()
        logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    
    # Initialize LLM service
    try:
        llm_service = LLMService()
        logger.info(f"Initialized LLM service with endpoint: {settings.OPENAI_API_BASE}")
    except Exception as e:
        logger.error(f"Failed to initialize LLM service: {e}")
        raise
    
    # Start Discord bot in a separate thread if enabled
    if settings.DISCORD_BOT_ENABLED:
        import asyncio
        import threading
        
        def run_discord_bot():
            asyncio.run(start_discord_bot())
            
        threading.Thread(target=run_discord_bot, daemon=True).start()
        logger.info("Started Discord bot")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
