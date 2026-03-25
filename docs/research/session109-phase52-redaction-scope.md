# Session 109 -- Phase 52: Secret Redaction in Logs & Tool Output

## Included Work

1. **`engine/src/agent33/security/redaction.py`** -- Core redaction module with 18 compiled regex patterns covering API keys (OpenAI, GitHub, Slack, Google, Perplexity, HuggingFace, Replicate, npm, PyPI, SendGrid, AWS, Stripe, DigitalOcean), ENV assignments, JSON secret fields, Authorization headers, PEM private keys, and database connection strings. Smart masking preserves prefix/suffix for longer tokens.

2. **`engine/src/agent33/observability/logging.py`** -- New `secret_redaction_processor` added to the structlog processor chain, inserted after the existing `pii_redaction_processor`. Reads `settings.redact_secrets_enabled` to support runtime toggling.

3. **`engine/src/agent33/agents/tool_loop.py`** -- Tool output sanitization at both the synchronous `run()` and streaming `run_streaming()` code paths. Redaction applied after truncation but before messages are appended to the conversation history.

4. **`engine/src/agent33/agents/runtime.py`** -- All three ToolLoop instantiation sites updated to pass `redact_secrets=settings.redact_secrets_enabled`.

5. **`engine/src/agent33/config.py`** -- New `redact_secrets_enabled: bool = True` setting in the Security section.

6. **`engine/tests/test_secret_redaction.py`** -- Comprehensive test suite covering: smart masking logic, all 14 API key patterns, structured secret patterns (ENV, JSON, headers, private keys), database URI redaction, disabled mode, edge cases, structlog processor integration, config integration, and false-positive resistance.

## Explicit Non-Goals

- **Runtime-configurable pattern list**: Patterns are compiled at module level for performance. Adding user-defined patterns is future work.
- **Redaction in database persistence**: This phase covers logs and tool output only, not database writes.
- **Redaction metrics/counters**: No Prometheus metrics for redaction events in this slice.
- **API route for testing redaction**: No endpoint to test redaction; test coverage is via unit tests.

## Implementation Notes

- Patterns are compiled once at module import (`re.compile` with `Final` annotation) for zero per-call overhead.
- The structlog processor uses a deferred import of `settings` to avoid circular imports during module loading.
- The ToolLoop integration uses the keyword-only `redact_secrets` parameter with a `True` default, so existing callsites (including the reasoning route) work without modification.
- The `_mask_token` function uses an 18-character threshold: tokens shorter than 18 chars are fully masked (`***`), longer tokens show `first6...last4`.

## Validation Plan

1. `ruff check src/ tests/` -- zero lint errors
2. `ruff format --check src/ tests/` -- formatting clean
3. `mypy src --config-file pyproject.toml` -- strict type checking passes
4. `pytest tests/test_secret_redaction.py -v` -- all new tests pass
5. `pytest tests/ -x -q` -- full suite remains green
