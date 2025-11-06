from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "Board Management Tool"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Database
    database_url: str

    # Authentication
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Claude API
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-5-20250929"

    # File Storage
    upload_dir: str = "./uploads"
    storage_dir: str = "./storage"
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list[str] = [".pdf", ".docx", ".xlsx", ".xls", ".doc"]

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
