# Research: Security Gap Analysis — 2026-02-12

## Existing Protections

### Authentication & Authorization ✅
- JWT auth with HS256, configurable expiry (60 min default)
- API key generation/validation with SHA-256 hashing (`a33_` prefix)
- Auth middleware on all routes except `/health`, `/docs`, `/redoc`, `/openapi.json`
- Scope system: admin, agents:read/write/invoke, workflows:read/write/execute, tools:execute

### Prompt Injection Defense ✅ (mostly integrated)
- `engine/src/agent33/security/injection.py` — detects system overrides, delimiter injection, instruction overrides, base64 payloads
- Wave 12 reality check: chat, agent invoke, workflow schedule/execute, and webhooks now scan user-controlled inputs. Route-level approval gates remain a follow-up.

### Network Controls ✅
- `DomainAllowlist` and `PathAllowlist` in `engine/src/agent33/security/allowlists.py`
- Used by web_fetch and tool governance

### Encryption & Secrets ✅
- AES-256-GCM encryption in `security/encryption.py`
- Credential vault in `security/vault.py`

## Critical Gaps

### 1. IDOR Vulnerabilities (8 endpoints) — ✅ CLOSED / SUPERSEDED
Wave 12 route audit found these historical findings are closed or superseded by scope checks, global-definition semantics, subject ownership checks, or tenant execution-history filtering.

| Endpoint | File | Current status |
|----------|------|-------|
| GET /v1/memory/sessions/{id}/observations | memory_search.py | Subject ownership enforced |
| POST /v1/memory/sessions/{id}/summarize | memory_search.py | Subject ownership enforced |
| GET /v1/agents/by-id/{id} | agents.py | Scope-protected global definition |
| GET /v1/agents/{name} | agents.py | Scope-protected global definition |
| POST /v1/agents/{name}/invoke | agents.py | Scope-protected, tenant context captured, inputs scanned |
| GET /v1/workflows/{name} | workflows.py | Scope-protected global definition |
| POST /v1/workflows/{name}/execute | workflows.py | Scope-protected, tenant execution history captured, inputs scanned |
| DELETE /v1/auth/api-keys/{key_id} | auth.py | Non-admin ownership enforced |

### 2. Prompt Injection — ✅ INTEGRATED, with route-level follow-up
- chat.py — scans message content
- agents.py — scans invoke inputs recursively
- workflows.py — scans schedule and execute inputs recursively
- webhooks.py — scans external messaging payloads recursively
- remaining follow-up: add explicit approval-token gates for sensitive route operations

### 3. SSRF — ✅ CLOSED
- web_fetch/web_research paths pass configured domain allowlists into governed fetch enforcement
- reader.py denies requests when the domain allowlist is empty and enforces allowed domains

### 4. Configuration Security — ✅ CLOSED / DEVELOPMENT-SAFE DEFAULTS
- config still has development defaults, but production startup rejects default secrets and `check_production_secrets()` reports unsafe settings
- CORS defaults to an empty origin list rather than wildcard allow-all

### 5. Approval Gates — 🟡 FOLLOW-UP
- approval token infrastructure exists and is persisted, but sensitive route operations still need explicit approval-token gates
- Wave 12 follow-up should prioritize destructive or privilege-expanding operations such as agent deletion/update, workflow creation, and admin API-key creation

### 6. XSS — 🟢 LOW
- Most endpoints return JSON (auto-escaped)
- Dashboard template uses `escapeHtml()`
- Minor: error messages may reflect unescaped user input

## Fix Priorities
1. Add route-level approval-token gates for sensitive operations.
2. Keep regression tests for prompt-injection scanning on chat, agent invoke, workflow execute/schedule, and webhooks.
3. Keep regression tests for memory/auth/workflow tenant or subject isolation.
4. Continue sanitizing reflected error output and logs.
