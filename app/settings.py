


from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/url_shortener")

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()
