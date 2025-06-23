import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings.
    """
    # Base settings
    PROJECT_NAME: str = "Candidate Management API"
    PROJECT_DESCRIPTION: str = "Simple API for managing candidates in a recruitment process."
    PROJECT_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # JWT settings
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # PostgreSQL settings
    DB_SERVER: str = os.getenv("DB_SERVER", "localhost")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "backend_service")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        SQLAlchemy database URI.

        :return: URI for PostgreSQL database.
        :rtype: str
        """
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def SQLALCHEMY_ASYNC_DATABASE_URI(self) -> str:
        # asyncpg driver, used by your FastAPI app
        return self.SQLALCHEMY_DATABASE_URI.replace(
            "postgresql://", "postgresql+asyncpg://"
        )

    # CORS settings
    CORS_ORIGINS: List[str] = [
        origin.strip() for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:8000,http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origin.strip()
    ]
    
    class Config:
        case_sensitive = True


# Create settings instance
settings = Settings()

# log settings for debugging
if settings.DEBUG:
    print("Settings loaded:")
    for key, value in settings.model_dump().items():
        print(f"{key}: {value}")
