from pydantic_settings import BaseSettings
from typing import Optional, List
import secrets

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "ZTA API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    APP_NAME: str = "Protected Resource"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PEP Service
    PEP_HOST: str = "localhost"
    PEP_PORT: int = 5003

    # Optional settings with defaults
    DATABASE_URL: Optional[str] = None
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # This will ignore extra fields in the .env file

settings = Settings()
