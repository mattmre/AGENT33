# Phase 22 PR-03: Wiring + Verification Hardening

## Scope
- Close runtime wiring issues discovered during live stack validation.
- Add regression tests for preflight auth/CORS and dashboard rendering.
- Complete end-to-end verification evidence for local/VPS-ready operation.

## Key Changes
- Fixed preflight behavior in auth middleware:
  - `engine/src/agent33/security/middleware.py`
- Hardened dashboard template lookup across runtime contexts:
  - `engine/src/agent33/api/routes/dashboard.py`
- Added shared-Ollama compose override for cross-project Docker networking:
  - `engine/docker-compose.shared-ollama.yml`
- Added/updated tests:
  - `engine/tests/test_integration_wiring.py`
  - `engine/tests/test_idor_access_control.py`
  - `engine/tests/test_phase14_security.py`
  - `engine/tests/test_security_hardening.py`

## Validation
- Targeted security/wiring tests:
  - `pytest tests/test_auth_bootstrap.py tests/test_idor_access_control.py::TestProductionSecrets tests/test_integration_wiring.py::TestSecurityMiddleware -q`
- Full backend suite:
  - `pytest tests -q` (`1218 passed`)
- Runtime checks:
  - `http://localhost:3000` returns `200`
  - `/v1/auth/token` login with local bootstrap user succeeds
  - protected `/v1/agents/` request with token returns `200`
  - CORS preflight OPTIONS on `/v1/chat/completions` returns `200` with allow-origin
  - `/v1/dashboard/` serves template HTML (no template-missing fallback)
