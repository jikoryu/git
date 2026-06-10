"""Application configuration via pydantic-settings.

Loads from environment variables with sensible defaults for local development.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "Price Tracker API"
    environment: str = "development"
    debug: bool = True

    # Database — defaults to SQLite for zero-dependency local dev
    database_url: str = "sqlite+aiosqlite:///./price_tracker.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # Scraping
    scrape_interval_hours: int = 4
    request_timeout_seconds: int = 30
    user_agent: str = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    )

    # Firebase
    firebase_credentials_path: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
