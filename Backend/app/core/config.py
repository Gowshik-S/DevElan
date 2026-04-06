from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _backend_root = Path(__file__).resolve().parents[2]

    model_config = SettingsConfigDict(
        env_file=str(_backend_root / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = "DevEla Backend"
    project_version: str = "0.2.0"

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/devela",
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(default="change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=200, alias="MAX_UPLOAD_SIZE_MB")

    mail_client_id: str | None = Field(default=None, alias="CLIENT_ID")
    mail_client_secret: str | None = Field(default=None, alias="CLIENT_SECRET")
    mail_tenant_id: str | None = Field(default=None, alias="TENANT_ID")
    mail_sender_user: str = Field(default="DevElan@ettalabs.in", alias="MAIL_SENDER_USER")
    mail_request_timeout_seconds: int = Field(default=20, alias="MAIL_REQUEST_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
