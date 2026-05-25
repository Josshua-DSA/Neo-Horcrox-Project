from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Neo-Horcrox Supply Chain API"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["*"]
    ARTIFACTS_DIR: str = "backend/artifacts"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/neo_horcrox"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()