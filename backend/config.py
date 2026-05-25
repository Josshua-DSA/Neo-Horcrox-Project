from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Neo-Horcrox Supply Chain API"
    DEBUG: bool = False

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Artifacts paths
    ARTIFACTS_DIR: str = "backend/artifacts"

    # Logging
    LOG_LEVEL: str = "INFO"

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/neo_horcrox"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()