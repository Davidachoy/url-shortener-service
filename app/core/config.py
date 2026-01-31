from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    # App settings
    PROJECT_NAME: str = "URL Shortener"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    SHORT_URL_BASE: str = "http://localhost:8000"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str
    REDIS_URL: str

    #redis
    REDIS_MAX_CONNECTIONS: int = 10
    CACHE_TTL_SECONDS: int = 86400  # 24 horas
    
# Singleton pattern - crear UNA instancia
settings = Settings()