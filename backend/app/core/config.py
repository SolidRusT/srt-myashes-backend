"""
Configuration settings for MyAshes.ai backend.

This backend provides product-specific services (builds, feedback, analytics).
RAG/vector search is handled by srt-data-layer.
"""
import os
from typing import List, Optional, Dict, Any, Union
from pydantic import field_validator, model_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API configuration
    API_V1_STR: str = "/api/v1"

    # CORS configuration - must include myashes.ai and localhost for dev
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://myashes.ai",
        "https://www.myashes.ai",
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database configuration (PostgreSQL via platform CNPG)
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "myashes")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def assemble_db_connection(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("SQLALCHEMY_DATABASE_URI"):
            return values

        user = values.get("POSTGRES_USER", "postgres")
        password = values.get("POSTGRES_PASSWORD", "postgres")
        host = values.get("POSTGRES_HOST", "localhost")
        port = values.get("POSTGRES_PORT", "5432")
        db = values.get("POSTGRES_DB", "myashes")

        values["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        return values

    # Redis/Valkey configuration (for caching + rate limiting)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Application configuration
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true" or os.getenv("ENV", "development") == "development"
    APP_NAME: str = "MyAshes.ai"
    WEBSITE_URL: str = os.getenv("WEBSITE_URL", "https://myashes.ai")

    # Session configuration
    SESSION_COOKIE_NAME: str = "myashes_session"
    SESSION_EXPIRE_DAYS: int = 30

    # PAM Platform configuration (authentication)
    # In K8s: http://pam-platform.srt-pam-platform.svc.cluster.local:80
    # Public: https://console.solidrust.ai
    PAM_PLATFORM_URL: str = os.getenv(
        "PAM_PLATFORM_URL",
        "http://pam-platform.srt-pam-platform.svc.cluster.local:80"
    )
    PAM_PLATFORM_TIMEOUT: int = int(os.getenv("PAM_PLATFORM_TIMEOUT", "5"))

    # Authentication settings
    # When True, authentication is required for write operations (create/update/delete builds)
    # When False, anonymous session-based ownership is used (backward compatible)
    AUTH_REQUIRED_FOR_WRITES: bool = os.getenv("AUTH_REQUIRED_FOR_WRITES", "false").lower() == "true"

    # Token validation cache TTL in seconds
    AUTH_TOKEN_CACHE_TTL: int = int(os.getenv("AUTH_TOKEN_CACHE_TTL", "300"))

    model_config = ConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
