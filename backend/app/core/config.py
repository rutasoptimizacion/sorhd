"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # Application Info
    APP_NAME: str = "SOR-HD API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://sorhd_user:sorhd_password@localhost:5432/sorhd"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # External APIs
    GOOGLE_MAPS_API_KEY: str = ""
    OSRM_ENDPOINT: str = "http://router.project-osrm.org"

    # Twilio SMS
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
