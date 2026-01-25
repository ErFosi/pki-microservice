"""
Configuración del servicio CA
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/pki_db"
    
    # Security
    MASTER_KEY: str  # Requerido - No tiene valor por defecto por seguridad
    
    # Application
    APP_NAME: str = "CA Service"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la configuración de la aplicación"""
    return Settings()
