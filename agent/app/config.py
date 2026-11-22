"""Agent settings. Everything comes from environment variables; nothing is hardcoded."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    openrouter_api_key: SecretStr
    redis_url: str
    postgres_db: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    # The agent only ever connects with the read-only role.
    postgres_readonly_user: str
    postgres_readonly_password: SecretStr

    @property
    def postgres_dsn(self) -> str:
        return (
            f"host={self.postgres_host} port={self.postgres_port} dbname={self.postgres_db} "
            f"user={self.postgres_readonly_user} "
            f"password={self.postgres_readonly_password.get_secret_value()} connect_timeout=3"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
