"""Application settings loaded from environment / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./scrapes.db"
    request_timeout_seconds: float = 15.0
    max_items: int = 100
    web_host: str = "0.0.0.0"
    web_port: int = 8000


settings = Settings()
