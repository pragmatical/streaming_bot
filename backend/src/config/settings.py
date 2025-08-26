from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Use Pydantic BaseSettings to parse env vars and provide defaults.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # Azure OpenAI
    azure_openai_api_key: str | None = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str | None = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: str | None = Field(default=None, env="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(
        default="2024-07-01-preview", env="AZURE_OPENAI_API_VERSION"
    )


settings = Settings()  # loads from environment and .env file
