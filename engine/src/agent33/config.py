"""Application configuration via environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """AGENT-33 engine settings loaded from environment."""

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}

    # API
    api_port: int = 8000
    api_log_level: str = "info"
    api_secret_key: str = "change-me-in-production"

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
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    encryption_key: str = ""

    # SearXNG
    searxng_url: str = "http://searxng:8080"

    # Optional cloud LLM
    openai_api_key: str = ""
    openai_base_url: str = ""

    # AirLLM (layer-sharded large model inference)
    airllm_enabled: bool = False
    airllm_model_path: str = ""
    airllm_device: str = "cuda:0"
    airllm_compression: str = ""  # "4bit" | "8bit" | ""
    airllm_max_seq_len: int = 2048
    airllm_prefetch: bool = True

    # Jina
    jina_api_key: str = ""
    jina_reader_url: str = "https://r.jina.ai"

    # Embeddings
    embedding_provider: str = "ollama"  # "ollama" | "jina"

    # Training (self-evolving loop)
    training_enabled: bool = False
    training_optimize_interval: int = 100
    training_idle_optimize_seconds: int = 300
    training_min_rollouts: int = 10
    training_eval_model: str = ""


settings = Settings()
