"""Application configuration via environment variables."""

from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """AGENT-33 engine settings loaded from environment."""

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}

    # API
    api_port: int = 8000
    api_log_level: str = "info"
    api_secret_key: SecretStr = SecretStr("change-me-in-production")
    cors_allowed_origins: str = ""  # comma-separated; empty = deny all origins (secure default)
    max_request_size_bytes: int = 10 * 1024 * 1024  # 10 MB default

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_default_model: str = "llama3.2"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://agent33:agent33@postgres:5432/agent33"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # NATS
    nats_url: str = "nats://nats:4222"

    # Security
    jwt_secret: SecretStr = SecretStr("change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    encryption_key: SecretStr = SecretStr("")

    # Rate limiting (per-tenant, sliding window)
    rate_limit_per_minute: int = 60  # max tool executions per minute
    rate_limit_burst: int = 10  # max burst above per-minute rate

    # SearXNG
    searxng_url: str = "http://searxng:8080"

    # Optional cloud LLM
    openai_api_key: SecretStr = SecretStr("")
    openai_base_url: str = ""

    # AirLLM (layer-sharded large model inference)
    airllm_enabled: bool = False
    airllm_model_path: str = ""
    airllm_device: str = "cuda:0"
    airllm_compression: str = ""  # "4bit" | "8bit" | ""
    airllm_max_seq_len: int = 2048
    airllm_prefetch: bool = True

    # Jina
    jina_api_key: SecretStr = SecretStr("")
    jina_reader_url: str = "https://r.jina.ai"

    # Embeddings
    embedding_provider: str = "ollama"  # "ollama" | "jina"

    # HTTP client pool settings
    http_max_connections: int = 20
    http_max_keepalive: int = 10
    embedding_batch_size: int = 100

    # Training (self-evolving loop)
    training_enabled: bool = True
    training_optimize_interval: int = 100
    training_idle_optimize_seconds: int = 300
    training_min_rollouts: int = 10
    training_eval_model: str = ""

    # Agent definitions
    agent_definitions_dir: str = "agent-definitions"

    # Environment
    environment: str = "development"

    # Self-improvement
    self_improve_enabled: bool = True
    self_improve_scope: str = "prompts,workflows,templates"
    self_improve_require_approval: bool = True
    offline_mode: bool = False
    intake_output_dir: str = "docs/research/repo_dossiers"
    analysis_template_dir: str = "docs/research/templates"

    def check_production_secrets(self) -> list[str]:
        """Check for default secrets.  Raises in production mode."""
        warnings = []
        if self.api_secret_key.get_secret_value() == "change-me-in-production":
            warnings.append("api_secret_key is using the default value")
        if self.jwt_secret.get_secret_value() == "change-me-in-production":
            warnings.append("jwt_secret is using the default value")
        if warnings and self.environment == "production":
            raise RuntimeError(
                "FATAL: Default secrets in production mode. "
                f"Override via environment variables: {', '.join(warnings)}"
            )
        return warnings


settings = Settings()
