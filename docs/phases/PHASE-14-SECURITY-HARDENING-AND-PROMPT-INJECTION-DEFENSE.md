# Phase 14: Security Hardening & Prompt Injection Defense

## Overview
- **Phase**: 14 of 20
- **Category**: Security
- **Status**: Complete
- **Tests**: 59 new tests (337 total)

## Objectives
- Codify sandboxing and approval gates for risky actions.
- Define prompt injection defenses and content sanitization.
- Standardize secrets handling and network allowlists.
- Implement ZeroClaw-inspired security parity features.

## Implemented Items

| # | Item | Source | Files Changed |
|---|------|--------|---------------|
| 1 | Multi-segment command validation | ZeroClaw `security/policy.rs` | `shell.py`, `governance.py` |
| 2 | Autonomy levels (ReadOnly/Supervised/Full) | ZeroClaw `security/policy.rs` | `definition.py`, `governance.py`, `runtime.py` |
| 3 | Rate limiting on tool execution | ZeroClaw `ActionTracker` | `governance.py`, `config.py` |
| 4 | Path traversal hardening | ZeroClaw path validation | `file_ops.py` |
| 5 | `tenant_id` in TokenPayload | Original Phase 14 | `auth.py` |
| 6 | Session ownership model | Original Phase 14 | `memory_search.py` |
| 7 | `run_command.py` env preserves PATH on Windows | Original Phase 14 | `run_command.py` |
| 8 | API key expiration support | Original Phase 14 | `auth.py` |
| 9 | Deny-first permission evaluation | Original Phase 14 | `permissions.py` |
| 10 | Pairing brute-force lockout | ZeroClaw `security/pairing.rs` | `pairing.py` |
| 11 | Request size limits | ZeroClaw gateway | `main.py`, `config.py` |
| 12 | `SecretStr` for sensitive config | Original Phase 14 | `config.py`, `auth.py`, `agents.py`, `reader.py`, `jina_embeddings.py` |

## Previously Completed (PRs #2-#5)
- [x] `require_scope()` wired into all routes (PR #5)
- [x] SHA-256 → PBKDF2-HMAC-SHA256 password hashing (PR #5)
- [x] Default secrets enforcement in production mode (PR #5)
- [x] NATS port bound to localhost (PR #2)
- [x] CORS methods/headers restricted (PR #2)
- [x] `/docs` auth bypass prefix fixed (PR #2)
- [x] Ownership-aware API key revocation (PR #5)
- [x] Governance constraints injected into prompts (PR #4)
- [x] Safety guardrails in every agent prompt (PR #4)

## Acceptance Criteria
- [x] Prompt injection controls are documented with examples.
- [x] Network and command allowlist governance is explicit.
- [x] Secrets handling guidance is documented.
- [x] Multi-segment command validation blocks pipe/chain injection.
- [x] Autonomy levels restrict tool access per-agent.
- [x] Rate limiting prevents tool abuse with sliding window + burst control.
- [x] Path traversal attacks blocked (null bytes, `..`, symlink escape).
- [x] JWT and API keys carry `tenant_id` for multi-tenant isolation.
- [x] Session ownership prevents cross-user observation access.
- [x] `run_command` preserves PATH environment on Windows.
- [x] API keys support time-based expiration.
- [x] Deny rules evaluated before allow rules in permission system.
- [x] Pairing codes enforce brute-force lockout after 5 failures.
- [x] Request body size limit middleware (configurable, default 10MB).
- [x] Sensitive config uses `SecretStr` to prevent accidental logging.

## Key Artifacts
- `core/orchestrator/SECURITY_HARDENING.md` - Prompt injection defense, sandbox approvals, secrets handling
- `core/packs/policy-pack-v1/RISK_TRIGGERS.md` - Updated with prompt injection and sandbox triggers
- `engine/tests/test_phase14_security.py` - 59 comprehensive tests covering all 12 items

## Dependencies
- Phase 13

## Blocks
- Phase 15
