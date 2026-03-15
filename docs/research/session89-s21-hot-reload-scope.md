# S21: Phase 32 Hot-Reload Polish

## Scope

Add fleet-level hot-reload capabilities to the MCP proxy subsystem, enabling
runtime configuration changes without full application restart.

## Deliverables

### 1. Fleet restart endpoint (`POST /v1/mcp/proxy/restart`)

Admin-scoped endpoint that restarts ALL enabled proxy servers. Returns
per-server results with success/failure breakdown.

### 2. Config reload endpoint (`POST /v1/mcp/proxy/reload-config`)

Admin-scoped endpoint that re-reads `mcp_proxy_config_path`, validates the new
config, computes a diff against running servers, and applies changes: add new
servers, restart changed servers, stop removed servers. Invalid config is
rejected without affecting running servers.

### 3. Config validation endpoint (`POST /v1/mcp/proxy/validate-config`)

Admin-scoped dry-run endpoint. Reads and validates the config file, returns
what would change without applying.

### 4. Single-server restart diagnostics

Enhance `POST /v1/mcp/proxy/servers/{server_id}/restart` response with
`restart_duration_ms` and `previous_state` fields.

### 5. ProxyManager `reload_config()` method

Core method that diffs current servers vs new config, adds new servers, removes
old servers, restarts servers whose config changed, and returns structured
results.

### 6. ProxyManager `diff_config()` method

Pure diff computation (no side effects). Returns `to_add`, `to_remove`,
`to_restart`, and `unchanged` lists.

## Files Modified

- `engine/src/agent33/mcp_server/proxy_manager.py` -- `reload_config()`, `diff_config()`
- `engine/src/agent33/api/routes/mcp_proxy.py` -- three new endpoints + restart diagnostics
- `engine/tests/test_mcp_proxy_hot_reload.py` -- new test file (11 test cases)
- `docs/research/session89-s21-hot-reload-scope.md` -- this file

## Constraints

- No new external dependencies
- Must not regress existing proxy tests
- Config file path from `settings.mcp_proxy_config_path`
