# S44: Embedding Model Hot-Swap

## Status: Implemented (Session 90)

## Problem

Changing the embedding model requires a full application restart. In production
environments, operators need to switch models at runtime for A/B testing, model
upgrades, and provider failover without downtime.

## Solution

An `EmbeddingSwapManager` that provides:

- **Runtime model switching** without application restart
- **Compatibility validation** before swap (dimension mismatch warnings)
- **Model metadata tracking** (dimensions, provider, version, max_tokens)
- **Swap history** with bounded audit log (configurable max_history)
- **Rollback support** to revert to the previous model
- **Cache invalidation** on model change to prevent stale embeddings
- **Thread-safe state management** via asyncio.Lock
- **Admin API endpoints** for management

## Architecture

```
EmbeddingSwapManager
  |-- _current_model: EmbeddingModelInfo (active model)
  |-- _models: dict[str, EmbeddingModelInfo] (registry)
  |-- _history: deque[SwapRecord] (bounded audit log)
  |-- _lock: asyncio.Lock (concurrency safety)
  |-- set_embedding_cache() -> wires cache for invalidation
  |-- set_embedding_provider() -> wires provider for model update
```

### API Endpoints

| Method | Path                    | Description              |
|--------|-------------------------|--------------------------|
| GET    | /v1/embeddings/current  | Current model info       |
| GET    | /v1/embeddings/models   | List registered models   |
| POST   | /v1/embeddings/models   | Register new model       |
| POST   | /v1/embeddings/swap     | Execute model swap       |
| POST   | /v1/embeddings/rollback | Rollback last swap       |
| GET    | /v1/embeddings/history  | Swap audit history       |
| GET    | /v1/embeddings/stats    | Usage statistics         |

All endpoints require `admin` scope.

### Config

```
embedding_hot_swap_enabled: bool = True
embedding_default_model: str = "default"
```

## Files

- `engine/src/agent33/memory/embedding_swap.py` -- Core manager
- `engine/src/agent33/api/routes/embedding_swap.py` -- API endpoints
- `engine/src/agent33/config.py` -- Config additions
- `engine/src/agent33/main.py` -- Lifespan wiring
- `engine/tests/test_embedding_swap.py` -- Test suite

## Swap Lifecycle

1. Operator registers target model via POST /v1/embeddings/models
2. Operator validates swap via internal validate_swap() (called by swap endpoint)
3. POST /v1/embeddings/swap executes the swap:
   a. Updates current model reference
   b. Updates provider model name
   c. Invalidates embedding cache
   d. Records swap in bounded history
4. If problems arise, POST /v1/embeddings/rollback reverts to previous model

## Design Decisions

- **Dimension mismatch is a warning, not a blocker**: Different-dimension models
  can coexist (operator may re-index), but the validation reports the mismatch.
- **Bounded history**: Uses `collections.deque(maxlen=N)` to prevent unbounded
  memory growth in long-running deployments.
- **Provider model update**: Directly mutates `_model` on the provider to avoid
  needing to reconstruct the HTTP client.
- **Cache invalidation on every swap**: All cached embeddings are from the old
  model and must be discarded.
