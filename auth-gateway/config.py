"""
Configuración del Auth Gateway
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CA Service URL (interno en Docker)
    CA_SERVICE_URL: str = "http://ca-service:8001"
    
    # Application
    APP_NAME: str = "Auth Gateway"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la configuración de la aplicación (singleton)"""
    return Settings()
