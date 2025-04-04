import os
from typing import List, Dict, Any, Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # Vector database settings
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    MILVUS_USER: str = os.getenv("MILVUS_USER", "")
    MILVUS_PASSWORD: str = os.getenv("MILVUS_PASSWORD", "")
    MILVUS_COLLECTION: str = os.getenv("MILVUS_COLLECTION", "ashes_knowledge")
    
    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # Embedding model settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
    EMBEDDING_DIMENSION: int = 1024  # Dimension for BGE Large model
    
    # Data source settings
    WIKI_URL: str = "https://ashesofcreation.wiki"
    CODEX_URL: str = "https://ashescodex.com"
    OFFICIAL_URL: str = "https://ashesofcreation.com"
    
    # Data directories
    DATA_DIR: str = "/data"
    RAW_DATA_DIR: str = "/data/raw"
    PROCESSED_DATA_DIR: str = "/data/processed"
    IMAGES_DIR: str = "/data/images"
    
    # Scraping settings
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    REQUEST_TIMEOUT: int = 30  # seconds
    REQUEST_DELAY: float = 1.0  # seconds between requests
    MAX_RETRIES: int = 3
    
    # Game servers
    GAME_SERVERS: List[str] = os.getenv("GAME_SERVERS", "Alpha-1,Alpha-2").split(",")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Schedule
    SCRAPE_INTERVAL: int = int(os.getenv("SCRAPE_INTERVAL", "86400"))  # 24 hours in seconds
    
    class Config:
        env_file = ".env"

# Create global settings instance
settings = Settings()
