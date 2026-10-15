# Vector Foundry - Backend Configuration
"""Application settings management using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Vector Foundry"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/vector_foundry.db"
    database_echo: bool = False

    # Authentication (Keycloak OIDC)
    keycloak_server_url: str = "http://localhost:8080"
    keycloak_realm: str = "vector-foundry"
    keycloak_client_id: str = "vector-foundry-frontend"
    keycloak_client_secret: str = ""
    keycloak_admin_user: str = "admin"
    keycloak_admin_password: str = ""

    # OIDC Discovery (operator-configured)
    oidc_discovery_url: str = ""
    oidc_issuer: str = ""
    oidc_audience: str = "vector-foundry-api"
    oidc_jwks_cache_ttl: int = 3600

    # Demo mode (explicitly enabled, refuses in production)
    demo_mode: bool = False

    # LLM Providers (optional, non-secret settings)
    llm_provider: str = "openai-compatible"  # openai-compatible, anthropic, gemini, ollama
    llm_model: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_timeout: float = 30.0
    llm_max_retries: int = 2

    # GitHub API (for issue ingestion)
    github_token: str = ""
    github_api_url: str = "https://api.github.com"
    github_repo_owner: str = "rust-lang"
    github_repo_name: str = "rust"

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # Security
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 30

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def effective_oidc_discovery_url(self) -> str:
        if self.oidc_discovery_url:
            return self.oidc_discovery_url
        return f"{self.keycloak_server_url}/realms/{self.keycloak_realm}/.well-known/openid-configuration"

    @property
    def effective_oidc_issuer(self) -> str:
        if self.oidc_issuer:
            return self.oidc_issuer
        return f"{self.keycloak_server_url}/realms/{self.keycloak_realm}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()