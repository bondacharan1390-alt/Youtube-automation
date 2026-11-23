import os
import secrets
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow")
    
    PROJECT_NAME: str = "AI YouTube Automation Studio"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    APP_ENV: str = os.getenv("APP_ENV", "development")
    
    # Secret Key for JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY") or (
        secrets.token_urlsafe(48) if os.getenv("APP_ENV", "development").lower() not in ("production", "prod") else ""
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Fernet key for encrypting provider API keys and YouTube tokens
    FERNET_KEY: str = os.getenv("FERNET_KEY", Fernet.generate_key().decode())
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./youtube_studio.db")
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000",
    ).split(",")

    # Higgsfield REST API (server-side only; credentials are stored encrypted per provider)
    HIGGSFIELD_API_BASE_URL: str = os.getenv("HIGGSFIELD_API_BASE_URL", "https://api.higgsfield.ai")
    HIGGSFIELD_TIMEOUT_SECONDS: float = float(os.getenv("HIGGSFIELD_TIMEOUT_SECONDS", "30"))
    HIGGSFIELD_POLL_INTERVAL_SECONDS: float = float(os.getenv("HIGGSFIELD_POLL_INTERVAL_SECONDS", "2"))
    HIGGSFIELD_MAX_POLL_SECONDS: int = int(os.getenv("HIGGSFIELD_MAX_POLL_SECONDS", "600"))

settings = Settings()
