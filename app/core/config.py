from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App settings
    PROJECT_NAME: str = "URL Shortener"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    DATABASE_URL: str = ""
    
    REDIS_URL: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Singleton pattern - crear UNA instancia
settings = Settings()