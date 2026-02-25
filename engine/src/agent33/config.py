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

    # Local "Heretic" & Ultra-Sparse Orchestration
    # (optimized for single RTX 3090 - 24GB VRAM).
    # Top targets: Qwen3-Coder-Next (via llama.cpp tensor offloading),
    # Qwen2.5-Coder-32B-Instruct-abliterated, Lexi-3.0.
    local_orchestration_model: str = "qwen3-coder-next"
    local_orchestration_format: str = "gguf_q4_k_m"
    local_orchestration_engine: str = "llama.cpp"

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
    auth_bootstrap_admin_password: SecretStr = SecretStr("")
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
    elevenlabs_api_key: SecretStr = SecretStr("")

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
    agent_effort_routing_enabled: bool = False
    agent_effort_default: str = "medium"
    agent_effort_low_model: str = ""
    agent_effort_medium_model: str = ""
    agent_effort_high_model: str = ""
    agent_effort_low_token_multiplier: float = 1.0
    agent_effort_medium_token_multiplier: float = 1.0
    agent_effort_high_token_multiplier: float = 1.0
    agent_effort_heuristic_enabled: bool = True
    agent_effort_policy_tenant: str = ""  # JSON object: {"tenant-id": "low|medium|high"}
    agent_effort_policy_domain: str = ""  # JSON object: {"domain": "low|medium|high"}
    agent_effort_policy_tenant_domain: str = (
        ""  # JSON object: {"tenant-id|domain": "low|medium|high"}
    )
    agent_effort_cost_per_1k_tokens: float = 0.0
    observability_effort_alerts_enabled: bool = True
    observability_effort_alert_high_effort_count_threshold: int = 25
    observability_effort_alert_high_cost_usd_threshold: float = 5.0
    observability_effort_alert_high_token_budget_threshold: int = 8000

    # Skills
    skill_definitions_dir: str = "skills"
    skill_max_instructions_chars: int = 16000
    skillsbench_skill_matcher_enabled: bool = False
    skillsbench_skill_matcher_model: str = "llama3.2"
    skillsbench_skill_matcher_top_k: int = 20
    skillsbench_skill_matcher_skip_llm_below: int = 3
    skillsbench_context_manager_enabled: bool = True

    # MCP (Model Context Protocol) servers
    mcp_servers: str = ""  # Comma-separated server URLs
    mcp_timeout_seconds: float = 30.0
    mcp_auto_discover: bool = True
    connector_boundary_enabled: bool = False
    connector_policy_pack: str = "default"
    connector_governance_blocked_connectors: str = ""  # comma-separated
    connector_governance_blocked_operations: str = ""  # comma-separated
    connector_circuit_breaker_enabled: bool = False
    connector_circuit_failure_threshold: int = 3
    connector_circuit_recovery_seconds: float = 30.0
    connector_circuit_half_open_successes: int = 1

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
    autonomy_max_stretch_hours: int = 24
    autonomy_allow_security_recon: bool = True
    offline_mode: bool = False
    intake_output_dir: str = "docs/research/repo_dossiers"
    analysis_template_dir: str = "docs/research/templates"

    # Continuous improvement learning signals (Phase 31)
    improvement_learning_enabled: bool = False
    improvement_learning_summary_default_limit: int = 50
    improvement_learning_auto_intake_enabled: bool = False
    improvement_learning_auto_intake_min_severity: str = "high"
    improvement_learning_auto_intake_max_items: int = 3
    improvement_learning_persistence_backend: str = "memory"  # memory | file | db
    improvement_learning_persistence_path: str = (
        "var/improvement_learning_signals.json"
    )
    improvement_learning_persistence_db_path: str = (
        "var/improvement_learning_signals.sqlite3"
    )
    improvement_learning_persistence_migrate_on_start: bool = False
    improvement_learning_file_corruption_behavior: str = "reset"  # reset | raise

    def check_production_secrets(self) -> list[str]:
        """Check for default secrets.  Raises in production mode."""
        warnings = []
        if self.api_secret_key.get_secret_value() == "change-me-in-production":
            warnings.append("api_secret_key is using the default value")
        if self.jwt_secret.get_secret_value() == "change-me-in-production":
            warnings.append("jwt_secret is using the default value")
        if self.auth_bootstrap_enabled:
            warnings.append("auth_bootstrap_enabled is true")
        bootstrap_password = self.auth_bootstrap_admin_password.get_secret_value()
        if self.auth_bootstrap_enabled and bootstrap_password in {"", "admin"}:
            warnings.append("auth_bootstrap_admin_password is empty or using default value")
        if warnings and self.environment == "production":
            raise RuntimeError(
                "FATAL: Default secrets in production mode. "
                f"Override via environment variables: {', '.join(warnings)}"
            )
        return warnings


settings = Settings()
