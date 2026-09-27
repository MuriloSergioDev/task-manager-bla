from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Stored as a raw comma-separated string (not list[str]) because pydantic-settings
    # attempts to JSON-decode list-typed env vars before any validator runs, which
    # rejects a plain "http://a,http://b" value. cors_origins exposes the parsed list.
    cors_origins_raw: str = Field(default="http://localhost:5173", validation_alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def cookie_secure(self) -> bool:
        # The `Secure` flag makes browsers refuse to send the cookie over plain
        # HTTP, which is exactly what local dev (http://localhost) is. Any other
        # environment is assumed to be served over HTTPS and gets the flag.
        return self.environment != "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
