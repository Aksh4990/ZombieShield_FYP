from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://zombieshield:zombieshield@db:5432/zombieshield"
    backend_cors_origins: str = "http://localhost:5173,http://localhost:8080"
    discovery_git_root: str = "./discovery-repositories"
    lifecycle_activity_window_days: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
