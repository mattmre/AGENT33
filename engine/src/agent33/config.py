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
    auth_bootstrap_enabled: bool = False
    auth_bootstrap_admin_username: str = "admin"
    auth_bootstrap_admin_password: SecretStr = SecretStr("admin")
    auth_bootstrap_admin_scopes: str = (
        "admin,agents:read,agents:write,agents:invoke,"
        "workflows:read,workflows:write,workflows:execute,tools:execute"
    )

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

    # Embedding cache
    embedding_cache_enabled: bool = True
    embedding_cache_max_size: int = 1024

    # RAG / Hybrid search
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.3
    rag_hybrid_enabled: bool = True
    rag_vector_weight: float = 0.7  # BM25 weight = 1 - vector_weight
    rag_rrf_k: int = 60

    # Chunking
    chunk_tokens: int = 1200
    chunk_overlap_tokens: int = 100

    # BM25 warm-up
    bm25_warmup_enabled: bool = True
    bm25_warmup_max_records: int = 10_000
    bm25_warmup_page_size: int = 200

    # Training (self-evolving loop)
    training_enabled: bool = True
    training_optimize_interval: int = 100
    training_idle_optimize_seconds: int = 300
    training_min_rollouts: int = 10
    training_eval_model: str = ""

    # Agent definitions
    agent_definitions_dir: str = "agent-definitions"

    # Skills
    skill_definitions_dir: str = "skills"
    skill_max_instructions_chars: int = 16000

    # Environment
    environment: str = "development"

    # Matrix messaging adapter
    matrix_homeserver_url: str = ""  # e.g. "https://matrix.org"
    matrix_access_token: SecretStr = SecretStr("")
    matrix_user_id: str = ""  # e.g. "@agent33:matrix.org"
    matrix_room_ids: str = ""  # comma-separated room IDs (empty = all joined rooms)
    matrix_sync_timeout_ms: int = 30_000

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
        if self.auth_bootstrap_enabled:
            warnings.append("auth_bootstrap_enabled is true")
        if (
            self.auth_bootstrap_enabled
            and self.auth_bootstrap_admin_password.get_secret_value() == "admin"
        ):
            warnings.append("auth_bootstrap_admin_password is using the default value")
        if warnings and self.environment == "production":
            raise RuntimeError(
                "FATAL: Default secrets in production mode. "
                f"Override via environment variables: {', '.join(warnings)}"
            )
        return warnings


settings = Settings()
