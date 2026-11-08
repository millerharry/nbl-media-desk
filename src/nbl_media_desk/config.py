"""Runtime settings, read from environment variables (see `.env.example`)."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration lives here. Secrets are never logged or committed."""

    model_config = SettingsConfigDict(
        env_prefix="NBL_DESK_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    anthropic_api_key: SecretStr | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    writer_model: str = "claude-opus-5-5"
    extractor_model: str = "claude-haiku-5-5"
    judge_model: str = "claude-opus-5-5"
    cache_dir: str = ".cache"
    run_db_path: str = ".cache/runs.sqlite3"
    max_repair_rounds: int = Field(default=2, ge=0, le=5)
    http_user_agent: str = "nbl-media-desk/0.0 (+https://github.com/millerharry/nbl-media-desk)"
