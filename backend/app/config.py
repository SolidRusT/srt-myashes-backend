from pydantic_settings import BaseSettings
import os
from typing import Optional, List


class Settings(BaseSettings):
    # API settings
    API_VERSION: str = "1.0.0"
    API_TITLE: str = "Ashes of Creation Assistant API"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    
    # Security
    API_KEY_HEADER: str = "X-API-Key"
    API_KEYS: List[str] = []
    
    # Milvus settings
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    MILVUS_USER: str = os.getenv("MILVUS_USER", "")
    MILVUS_PASSWORD: str = os.getenv("MILVUS_PASSWORD", "")
    MILVUS_COLLECTION: str = os.getenv("MILVUS_COLLECTION", "ashes_knowledge")
    
    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "ashes_default_pass")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Discord settings
    DISCORD_BOT_ENABLED: bool = os.getenv("DISCORD_BOT_ENABLED", "True").lower() == "true"
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_COMMAND_PREFIX: str = os.getenv("DISCORD_COMMAND_PREFIX", "!ashes")
    
    # Game data settings
    DATA_REFRESH_INTERVAL: int = int(os.getenv("DATA_REFRESH_INTERVAL", "86400"))  # 24 hours
    GAME_SERVERS: List[str] = os.getenv("GAME_SERVERS", "Alpha-1,Alpha-2").split(",")
    
    # Vector search settings
    VECTOR_SEARCH_TOP_K: int = int(os.getenv("VECTOR_SEARCH_TOP_K", "5"))
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
