from typing import List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Vib-O-Mat API Series 2000"

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[AnyHttpUrl], str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip().strip("\"'") for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn = "redis://localhost:6379"  # type: ignore

    # Security
    SECRET_KEY: str
    FASTAPI_SECRET: str  # Kept for backward compatibility, but we should unify
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Admin
    ADMIN_EMAILS: Union[List[EmailStr], str] = []

    @field_validator("ADMIN_EMAILS", mode="before")
    def assemble_admin_emails(cls, v: Union[str, List[str]]) -> List[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [i.strip().strip("\"'") for i in v.split(",") if i.strip()]
        return v

    # Integrations - Spotify
    SPOTIFY_CLIENT_ID: Optional[str] = None
    SPOTIFY_CLIENT_SECRET: Optional[str] = None
    SPOTIFY_REDIRECT_URI: Optional[str] = None

    # Integrations - AI
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-flash-latest"

    # Integrations - Discogs
    DISCOGS_PAT: Optional[str] = None

    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: EmailStr = "noreply@vibomat.app"

    # OAuth
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = None
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = None
    GITHUB_OAUTH_CLIENT_ID: Optional[str] = None
    GITHUB_OAUTH_CLIENT_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")


settings = Settings()  # type: ignore
