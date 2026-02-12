# Research: Security Gap Analysis — 2026-02-12

## Existing Protections

### Authentication & Authorization ✅
- JWT auth with HS256, configurable expiry (60 min default)
- API key generation/validation with SHA-256 hashing (`a33_` prefix)
- Auth middleware on all routes except `/health`, `/docs`, `/redoc`, `/openapi.json`
- Scope system: admin, agents:read/write/invoke, workflows:read/write/execute, tools:execute

### Prompt Injection Defense ✅ (built, NOT integrated)
- `engine/src/agent33/security/injection.py` — detects system overrides, delimiter injection, instruction overrides, base64 payloads
- **CRITICAL**: `scan_input()` is never called in any API route

### Network Controls ✅
- `DomainAllowlist` and `PathAllowlist` in `engine/src/agent33/security/allowlists.py`
- Used by web_fetch and tool governance

### Encryption & Secrets ✅
- AES-256-GCM encryption in `security/encryption.py`
- Credential vault in `security/vault.py`

## Critical Gaps

### 1. IDOR Vulnerabilities (8 endpoints) — 🔴 CRITICAL
| Endpoint | File | Issue |
|----------|------|-------|
| GET /v1/memory/sessions/{id}/observations | memory_search.py:53-76 | No ownership check |
| POST /v1/memory/sessions/{id}/summarize | memory_search.py:79-98 | No ownership check |
| GET /v1/agents/by-id/{id} | agents.py:115-127 | No access control |
| GET /v1/agents/{name} | agents.py:138-147 | No access control |
| POST /v1/agents/{name}/invoke | agents.py:160-190 | No ownership check |
| GET /v1/workflows/{name} | workflows.py:68-74 | No access control |
| POST /v1/workflows/{name}/execute | workflows.py:102-132 | No ownership check |
| DELETE /v1/auth/api-keys/{key_id} | auth.py:79-84 | No ownership check |

### 2. Prompt Injection — 🔴 CRITICAL (0% integration)
- chat.py:30-72 — no `scan_input()` on messages
- agents.py:160-190 — no `scan_input()` on body.inputs
- workflows.py:102-132 — no `scan_input()` on request.inputs
- webhooks.py:28-141 — no scanning of external payloads

### 3. SSRF — 🟡 MEDIUM
- web_fetch.py:46 — domain allowlist check skipped if allowlist is empty (`if context.domain_allowlist and ...`)
- reader.py:50-141 — no domain allowlist enforcement at all

### 4. Configuration Security — 🔴 CRITICAL
- config.py:16,32 — hardcoded `"change-me-in-production"` secrets
- main.py:241 — CORS `allow_origins=["*"]`

### 5. Approval Gates — 🔴 NOT IMPLEMENTED
- Documentation exists in SECURITY_HARDENING.md but zero code implementation
- Missing: AG-01 through AG-05 approval gates

### 6. XSS — 🟢 LOW
- Most endpoints return JSON (auto-escaped)
- Dashboard template uses `escapeHtml()`
- Minor: error messages may reflect unescaped user input

## Fix Priorities
1. Integrate prompt injection scanning into all API routes
2. Add IDOR protections (ownership validation)
3. Harden SSRF (mandatory domain allowlists)
4. Fix hardcoded secrets / CORS wildcard
5. Sanitize error message output
